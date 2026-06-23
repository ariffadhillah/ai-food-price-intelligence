import json
import pandas as pd
from pathlib import Path


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def load_chart_json(file_path: Path) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("data", [])


def normalize_chart_file(file_path: Path) -> pd.DataFrame:
    rows = load_chart_json(file_path)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "date": "price_date",
            "name": "commodity_name",
            "denomination": "unit",
            "nominal": "price",
            "harga": "price_change",
            "fluc": "percentage_change",
        }
    )

    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date
    df["source"] = "PIHPS Bank Indonesia"
    df["province"] = "Semua Provinsi"

    return df[
        [
            "price_date",
            "commodity_name",
            "unit",
            "price",
            "price_change",
            "percentage_change",
            "province",
            "source",
        ]
    ]


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = list(RAW_DIR.glob("pihps_chart_*.json"))

    all_data = []

    for file_path in files:
        print(f"Normalizing: {file_path.name}")
        df = normalize_chart_file(file_path)

        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("No chart data found.")
        return

    final_df = pd.concat(all_data, ignore_index=True)

    output_path = PROCESSED_DIR / "pihps_prices_normalized.csv"
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved normalized data to: {output_path}")
    print(final_df.head())


if __name__ == "__main__":
    main()