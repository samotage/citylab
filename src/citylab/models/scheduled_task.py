"""ScheduledTask model for APScheduler-managed cron jobs."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel


class ScheduledTask(BaseModel):
    """A scheduled task that triggers an agent action on a cron schedule."""

    __tablename__ = "scheduled_tasks"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_persona: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_action: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "agent_persona": self.agent_persona,
            "agent_action": self.agent_action,
            "is_active": self.is_active,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<ScheduledTask {self.name}>"
