"""
Cost analysis endpoints.

Reports token usage and estimated LLM spend for the current NVIDIA NIM
provider plus what-if cost projections for AWS Bedrock models.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.config import get_settings
from backend.core.pricing import (
    OPUS_45_INPUT_PER_1M_BATCH,
    OPUS_45_INPUT_PER_1M_ON_DEMAND,
    OPUS_45_MODEL_ID,
    OPUS_45_OUTPUT_PER_1M_BATCH,
    OPUS_45_OUTPUT_PER_1M_ON_DEMAND,
    calculate_nim_cost,
    calculate_opus_45_cost,
    estimate_all_bedrock_costs,
    get_nim_price,
)
from backend.models.db_models import LLMUsageLog

router = APIRouter(prefix="/api", tags=["costs"])


def _opus_45_analysis(rows: list[LLMUsageLog], run_map: dict[str, list]) -> dict:
    """Detailed Claude Opus 4.5 cost projection for given usage rows."""
    total_calls = len(rows)
    total_prompt = sum(r.prompt_tokens for r in rows)
    total_completion = sum(r.completion_tokens for r in rows)

    avg_prompt = round(total_prompt / total_calls, 1) if total_calls else 0
    avg_completion = round(total_completion / total_calls, 1) if total_calls else 0

    on_demand_total = calculate_opus_45_cost(total_prompt, total_completion, batch=False)
    batch_total = calculate_opus_45_cost(total_prompt, total_completion, batch=True)

    per_run = []
    for run_id, run_rows in run_map.items():
        rpt = sum(r.prompt_tokens for r in run_rows)
        rct = sum(r.completion_tokens for r in run_rows)
        per_run.append({
            "run_set_id": run_id,
            "records": len(run_rows),
            "prompt_tokens": rpt,
            "completion_tokens": rct,
            "total_tokens": rpt + rct,
            "avg_prompt_tokens": round(rpt / len(run_rows), 1) if run_rows else 0,
            "avg_completion_tokens": round(rct / len(run_rows), 1) if run_rows else 0,
            "on_demand_cost_usd": round(calculate_opus_45_cost(rpt, rct, batch=False), 6),
            "batch_cost_usd": round(calculate_opus_45_cost(rpt, rct, batch=True), 6),
            "started_at": run_rows[0].created_at.isoformat() if run_rows[0].created_at else None,
        })

    return {
        "model_id": OPUS_45_MODEL_ID,
        "model_name": "Claude Opus 4.5",
        "on_demand": {
            "input_per_1m_usd": OPUS_45_INPUT_PER_1M_ON_DEMAND,
            "output_per_1m_usd": OPUS_45_OUTPUT_PER_1M_ON_DEMAND,
            "total_cost_usd": round(on_demand_total, 6),
        },
        "batch": {
            "input_per_1m_usd": OPUS_45_INPUT_PER_1M_BATCH,
            "output_per_1m_usd": OPUS_45_OUTPUT_PER_1M_BATCH,
            "total_cost_usd": round(batch_total, 6),
            "discount_pct": 50,
        },
        "token_stats": {
            "total_records": total_calls,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "avg_prompt_tokens_per_record": avg_prompt,
            "avg_completion_tokens_per_record": avg_completion,
        },
        "per_run": per_run,
        "source": "https://aws.amazon.com/blogs/machine-learning/claude-opus-4-5-now-in-amazon-bedrock/",
    }


def _cost_summary(rows: list[LLMUsageLog], model: str) -> dict:
    total_prompt = sum(r.prompt_tokens for r in rows)
    total_completion = sum(r.completion_tokens for r in rows)
    total_tokens = total_prompt + total_completion
    total_calls = len(rows)
    current_cost = calculate_nim_cost(model, total_prompt, total_completion)
    bedrock = estimate_all_bedrock_costs(total_prompt, total_completion)
    cheapest_bedrock = bedrock[0] if bedrock else None

    by_type: dict[str, dict] = {}
    for r in rows:
        ct = r.call_type
        if ct not in by_type:
            by_type[ct] = {"call_type": ct, "calls": 0, "prompt_tokens": 0,
                           "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}
        by_type[ct]["calls"] += 1
        by_type[ct]["prompt_tokens"] += r.prompt_tokens
        by_type[ct]["completion_tokens"] += r.completion_tokens
        by_type[ct]["total_tokens"] += r.total_tokens
        by_type[ct]["cost_usd"] = round(
            calculate_nim_cost(model, by_type[ct]["prompt_tokens"],
                               by_type[ct]["completion_tokens"]),
            6,
        )

    inp_per_m, out_per_m = get_nim_price(model)

    return {
        "summary": {
            "total_calls": total_calls,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "current_model": model,
            "input_price_per_1m": inp_per_m,
            "output_price_per_1m": out_per_m,
            "estimated_current_cost_usd": round(current_cost, 6),
            "cheapest_bedrock_model": cheapest_bedrock["name"] if cheapest_bedrock else None,
            "cheapest_bedrock_cost_usd": cheapest_bedrock["estimated_cost_usd"] if cheapest_bedrock else None,
        },
        "breakdown_by_call_type": sorted(by_type.values(), key=lambda x: -x["total_tokens"]),
        "bedrock_comparison": [
            {
                **m,
                "savings_vs_current_pct": round(
                    (current_cost - m["estimated_cost_usd"]) / current_cost * 100, 1
                ) if current_cost > 0 else 0.0,
            }
            for m in bedrock
        ],
    }


@router.get("/jobs/{job_id}/costs")
async def get_job_costs(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cost breakdown for a specific job (all runs)."""
    settings = get_settings()
    model = f"openai/{settings.nvidia_model}"
    nim_model = settings.nvidia_model

    result = await db.execute(
        select(LLMUsageLog)
        .where(LLMUsageLog.job_id == job_id)
        .order_by(LLMUsageLog.created_at)
    )
    rows = list(result.scalars().all())

    # Per-run breakdown
    run_map: dict[str, list[LLMUsageLog]] = {}
    for r in rows:
        key = r.run_set_id or "unknown"
        run_map.setdefault(key, []).append(r)

    runs_summary = []
    for run_id, run_rows in run_map.items():
        pt = sum(r.prompt_tokens for r in run_rows)
        ct = sum(r.completion_tokens for r in run_rows)
        runs_summary.append(
            {
                "run_set_id": run_id,
                "calls": len(run_rows),
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": pt + ct,
                "estimated_cost_usd": round(calculate_nim_cost(nim_model, pt, ct), 6),
                "started_at": run_rows[0].created_at.isoformat() if run_rows[0].created_at else None,
            }
        )

    data = _cost_summary(rows, nim_model)
    data["breakdown_by_run"] = runs_summary
    data["opus_45_analysis"] = _opus_45_analysis(rows, run_map)
    return data


@router.get("/costs/summary")
async def get_all_costs(db: AsyncSession = Depends(get_db)):
    """Aggregate cost summary across all jobs."""
    settings = get_settings()
    nim_model = settings.nvidia_model

    result = await db.execute(
        select(LLMUsageLog).order_by(LLMUsageLog.created_at)
    )
    rows = list(result.scalars().all())
    run_map: dict[str, list] = {}
    for r in rows:
        run_map.setdefault(r.run_set_id or "unknown", []).append(r)
    data = _cost_summary(rows, nim_model)
    data["opus_45_analysis"] = _opus_45_analysis(rows, run_map)
    return data


@router.get("/costs/pricing")
async def get_pricing():
    """Return the full pricing reference table (NIM + Bedrock)."""
    from backend.core.pricing import BEDROCK_MODELS
    settings = get_settings()
    nim_model = settings.nvidia_model
    inp, out = get_nim_price(nim_model)
    return {
        "current_provider": "NVIDIA NIM",
        "current_model": nim_model,
        "current_input_per_1m": inp,
        "current_output_per_1m": out,
        "bedrock_models": BEDROCK_MODELS,
    }
