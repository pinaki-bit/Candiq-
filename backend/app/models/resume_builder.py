"""
backend/app/models/resume_builder.py

Phase 35 — Resume Draft & Versioning ORM Models.
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any, Dict

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResumeDraft(Base):
    __tablename__ = "resume_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default_tenant", index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled Resume Draft")

    target_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    candidate_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True
    )
    original_resume_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )

    structured_content_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    raw_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    versions: Mapped[list["ResumeVersion"]] = relationship(
        "ResumeVersion", back_populates="draft", cascade="all, delete-orphan", lazy="selectin"
    )

    def get_content_dict(self) -> Dict[str, Any]:
        try:
            return json.loads(self.structured_content_json) if self.structured_content_json else {}
        except Exception:
            return {}

    def set_content_dict(self, data: Dict[str, Any]) -> None:
        self.structured_content_json = json.dumps(data, default=str)


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )
    draft_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resume_drafts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="Saved Version")
    structured_content_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    draft: Mapped["ResumeDraft"] = relationship("ResumeDraft", back_populates="versions")
