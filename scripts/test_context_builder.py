import json

import pandas as pd

from app.ai.context_builder import (
    build_national_analysis_context,
)


def main():
    scores = pd.DataFrame(
        [
            {
                "province_name": "Sulawesi Tenggara",
                "commodity_name": "Cabai Merah",
                "score": 25.8,
                "risk_level": "HIGH",
                "latest_price": 75000,
                "change_1m": 12.6,
                "change_3m": 18.4,
                "change_6m": 21.2,
            },
            {
                "province_name": "Aceh",
                "commodity_name": "Beras",
                "score": 8.4,
                "risk_level": "LOW",
                "latest_price": 15000,
                "change_1m": 1.2,
                "change_3m": 2.4,
                "change_6m": 3.1,
            },
        ]
    )

    provinces = pd.DataFrame(
        [
            {
                "province_name": "Sulawesi Tenggara",
                "avg_risk_score": 18.4,
                "max_risk_score": 25.8,
                "high_risk_count": 1,
                "top_risk_commodity": "Cabai Merah",
                "top_risk_price": 75000,
                "avg_change_1m": 12.6,
                "avg_change_3m": 18.4,
                "avg_change_6m": 21.2,
            },
            {
                "province_name": "Aceh",
                "avg_risk_score": 8.4,
                "max_risk_score": 8.4,
                "high_risk_count": 0,
                "top_risk_commodity": "Beras",
                "top_risk_price": 15000,
                "avg_change_1m": 1.2,
                "avg_change_3m": 2.4,
                "avg_change_6m": 3.1,
            },
        ]
    )

    analytics = pd.DataFrame(
        [
            {
                "province_name": "Sulawesi Tenggara",
                "commodity_name": "Cabai Merah",
                "latest_price": 75000,
                "avg_price": 68000,
                "min_price": 55000,
                "max_price": 76000,
                "std_price": 7200,
                "change_1m": 12.6,
                "change_3m": 18.4,
                "change_6m": 21.2,
            }
        ]
    )

    rule_report = {
        "market_status": "WATCHLIST",
        "headline": (
            "Pasar nasional berada dalam kondisi waspada."
        ),
        "key_findings": [
            "Cabai Merah memiliki skor tertinggi."
        ],
        "recommendations": [
            "Tingkatkan pemantauan harga Cabai Merah."
        ],
    }

    context = build_national_analysis_context(
        rule_report=rule_report,
        scores=scores,
        provinces=provinces,
        analytics=analytics,
        expected_provinces=[
            "Aceh",
            "Sulawesi Tenggara",
            "Papua Selatan",
        ],
    )

    print(
        json.dumps(
            context,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()