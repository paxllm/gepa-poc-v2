"""Tests for seed candidate composition."""

from backend.gepa_integration.prompt_templates import (
    build_seed_candidate,
    compose_talent_lens_prompt,
    extract_user_lens,
    is_composed_prompt,
)


def test_compose_talent_lens_prompt_includes_job_and_core_values():
    composed = compose_talent_lens_prompt(
        user_lens="Assess technical ownership and system design depth.",
        job_description="Senior Software Engineer role.",
        core_values=[{"name": "Excellence", "description": "Ship quality code."}],
    )

    assert "Senior Software Engineer role." in composed
    assert "**Excellence**: Ship quality code." in composed
    assert "Assess technical ownership and system design depth." in composed


def test_build_seed_candidate_stores_lens_only():
    jd = "Engineer"
    cv = [{"name": "Integrity", "description": "Be honest."}]

    seed = build_seed_candidate(
        ["lens 1", "lens 2", "lens 3", "lens 4", "lens 5"],
        job_description=jd,
        core_values=cv,
    )

    assert set(seed.keys()) == {
        "prompt_1",
        "prompt_2",
        "prompt_3",
        "prompt_4",
        "prompt_5",
    }
    assert seed["prompt_1"] == "lens 1"
    assert seed["prompt_5"] == "lens 5"
    assert jd not in seed["prompt_1"]


def test_extract_user_lens_from_legacy_composed_prompt():
    composed = compose_talent_lens_prompt(
        user_lens="Assess leadership and mentoring.",
        job_description="Senior Engineer",
        core_values=[{"name": "Collaboration", "description": "Work as a team."}],
    )
    assert is_composed_prompt(composed)
    assert extract_user_lens(composed) == "Assess leadership and mentoring."


def test_extract_user_lens_passthrough_for_lens_only():
    lens = "Assess technical depth only."
    assert not is_composed_prompt(lens)
    assert extract_user_lens(lens) == lens


def test_build_seed_candidate_normalizes_legacy_composed_input():
    jd = "Engineer"
    cv = [{"name": "Integrity", "description": "Be honest."}]
    composed = compose_talent_lens_prompt("legacy lens", jd, cv)

    seed = build_seed_candidate(
        [composed, "lens 2", "lens 3", "lens 4", "lens 5"],
        job_description=jd,
        core_values=cv,
    )

    assert seed["prompt_1"] == "legacy lens"
    assert jd not in seed["prompt_1"]
