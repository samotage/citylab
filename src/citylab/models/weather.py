"""Weather models — BOM forecast/observation time-series + tracked locations.

All models inherit BaseModel (id, created_at, updated_at). Locations are seeded
on first deploy; forecasts and observations are time-series keyed by location.
region_relevance ("hydro_catchment", "wind_corridor", "demand_centre",
"solar_region") explains why each location matters for Victorian energy price.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel


class WeatherLocation(BaseModel):
    """A tracked forecast location and why it matters for energy price."""

    __tablename__ = "weather_locations"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    bom_station_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bom_forecast_area_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str] = mapped_column(String(10), nullable=False)
    region_relevance: Mapped[str] = mapped_column(String(40), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "bom_station_id": self.bom_station_id,
            "bom_forecast_area_id": self.bom_forecast_area_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "state": self.state,
            "region_relevance": self.region_relevance,
        }

    def __repr__(self) -> str:
        return f"<WeatherLocation {self.name} ({self.region_relevance})>"


class WeatherForecast(BaseModel):
    """A forecast for a location at a target datetime."""

    __tablename__ = "weather_forecasts"
    __table_args__ = (
        Index("ix_weather_forecasts_location_for", "location_id", "forecast_for"),
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("weather_locations.id"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    forecast_period: Mapped[str] = mapped_column(
        String(20), default="hourly", nullable=False
    )
    temperature_min_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_max_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    wind_gust_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_probability_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    cloud_cover_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location_id": self.location_id,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "forecast_for": self.forecast_for.isoformat()
            if self.forecast_for
            else None,
            "forecast_period": self.forecast_period,
            "temperature_min_c": self.temperature_min_c,
            "temperature_max_c": self.temperature_max_c,
            "temperature_c": self.temperature_c,
            "wind_speed_kmh": self.wind_speed_kmh,
            "wind_direction": self.wind_direction,
            "wind_gust_kmh": self.wind_gust_kmh,
            "rainfall_mm": self.rainfall_mm,
            "rainfall_probability_pct": self.rainfall_probability_pct,
            "cloud_cover_pct": self.cloud_cover_pct,
            "humidity_pct": self.humidity_pct,
            "weather_description": self.weather_description,
        }

    def __repr__(self) -> str:
        return f"<WeatherForecast loc={self.location_id} {self.forecast_for}>"


class WeatherObservation(BaseModel):
    """An actual observation for a location at a point in time."""

    __tablename__ = "weather_observations"
    __table_args__ = (
        Index(
            "ix_weather_observations_location_observed",
            "location_id",
            "observed_at",
        ),
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("weather_locations.id"), nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    wind_gust_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_since_9am_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location_id": self.location_id,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "temperature_c": self.temperature_c,
            "wind_speed_kmh": self.wind_speed_kmh,
            "wind_direction": self.wind_direction,
            "wind_gust_kmh": self.wind_gust_kmh,
            "rainfall_since_9am_mm": self.rainfall_since_9am_mm,
            "humidity_pct": self.humidity_pct,
            "pressure_hpa": self.pressure_hpa,
        }

    def __repr__(self) -> str:
        return f"<WeatherObservation loc={self.location_id} {self.observed_at}>"
