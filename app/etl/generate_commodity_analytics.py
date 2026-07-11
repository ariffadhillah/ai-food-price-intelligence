import pandas as pd
from sqlalchemy import text
from app.database.db import engine


def classify_volatility(std_price, avg_price):
    if avg_price == 0 or pd.isna(std_price):
        return "UNKNOWN"

    ratio = (std_price / avg_price) * 100

    if ratio >= 25:
        return "HIGH"
    elif ratio >= 10:
        return "MEDIUM"
    return "LOW"


def classify_trend(first_price, latest_price):
    if first_price == 0 or pd.isna(first_price):
        return "UNKNOWN"

    change = ((latest_price - first_price) / first_price) * 100

    if change >= 20:
        return "STRONG_UPTREND"
    elif change >= 5:
        return "UPTREND"
    elif change <= -20:
        return "STRONG_DOWNTREND"
    elif change <= -5:
        return "DOWNTREND"
    return "STABLE"


def main():
    df = pd.read_sql(
        """
        SELECT
            price_date,
            commodity_name,
            province_name,
            price
        FROM commodity_prices
        WHERE price IS NOT NULL
        """,
        engine,
    )

    df["price_date"] = pd.to_datetime(df["price_date"])

    rows = []

    for (commodity, province), group in df.groupby(["commodity_name", "province_name"]):
        group = group.sort_values("price_date")

        avg_price = group["price"].mean()
        min_price = group["price"].min()
        max_price = group["price"].max()
        median_price = group["price"].median()
        std_price = group["price"].std()
        latest_price = group.iloc[-1]["price"]
        first_price = group.iloc[0]["price"]
        price_range = max_price - min_price
        data_points = len(group)

        rows.append(
            {
                "commodity_name": commodity,
                "province_name": province,
                "avg_price": round(avg_price, 2),
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "median_price": round(median_price, 2),
                "std_price": round(std_price, 2) if not pd.isna(std_price) else 0,
                "volatility_level": classify_volatility(std_price, avg_price),
                "trend_strength": classify_trend(first_price, latest_price),
                "latest_price": round(latest_price, 2),
                "price_range": round(price_range, 2),
                "data_points": data_points,
            }
        )

    analytics_df = pd.DataFrame(rows)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS commodity_analytics"))

    analytics_df.to_sql(
        "commodity_analytics",
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Generated {len(analytics_df)} commodity analytics rows")
    print(analytics_df.head())


if __name__ == "__main__":
    main()