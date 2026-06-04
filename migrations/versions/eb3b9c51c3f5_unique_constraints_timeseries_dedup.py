"""unique constraints on time-series natural keys (+ dedup)

Adds UNIQUE constraints on the natural keys of all 9 time-series tables so that
ingestion can upsert via ON CONFLICT DO UPDATE (idempotent backfill/gap-fill).

Before each constraint is added, existing duplicate rows are removed — keeping
the row with the most recent updated_at per natural-key group. This handles any
duplicates left behind by the prior naive INSERT store() path.

Revision ID: eb3b9c51c3f5
Revises: f7cf7bc31bf2
Create Date: 2026-06-04

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'eb3b9c51c3f5'
down_revision = 'f7cf7bc31bf2'
branch_labels = None
depends_on = None


# (table, constraint_name, [natural key columns])
NATURAL_KEYS = [
    ("energy_prices", "uq_energy_prices_region_interval_type",
     ["region", "interval_start", "interval_type"]),
    ("energy_demand", "uq_energy_demand_region_interval_type",
     ["region", "interval_start", "demand_type"]),
    ("generation_output", "uq_generation_output_region_interval_fuel",
     ["region", "interval_start", "fuel_type"]),
    ("interconnector_flows", "uq_interconnector_flows_id_interval",
     ["interconnector_id", "interval_start"]),
    ("generator_submissions", "uq_generator_submissions_unit_interval_band",
     ["unit_id", "interval_start", "bid_band"]),
    ("price_forecasts", "uq_price_forecasts_region_issued_for_type",
     ["region", "forecast_issued_at", "forecast_for", "forecast_type"]),
    ("weather_forecasts", "uq_weather_forecasts_loc_issued_for_period",
     ["location_id", "issued_at", "forecast_for", "forecast_period"]),
    ("weather_observations", "uq_weather_observations_loc_observed",
     ["location_id", "observed_at"]),
    ("solar_forecasts", "uq_solar_forecasts_loc_issued_for_period",
     ["location_id", "issued_at", "forecast_for", "forecast_period"]),
]


def _dedup_sql(table: str, cols: list[str]) -> str:
    """Delete duplicate rows keeping the latest updated_at per natural-key group.

    Ties on updated_at are broken by the highest id.
    """
    partition = ", ".join(cols)
    return f"""
        DELETE FROM {table}
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       row_number() OVER (
                           PARTITION BY {partition}
                           ORDER BY updated_at DESC, id DESC
                       ) AS rn
                FROM {table}
            ) ranked
            WHERE ranked.rn > 1
        )
    """


def upgrade():
    for table, name, cols in NATURAL_KEYS:
        op.execute(_dedup_sql(table, cols))
        op.create_unique_constraint(name, table, cols)


def downgrade():
    for table, name, _cols in NATURAL_KEYS:
        op.drop_constraint(name, table, type_="unique")
