import pandas as pd
from sqlalchemy import text
from app.database.db import engine


def main():
    scores = pd.read_sql(
        """
        SELECT
            commodity_name,
            province_name,
            latest_price,
            change_1m,
            change_3m,
            change_6m,
            score,
            risk_level
        FROM commodity_scores
        """,
        engine,
    )

    rows = []

    for province, group in scores.groupby("province_name"):
        top_row = group.sort_values("score", ascending=False).iloc[0]

        rows.append(
            {
                "province_name": province,
                "avg_risk_score": round(group["score"].mean(), 2),
                "max_risk_score": round(group["score"].max(), 2),
                "high_risk_count": int((group["risk_level"] == "HIGH").sum()),
                "avg_change_1m": round(group["change_1m"].mean(), 2),
                "avg_change_3m": round(group["change_3m"].mean(), 2),
                "avg_change_6m": round(group["change_6m"].mean(), 2),
                "top_risk_commodity": top_row["commodity_name"],
                "top_risk_price": round(top_row["latest_price"], 2),
                "top_risk_level": top_row["risk_level"],
            }
        )

    province_df = pd.DataFrame(rows)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS province_analytics"))

    province_df.to_sql(
        "province_analytics",
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Generated {len(province_df)} province analytics rows")
    print(province_df.sort_values("avg_risk_score", ascending=False).head(10))


if __name__ == "__main__":
    main()