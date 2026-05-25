"""
LLM model pricing tables.

All costs are in USD per 1 million tokens.
Sources:
  - NVIDIA NIM: public pricing page (May 2026)
  - AWS Bedrock: aws.amazon.com/bedrock/pricing/ + AWS blog announcements (May 2026)
"""

from __future__ import annotations

# ── Claude Opus 4.5 on AWS Bedrock ────────────────────────────────────────────
# Source: https://aws.amazon.com/blogs/machine-learning/claude-opus-4-5-now-in-amazon-bedrock/
OPUS_45_MODEL_ID = "anthropic.claude-opus-4-5-20250514-v1:0"
OPUS_45_INPUT_PER_1M_ON_DEMAND = 5.00    # USD per 1M input tokens
OPUS_45_OUTPUT_PER_1M_ON_DEMAND = 25.00  # USD per 1M output tokens
# Batch mode: 50% discount (standard AWS Bedrock batch rate)
OPUS_45_INPUT_PER_1M_BATCH = 2.50
OPUS_45_OUTPUT_PER_1M_BATCH = 12.50


def calculate_opus_45_cost(
    prompt_tokens: int,
    completion_tokens: int,
    *,
    batch: bool = False,
) -> float:
    """Cost in USD for the given token counts on Claude Opus 4.5 (Bedrock)."""
    inp = OPUS_45_INPUT_PER_1M_BATCH if batch else OPUS_45_INPUT_PER_1M_ON_DEMAND
    out = OPUS_45_OUTPUT_PER_1M_BATCH if batch else OPUS_45_OUTPUT_PER_1M_ON_DEMAND
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


# ── NVIDIA NIM (current provider) ────────────────────────────────────────────
# (input_usd_per_1m, output_usd_per_1m)
_NIM_PRICES: dict[str, tuple[float, float]] = {
    "meta/llama-3.3-70b-instruct": (0.35, 0.40),
    "meta/llama-3.1-70b-instruct": (0.35, 0.40),
    "meta/llama-3.1-8b-instruct":  (0.10, 0.12),
    "nvidia/llama-3.1-nemotron-70b-instruct": (0.20, 0.20),
    "mistralai/mistral-7b-instruct-v0.2": (0.15, 0.15),
    # Fallback for any unrecognised NIM model
    "_default": (0.35, 0.40),
}


# ── AWS Bedrock models (production target) ────────────────────────────────────
BEDROCK_MODELS: list[dict] = [
    {
        "id": "amazon.nova-micro-v1:0",
        "name": "Amazon Nova Micro",
        "provider": "Amazon",
        "input_per_1m": 0.035,
        "output_per_1m": 0.14,
        "note": "Fastest, lowest cost. Good for simple scoring.",
    },
    {
        "id": "amazon.nova-lite-v1:0",
        "name": "Amazon Nova Lite",
        "provider": "Amazon",
        "input_per_1m": 0.06,
        "output_per_1m": 0.24,
        "note": "Balanced speed/quality for most evaluation tasks.",
    },
    {
        "id": "amazon.nova-pro-v1:0",
        "name": "Amazon Nova Pro",
        "provider": "Amazon",
        "input_per_1m": 0.80,
        "output_per_1m": 3.20,
        "note": "High quality reasoning and instruction following.",
    },
    {
        "id": "anthropic.claude-3-haiku-20240307-v1:0",
        "name": "Claude 3 Haiku",
        "provider": "Anthropic",
        "input_per_1m": 0.25,
        "output_per_1m": 1.25,
        "note": "Fast and affordable. Strong instruction following.",
    },
    {
        "id": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "input_per_1m": 0.80,
        "output_per_1m": 4.00,
        "note": "Best Anthropic price/performance for agentic tasks.",
    },
    {
        "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "Claude 3.5 Sonnet v2",
        "provider": "Anthropic",
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
        "note": "Highest quality. Best for complex reflection/reasoning.",
    },
    {
        "id": OPUS_45_MODEL_ID,
        "name": "Claude Opus 4.5",
        "provider": "Anthropic",
        "input_per_1m": OPUS_45_INPUT_PER_1M_ON_DEMAND,
        "output_per_1m": OPUS_45_OUTPUT_PER_1M_ON_DEMAND,
        "note": "Frontier intelligence. Best reasoning for GEPA reflection. 50% cheaper in batch.",
    },
    {
        "id": "meta.llama3-8b-instruct-v1:0",
        "name": "Llama 3 8B Instruct",
        "provider": "Meta",
        "input_per_1m": 0.30,
        "output_per_1m": 0.60,
        "note": "Low cost open-source option.",
    },
    {
        "id": "meta.llama3-70b-instruct-v1:0",
        "name": "Llama 3 70B Instruct",
        "provider": "Meta",
        "input_per_1m": 2.65,
        "output_per_1m": 3.50,
        "note": "Matches quality of current NIM model on Bedrock.",
    },
    {
        "id": "mistral.mistral-7b-instruct-v0:2",
        "name": "Mistral 7B Instruct",
        "provider": "Mistral",
        "input_per_1m": 0.15,
        "output_per_1m": 0.20,
        "note": "Budget option for high-volume evaluation.",
    },
    {
        "id": "mistral.mixtral-8x7b-instruct-v0:1",
        "name": "Mixtral 8x7B Instruct",
        "provider": "Mistral",
        "input_per_1m": 0.45,
        "output_per_1m": 0.70,
        "note": "Good balance of cost and capability.",
    },
]


def get_nim_price(model: str) -> tuple[float, float]:
    return _NIM_PRICES.get(model, _NIM_PRICES["_default"])


def calculate_nim_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = get_nim_price(model)
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


def calculate_bedrock_cost(
    bedrock_model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    m = next((x for x in BEDROCK_MODELS if x["id"] == bedrock_model_id), None)
    if not m:
        return 0.0
    return (prompt_tokens * m["input_per_1m"] + completion_tokens * m["output_per_1m"]) / 1_000_000


def estimate_all_bedrock_costs(
    prompt_tokens: int,
    completion_tokens: int,
) -> list[dict]:
    """Return cost estimates for all Bedrock models for a given token volume."""
    results = []
    for m in BEDROCK_MODELS:
        cost = (
            prompt_tokens * m["input_per_1m"] + completion_tokens * m["output_per_1m"]
        ) / 1_000_000
        results.append(
            {
                "model_id": m["id"],
                "name": m["name"],
                "provider": m["provider"],
                "input_per_1m": m["input_per_1m"],
                "output_per_1m": m["output_per_1m"],
                "note": m["note"],
                "estimated_cost_usd": round(cost, 6),
            }
        )
    # Sort cheapest first
    results.sort(key=lambda x: x["estimated_cost_usd"])
    return results
