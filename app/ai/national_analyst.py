import logging

import pandas as pd

from app.ai.executive_ai import generate_national_ai_report
from app.ai.llm_client import (
    LLMConfigurationError,
    LLMGenerationError,
    create_llm_client,
)
from app.ai.prompt_engine import (
    NATIONAL_ANALYST_INSTRUCTIONS,
    build_national_report_prompt,
)
from app.ai.schemas import NationalAIReport

logger = logging.getLogger(__name__)


def dataframe_to_records(
    dataframe: pd.DataFrame,
    columns: list[str],
    limit: int,
) -> list[dict]:
    """
    Convert selected DataFrame columns to JSON-compatible records.
    """

    if dataframe.empty:
        return []

    available_columns = [
        column
        for column in columns
        if column in dataframe.columns
    ]

    if not available_columns:
        return []

    selected = dataframe[
        available_columns
    ].head(limit).copy()

    selected = selected.where(
        pd.notna(selected),
        None,
    )

    return selected.to_dict(
        orient="records",
    )


def generate_openai_national_report(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
) -> NationalAIReport:
    """
    Generate a validated national report using OpenAI.
    """

    if scores.empty:
        raise ValueError(
            "Commodity scores tidak tersedia."
        )

    if provinces.empty:
        raise ValueError(
            "Province analytics tidak tersedia."
        )

    if analytics.empty:
        raise ValueError(
            "Commodity analytics tidak tersedia."
        )

    rule_report = generate_national_ai_report(
        scores=scores,
        provinces=provinces,
        analytics=analytics,
    )

    province_records = dataframe_to_records(
        dataframe=provinces.sort_values(
            "avg_risk_score",
            ascending=False,
        ),
        columns=[
            "province_name",
            "avg_risk_score",
            "max_risk_score",
            "high_risk_count",
            "top_risk_commodity",
            "top_risk_price",
            "avg_change_1m",
            "avg_change_3m",
            "avg_change_6m",
        ],
        limit=10,
    )

    commodity_records = dataframe_to_records(
        dataframe=scores.sort_values(
            "score",
            ascending=False,
        ),
        columns=[
            "province_name",
            "commodity_name",
            "score",
            "risk_level",
            "latest_price",
            "change_1m",
            "change_3m",
            "change_6m",
        ],
        limit=15,
    )

    analytics_records = dataframe_to_records(
        dataframe=analytics.sort_values(
            "std_price",
            ascending=False,
        ),
        columns=[
            "province_name",
            "commodity_name",
            "latest_price",
            "avg_price",
            "min_price",
            "max_price",
            "std_price",
            "change_1m",
            "change_3m",
            "change_6m",
        ],
        limit=10,
    )

    prompt = build_national_report_prompt(
        rule_report=rule_report,
        province_records=province_records,
        commodity_records=commodity_records,
        analytics_records=analytics_records,
    )

    client = create_llm_client()

    return client.generate_structured(
        prompt=prompt,
        instructions=NATIONAL_ANALYST_INSTRUCTIONS,
        response_schema=NationalAIReport,
        max_output_tokens=1800,
    )


def try_generate_openai_national_report(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
) -> tuple[NationalAIReport | None, str | None]:
    """
    Safe wrapper for dashboard use.

    Returns:
        (report, None) on success.
        (None, error_message) when OpenAI is unavailable.
    """

    try:
        report = generate_openai_national_report(
            scores=scores,
            provinces=provinces,
            analytics=analytics,
        )

        return report, None

    except (
        LLMConfigurationError,
        LLMGenerationError,
        ValueError,
    ) as exc:
        logger.warning(
            "OpenAI national report unavailable: %s",
            exc,
        )

        return None, str(exc)