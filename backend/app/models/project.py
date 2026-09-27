"""Project model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    cloud_target: Mapped[str] = mapped_column(
        String(32), nullable=False, default="azure"
    )
    environment: Mapped[str] = mapped_column(
        String(32), nullable=False, default="development"
    )
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="eastus")
    availability_requirement: Mapped[str] = mapped_column(
        String(32), nullable=False, default="standard"
    )
    compliance_framework: Mapped[str] = mapped_column(
        String(32), nullable=False, default="none"
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
