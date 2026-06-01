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
            sync_jobs()
        except Exception as e:
            logger.warning(f"Initial job sync failed: {e}")


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
