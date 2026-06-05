"""Demand response models — controllable loads and curtailment event log."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel


class ControllableLoad(BaseModel):
    """A demand-side asset that can be curtailed during supply stress."""

    __tablename__ = "controllable_loads"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    load_type: Mapped[str] = mapped_column(String(40), nullable=False)
    capacity_mw: Mapped[float] = mapped_column(Float, nullable=False)
    curtailment_cost: Mapped[float] = mapped_column(Float, nullable=False)
    min_duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    max_duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available", nullable=False)
    curtailed_since: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "load_type": self.load_type,
            "capacity_mw": self.capacity_mw,
            "curtailment_cost": self.curtailment_cost,
            "min_duration_min": self.min_duration_min,
            "max_duration_min": self.max_duration_min,
            "status": self.status,
            "curtailed_since": (
                self.curtailed_since.isoformat() if self.curtailed_since else None
            ),
        }

    def __repr__(self) -> str:
        return f"<ControllableLoad {self.name} {self.status}>"


class DemandResponseEvent(BaseModel):
    """A demand response decision log entry."""

    __tablename__ = "demand_response_events"
    __table_args__ = (
        Index(
            "ix_demand_response_events_load_timestamp", "load_id", "timestamp"
        ),
    )

    load_id: Mapped[int] = mapped_column(
        ForeignKey("controllable_loads.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity_mw: Mapped[float] = mapped_column(Float, nullable=False)
    trigger: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    market_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "load_id": self.load_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "capacity_mw": self.capacity_mw,
            "trigger": self.trigger,
            "reason": self.reason,
            "market_price": self.market_price,
        }

    def __repr__(self) -> str:
        return f"<DemandResponseEvent load={self.load_id} {self.action} {self.trigger}>"
