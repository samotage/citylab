"""Battery storage models — managed BESS assets and dispatch event log."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel


class BatteryAsset(BaseModel):
    """A managed battery energy storage system (BESS)."""

    __tablename__ = "battery_assets"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    max_power_mw: Mapped[float] = mapped_column(Float, nullable=False)
    roundtrip_eff: Mapped[float] = mapped_column(Float, nullable=False)
    min_soc_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_soc_pct: Mapped[float] = mapped_column(Float, nullable=False)
    reserve_soc_pct: Mapped[float] = mapped_column(Float, nullable=False)
    current_soc_pct: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="idle", nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "capacity_mwh": self.capacity_mwh,
            "max_power_mw": self.max_power_mw,
            "roundtrip_eff": self.roundtrip_eff,
            "min_soc_pct": self.min_soc_pct,
            "max_soc_pct": self.max_soc_pct,
            "reserve_soc_pct": self.reserve_soc_pct,
            "current_soc_pct": self.current_soc_pct,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return f"<BatteryAsset {self.name} SoC={self.current_soc_pct}%>"


class DispatchEvent(BaseModel):
    """A dispatch decision log entry — the explainability surface."""

    __tablename__ = "dispatch_events"
    __table_args__ = (
        Index("ix_dispatch_events_battery_timestamp", "battery_id", "timestamp"),
    )

    battery_id: Mapped[int] = mapped_column(
        ForeignKey("battery_assets.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    power_mw: Mapped[float] = mapped_column(Float, nullable=False)
    soc_before_pct: Mapped[float] = mapped_column(Float, nullable=False)
    soc_after_pct: Mapped[float] = mapped_column(Float, nullable=False)
    trigger: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    market_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "battery_id": self.battery_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "power_mw": self.power_mw,
            "soc_before_pct": self.soc_before_pct,
            "soc_after_pct": self.soc_after_pct,
            "trigger": self.trigger,
            "reason": self.reason,
            "market_price": self.market_price,
            "forecast_price": self.forecast_price,
        }

    def __repr__(self) -> str:
        return f"<DispatchEvent battery={self.battery_id} {self.action} {self.trigger}>"
