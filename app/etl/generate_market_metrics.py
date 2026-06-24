import pandas as pd
from sqlalchemy import text
from app.database.db import engine


def calculate_change(latest_price, past_price):
    if pd.isna(past_price) or past_price == 0:
        return None

    return round(((latest_price - past_price) / past_price) * 100, 2)


def get_past_price(group, latest_date, months_back):
    target_date = latest_date - pd.DateOffset(months=months_back)

    past_rows = group[group["price_date"] <= target_date]

    if past_rows.empty:
        return None

    return past_rows.sort_values("price_date").iloc[-1]["price"]


def classify_trend(change_3m):
    if change_3m is None:
        return "insufficient_data"

    if change_3m >= 5:
        return "bullish"

    if change_3m <= -5:
        return "bearish"

    return "stable"


def main():
    query = """
        SELECT
            price_date,
            commodity_name,
            province_name,
            price
        FROM commodity_prices
        WHERE price IS NOT NULL
    """

    df = pd.read_sql(query, engine)
    df["price_date"] = pd.to_datetime(df["price_date"])

    metrics = []

    for (commodity, province), group in df.groupby(["commodity_name", "province_name"]):
        group = group.sort_values("price_date")

        latest = group.iloc[-1]
        latest_date = latest["price_date"]
        latest_price = latest["price"]

        price_1m = get_past_price(group, latest_date, 1)
        price_3m = get_past_price(group, latest_date, 3)
        price_6m = get_past_price(group, latest_date, 6)

        change_1m = calculate_change(latest_price, price_1m)
        change_3m = calculate_change(latest_price, price_3m)
        change_6m = calculate_change(latest_price, price_6m)

        metrics.append(
            {
                "commodity_name": commodity,
                "province_name": province,
                "latest_date": latest_date.date(),
                "latest_price": latest_price,
                "price_1m_ago": price_1m,
                "change_1m": change_1m,
                "price_3m_ago": price_3m,
                "change_3m": change_3m,
                "price_6m_ago": price_6m,
                "change_6m": change_6m,
                "trend": classify_trend(change_3m),
            }
        )

    metrics_df = pd.DataFrame(metrics)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS market_metrics"))

    metrics_df.to_sql(
        "market_metrics",
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Generated {len(metrics_df)} market metrics rows")
    print(metrics_df.head())


if __name__ == "__main__":
    main()