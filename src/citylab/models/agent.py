"""Remote agent models — agent configuration and running session state.

`AgentConfig` is the catalogue of available Headspace personas (Ray and any
future agents). `AgentSession` tracks a running Headspace remote-agent session
for one config: its Headspace agent id, embed URL, server-side session token,
and lifecycle status. At most one *active* session per config is enforced by a
partial unique index plus service-layer resume-or-create logic.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citylab.models.base import BaseModel


class SessionStatus(enum.Enum):
    """Lifecycle status of an agent session."""

    active = "active"
    disconnected = "disconnected"
    dead = "dead"
    shutdown = "shutdown"


class AgentConfig(BaseModel):
    """A configured remote-agent persona that can be started in CityLab.

    Multi-agent ready — each row is one Headspace persona. Exactly one row may
    be marked the default; setting a new default unsets the previous one
    (service-layer logic, FR2).
    """

    __tablename__ = "agent_config"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    persona_slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sessions = relationship(
        "AgentSession", back_populates="config", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "persona_slug": self.persona_slug,
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        flag = " (default)" if self.is_default else ""
        return f"<AgentConfig {self.name} [{self.persona_slug}]{flag}>"


class AgentSession(BaseModel):
    """A running (or terminated) Headspace remote-agent session.

    Stores the Headspace agent id, the operator-facing embed URL, and the
    server-side session token. The token is NEVER serialised to clients
    (NFR1) — `to_dict()` deliberately omits it.
    """

    __tablename__ = "agent_session"

    config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent_config.id"), nullable=False
    )
    headspace_agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    embed_url: Mapped[str] = mapped_column(Text, nullable=False)
    session_token: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="agent_session_status"),
        default=SessionStatus.active,
        nullable=False,
    )
    last_alive_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    config = relationship("AgentConfig", back_populates="sessions")

    # At most one active session per config (FR9).
    __table_args__ = (
        Index(
            "ix_agent_session_active_config",
            "config_id",
            unique=True,
            postgresql_where=(status == SessionStatus.active),
        ),
    )

    def mark_alive(self) -> None:
        self.last_alive_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Serialise for API/CLI — session_token is intentionally excluded."""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "headspace_agent_id": self.headspace_agent_id,
            "embed_url": self.embed_url,
            "status": self.status.value,
            "started_at": self.created_at.isoformat() if self.created_at else None,
            "last_alive_at": (
                self.last_alive_at.isoformat() if self.last_alive_at else None
            ),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AgentSession {self.id} config={self.config_id} "
            f"status={self.status.value}>"
        )
