"""Solar models — Solcast irradiance/PV forecasts + tracked solar locations.

All models inherit BaseModel (id, created_at, updated_at). Locations are seeded
on first deploy; forecasts are time-series keyed by location. region_relevance
("utility_solar", "rooftop_aggregate", "hybrid_zone") explains why each location
matters for Victorian/SA solar generation and therefore energy price.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel


class SolarLocation(BaseModel):
    """A tracked solar forecast point and why it matters for energy price."""

    __tablename__ = "solar_locations"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str] = mapped_column(String(10), nullable=False)
    region_relevance: Mapped[str] = mapped_column(String(40), nullable=False)
    reference_pv_capacity_kw: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "state": self.state,
            "region_relevance": self.region_relevance,
            "reference_pv_capacity_kw": self.reference_pv_capacity_kw,
        }

    def __repr__(self) -> str:
        return f"<SolarLocation {self.name} ({self.region_relevance})>"


class SolarForecast(BaseModel):
    """A solar irradiance/PV forecast for a location at a target datetime."""

    __tablename__ = "solar_forecasts"
    __table_args__ = (
        Index("ix_solar_forecasts_location_for", "location_id", "forecast_for"),
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("solar_locations.id"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    forecast_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    forecast_period: Mapped[str] = mapped_column(
        String(20), default="30min", nullable=False
    )
    ghi_wm2: Mapped[float | None] = mapped_column(Float, nullable=True)
    dni_wm2: Mapped[float | None] = mapped_column(Float, nullable=True)
    dhi_wm2: Mapped[float | None] = mapped_column(Float, nullable=True)
    cloud_opacity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_pv_output_kw: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location_id": self.location_id,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "forecast_for": self.forecast_for.isoformat()
            if self.forecast_for
            else None,
            "forecast_period": self.forecast_period,
            "ghi_wm2": self.ghi_wm2,
            "dni_wm2": self.dni_wm2,
            "dhi_wm2": self.dhi_wm2,
            "cloud_opacity_pct": self.cloud_opacity_pct,
            "air_temp_c": self.air_temp_c,
            "estimated_pv_output_kw": self.estimated_pv_output_kw,
        }

    def __repr__(self) -> str:
        return f"<SolarForecast loc={self.location_id} {self.forecast_for}>"
