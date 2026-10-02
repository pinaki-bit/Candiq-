"""
backend/app/models/pipeline.py

Pipeline Stage ORM model.

Tracks each candidate's journey through the hiring pipeline per job.
Each stage transition is timestamped and attributed to the recruiter
who moved the candidate, creating a full audit trail.

Stages: applied → screened → shortlisted → interview → offer → hired / rejected
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job
    from app.models.user import User


class PipelineStage:
    """Valid pipeline stages with ordering."""
    APPLIED = "applied"
    SCREENED = "screened"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"

    # Ordered progression (rejected can happen from any stage)
    ORDERED = [APPLIED, SCREENED, SHORTLISTED, INTERVIEW, OFFER, HIRED]
    ALL = {APPLIED, SCREENED, SHORTLISTED, INTERVIEW, OFFER, HIRED, REJECTED}

    # Stages that are considered terminal (no further progression)
    TERMINAL = {HIRED, REJECTED}

    # Valid transitions: from_stage -> set of allowed next stages
    TRANSITIONS = {
        APPLIED:     {SCREENED, REJECTED},
        SCREENED:    {SHORTLISTED, REJECTED},
        SHORTLISTED: {INTERVIEW, REJECTED},
        INTERVIEW:   {OFFER, SHORTLISTED, REJECTED},  # can loop back to shortlisted
        OFFER:       {HIRED, REJECTED},
        HIRED:       set(),   # terminal
        REJECTED:    {APPLIED},  # can be re-opened
    }

    @classmethod
    def is_valid_transition(cls, from_stage: str, to_stage: str) -> bool:
        """Check if a stage transition is allowed."""
        if from_stage not in cls.ALL or to_stage not in cls.ALL:
            return False
        return to_stage in cls.TRANSITIONS.get(from_stage, set())

    @classmethod
    def stage_order(cls, stage: str) -> int:
        """Return numeric order for sorting. Rejected sorts last."""
        if stage == cls.REJECTED:
            return 99
        try:
            return cls.ORDERED.index(stage)
        except ValueError:
            return -1


class PipelineEntry(Base):
    """
    Tracks a candidate's current stage in the pipeline for a specific job.
    One entry per (candidate, job) pair.
    """
    __tablename__ = "pipeline_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )

    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Current stage
    stage: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PipelineStage.APPLIED, index=True
    )

    # Who last moved this candidate
    moved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Optional notes from the recruiter
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    entered_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    stage_changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate")
    job: Mapped["Job"] = relationship("Job")

    def __repr__(self) -> str:
        return (
            f"<PipelineEntry id={self.id} candidate={self.candidate_id} "
            f"job={self.job_id} stage={self.stage!r}>"
        )


class PipelineHistory(Base):
    """
    Immutable audit log of every stage transition.
    Never deleted — provides full hiring decision traceability.
    """
    __tablename__ = "pipeline_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    pipeline_entry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_entries.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    from_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(32), nullable=False)

    moved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    transitioned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<PipelineHistory {self.from_stage!r} → {self.to_stage!r} "
            f"candidate={self.candidate_id} job={self.job_id}>"
        )
