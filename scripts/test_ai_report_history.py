from datetime import date

from app.ai.context_hash import (
    generate_context_hash,
)
from app.database.ai_report_repository import (
    AIReportRepository,
)


def main():
    context = {
        "context_metadata": {
            "context_type": (
                "national_food_price_analysis"
            ),
            "context_version": "1.0.0",
            "generated_at": (
                "2026-07-21T10:00:00+00:00"
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
        },
    }

    context_hash = generate_context_hash(
        context,
    )

    repository = AIReportRepository()

    run_id = repository.create_analysis_run(
        report_type="national",
        analysis_date=date.today(),
        context_version="1.0.0",
        context_hash=context_hash,
        context_json=context,
    )

    report = {
        "market_status": "WATCHLIST",
        "confidence_score": 90.0,
        "headline": (
            "Pasar pangan nasional berada "
            "dalam kondisi waspada."
        ),
        "executive_summary": (
            "Laporan pengujian penyimpanan "
            "AI report history."
        ),
        "critical_provinces": [],
        "critical_commodities": [],
        "key_findings": [],
        "recommendations": [],
        "data_limitations": [],
    }

    version_id = repository.save_report_version(
        analysis_run_id=run_id,
        provider="test",
        model_name="test-model",
        prompt_version="1.0.0",
        schema_version="1.0.0",
        system_instructions=(
            "Test system instructions"
        ),
        prompt_text="Test prompt",
        report_json=report,
        market_status="WATCHLIST",
        confidence_score=90.0,
        headline=report["headline"],
        input_tokens=100,
        output_tokens=200,
        reasoning_tokens=0,
        total_tokens=300,
        estimated_cost_usd=None,
        latency_ms=1500,
        response_id="test-response",
        response_status="completed",
    )

    repository.mark_run_completed(
        run_id,
    )

    latest = repository.get_latest_report(
        report_type="national",
    )

    print(
        f"Analysis run ID: {run_id}"
    )
    print(
        f"Report version ID: {version_id}"
    )
    print(
        f"Context hash: {context_hash}"
    )
    print(
        "Latest report:"
    )
    print(latest)


if __name__ == "__main__":
    main()