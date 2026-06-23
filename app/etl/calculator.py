import pandas as pd
from pathlib import Path


INPUT_PATH = Path("data/processed/pihps_prices_normalized.csv")
OUTPUT_PATH = Path("data/processed/pihps_price_summary.csv")


def calculate_summary(df: pd.DataFrame) -> pd.DataFrame:
    df["price_date"] = pd.to_datetime(df["price_date"])
    df = df.sort_values(["commodity_name", "price_date"])

    summaries = []

    for commodity, group in df.groupby("commodity_name"):
        group = group.sort_values("price_date")

        first = group.iloc[0]
        latest = group.iloc[-1]

        first_price = first["price"]
        latest_price = latest["price"]

        price_change = latest_price - first_price

        if first_price and first_price != 0:
            percentage_change = (price_change / first_price) * 100
        else:
            percentage_change = None

        summaries.append(
            {
                "commodity_name": commodity,
                "unit": latest["unit"],
                "start_date": first["price_date"].date(),
                "latest_date": latest["price_date"].date(),
                "start_price": first_price,
                "latest_price": latest_price,
                "price_change": price_change,
                "percentage_change": round(percentage_change, 2)
                if percentage_change is not None
                else None,
                "min_price": group["price"].min(),
                "max_price": group["price"].max(),
                "province": latest["province"],
                "source": latest["source"],
            }
        )

    return pd.DataFrame(summaries)


def main():
    df = pd.read_csv(INPUT_PATH)

    summary_df = calculate_summary(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved summary to: {OUTPUT_PATH}")
    print(summary_df)


if __name__ == "__main__":
    main()