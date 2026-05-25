"""
Pydantic request/response schemas for the REST API.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ─── Job ───────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title: str
    description: str


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Core Value ────────────────────────────────────────────────

class CoreValueCreate(BaseModel):
    name: str
    description: str


class CoreValueBatchCreate(BaseModel):
    core_values: list[CoreValueCreate]


class CoreValueResponse(BaseModel):
    id: int
    job_id: int
    name: str
    description: str

    model_config = {"from_attributes": True}


# ─── Resume ────────────────────────────────────────────────────

class ResumeResponse(BaseModel):
    id: int
    job_id: int
    candidate_name: str
    file_type: str
    hiring_label: str | None = None
    status: str = "decided"
    entry_source: str = "historical"
    decision_made_at: datetime | None = None
    dataset_split: str | None = None
    parsed_text: str | None = None

    model_config = {"from_attributes": True}


# ─── Talent Lens / Prompts ─────────────────────────────────────

class PromptInput(BaseModel):
    """A single human-authored prompt."""
    prompt_text: str


class PromptSetInput(BaseModel):
    """The set of 5 human-authored prompts that form one GEPA candidate."""
    prompts: list[PromptInput] = Field(..., min_length=5, max_length=5)


class SeedPromptResponse(BaseModel):
    """A human-authored seed prompt for the setup wizard."""
    prompt_index: int
    prompt_text: str


class TalentLensResponse(BaseModel):
    id: int
    job_id: int
    candidate_set_id: str
    prompt_index: int
    prompt_text: str
    iteration: int
    generation: str
    fitness_score: float | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class CandidateSetResponse(BaseModel):
    """A complete candidate: set of 5 prompts."""
    candidate_set_id: str
    iteration: int
    generation: str
    fitness_score: float | None = None
    prompts: list[TalentLensResponse]


# ─── Evaluation ────────────────────────────────────────────────

class EvaluationResponse(BaseModel):
    id: int
    resume_id: int
    talent_lens_id: int
    candidate_set_id: str
    iteration: int
    score: float
    rationale: str | None = None

    model_config = {"from_attributes": True}


# ─── Candidate Prediction ─────────────────────────────────────

class CandidatePredictionResponse(BaseModel):
    id: int
    resume_id: int
    candidate_set_id: str
    iteration: int
    aggregate_score: float
    prediction: str
    actual_label: str | None = None
    is_correct: bool | None = None

    model_config = {"from_attributes": True}


# ─── Iteration Metrics ─────────────────────────────────────────

class IterationMetricsResponse(BaseModel):
    id: int
    job_id: int
    candidate_set_id: str
    iteration: int
    accuracy: float
    train_accuracy: float | None = None
    val_accuracy: float | None = None
    test_accuracy: float | None = None
    overfit_gap: float | None = None
    stop_reason: str | None = None
    precision_val: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    model_config = {"from_attributes": True}


class SplitSummaryResponse(BaseModel):
    train: int
    val: int
    test: int
    total: int
    assigned: bool


# ─── Prompt Evolution ──────────────────────────────────────────

class PromptEvolutionResponse(BaseModel):
    id: int
    parent_candidate_set_id: str | None = None
    child_candidate_set_id: str
    iteration: int
    prompt_index: int
    original_prompt: str | None = None
    evolved_prompt: str
    reflection_reasoning: str | None = None
    promoted: bool = False

    model_config = {"from_attributes": True}


# ─── Optimization ──────────────────────────────────────────────

class OptimizationRequest(BaseModel):
    """Request to start a GEPA optimization run."""
    prompts: PromptSetInput
    max_metric_calls: int | None = None
    hire_threshold: float | None = None
    early_stop_patience: int | None = None
    force_resplit: bool = False


class InterimPromptResponse(BaseModel):
    prompt_index: int
    prompt_text: str


class LiveEvalOutcomeResponse(BaseModel):
    resume_id: int | None = None
    candidate_name: str | None = None
    prediction: str
    actual_label: str
    aggregate_score: float | None = None
    is_correct: bool
    eval_error: str | None = None
    split: str | None = None


class OptimizationStatusResponse(BaseModel):
    status: str  # idle / running / completed / error
    phase: str | None = None  # generating_seed | seed_evaluation | optimizing (while running)
    seed_eval_completed: int | None = None
    seed_eval_total: int | None = None
    max_metric_calls: int | None = None
    hire_threshold: float | None = None
    current_iteration: int | None = None
    total_metric_calls: int | None = None
    best_accuracy: float | None = None
    error_message: str | None = None
    stop_reason: str | None = None
    overfit_gap: float | None = None
    train_accuracy: float | None = None
    test_accuracy: float | None = None
    split_summary: SplitSummaryResponse | None = None
    metrics_history: list[IterationMetricsResponse] | None = None
    interim_best_prompts: list[InterimPromptResponse] | None = None
    live_eval_outcomes: list[LiveEvalOutcomeResponse] | None = None


class OptimizationResultResponse(BaseModel):
    """Final results of a completed optimization run."""
    best_candidate_set_id: str
    best_accuracy: float
    total_iterations: int
    metrics_history: list[IterationMetricsResponse]
    best_prompts: list[TalentLensResponse]
    predictions: list[CandidatePredictionResponse]
    evolution_log: list[PromptEvolutionResponse]


# ─── Live loop: score / decision / pending / training-status ───

class PromptScoreDetail(BaseModel):
    prompt_index: int
    score: float
    rationale: str


class ScoreCandidateResponse(BaseModel):
    resume_id: int
    candidate_name: str
    aggregate_score: float
    prediction: str  # Hired / Rejected
    hire_threshold: float
    candidate_set_id_used: str
    prompt_scores: list[PromptScoreDetail]


class DecisionRequest(BaseModel):
    hiring_label: str  # "Hired" or "Rejected"
    note: str | None = None


class DecisionResponse(BaseModel):
    resume_id: int
    hiring_label: str
    decisions_since_last_train: int
    auto_retrain_threshold: int
    auto_retrain_triggered: bool


class PendingCandidateResponse(BaseModel):
    resume_id: int
    candidate_name: str
    file_type: str
    aggregate_score: float | None = None
    prediction: str | None = None
    candidate_set_id_used: str | None = None
    scored_at: datetime | None = None

    model_config = {"from_attributes": True}


class TrainingStatusResponse(BaseModel):
    decisions_since_last_train: int
    auto_retrain_threshold: int
    last_optimized_at: datetime | None = None
    has_active_best_prompts: bool
    run_status: str  # idle / running / completed / error


# ─── Batch Resume Upload ───────────────────────────────────────

class BatchResumeItem(BaseModel):
    candidate_name: str
    hiring_label: str  # "Hired" or "Rejected"
    file_name: str
    file_content_base64: str  # base64-encoded file content


class BatchResumesUploadRequest(BaseModel):
    resumes: list[BatchResumeItem]
    auto_retrain: bool = False


class BatchResumeUploadResult(BaseModel):
    candidate_name: str
    resume_id: int
    status: str  # "success" or "error"
    error_message: str | None = None


class BatchResumesUploadResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: list[BatchResumeUploadResult]
    auto_retrain_triggered: bool
