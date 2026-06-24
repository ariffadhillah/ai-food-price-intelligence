import pandas as pd
from app.database.db import engine


CSV_PATH = "data/processed/pihps_grid_history_normalized.csv"
TABLE_NAME = "commodity_prices"


def main():
    df = pd.read_csv(CSV_PATH)

    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date

    df = df[
        [
            "price_date",
            "commodity_name",
            "province_id",
            "province_name",
            "price",
            "price_change",
            "percentage_change",
            "source",
        ]
    ]

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
    )

    print(f"Imported {len(df)} rows into {TABLE_NAME}")


if __name__ == "__main__":
    main()