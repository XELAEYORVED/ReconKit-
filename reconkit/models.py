"""SQLAlchemy ORM models for ReconKit."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# Reserved tag used to mark a scan as a favorite (avoids a schema migration).
FAVORITE_TAG = "favorite"


class Base(DeclarativeBase):
    pass


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TargetType(str, enum.Enum):
    DOMAIN = "domain"
    IP = "ip"
    EMAIL = "email"
    USERNAME = "username"
    UNKNOWN = "unknown"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: _new_id("scan"))
    target: Mapped[str] = mapped_column(String(512), index=True)
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), default=TargetType.UNKNOWN)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.PENDING, index=True)
    threat_score: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list[Result]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", lazy="selectin"
    )
    tags: Mapped[list[ScanTag]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", lazy="selectin"
    )
    notes: Mapped[list[ScanNote]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", lazy="selectin"
    )

    def to_dict(self, include_results: bool = False) -> dict:
        all_tags = [t.tag for t in self.tags]
        d = {
            "id": self.id,
            "target": self.target,
            "target_type": self.target_type.value if self.target_type else None,
            "status": self.status.value if self.status else None,
            "threat_score": self.threat_score,
            "config": self.config or {},
            "summary": self.summary or {},
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            # User-facing tags exclude the reserved favorite marker.
            "tags": [t for t in all_tags if t != FAVORITE_TAG],
            "favorite": FAVORITE_TAG in all_tags,
            "notes": [n.to_dict() for n in self.notes],
        }
        if include_results:
            d["results"] = [r.to_dict() for r in self.results]
        return d


class Result(Base):
    __tablename__ = "results"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: _new_id("res"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    module_name: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="ok")  # ok | error | skipped
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    scan: Mapped[Scan] = relationship(back_populates="results")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "module_name": self.module_name,
            "status": self.status,
            "data": self.data or {},
            "confidence": self.confidence,
            "tags": self.tags or [],
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (UniqueConstraint("service", name="uq_apikey_service"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: _new_id("key"))
    service: Mapped[str] = mapped_column(String(64), index=True)
    key_encrypted: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScanTag(Base):
    __tablename__ = "scan_tags"
    __table_args__ = (UniqueConstraint("scan_id", "tag", name="uq_scan_tag"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    tag: Mapped[str] = mapped_column(String(64))

    scan: Mapped[Scan] = relationship(back_populates="tags")


class ScanNote(Base):
    __tablename__ = "scan_notes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: _new_id("note"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    scan: Mapped[Scan] = relationship(back_populates="notes")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: _new_id("usr"))
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
