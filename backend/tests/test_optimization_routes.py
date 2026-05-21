"""Tests for optimization route helpers."""

from backend.models.db_models import PromptEvolutionLog, TalentLens
from backend.routes.optimization import (
    _build_evolution_responses,
    _current_best_by_index,
)


def test_build_evolution_responses_marks_promoted_mutations():
    entry = PromptEvolutionLog(
        id=1,
        job_id=1,
        parent_candidate_set_id="run_1",
        child_candidate_set_id="run_1_iter3",
        iteration=3,
        prompt_index=1,
        original_prompt="seed lens",
        evolved_prompt="evolved lens",
    )
    best_by_index = {1: "evolved lens"}
    responses = _build_evolution_responses([entry], best_by_index)

    assert len(responses) == 1
    assert responses[0].promoted is True


def test_build_evolution_responses_marks_unpromoted_mutations():
    entry = PromptEvolutionLog(
        id=2,
        job_id=1,
        parent_candidate_set_id="run_1",
        child_candidate_set_id="run_1_iter4",
        iteration=4,
        prompt_index=2,
        original_prompt="seed lens 2",
        evolved_prompt="explored lens 2",
    )
    best_by_index = {2: "seed lens 2"}
    responses = _build_evolution_responses([entry], best_by_index)

    assert responses[0].promoted is False


def test_current_best_by_index_uses_interim_while_running():
    status = {
        "interim_best_prompts": [
            {"prompt_index": 1, "prompt_text": "interim lens"},
        ]
    }
    best_by_index = _current_best_by_index(
        status=status,
        best_lenses=[],
        is_running=True,
    )
    assert best_by_index[1] == "interim lens"


def test_current_best_by_index_uses_active_lenses_when_completed():
    lens = TalentLens(
        job_id=1,
        candidate_set_id="best_abc",
        prompt_index=3,
        prompt_text="final lens",
        iteration=-1,
        generation="evolved",
        is_active=True,
    )
    best_by_index = _current_best_by_index(
        status={},
        best_lenses=[lens],
        is_running=False,
    )
    assert best_by_index[3] == "final lens"
