"""
SQLAlchemy ORM models for the Resume GEPA system.
"""

import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    # Set when run_optimization completes successfully; drives the
    # "decisions since last train" auto-retrain trigger.
    last_optimized_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    auto_retrain_threshold: Mapped[int] = mapped_column(Integer, default=5)

    # Relationships
    core_values: Mapped[list["CoreValue"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    talent_lenses: Mapped[list["TalentLens"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    iteration_metrics: Mapped[list["IterationMetrics"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class CoreValue(Base):
    __tablename__ = "core_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="core_values")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, txt
    parsed_text: Mapped[str] = mapped_column(Text, nullable=True)
    # None for `pending_decision` resumes that have been scored but not yet decided.
    hiring_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # pending_decision until a hiring manager records a decision, then decided.
    status: Mapped[str] = mapped_column(String(20), default="decided", nullable=False)
    # historical = bulk-uploaded with a label; live = scored via /candidates/score.
    entry_source: Mapped[str] = mapped_column(String(20), default="historical", nullable=False)
    decision_made_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    # train / val / test — assigned before optimization; None until first split
    dataset_split: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="resumes")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    predictions: Mapped[list["CandidatePrediction"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class TalentLens(Base):
    """
    A TalentLens is a single prompt within a candidate prompt set.
    A complete candidate = 5 TalentLens records with the same candidate_set_id.
    """
    __tablename__ = "talent_lenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_set_id: Mapped[str] = mapped_column(String(64), nullable=False)  # Groups 5 prompts into one candidate
    prompt_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    generation: Mapped[str] = mapped_column(String(20), default="seed")  # seed / evolved
    fitness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="talent_lenses")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="talent_lens", cascade="all, delete-orphan")


class Evaluation(Base):
    """Individual evaluation: one resume scored by one talent lens prompt."""
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id"), nullable=False)
    talent_lens_id: Mapped[int] = mapped_column(Integer, ForeignKey("talent_lenses.id"), nullable=False)
    candidate_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 1-5
    rationale: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    resume: Mapped["Resume"] = relationship(back_populates="evaluations")
    talent_lens: Mapped["TalentLens"] = relationship(back_populates="evaluations")


class CandidatePrediction(Base):
    """Aggregate prediction for a resume by a candidate prompt set."""
    __tablename__ = "candidate_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id"), nullable=False)
    candidate_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    aggregate_score: Mapped[float] = mapped_column(Float, nullable=False)
    prediction: Mapped[str] = mapped_column(String(20), nullable=False)  # Hired / Rejected
    # Null for live-scored predictions until a decision is recorded.
    actual_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # Relationships
    resume: Mapped["Resume"] = relationship(back_populates="predictions")


class IterationMetrics(Base):
    """Performance metrics for each GEPA iteration."""
    __tablename__ = "iteration_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    # Split metrics: during optimization iterations, val_accuracy mirrors accuracy (val-only).
    train_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    val_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overfit_gap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    precision_val: Mapped[float] = mapped_column(Float, nullable=True)
    recall: Mapped[float] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float] = mapped_column(Float, nullable=True)
    true_positives: Mapped[int] = mapped_column(Integer, default=0)
    false_positives: Mapped[int] = mapped_column(Integer, default=0)
    true_negatives: Mapped[int] = mapped_column(Integer, default=0)
    false_negatives: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="iteration_metrics")


class PromptEvolutionLog(Base):
    """Tracks how prompts evolve across GEPA iterations."""
    __tablename__ = "prompt_evolution_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    parent_candidate_set_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    child_candidate_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    iteration: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Which of the 5 prompts changed
    original_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    evolved_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    reflection_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class LLMUsageLog(Base):
    """Per-call token usage for cost tracking and Bedrock projection."""
    __tablename__ = "llm_usage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=True)
    run_set_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # evaluation | reflection | seed_generation | scoring | unknown
    call_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
