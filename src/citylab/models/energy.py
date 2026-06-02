"""Energy market data models — Victorian NEM time-series.

All models inherit BaseModel (id, created_at, updated_at). Indexes follow the
PRD retention section: (region, interval_start) on every time-series table,
plus a composite (region, interval_start, fuel_type) on GenerationOutput.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel


class EnergyPrice(BaseModel):
    """Spot market price for a region/interval."""

    __tablename__ = "energy_prices"
    __table_args__ = (
        Index("ix_energy_prices_region_interval", "region", "interval_start"),
    )

    region: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interval_type: Mapped[str] = mapped_column(String(10), default="5min", nullable=False)
    price_aud_mwh: Mapped[float] = mapped_column(Float, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "region": self.region,
            "interval_start": self.interval_start.isoformat()
            if self.interval_start
            else None,
            "interval_end": self.interval_end.isoformat()
            if self.interval_end
            else None,
            "interval_type": self.interval_type,
            "price_aud_mwh": self.price_aud_mwh,
        }

    def __repr__(self) -> str:
        return f"<EnergyPrice {self.region} {self.interval_start} ${self.price_aud_mwh}>"


class EnergyDemand(BaseModel):
    """Demand (load) for a region/interval."""

    __tablename__ = "energy_demand"
    __table_args__ = (
        Index("ix_energy_demand_region_interval", "region", "interval_start"),
    )

    region: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    demand_mw: Mapped[float] = mapped_column(Float, nullable=False)
    demand_type: Mapped[str] = mapped_column(String(20), default="actual", nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "region": self.region,
            "interval_start": self.interval_start.isoformat()
            if self.interval_start
            else None,
            "demand_mw": self.demand_mw,
            "demand_type": self.demand_type,
        }

    def __repr__(self) -> str:
        return f"<EnergyDemand {self.region} {self.interval_start} {self.demand_mw}MW>"


class GenerationOutput(BaseModel):
    """Generation output by fuel type for a region/interval."""

    __tablename__ = "generation_output"
    __table_args__ = (
        Index("ix_generation_output_region_interval", "region", "interval_start"),
        Index(
            "ix_generation_output_region_interval_fuel",
            "region",
            "interval_start",
            "fuel_type",
        ),
    )

    region: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(40), nullable=False)
    output_mw: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_mw: Mapped[float | None] = mapped_column(Float, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "region": self.region,
            "interval_start": self.interval_start.isoformat()
            if self.interval_start
            else None,
            "fuel_type": self.fuel_type,
            "output_mw": self.output_mw,
            "capacity_mw": self.capacity_mw,
        }

    def __repr__(self) -> str:
        return f"<GenerationOutput {self.region} {self.fuel_type} {self.output_mw}MW>"


class InterconnectorFlow(BaseModel):
    """Flow across an interconnector corridor for an interval."""

    __tablename__ = "interconnector_flows"
    __table_args__ = (
        Index(
            "ix_interconnector_flows_from_interval", "from_region", "interval_start"
        ),
        Index("ix_interconnector_flows_id_interval", "interconnector_id", "interval_start"),
    )

    interconnector_id: Mapped[str] = mapped_column(String(40), nullable=False)
    from_region: Mapped[str] = mapped_column(String(20), nullable=False)
    to_region: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    flow_mw: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_mw: Mapped[float | None] = mapped_column(Float, nullable=True)
    limit_mw: Mapped[float | None] = mapped_column(Float, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "interconnector_id": self.interconnector_id,
            "from_region": self.from_region,
            "to_region": self.to_region,
            "interval_start": self.interval_start.isoformat()
            if self.interval_start
            else None,
            "flow_mw": self.flow_mw,
            "capacity_mw": self.capacity_mw,
            "limit_mw": self.limit_mw,
        }

    def __repr__(self) -> str:
        return f"<InterconnectorFlow {self.interconnector_id} {self.flow_mw}MW>"


class GeneratorSubmission(BaseModel):
    """A generator's bid/offer band — reveals the supply curve."""

    __tablename__ = "generator_submissions"
    __table_args__ = (
        Index(
            "ix_generator_submissions_region_interval", "region", "interval_start"
        ),
    )

    station_name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(40), nullable=False)
    fuel_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bid_band: Mapped[int] = mapped_column(nullable=False)
    price_aud_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    volume_mw: Mapped[float] = mapped_column(Float, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "station_name": self.station_name,
            "unit_id": self.unit_id,
            "fuel_type": self.fuel_type,
            "region": self.region,
            "interval_start": self.interval_start.isoformat()
            if self.interval_start
            else None,
            "bid_band": self.bid_band,
            "price_aud_mwh": self.price_aud_mwh,
            "volume_mw": self.volume_mw,
        }

    def __repr__(self) -> str:
        return f"<GeneratorSubmission {self.station_name} band{self.bid_band}>"


class PriceForecast(BaseModel):
    """Forward price forecast (pre-dispatch / ST PASA)."""

    __tablename__ = "price_forecasts"
    __table_args__ = (
        Index("ix_price_forecasts_region_for", "region", "forecast_for"),
    )

    region: Mapped[str] = mapped_column(String(20), nullable=False)
    forecast_issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_aud_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    forecast_type: Mapped[str] = mapped_column(
        String(30), default="predispatch_30min", nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "region": self.region,
            "forecast_issued_at": self.forecast_issued_at.isoformat()
            if self.forecast_issued_at
            else None,
            "forecast_for": self.forecast_for.isoformat()
            if self.forecast_for
            else None,
            "price_aud_mwh": self.price_aud_mwh,
            "forecast_type": self.forecast_type,
        }

    def __repr__(self) -> str:
        return f"<PriceForecast {self.region} {self.forecast_for} ${self.price_aud_mwh}>"
