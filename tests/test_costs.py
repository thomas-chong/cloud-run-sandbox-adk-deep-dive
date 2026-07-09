import pytest

from sandbox_analyst.costs import estimate_cost


def test_cost_estimate_includes_compute_and_model() -> None:
    result = estimate_cost(
        invocations=1_000,
        active_seconds_per_invocation=10,
        vcpu=2,
        memory_gib=2,
        effective_concurrency=2,
        input_tokens_per_invocation=2_000,
        output_tokens_per_invocation=500,
    )
    assert result.cloud_run_compute_usd > 0
    assert result.gemini_output_usd > result.gemini_input_usd
    assert result.total_usd > result.gemini_output_usd
    assert any("no separate" in item.lower() for item in result.assumptions)


def test_zero_concurrency_is_invalid() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        estimate_cost(
            invocations=1,
            active_seconds_per_invocation=1,
            vcpu=1,
            memory_gib=1,
            effective_concurrency=0,
            input_tokens_per_invocation=1,
            output_tokens_per_invocation=1,
        )
