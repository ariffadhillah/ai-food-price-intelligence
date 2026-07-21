from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.ai.llm_client import LLMUsage


ONE_MILLION = Decimal("1000000")
COST_QUANTIZATION = Decimal("0.00000001")


class CostConfigurationError(ValueError):
    """
    Raised when AI pricing configuration is invalid.
    """


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """
    Token pricing expressed in USD per one million tokens.
    """

    input_cost_per_1m: Decimal
    output_cost_per_1m: Decimal
    reasoning_cost_per_1m: Decimal | None = None

    @classmethod
    def from_environment(cls) -> "ModelPricing":
        return cls(
            input_cost_per_1m=_read_decimal_environment(
                "OPENAI_INPUT_COST_PER_1M",
                default="0",
            ),
            output_cost_per_1m=_read_decimal_environment(
                "OPENAI_OUTPUT_COST_PER_1M",
                default="0",
            ),
            reasoning_cost_per_1m=_read_optional_decimal_environment(
                "OPENAI_REASONING_COST_PER_1M",
            ),
        )


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    input_cost_usd: Decimal
    output_cost_usd: Decimal
    reasoning_cost_usd: Decimal
    total_cost_usd: Decimal

    def to_dict(self) -> dict[str, float]:
        return {
            "input_cost_usd": float(self.input_cost_usd),
            "output_cost_usd": float(self.output_cost_usd),
            "reasoning_cost_usd": float(self.reasoning_cost_usd),
            "total_cost_usd": float(self.total_cost_usd),
        }


def _read_decimal_environment(
    variable_name: str,
    default: str,
) -> Decimal:
    raw_value = os.getenv(variable_name, default).strip()

    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise CostConfigurationError(
            f"{variable_name} harus berupa angka desimal."
        ) from exc

    if value < 0:
        raise CostConfigurationError(
            f"{variable_name} tidak boleh bernilai negatif."
        )

    return value


def _read_optional_decimal_environment(
    variable_name: str,
) -> Decimal | None:
    raw_value = os.getenv(variable_name, "").strip()

    if not raw_value:
        return None

    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise CostConfigurationError(
            f"{variable_name} harus berupa angka desimal."
        ) from exc

    if value < 0:
        raise CostConfigurationError(
            f"{variable_name} tidak boleh bernilai negatif."
        )

    return value


def _normalize_token_count(
    token_count: int | None,
) -> int:
    if token_count is None:
        return 0

    if token_count < 0:
        raise ValueError(
            "Jumlah token tidak boleh bernilai negatif."
        )

    return token_count


def _calculate_token_cost(
    token_count: int,
    cost_per_1m: Decimal,
) -> Decimal:
    cost = (
        Decimal(token_count)
        / ONE_MILLION
        * cost_per_1m
    )

    return cost.quantize(
        COST_QUANTIZATION,
        rounding=ROUND_HALF_UP,
    )


def estimate_llm_cost(
    usage: LLMUsage,
    pricing: ModelPricing | None = None,
) -> CostBreakdown:
    """
    Estimate the OpenAI request cost using token usage metadata.

    Reasoning tokens are normally included inside output tokens by the
    provider. Therefore, they are not charged separately unless an
    explicit reasoning token price is configured.
    """

    selected_pricing = pricing or ModelPricing.from_environment()

    input_tokens = _normalize_token_count(
        usage.input_tokens,
    )
    output_tokens = _normalize_token_count(
        usage.output_tokens,
    )
    reasoning_tokens = _normalize_token_count(
        usage.reasoning_tokens,
    )

    input_cost = _calculate_token_cost(
        token_count=input_tokens,
        cost_per_1m=selected_pricing.input_cost_per_1m,
    )

    output_cost = _calculate_token_cost(
        token_count=output_tokens,
        cost_per_1m=selected_pricing.output_cost_per_1m,
    )

    reasoning_cost = Decimal("0.00000000")

    if selected_pricing.reasoning_cost_per_1m is not None:
        reasoning_cost = _calculate_token_cost(
            token_count=reasoning_tokens,
            cost_per_1m=selected_pricing.reasoning_cost_per_1m,
        )

    total_cost = (
        input_cost
        + output_cost
        + reasoning_cost
    ).quantize(
        COST_QUANTIZATION,
        rounding=ROUND_HALF_UP,
    )

    return CostBreakdown(
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        reasoning_cost_usd=reasoning_cost,
        total_cost_usd=total_cost,
    )