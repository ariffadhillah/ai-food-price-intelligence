from __future__ import annotations

import time
from datetime import date

import pandas as pd

from app.ai.context_builder import (
    build_national_analysis_context,
)
from app.ai.context_hash import (
    generate_context_hash,
)
from app.ai.cost_estimator import (
    estimate_openai_cost,
)
from app.ai.executive_ai import (
    generate_national_ai_report,
)
from app.ai.llm_client import (
    LLMGenerationError,
    create_llm_client,
)
from app.ai.national_analyst import (
    EXPECTED_INDONESIAN_PROVINCES,
    validate_analysis_inputs,
)
from app.ai.prompt_engine import (
    NATIONAL_ANALYST_INSTRUCTIONS,
    build_national_report_prompt,
)
from app.ai.schemas import (
    NationalAIReport,
)
from app.database.ai_report_repository import (
    AIReportRepository,
)


CONTEXT_VERSION = "1.0.0"
PROMPT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


class NationalReportGenerationResult:
    def __init__(
        self,
        report: NationalAIReport,
        analysis_run_id: int,
        report_version_id: int,
        context_hash: str,
    ):
        self.report = report
        self.analysis_run_id = analysis_run_id
        self.report_version_id = report_version_id
        self.context_hash = context_hash


def generate_and_store_national_report(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
    analysis_date: date | None = None,
) -> NationalReportGenerationResult:
    """
    Generate a structured national AI report and persist the full
    analysis lifecycle to PostgreSQL.
    """

    validate_analysis_inputs(
        scores=scores,
        provinces=provinces,
        analytics=analytics,
    )

    selected_date = (
        analysis_date
        or date.today()
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
        expected_provinces=(
            EXPECTED_INDONESIAN_PROVINCES
        ),
    )

    context_hash = generate_context_hash(
        analysis_context,
    )

    prompt = build_national_report_prompt(
        analysis_context=analysis_context,
    )

    repository = AIReportRepository()

    analysis_run_id = repository.create_analysis_run(
        report_type="national",
        analysis_date=selected_date,
        context_version=CONTEXT_VERSION,
        context_hash=context_hash,
        context_json=analysis_context,
    )

    client = create_llm_client()

    started_at = time.perf_counter()

    try:
        result = (
            client.generate_structured_with_metadata(
                prompt=prompt,
                instructions=(
                    NATIONAL_ANALYST_INSTRUCTIONS
                ),
                response_schema=NationalAIReport,
                max_output_tokens=1800,
            )
        )

        report = result.data
        usage = result.usage

        estimated_cost = estimate_openai_cost(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )

        report_version_id = (
            repository.save_report_version(
                analysis_run_id=analysis_run_id,
                provider=result.provider,
                model_name=result.model_name,
                prompt_version=PROMPT_VERSION,
                schema_version=SCHEMA_VERSION,
                system_instructions=(
                    NATIONAL_ANALYST_INSTRUCTIONS
                ),
                prompt_text=prompt,
                report_json=report.model_dump(
                    mode="json",
                ),
                market_status=(
                    report.market_status.value
                ),
                confidence_score=(
                    report.confidence_score
                ),
                headline=report.headline,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                reasoning_tokens=(
                    usage.reasoning_tokens
                ),
                total_tokens=usage.total_tokens,
                estimated_cost_usd=estimated_cost,
                latency_ms=result.latency_ms,
                response_id=result.response_id,
                response_status=(
                    result.response_status
                ),
            )
        )

        repository.mark_run_completed(
            analysis_run_id,
        )

        return NationalReportGenerationResult(
            report=report,
            analysis_run_id=analysis_run_id,
            report_version_id=report_version_id,
            context_hash=context_hash,
        )

    except Exception as exc:
        latency_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000
        )

        try:
            repository.save_failed_version(
                analysis_run_id=analysis_run_id,
                provider="openai",
                model_name=client.config.model,
                prompt_version=PROMPT_VERSION,
                schema_version=SCHEMA_VERSION,
                system_instructions=(
                    NATIONAL_ANALYST_INSTRUCTIONS
                ),
                prompt_text=prompt,
                error_message=str(exc),
                latency_ms=latency_ms,
            )

            repository.mark_run_failed(
                analysis_run_id=analysis_run_id,
                error_message=str(exc),
            )

        except Exception:
            # Preserve the original AI exception if history persistence
            # also fails.
            pass

        if isinstance(
            exc,
            LLMGenerationError,
        ):
            raise

        raise