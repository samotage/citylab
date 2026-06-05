"""APScheduler service — background scheduler with sync loop."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_app = None


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler


def init_scheduler(app, config):
    """Initialize APScheduler with background scheduler."""
    global _scheduler, _app

    _app = app
    _scheduler = BackgroundScheduler(
        executors={"default": ThreadPoolExecutor(5)},
        job_defaults={"coalesce": True, "max_instances": 1},
    )
    _scheduler.start()
    logger.info("APScheduler started")

    # Initial sync
    with app.app_context():
        try:
            from citylab.services.ingestion.seed import (
                seed_battery_assets,
                seed_data_sources,
                seed_solar_locations,
                seed_weather_locations,
            )

            seed_data_sources()
            seed_weather_locations()
            seed_solar_locations()
            seed_battery_assets()
        except Exception as e:
            logger.warning(f"Initial seed failed: {e}")
        try:
            sync_jobs()
        except Exception as e:
            logger.warning(f"Initial job sync failed: {e}")
        try:
            sync_data_sources()
        except Exception as e:
            logger.warning(f"Initial data source sync failed: {e}")


def sync_jobs() -> int:
    """Sync ScheduledTask rows to APScheduler jobs."""
    global _scheduler, _app
    if not _scheduler:
        return 0

    from citylab.extensions import db
    from citylab.models.scheduled_task import ScheduledTask

    tasks = db.session.query(ScheduledTask).filter_by(is_active=True).all()
    existing_job_ids = {job.id for job in _scheduler.get_jobs()}
    task_job_ids = set()

    for task in tasks:
        job_id = f"task_{task.id}"
        task_job_ids.add(job_id)

        try:
            parts = task.cron_expression.split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
            else:
                logger.warning(f"Invalid cron for task {task.name}: {task.cron_expression}")
                continue

            if job_id in existing_job_ids:
                _scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                _scheduler.add_job(
                    _trigger_agent_job,
                    trigger=trigger,
                    id=job_id,
                    name=task.name,
                    args=[task.agent_persona, task.agent_action, task.id],
                    replace_existing=True,
                )

            # Update next_run_at
            job = _scheduler.get_job(job_id)
            if job and job.next_run_time:
                task.next_run_at = job.next_run_time
                db.session.commit()

        except Exception as e:
            logger.error(f"Failed to sync task {task.name}: {e}")

    # Remove orphaned jobs
    for job_id in existing_job_ids - task_job_ids:
        if job_id.startswith("task_"):
            _scheduler.remove_job(job_id)

    logger.info(f"Synced {len(task_job_ids)} scheduled tasks")
    return len(task_job_ids)


def sync_data_sources() -> int:
    """Sync active DataSource rows to APScheduler ingestion jobs.

    Mirrors sync_jobs(): each active DataSource gets a cron job that resolves
    its fetcher via the registry and calls run(). Updates next_fetch_at.
    """
    global _scheduler, _app
    if not _scheduler:
        return 0

    from citylab.extensions import db
    from citylab.models.data_source import DataSource

    sources = db.session.query(DataSource).filter_by(is_active=True).all()
    existing_job_ids = {job.id for job in _scheduler.get_jobs()}
    source_job_ids = set()

    for source in sources:
        job_id = f"datasource_{source.id}"
        source_job_ids.add(job_id)

        try:
            parts = (source.cron_expression or "").split()
            if len(parts) != 5:
                logger.warning(
                    f"Invalid cron for data source {source.name}: {source.cron_expression}"
                )
                continue
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )

            if job_id in existing_job_ids:
                _scheduler.reschedule_job(job_id, trigger=trigger)
            else:
                _scheduler.add_job(
                    _run_ingestion_job,
                    trigger=trigger,
                    id=job_id,
                    name=f"ingest:{source.name}",
                    args=[source.id],
                    replace_existing=True,
                )

            job = _scheduler.get_job(job_id)
            if job and job.next_run_time:
                source.next_fetch_at = job.next_run_time
                db.session.commit()

        except Exception as e:
            logger.error(f"Failed to sync data source {source.name}: {e}")

    # Remove orphaned ingestion jobs
    for job_id in existing_job_ids - source_job_ids:
        if job_id.startswith("datasource_"):
            _scheduler.remove_job(job_id)

    logger.info(f"Synced {len(source_job_ids)} data sources")
    return len(source_job_ids)


def _run_ingestion_job(source_id: int):
    """Resolve the fetcher for a DataSource and run its ingestion cycle."""
    global _app
    if not _app:
        return

    with _app.app_context():
        from citylab.extensions import db
        from citylab.models.data_source import DataSource
        from citylab.services.ingestion.registry import get_fetcher

        source = db.session.get(DataSource, source_id)
        if not source or not source.is_active:
            return

        fetcher_cls = get_fetcher(source.source_type)
        if not fetcher_cls:
            logger.error(
                f"No fetcher registered for source_type={source.source_type}"
            )
            source.last_fetch_status = "error"
            source.last_error = f"No fetcher registered for {source.source_type}"
            db.session.commit()
            return

        logger.info(f"Running ingestion for data source: {source.name}")
        try:
            result = fetcher_cls(source).run()
            logger.info(f"Ingestion {source.name}: {result}")

            if result.get("ok") and source.source_type == "opennem":
                _post_ingestion_dispatch(source)
        except Exception as e:
            logger.error(f"Ingestion failed for {source.name}: {e}")


def _post_ingestion_dispatch(source):
    """Run dispatch evaluation for all batteries in the ingested region."""
    region = (source.config or {}).get("region")
    if not region:
        return

    try:
        from citylab.services.dispatch import evaluate_region

        results = evaluate_region(region)
        if results:
            logger.info(
                "Post-ingestion dispatch for %s: %d battery decision(s)",
                region,
                len(results),
            )
    except Exception as e:
        logger.error("Post-ingestion dispatch failed for %s: %s", region, e)


def _trigger_agent_job(persona: str, action: str, task_id: int):
    """Job function that triggers an agent via Headspace."""
    global _app
    if not _app:
        return

    with _app.app_context():
        from citylab.extensions import db
        from citylab.models.scheduled_task import ScheduledTask
        from citylab.services.headspace_client import trigger_agent

        logger.info(f"Triggering agent: persona={persona}, action={action}")

        # Update last_run_at
        task = db.session.get(ScheduledTask, task_id)
        if task:
            task.last_run_at = datetime.now(timezone.utc)
            db.session.commit()

        try:
            trigger_agent(persona, action)
        except Exception as e:
            logger.error(f"Agent trigger failed: {e}")
