from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.ai.llm_client import (
    LLMUsage,
    StructuredGenerationResult,
)
from app.ai.schemas import (
    CriticalCommodity,
    CriticalProvince,
    KeyFinding,
    MarketStatus,
    NationalAIReport,
    Recommendation,
    RiskLevel,
)
from app.ai.services.national_report_service import (
    GeneratedNationalReport,
    NationalReportService,
)
from app.database.ai_report_repository import (
    AIReportRepository,
)


@dataclass(frozen=True)
class FakeLLMConfig:
    provider: str = "test"
    model: str = "fake-national-model"


class FakeLLMClient:
    """
    Test double that behaves like LLMClient without calling OpenAI.
    """

    def __init__(self) -> None:
        self.config = FakeLLMConfig()

    def generate_structured_with_metadata(
        self,
        *,
        prompt: str,
        response_schema,
        instructions: str,
        max_output_tokens: int,
        model=None,
    ) -> StructuredGenerationResult:
        assert prompt
        assert instructions
        assert response_schema is NationalAIReport
        assert max_output_tokens == 1800

        report = NationalAIReport(
            market_status=MarketStatus.WATCHLIST,
            confidence_score=90.0,
            headline=(
                "Pasar pangan nasional berada "
                "dalam kondisi waspada."
            ),
            executive_summary=(
                "Sebagian wilayah menunjukkan tekanan harga, "
                "meskipun cakupan data nasional tetap memadai."
            ),
            critical_provinces=[
                CriticalProvince(
                    province_name="Aceh",
                    risk_score=35.5,
                    risk_level=RiskLevel.HIGH,
                    main_risk_driver="Cabai Merah",
                    explanation=(
                        "Risk score berada pada kelompok "
                        "tertinggi dalam context pengujian."
                    ),
                )
            ],
            critical_commodities=[
                CriticalCommodity(
                    commodity_name="Cabai Merah",
                    province_name="Aceh",
                    risk_score=35.5,
                    price_change_1m=8.2,
                    explanation=(
                        "Komoditas mempunyai perubahan harga "
                        "dan risk score tertinggi."
                    ),
                )
            ],
            key_findings=[
                KeyFinding(
                    title="Tekanan harga regional",
                    finding=(
                        "Tekanan tertinggi terdapat pada "
                        "provinsi dan komoditas terpilih."
                    ),
                    importance=RiskLevel.HIGH,
                )
            ],
            recommendations=[
                Recommendation(
                    priority=1,
                    action=(
                        "Pantau perubahan harga komoditas "
                        "berisiko tinggi."
                    ),
                    reason=(
                        "Perubahan harga dan risk score "
                        "memerlukan pemantauan lebih dekat."
                    ),
                )
            ],
            data_limitations=[
                "Laporan ini menggunakan data pengujian."
            ],
        )

        return StructuredGenerationResult(
            data=report,
            provider="test",
            model_name="fake-national-model",
            response_id="fake-response-001",
            response_status="completed",
            latency_ms=1250,
            usage=LLMUsage(
                input_tokens=1000,
                output_tokens=500,
                reasoning_tokens=0,
                total_tokens=1500,
            ),
        )


def build_test_context() -> dict:
    return {
        "context_metadata": {
            "context_type": (
                "national_food_price_analysis"
            ),
            "context_version": "1.0.0",
            "generated_at": (
                "2026-07-21T12:00:00+07:00"
            ),
            "country": "Indonesia",
        },
        "data_coverage": {
            "score_record_count": 100,
            "province_analytics_record_count": 38,
            "commodity_analytics_record_count": 250,
            "covered_province_count": 38,
            "province_coverage_percentage": 100.0,
        },
        "market_statistics": {
            "high_risk_ratio_percentage": 14.5,
            "national_average_score": 18.4,
        },
        "rule_based_assessment": {
            "market_status": "WATCHLIST",
            "confidence_score": 90.0,
        },
        "highest_risk_provinces": [
            {
                "province_name": "Aceh",
                "risk_score": 35.5,
                "risk_level": "HIGH",
                "main_risk_driver": "Cabai Merah",
            }
        ],
        "highest_risk_commodities": [
            {
                "commodity_name": "Cabai Merah",
                "province_name": "Aceh",
                "risk_score": 35.5,
                "price_change_1m": 8.2,
            }
        ],
        "analysis_constraints": [
            "Use only supplied data.",
            "Do not infer unsupported causes.",
        ],
    }


def main() -> None:
    repository = AIReportRepository()
    llm_client = FakeLLMClient()

    service = NationalReportService(
        repository=repository,
        llm_client=llm_client,
    )

    result = service.generate_report(
        analytics_context=build_test_context(),
        analysis_date=date(2026, 7, 21),
        report_type="national",
    )

    assert isinstance(
        result,
        GeneratedNationalReport,
    )

    assert result.analysis_run_id > 0
    assert result.report_version_id > 0

    assert result.report_type == "national"
    assert result.status == "COMPLETED"

    assert result.provider == "test"
    assert result.model_name == "fake-national-model"

    assert result.input_tokens == 1000
    assert result.output_tokens == 500
    assert result.total_tokens == 1500

    assert len(result.context_hash) == 64

    assert (
        result.report.market_status
        == MarketStatus.WATCHLIST
    )

    latest_report = repository.get_latest_report(
        report_type="national"
    )

    assert latest_report is not None

    assert (
        latest_report["analysis_run_id"]
        == result.analysis_run_id
    )

    assert (
        latest_report["report_version_id"]
        == result.report_version_id
    )

    print("Generated National Report:")
    print(result.to_dict())
    print()

    print(
        f"Analysis run ID  : "
        f"{result.analysis_run_id}"
    )
    print(
        f"Report version ID: "
        f"{result.report_version_id}"
    )
    print(
        f"Provider         : "
        f"{result.provider}"
    )
    print(
        f"Model            : "
        f"{result.model_name}"
    )
    print(
        f"Input tokens     : "
        f"{result.input_tokens}"
    )
    print(
        f"Output tokens    : "
        f"{result.output_tokens}"
    )
    print(
        f"Total tokens     : "
        f"{result.total_tokens}"
    )
    print(
        f"Latency          : "
        f"{result.latency_ms} ms"
    )
    print(
        f"Estimated cost   : "
        f"${result.estimated_cost_usd}"
    )
    print(
        f"Status           : "
        f"{result.status}"
    )
    print()

    print(
        "NationalReportService Step 11 test berhasil."
    )


if __name__ == "__main__":
    main()