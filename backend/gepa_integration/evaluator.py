"""
Custom evaluator for the GEPA optimization loop.
Implements the Evaluator protocol expected by gepa's DefaultAdapter.

Each evaluation:
1. Takes a candidate (dict of 5 prompts) and a data instance (resume + label)
2. Runs all 5 prompts against the resume via NVIDIA NIM
3. Aggregates scores and compares prediction vs actual hiring label
4. Returns score (1.0 = correct, 0.0 = wrong) + detailed feedback for GEPA reflection
"""

import json
from typing import Any

from backend.core.litellm_client import completion_with_retry
from gepa.adapters.default_adapter.default_adapter import EvaluationResult

from backend.core.config import get_settings
from backend.gepa_integration.prompt_templates import (
    build_evaluation_prompt,
    compose_talent_lens_prompt,
    extract_user_lens,
)


class HiringEvaluator:
    """
    Evaluator that scores a candidate prompt set against a resume.

    The candidate is a dict[str, str] with keys "prompt_1" through "prompt_5".
    Each data instance is a DefaultDataInst with:
        - input: resume text
        - additional_context: {"job_description": ..., "core_values_json": ...}
        - answer: "Hired" or "Rejected"
    """

    def __init__(self, hire_threshold: float | None = None):
        settings = get_settings()
        self.hire_threshold = hire_threshold or settings.hire_threshold

    def __call__(self, data: dict[str, Any], response: str) -> EvaluationResult:
        """
        Evaluate the LLM's response for a single prompt against a resume.

        This is called by GEPA's DefaultAdapter for each (prompt_component, data_instance) pair.
        The DefaultAdapter handles running each component prompt separately.

        Args:
            data: The data instance with resume text, context, and expected answer.
            response: The LLM's response text for this specific prompt.

        Returns:
            EvaluationResult with score, feedback, and optional objective_scores.
        """
        expected_label = data["answer"]

        # Parse the LLM's evaluation response
        try:
            eval_result = json.loads(response)
            prompt_score = float(eval_result.get("score", 0))
            rationale = eval_result.get("rationale", "No rationale provided")
        except (json.JSONDecodeError, ValueError):
            # Try to extract score from text
            prompt_score = self._extract_score_from_text(response)
            rationale = response

        # Clamp score to 1-5
        prompt_score = max(1.0, min(5.0, prompt_score))

        # For individual prompt evaluation, score is normalized to 0-1
        # (GEPA's DefaultAdapter handles per-component scoring)
        normalized_score = (prompt_score - 1.0) / 4.0  # Map 1-5 to 0-1

        # Build feedback for GEPA reflection
        feedback = self._build_feedback(
            prompt_score=prompt_score,
            rationale=rationale,
            expected_label=expected_label,
            resume_snippet=data["input"][:500],
        )

        return EvaluationResult(
            score=normalized_score,
            feedback=feedback,
            objective_scores=None,
        )

    def _extract_score_from_text(self, text: str) -> float:
        """Attempt to extract a numeric score from text response."""
        import re
        patterns = [
            r'"score"\s*:\s*(\d+(?:\.\d+)?)',
            r'score[:\s]+(\d+(?:\.\d+)?)',
            r'\b([1-5])\s*(?:/\s*5|out of 5)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 3.0  # Default to middle score if parsing fails

    def _build_feedback(
        self,
        prompt_score: float,
        rationale: str,
        expected_label: str,
        resume_snippet: str,
    ) -> str:
        """Build detailed feedback string for GEPA reflection."""
        prediction = "Hired" if prompt_score >= self.hire_threshold else "Rejected"
        is_correct = prediction == expected_label

        feedback_parts = [
            f"Prompt Score: {prompt_score}/5",
            f"Prediction (threshold={self.hire_threshold}): {prediction}",
            f"Expected: {expected_label}",
            f"Correct: {'Yes' if is_correct else 'NO - MISMATCH'}",
            f"Rationale: {rationale}",
        ]

        if not is_correct:
            if prediction == "Hired" and expected_label == "Rejected":
                feedback_parts.append(
                    "ISSUE: The prompt scored this candidate too HIGH. "
                    "The candidate was actually rejected. The prompt may be too lenient "
                    "or missing criteria that would identify weaknesses."
                )
            else:
                feedback_parts.append(
                    "ISSUE: The prompt scored this candidate too LOW. "
                    "The candidate was actually hired. The prompt may be too strict "
                    "or not recognizing relevant qualifications."
                )

            feedback_parts.append(f"Resume snippet: {resume_snippet}")

        return "\n".join(feedback_parts)


def create_hiring_evaluator(hire_threshold: float | None = None) -> HiringEvaluator:
    """Factory function to create a HiringEvaluator."""
    return HiringEvaluator(hire_threshold=hire_threshold)


def _parse_prompt_score(response_text: str, hire_threshold: float) -> float:
    """Parse score 1-5 from model JSON or text (mirrors HiringEvaluator logic)."""
    ev = HiringEvaluator(hire_threshold=hire_threshold)
    try:
        eval_result = json.loads(response_text)
        prompt_score = float(eval_result.get("score", 0))
    except (json.JSONDecodeError, ValueError):
        prompt_score = ev._extract_score_from_text(response_text)
    return max(1.0, min(5.0, prompt_score))


def evaluate_candidate_on_dataset(
    candidate: dict[str, str],
    dataset: list[dict[str, Any]],
    *,
    hire_threshold: float,
    task_lm_model: str,
    job_description: str,
    core_values: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Run the 5-prompt candidate on each resume in dataset (synchronous LLM calls).

    Returns accuracy, precision, recall, f1, confusion counts, and per-row outcomes
    with keys: resume_id (int|None), aggregate_score, prediction, actual_label, is_correct.
    """
    outcomes: list[dict[str, Any]] = []
    for inst in dataset:
        scores: list[float] = []
        resume_text = inst["input"]

        for k in ("prompt_1", "prompt_2", "prompt_3", "prompt_4", "prompt_5"):
            lens = extract_user_lens(candidate[k])
            composed = compose_talent_lens_prompt(lens, job_description, core_values)
            messages = build_evaluation_prompt(
                talent_lens_prompt=composed,
                resume_text=resume_text,
            )
            completion = completion_with_retry(
                model=task_lm_model,
                messages=messages,
                timeout=120,
            )
            response_text = completion.choices[0].message.content or ""
            scores.append(_parse_prompt_score(response_text, hire_threshold))

        aggregate = sum(scores) / len(scores)
        prediction = "Hired" if aggregate >= hire_threshold else "Rejected"
        actual = inst["answer"]
        is_correct = prediction == actual
        rid = inst["additional_context"].get("resume_id")
        resume_id = int(rid) if rid is not None else None
        outcomes.append({
            "resume_id": resume_id,
            "aggregate_score": aggregate,
            "prediction": prediction,
            "actual_label": actual,
            "is_correct": is_correct,
        })

    tp = sum(1 for o in outcomes if o["prediction"] == "Hired" and o["actual_label"] == "Hired")
    fp = sum(1 for o in outcomes if o["prediction"] == "Hired" and o["actual_label"] == "Rejected")
    tn = sum(1 for o in outcomes if o["prediction"] == "Rejected" and o["actual_label"] == "Rejected")
    fn = sum(1 for o in outcomes if o["prediction"] == "Rejected" and o["actual_label"] == "Hired")
    n = len(outcomes)
    accuracy = sum(1 for o in outcomes if o["is_correct"]) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = None

    return {
        "accuracy": accuracy,
        "precision_val": precision,
        "recall": recall,
        "f1_score": f1,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "outcomes": outcomes,
    }
