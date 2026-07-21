import logging

import pandas as pd

from app.ai.context_builder import (
    build_national_analysis_context,
)
from app.ai.executive_ai import (
    generate_national_ai_report,
)
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


EXPECTED_INDONESIAN_PROVINCES = [
    "Aceh",
    "Sumatera Utara",
    "Sumatera Barat",
    "Riau",
    "Kepulauan Riau",
    "Jambi",
    "Sumatera Selatan",
    "Kepulauan Bangka Belitung",
    "Bengkulu",
    "Lampung",
    "DKI Jakarta",
    "Jawa Barat",
    "Banten",
    "Jawa Tengah",
    "DI Yogyakarta",
    "Jawa Timur",
    "Bali",
    "Nusa Tenggara Barat",
    "Nusa Tenggara Timur",
    "Kalimantan Barat",
    "Kalimantan Tengah",
    "Kalimantan Selatan",
    "Kalimantan Timur",
    "Kalimantan Utara",
    "Sulawesi Utara",
    "Gorontalo",
    "Sulawesi Tengah",
    "Sulawesi Barat",
    "Sulawesi Selatan",
    "Sulawesi Tenggara",
    "Maluku",
    "Maluku Utara",
    "Papua",
    "Papua Barat",
    "Papua Barat Daya",
    "Papua Selatan",
    "Papua Tengah",
    "Papua Pegunungan",
]


def validate_analysis_inputs(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
) -> None:
    """
    Validate required input datasets.
    """

    if scores is None or scores.empty:
        raise ValueError(
            "Commodity scores tidak tersedia."
        )

    if provinces is None or provinces.empty:
        raise ValueError(
            "Province analytics tidak tersedia."
        )

    if analytics is None or analytics.empty:
        raise ValueError(
            "Commodity analytics tidak tersedia."
        )


def generate_openai_national_report(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
) -> NationalAIReport:
    """
    Generate a validated national report using the complete
    context-builder pipeline.
    """

    validate_analysis_inputs(
        scores=scores,
        provinces=provinces,
        analytics=analytics,
    )

    rule_report = generate_national_ai_report(
        scores=scores,
        provinces=provinces,
        analytics=analytics,
    )

    analysis_context = build_national_analysis_context(
        rule_report=rule_report,
        scores=scores,
        provinces=provinces,
        analytics=analytics,
        expected_provinces=EXPECTED_INDONESIAN_PROVINCES,
    )

    prompt = build_national_report_prompt(
        analysis_context=analysis_context,
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
    Generate the national report safely for dashboard usage.

    Returns:
        (report, None) when successful.
        (None, error_message) when unavailable.
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