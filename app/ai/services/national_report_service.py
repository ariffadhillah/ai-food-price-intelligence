from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from app.ai.context_hash import generate_context_hash
from app.ai.cost_estimator import CostBreakdown, estimate_llm_cost
from app.ai.llm_client import LLMClient, StructuredGenerationResult
from app.ai.prompt_engine import (
    NATIONAL_ANALYST_INSTRUCTIONS,
    build_national_report_prompt,
)
from app.ai.schemas import NationalAIReport
from app.database.ai_report_repository import AIReportRepository


DEFAULT_REPORT_TYPE = "national"
DEFAULT_CONTEXT_VERSION = "1.0.0"

PROMPT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
DEFAULT_MAX_OUTPUT_TOKENS = 1800


class NationalReportServiceError(RuntimeError):
    """
    Raised when the national report workflow cannot be completed.
    """


class InvalidAnalysisContextError(ValueError):
    """
    Raised when the supplied analytics context is invalid.
    """


@dataclass(frozen=True, slots=True)
class AnalysisRunResult:
    """
    Metadata returned after an analysis run is initialized.
    """

    analysis_run_id: int
    report_type: str
    analysis_date: date
    context_version: str
    context_hash: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_run_id": self.analysis_run_id,
            "report_type": self.report_type,
            "analysis_date": self.analysis_date.isoformat(),
            "context_version": self.context_version,
            "context_hash": self.context_hash,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class GeneratedNationalReport:
    """
    Complete result returned after successful AI report generation.
    """

    report: NationalAIReport

    analysis_run_id: int
    report_version_id: int

    report_type: str
    analysis_date: date

    context_version: str
    context_hash: str

    provider: str
    model_name: str

    prompt_version: str
    schema_version: str

    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    total_tokens: int | None

    latency_ms: int
    estimated_cost_usd: Decimal

    response_id: str | None
    response_status: str | None

    status: str = "COMPLETED"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the generated report and metadata into JSON-safe values.
        """

        return {
            "report": self.report.model_dump(mode="json"),
            "analysis_run_id": self.analysis_run_id,
            "report_version_id": self.report_version_id,
            "report_type": self.report_type,
            "analysis_date": self.analysis_date.isoformat(),
            "context_version": self.context_version,
            "context_hash": self.context_hash,
            "provider": self.provider,
            "model_name": self.model_name,
            "prompt_version": self.prompt_version,
            "schema_version": self.schema_version,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": float(
                self.estimated_cost_usd
            ),
            "response_id": self.response_id,
            "response_status": self.response_status,
            "status": self.status,
        }


class NationalReportService:
    """
    Orchestrate national AI report generation and persistence.

    Responsibilities:

    1. Validate prepared analytics context.
    2. Generate deterministic context hash.
    3. Create an analysis run.
    4. Build the national report prompt.
    5. Generate structured output through the LLM client.
    6. Estimate request cost.
    7. Save the generated report version.
    8. Mark the analysis run as completed or failed.
    """

    def __init__(
        self,
        repository: AIReportRepository,
        llm_client: LLMClient,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client

    def start_analysis(
        self,
        *,
        analytics_context: dict[str, Any],
        analysis_date: date | None = None,
        report_type: str = DEFAULT_REPORT_TYPE,
    ) -> AnalysisRunResult:
        """
        Validate context and initialize a database analysis run.
        """

        self._validate_context(analytics_context)

        normalized_report_type = self._normalize_report_type(
            report_type
        )

        selected_analysis_date = analysis_date or date.today()

        context_version = self._resolve_context_version(
            analytics_context
        )

        context_hash = generate_context_hash(
            analytics_context
        )

        try:
            analysis_run_id = (
                self.repository.create_analysis_run(
                    report_type=normalized_report_type,
                    analysis_date=selected_analysis_date,
                    context_version=context_version,
                    context_hash=context_hash,
                    context_json=analytics_context,
                )
            )
        except Exception as exc:
            raise NationalReportServiceError(
                "Gagal membuat national analysis run."
            ) from exc

        return AnalysisRunResult(
            analysis_run_id=analysis_run_id,
            report_type=normalized_report_type,
            analysis_date=selected_analysis_date,
            context_version=context_version,
            context_hash=context_hash,
            status="PROCESSING",
        )

    def generate_report(
        self,
        *,
        analytics_context: dict[str, Any],
        analysis_date: date | None = None,
        report_type: str = DEFAULT_REPORT_TYPE,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> GeneratedNationalReport:
        """
        Generate, persist, and return a national AI report.

        A new analysis run is created before the LLM request. If any
        later step fails, the run is marked as FAILED.
        """

        if max_output_tokens <= 0:
            raise ValueError(
                "max_output_tokens harus lebih besar dari 0."
            )

        analysis_run = self.start_analysis(
            analytics_context=analytics_context,
            analysis_date=analysis_date,
            report_type=report_type,
        )

        prompt_text = build_national_report_prompt(
            analysis_context=analytics_context
        )

        provider = self._resolve_provider_name()
        model_name = self._resolve_model_name()

        generation_result: (
            StructuredGenerationResult[NationalAIReport] | None
        ) = None

        try:
            generation_result = (
                self.llm_client.generate_structured_with_metadata(
                    prompt=prompt_text,
                    instructions=NATIONAL_ANALYST_INSTRUCTIONS,
                    response_schema=NationalAIReport,
                    max_output_tokens=max_output_tokens,
                )
            )

            cost_breakdown = estimate_llm_cost(
                usage=generation_result.usage
            )

            report = generation_result.data

            report_json = report.model_dump(
                mode="json"
            )

            report_version_id = (
                self.repository.save_report_version(
                    analysis_run_id=(
                        analysis_run.analysis_run_id
                    ),
                    provider=generation_result.provider,
                    model_name=(
                        generation_result.model_name
                    ),
                    prompt_version=PROMPT_VERSION,
                    schema_version=SCHEMA_VERSION,
                    system_instructions=(
                        NATIONAL_ANALYST_INSTRUCTIONS
                    ),
                    prompt_text=prompt_text,
                    report_json=report_json,
                    market_status=(
                        report.market_status.value
                    ),
                    confidence_score=(
                        report.confidence_score
                    ),
                    headline=report.headline,
                    input_tokens=(
                        generation_result.usage.input_tokens
                    ),
                    output_tokens=(
                        generation_result.usage.output_tokens
                    ),
                    reasoning_tokens=(
                        generation_result.usage.reasoning_tokens
                    ),
                    total_tokens=(
                        generation_result.usage.total_tokens
                    ),
                    estimated_cost_usd=(
                        cost_breakdown.total_cost_usd
                    ),
                    latency_ms=(
                        generation_result.latency_ms
                    ),
                    response_id=(
                        generation_result.response_id
                    ),
                    response_status=(
                        generation_result.response_status
                    ),
                )
            )

            self.repository.mark_run_completed(
                analysis_run_id=(
                    analysis_run.analysis_run_id
                )
            )

            return self._build_generated_result(
                report=report,
                analysis_run=analysis_run,
                report_version_id=report_version_id,
                generation_result=generation_result,
                cost_breakdown=cost_breakdown,
            )

        except Exception as exc:
            self._handle_generation_failure(
                analysis_run_id=(
                    analysis_run.analysis_run_id
                ),
                provider=provider,
                model_name=model_name,
                prompt_text=prompt_text,
                error=exc,
                generation_result=generation_result,
            )

            raise NationalReportServiceError(
                "Gagal menghasilkan national AI report."
            ) from exc

    def _handle_generation_failure(
        self,
        *,
        analysis_run_id: int,
        provider: str,
        model_name: str,
        prompt_text: str,
        error: Exception,
        generation_result: (
            StructuredGenerationResult[NationalAIReport] | None
        ),
    ) -> None:
        """
        Best-effort persistence for a failed generation workflow.

        Failure logging errors must not hide the original exception.
        """

        error_message = self._sanitize_error_message(
            str(error)
        )

        latency_ms = (
            generation_result.latency_ms
            if generation_result is not None
            else None
        )

        try:
            self.repository.save_failed_version(
                analysis_run_id=analysis_run_id,
                provider=provider,
                model_name=model_name,
                prompt_version=PROMPT_VERSION,
                schema_version=SCHEMA_VERSION,
                system_instructions=(
                    NATIONAL_ANALYST_INSTRUCTIONS
                ),
                prompt_text=prompt_text,
                error_message=error_message,
                latency_ms=latency_ms,
            )
        except Exception:
            # Do not replace the original workflow exception.
            pass

        try:
            self.repository.mark_run_failed(
                analysis_run_id=analysis_run_id,
                error_message=error_message,
            )
        except Exception:
            # Do not replace the original workflow exception.
            pass

    @staticmethod
    def _build_generated_result(
        *,
        report: NationalAIReport,
        analysis_run: AnalysisRunResult,
        report_version_id: int,
        generation_result: StructuredGenerationResult[
            NationalAIReport
        ],
        cost_breakdown: CostBreakdown,
    ) -> GeneratedNationalReport:
        """
        Create the public service result object.
        """

        usage = generation_result.usage

        return GeneratedNationalReport(
            report=report,
            analysis_run_id=(
                analysis_run.analysis_run_id
            ),
            report_version_id=report_version_id,
            report_type=analysis_run.report_type,
            analysis_date=analysis_run.analysis_date,
            context_version=(
                analysis_run.context_version
            ),
            context_hash=analysis_run.context_hash,
            provider=generation_result.provider,
            model_name=generation_result.model_name,
            prompt_version=PROMPT_VERSION,
            schema_version=SCHEMA_VERSION,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=generation_result.latency_ms,
            estimated_cost_usd=(
                cost_breakdown.total_cost_usd
            ),
            response_id=generation_result.response_id,
            response_status=(
                generation_result.response_status
            ),
        )

    def _resolve_provider_name(self) -> str:
        """
        Read the configured provider for failure-history records.
        """

        config = getattr(
            self.llm_client,
            "config",
            None,
        )

        provider = getattr(
            config,
            "provider",
            None,
        )

        if isinstance(provider, str) and provider.strip():
            return provider.strip().lower()

        return "unknown"

    def _resolve_model_name(self) -> str:
        """
        Read the configured model for failure-history records.
        """

        config = getattr(
            self.llm_client,
            "config",
            None,
        )

        model_name = getattr(
            config,
            "model",
            None,
        )

        if (
            isinstance(model_name, str)
            and model_name.strip()
        ):
            return model_name.strip()

        return "unknown"

    @staticmethod
    def _sanitize_error_message(
        error_message: str,
        max_length: int = 2000,
    ) -> str:
        """
        Limit error text before storing it in PostgreSQL.
        """

        normalized = (
            error_message.strip()
            or "Unknown national report generation error."
        )

        return normalized[:max_length]

    @staticmethod
    def _validate_context(
        analytics_context: dict[str, Any],
    ) -> None:
        """
        Validate the minimum context structure.
        """

        if not isinstance(analytics_context, dict):
            raise InvalidAnalysisContextError(
                "analytics_context harus berupa dictionary."
            )

        if not analytics_context:
            raise InvalidAnalysisContextError(
                "analytics_context tidak boleh kosong."
            )

        context_metadata = analytics_context.get(
            "context_metadata"
        )

        if not isinstance(context_metadata, dict):
            raise InvalidAnalysisContextError(
                "analytics_context harus memiliki "
                "'context_metadata' berupa dictionary."
            )

        context_version = context_metadata.get(
            "context_version"
        )

        if context_version is not None:
            if not isinstance(context_version, str):
                raise InvalidAnalysisContextError(
                    "context_metadata.context_version "
                    "harus berupa string."
                )

            if not context_version.strip():
                raise InvalidAnalysisContextError(
                    "context_metadata.context_version "
                    "tidak boleh berupa string kosong."
                )

    @staticmethod
    def _resolve_context_version(
        analytics_context: dict[str, Any],
    ) -> str:
        """
        Resolve context version from metadata.
        """

        context_metadata = analytics_context[
            "context_metadata"
        ]

        raw_version = context_metadata.get(
            "context_version",
            DEFAULT_CONTEXT_VERSION,
        )

        return str(raw_version).strip()

    @staticmethod
    def _normalize_report_type(
        report_type: str,
    ) -> str:
        """
        Validate and normalize report type.
        """

        if not isinstance(report_type, str):
            raise ValueError(
                "report_type harus berupa string."
            )

        normalized = report_type.strip().lower()

        if not normalized:
            raise ValueError(
                "report_type tidak boleh kosong."
            )

        return normalized