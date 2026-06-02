"""DataSource model — registry of ingestion sources."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from citylab.models.base import BaseModel

# Valid source types
SOURCE_TYPES = ("opennem", "bom", "solcast", "custom")
# Valid fetch statuses
FETCH_STATUSES = ("success", "error", "pending")


class DataSource(BaseModel):
    """A registered data ingestion source with scheduling and status tracking."""

    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetch_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_fetch_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_fetch_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_dict(self) -> dict:
        # Redact sensitive config keys for output
        safe_config = {}
        for k, v in (self.config or {}).items():
            if any(s in k.lower() for s in ("key", "token", "secret", "password")):
                safe_config[k] = "***" if v else None
            else:
                safe_config[k] = v
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "base_url": self.base_url,
            "config": safe_config,
            "cron_expression": self.cron_expression,
            "is_active": self.is_active,
            "last_fetch_at": self.last_fetch_at.isoformat()
            if self.last_fetch_at
            else None,
            "last_fetch_status": self.last_fetch_status,
            "last_error": self.last_error,
            "next_fetch_at": self.next_fetch_at.isoformat()
            if self.next_fetch_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<DataSource {self.name} ({self.source_type})>"
