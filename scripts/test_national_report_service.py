from __future__ import annotations

from datetime import date

from app.ai.services.national_report_service import (
    AnalysisRunResult,
    NationalReportService,
)
from app.database.ai_report_repository import (
    AIReportRepository,
)


def build_test_context() -> dict:
    """
    Build a prepared analytics context for service testing.
    """

    return {
        "context_metadata": {
            "context_type": "national_food_price_analysis",
            "context_version": "1.0.0",
            "generated_at": "2026-07-21T12:00:00+07:00",
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
    }


def main() -> None:
    repository = AIReportRepository()

    service = NationalReportService(
        repository=repository,
    )

    context = build_test_context()

    result = service.start_analysis(
        analytics_context=context,
        analysis_date=date(2026, 7, 21),
        report_type="national",
    )

    assert isinstance(
        result,
        AnalysisRunResult,
    )

    assert result.analysis_run_id > 0
    assert result.report_type == "national"
    assert result.analysis_date == date(2026, 7, 21)
    assert result.context_version == "1.0.0"
    assert result.status == "PROCESSING"
    assert len(result.context_hash) == 64

    print("National Report Service result:")
    print(result.to_dict())
    print()

    print(
        f"Analysis run ID : "
        f"{result.analysis_run_id}"
    )
    print(
        f"Report type     : "
        f"{result.report_type}"
    )
    print(
        f"Analysis date   : "
        f"{result.analysis_date}"
    )
    print(
        f"Context version : "
        f"{result.context_version}"
    )
    print(
        f"Context hash    : "
        f"{result.context_hash}"
    )
    print(
        f"Status          : "
        f"{result.status}"
    )
    print()

    print(
        "NationalReportService Step 10 test berhasil."
    )


if __name__ == "__main__":
    main()