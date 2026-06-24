import pandas as pd
from sqlalchemy import text
from app.database.db import engine


def safe_abs(value):
    if pd.isna(value):
        return 0
    return abs(value)


def calculate_score(row):
    score = (
        safe_abs(row["change_1m"]) * 0.3
        + safe_abs(row["change_3m"]) * 0.4
        + safe_abs(row["change_6m"]) * 0.3
    )

    return round(score, 2)


def classify_risk(score):
    if score >= 25:
        return "HIGH"
    elif score >= 10:
        return "MEDIUM"
    return "LOW"


def main():
    query = """
        SELECT
            commodity_name,
            province_name,
            latest_date,
            latest_price,
            change_1m,
            change_3m,
            change_6m
        FROM market_metrics
    """

    df = pd.read_sql(query, engine)

    df["score"] = df.apply(calculate_score, axis=1)
    df["risk_level"] = df["score"].apply(classify_risk)

    scores_df = df[
        [
            "commodity_name",
            "province_name",
            "latest_date",
            "latest_price",
            "change_1m",
            "change_3m",
            "change_6m",
            "score",
            "risk_level",
        ]
    ]

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS commodity_scores"))

    scores_df.to_sql(
        "commodity_scores",
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Generated {len(scores_df)} commodity score rows")
    print(scores_df.sort_values("score", ascending=False).head(10))


if __name__ == "__main__":
    main()