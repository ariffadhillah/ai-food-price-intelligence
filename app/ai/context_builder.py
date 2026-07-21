from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd


def make_json_safe(value: Any) -> Any:
    """
    Convert common pandas, NumPy, datetime, and NaN values
    into JSON-compatible Python values.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except (TypeError, ValueError):
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            pass

    return value


def sanitize_data(value: Any) -> Any:
    """
    Recursively sanitize dictionaries, lists, tuples, and scalar values.
    """

    if isinstance(value, dict):
        return {
            str(key): sanitize_data(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            sanitize_data(item)
            for item in value
        ]

    return make_json_safe(value)


def dataframe_to_records(
    dataframe: pd.DataFrame,
    columns: list[str],
    limit: int | None = None,
) -> list[dict]:
    """
    Convert selected DataFrame columns into JSON-safe records.
    """

    if dataframe is None or dataframe.empty:
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
    ].copy()

    if limit is not None:
        selected = selected.head(limit)

    records = selected.to_dict(
        orient="records",
    )

    return sanitize_data(records)


def safe_numeric_series(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:
    """
    Return a cleaned numeric series for a DataFrame column.
    """

    if dataframe is None:
        return pd.Series(dtype="float64")

    if dataframe.empty:
        return pd.Series(dtype="float64")

    if column not in dataframe.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).dropna()


def calculate_data_coverage(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
) -> dict:
    """
    Calculate basic coverage information used by the AI
    when assigning its confidence score.
    """

    score_rows = len(scores) if scores is not None else 0
    province_rows = len(provinces) if provinces is not None else 0
    analytics_rows = (
        len(analytics)
        if analytics is not None
        else 0
    )

    score_provinces = 0
    score_commodities = 0

    if (
        scores is not None
        and not scores.empty
    ):
        if "province_name" in scores.columns:
            score_provinces = int(
                scores["province_name"]
                .dropna()
                .nunique()
            )

        if "commodity_name" in scores.columns:
            score_commodities = int(
                scores["commodity_name"]
                .dropna()
                .nunique()
            )

    province_coverage_percentage = min(
        score_provinces / 38 * 100,
        100,
    )

    return {
        "score_record_count": score_rows,
        "province_analytics_record_count": province_rows,
        "commodity_analytics_record_count": analytics_rows,
        "covered_province_count": score_provinces,
        "expected_province_count": 38,
        "province_coverage_percentage": round(
            province_coverage_percentage,
            2,
        ),
        "covered_commodity_count": score_commodities,
        "has_score_data": score_rows > 0,
        "has_province_analytics": province_rows > 0,
        "has_commodity_analytics": analytics_rows > 0,
    }


def calculate_market_statistics(
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
) -> dict:
    """
    Calculate deterministic national summary statistics.
    """

    score_values = safe_numeric_series(
        scores,
        "score",
    )

    province_risk_values = safe_numeric_series(
        provinces,
        "avg_risk_score",
    )

    volatility_values = safe_numeric_series(
        analytics,
        "std_price",
    )

    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0

    if (
        scores is not None
        and not scores.empty
        and "risk_level" in scores.columns
    ):
        normalized_risk = (
            scores["risk_level"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        high_risk_count = int(
            (normalized_risk == "HIGH").sum()
        )

        medium_risk_count = int(
            (normalized_risk == "MEDIUM").sum()
        )

        low_risk_count = int(
            (normalized_risk == "LOW").sum()
        )

    total_risk_records = (
        high_risk_count
        + medium_risk_count
        + low_risk_count
    )

    high_risk_ratio = (
        high_risk_count
        / total_risk_records
        * 100
        if total_risk_records
        else 0
    )

    return {
        "total_risk_records": total_risk_records,
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "low_risk_count": low_risk_count,
        "high_risk_ratio_percentage": round(
            high_risk_ratio,
            2,
        ),
        "national_average_score": (
            round(float(score_values.mean()), 2)
            if not score_values.empty
            else None
        ),
        "maximum_score": (
            round(float(score_values.max()), 2)
            if not score_values.empty
            else None
        ),
        "national_average_province_risk": (
            round(
                float(province_risk_values.mean()),
                2,
            )
            if not province_risk_values.empty
            else None
        ),
        "maximum_province_risk": (
            round(
                float(province_risk_values.max()),
                2,
            )
            if not province_risk_values.empty
            else None
        ),
        "average_price_volatility": (
            round(
                float(volatility_values.mean()),
                2,
            )
            if not volatility_values.empty
            else None
        ),
        "maximum_price_volatility": (
            round(
                float(volatility_values.max()),
                2,
            )
            if not volatility_values.empty
            else None
        ),
    }


def get_missing_provinces(
    scores: pd.DataFrame,
    expected_provinces: list[str] | None = None,
) -> list[str]:
    """
    Return expected provinces that do not appear in score data.

    The expected list is optional because province naming can vary
    between datasets.
    """

    if not expected_provinces:
        return []

    available_provinces: set[str] = set()

    if (
        scores is not None
        and not scores.empty
        and "province_name" in scores.columns
    ):
        available_provinces = {
            str(value).strip()
            for value in scores["province_name"].dropna()
        }

    return sorted(
        province
        for province in expected_provinces
        if province not in available_provinces
    )


def build_national_analysis_context(
    rule_report: dict,
    scores: pd.DataFrame,
    provinces: pd.DataFrame,
    analytics: pd.DataFrame,
    expected_provinces: list[str] | None = None,
) -> dict:
    """
    Build a reusable structured context for national AI analysis.

    This function is responsible for understanding DataFrames.
    The prompt engine only receives the resulting dictionary.
    """

    sorted_scores = (
        scores.sort_values(
            "score",
            ascending=False,
        )
        if (
            scores is not None
            and not scores.empty
            and "score" in scores.columns
        )
        else pd.DataFrame()
    )

    sorted_provinces = (
        provinces.sort_values(
            "avg_risk_score",
            ascending=False,
        )
        if (
            provinces is not None
            and not provinces.empty
            and "avg_risk_score" in provinces.columns
        )
        else pd.DataFrame()
    )

    sorted_volatility = (
        analytics.sort_values(
            "std_price",
            ascending=False,
        )
        if (
            analytics is not None
            and not analytics.empty
            and "std_price" in analytics.columns
        )
        else pd.DataFrame()
    )

    context = {
        "context_metadata": {
            "context_type": "national_food_price_analysis",
            "context_version": "1.0.0",
            "generated_at": datetime.now(
                timezone.utc,
            ).isoformat(),
            "country": "Indonesia",
            "currency": "IDR",
            "expected_province_count": 38,
        },
        "data_coverage": calculate_data_coverage(
            scores=scores,
            provinces=provinces,
            analytics=analytics,
        ),
        "market_statistics": calculate_market_statistics(
            scores=scores,
            provinces=provinces,
            analytics=analytics,
        ),
        "rule_based_assessment": sanitize_data(
            rule_report,
        ),
        "highest_risk_provinces": dataframe_to_records(
            dataframe=sorted_provinces,
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
        ),
        "highest_risk_commodities": dataframe_to_records(
            dataframe=sorted_scores,
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
        ),
        "highest_volatility_records": dataframe_to_records(
            dataframe=sorted_volatility,
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
        ),
        "missing_provinces": get_missing_provinces(
            scores=scores,
            expected_provinces=expected_provinces,
        ),
        "analysis_constraints": [
            "Gunakan hanya data yang tersedia dalam context.",
            "Jangan mengarang penyebab perubahan harga.",
            "Jangan menganggap korelasi sebagai hubungan sebab-akibat.",
            "Sebutkan keterbatasan apabila cakupan data tidak lengkap.",
            "Pertahankan angka sesuai dengan context.",
        ],
    }

    return sanitize_data(context)