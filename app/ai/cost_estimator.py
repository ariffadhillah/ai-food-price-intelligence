from __future__ import annotations

import os
from decimal import Decimal


ONE_MILLION = Decimal("1000000")


def get_decimal_env(
    name: str,
    default: str = "0",
) -> Decimal:
    raw_value = os.getenv(
        name,
        default,
    )

    try:
        return Decimal(raw_value)
    except Exception:
        return Decimal(default)


def estimate_openai_cost(
    input_tokens: int | None,
    output_tokens: int | None,
) -> Decimal | None:
    """
    Estimate API cost using environment-configured rates.

    Rates are expressed in USD per one million tokens.
    """

    if (
        input_tokens is None
        and output_tokens is None
    ):
        return None

    input_rate = get_decimal_env(
        "OPENAI_INPUT_COST_PER_1M",
    )

    output_rate = get_decimal_env(
        "OPENAI_OUTPUT_COST_PER_1M",
    )

    input_cost = (
        Decimal(input_tokens or 0)
        / ONE_MILLION
        * input_rate
    )

    output_cost = (
        Decimal(output_tokens or 0)
        / ONE_MILLION
        * output_rate
    )

    return (
        input_cost
        + output_cost
    ).quantize(
        Decimal("0.00000001"),
    )