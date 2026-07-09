"""Transparent cost model using public list prices, excluding free tiers/CUDs."""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Sources checked 2026-07-09:
# https://cloud.google.com/run/pricing (request-based active time, tier 1)
# https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
CLOUD_RUN_VCPU_SECOND = 0.000024
CLOUD_RUN_GIB_SECOND = 0.0000025
CLOUD_RUN_REQUEST = 0.40 / 1_000_000
GEMINI_35_FLASH_INPUT_MTOKEN = 1.50
GEMINI_35_FLASH_OUTPUT_MTOKEN = 9.00


@dataclass(frozen=True, slots=True)
class CostEstimate:
    cloud_run_compute_usd: float
    cloud_run_requests_usd: float
    gemini_input_usd: float
    gemini_output_usd: float
    total_usd: float
    assumptions: list[str]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_cost(
    *,
    invocations: int,
    active_seconds_per_invocation: float,
    vcpu: float,
    memory_gib: float,
    effective_concurrency: float,
    input_tokens_per_invocation: int,
    output_tokens_per_invocation: int,
) -> CostEstimate:
    """Estimate list-price request costs; this is not a billing quote."""

    if min(
        invocations,
        active_seconds_per_invocation,
        vcpu,
        memory_gib,
        effective_concurrency,
        input_tokens_per_invocation,
        output_tokens_per_invocation,
    ) < 0:
        raise ValueError("cost inputs must be non-negative")
    if effective_concurrency == 0:
        raise ValueError("effective_concurrency must be greater than zero")

    billable_seconds = (
        invocations * active_seconds_per_invocation / effective_concurrency
    )
    compute = billable_seconds * (
        vcpu * CLOUD_RUN_VCPU_SECOND + memory_gib * CLOUD_RUN_GIB_SECOND
    )
    request_cost = invocations * CLOUD_RUN_REQUEST
    input_cost = (
        invocations
        * input_tokens_per_invocation
        / 1_000_000
        * GEMINI_35_FLASH_INPUT_MTOKEN
    )
    output_cost = (
        invocations
        * output_tokens_per_invocation
        / 1_000_000
        * GEMINI_35_FLASH_OUTPUT_MTOKEN
    )
    total = compute + request_cost + input_cost + output_cost
    return CostEstimate(
        cloud_run_compute_usd=round(compute, 6),
        cloud_run_requests_usd=round(request_cost, 6),
        gemini_input_usd=round(input_cost, 6),
        gemini_output_usd=round(output_cost, 6),
        total_usd=round(total, 6),
        assumptions=[
            "USD list prices checked 2026-07-09; excludes free tier and discounts",
            "Cloud Run request-based tier-1 active CPU/memory pricing",
            "Gemini 3.5 Flash global Standard PayGo token pricing",
            "No separate Cloud Run sandbox premium; sandbox shares host resources",
            "Excludes Cloud Build, Artifact Registry, logging, storage, and egress",
            "Concurrency is an observed workload input, not guaranteed capacity",
        ],
    )
