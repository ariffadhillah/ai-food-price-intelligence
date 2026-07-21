from decimal import Decimal

from app.ai.cost_estimator import (
    ModelPricing,
    estimate_llm_cost,
)
from app.ai.llm_client import LLMUsage


def main() -> None:
    usage = LLMUsage(
        input_tokens=1_000_000,
        output_tokens=500_000,
        reasoning_tokens=100_000,
        total_tokens=1_500_000,
    )

    pricing = ModelPricing(
        input_cost_per_1m=Decimal("0.40"),
        output_cost_per_1m=Decimal("1.60"),
        reasoning_cost_per_1m=None,
    )

    result = estimate_llm_cost(
        usage=usage,
        pricing=pricing,
    )

    print("Cost breakdown:")
    print(result.to_dict())
    print()

    assert result.input_cost_usd == Decimal("0.40000000")
    assert result.output_cost_usd == Decimal("0.80000000")
    assert result.reasoning_cost_usd == Decimal("0.00000000")
    assert result.total_cost_usd == Decimal("1.20000000")

    empty_usage_result = estimate_llm_cost(
        usage=LLMUsage(),
        pricing=pricing,
    )

    assert empty_usage_result.total_cost_usd == Decimal(
        "0.00000000"
    )

    print("AI cost estimator test berhasil.")


if __name__ == "__main__":
    main()