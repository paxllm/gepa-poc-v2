"""
GEPA callback that persists per-iteration validation metrics and updates run status.
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.models.db_models import IterationMetrics, PromptEvolutionLog, TalentLens


class MetricsPersistenceCallback:
    """Observes GEPA iterations and writes intermediate results to the database."""

    def __init__(
        self,
        job_id: int,
        candidate_set_id: str,
        session_factory: async_sessionmaker[AsyncSession],
        loop: asyncio.AbstractEventLoop,
        run_status: dict[int, dict[str, Any]],
    ):
        self.job_id = job_id
        self.candidate_set_id = candidate_set_id
        self.session_factory = session_factory
        self.loop = loop
        self.run_status = run_status
        self._last_proposal_parent: dict[str, str] | None = None

    def on_optimization_start(self, event: dict[str, Any]) -> None:
        self.run_status[self.job_id]["phase"] = "seed_evaluation"

    def _run_async(self, coro) -> None:
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.result(timeout=120)

    def on_budget_updated(self, event: dict[str, Any]) -> None:
        status = self.run_status[self.job_id]
        status["total_metric_calls"] = event["metric_calls_used"]
        status["phase"] = "optimizing"
        status.pop("seed_eval_completed", None)
        status.pop("seed_eval_total", None)

    def on_proposal_start(self, event: dict[str, Any]) -> None:
        self._last_proposal_parent = dict(event["parent_candidate"])

    def on_proposal_end(self, event: dict[str, Any]) -> None:
        if not self._last_proposal_parent:
            return

        iteration = event["iteration"]
        new_instructions = event["new_instructions"]
        parent = self._last_proposal_parent
        changes: list[tuple[int, str, str]] = []

        for key, new_text in new_instructions.items():
            old_text = parent.get(key, "")
            if new_text != old_text:
                idx = int(key.split("_")[1])
                changes.append((idx, old_text, new_text))

        if changes:
            self._run_async(self._persist_evolutions(iteration, changes))

    def on_valset_evaluated(self, event: dict[str, Any]) -> None:
        if not event.get("is_best_program"):
            return

        iteration = event["iteration"]
        candidate = event["candidate"]
        score = event["average_score"]
        status = self.run_status[self.job_id]

        # During seed eval, live_eval_outcomes drives best_accuracy (matches the UI table).
        if status.get("phase") != "seed_evaluation":
            status["best_accuracy"] = score
        status["interim_best_prompts"] = [
            {"prompt_index": int(key.split("_")[1]), "prompt_text": text}
            for key, text in sorted(candidate.items())
        ]

        if iteration == 0:
            num_evaluated = event.get("num_examples_evaluated")
            if num_evaluated is not None:
                status["total_metric_calls"] = num_evaluated
            status.pop("seed_eval_completed", None)
            status.pop("seed_eval_total", None)

        self._run_async(self._persist_interim_best(iteration, candidate, score))

    def on_iteration_end(self, event: dict[str, Any]) -> None:
        iteration = event["iteration"]
        state = event["state"]
        scores = state.program_full_scores_val_set
        val_score = max(scores) if scores else 0.0

        self.run_status[self.job_id]["current_iteration"] = iteration + 1
        self.run_status[self.job_id]["best_accuracy"] = val_score

        self._run_async(self._persist_metrics(iteration + 1, val_score))

    async def _persist_metrics(self, iteration: int, val_score: float) -> None:
        async with self.session_factory() as session:
            metrics = IterationMetrics(
                job_id=self.job_id,
                candidate_set_id=self.candidate_set_id,
                iteration=iteration,
                accuracy=val_score,
                val_accuracy=val_score,
                train_accuracy=None,
                test_accuracy=None,
                overfit_gap=None,
                stop_reason=None,
                precision_val=None,
                recall=None,
                f1_score=None,
                true_positives=0,
                false_positives=0,
                true_negatives=0,
                false_negatives=0,
            )
            session.add(metrics)
            await session.commit()

    async def _persist_evolutions(
        self,
        iteration: int,
        changes: list[tuple[int, str, str]],
    ) -> None:
        async with self.session_factory() as session:
            for idx, old_text, new_text in changes:
                session.add(
                    PromptEvolutionLog(
                        job_id=self.job_id,
                        parent_candidate_set_id=self.candidate_set_id,
                        child_candidate_set_id=f"{self.candidate_set_id}_iter{iteration}",
                        iteration=iteration,
                        prompt_index=idx,
                        original_prompt=old_text,
                        evolved_prompt=new_text,
                    )
                )
            await session.commit()

    async def _persist_interim_best(
        self,
        iteration: int,
        candidate: dict[str, str],
        score: float,
    ) -> None:
        interim_set_id = f"{self.candidate_set_id}_interim"
        async with self.session_factory() as session:
            await session.execute(
                delete(TalentLens).where(
                    TalentLens.job_id == self.job_id,
                    TalentLens.candidate_set_id == interim_set_id,
                )
            )
            for key, prompt_text in candidate.items():
                idx = int(key.split("_")[1])
                session.add(
                    TalentLens(
                        job_id=self.job_id,
                        candidate_set_id=interim_set_id,
                        prompt_index=idx,
                        prompt_text=prompt_text,
                        iteration=iteration,
                        generation="evolved",
                        fitness_score=score,
                        is_active=False,
                    )
                )
            await session.commit()
