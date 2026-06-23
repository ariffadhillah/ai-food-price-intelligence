import json
import pandas as pd
from pathlib import Path


RAW_DIR = Path("data/raw/grid_history")
OUTPUT_PATH = Path("data/processed/pihps_grid_history_normalized.csv")


MONTH_MAP = {
    "Jan": "Jan",
    "Feb": "Feb",
    "Mar": "Mar",
    "Apr": "Apr",
    "Mei": "May",
    "Jun": "Jun",
    "Jul": "Jul",
    "Agt": "Aug",
    "Sep": "Sep",
    "Okt": "Oct",
    "Nov": "Nov",
    "Des": "Dec",
}


def parse_indonesian_date(date_text: str):
    if pd.isna(date_text):
        return None

    parts = str(date_text).split()

    if len(parts) != 3:
        return None

    day, month, year = parts
    month_en = MONTH_MAP.get(month, month)

    normalized = f"{day} {month_en} 20{year}"
    return pd.to_datetime(normalized, format="%d %b %Y").date()


def clean_rupiah(value):
    if pd.isna(value):
        return None

    text = str(value)
    text = text.replace("Rp", "")
    text = text.replace(".", "")
    text = text.replace(",", "")
    text = text.strip()

    if text == "":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def load_json(file_path: Path) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("data", [])


def normalize_file(file_path: Path) -> pd.DataFrame:
    rows = load_json(file_path)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df = df.rename(
        columns={
            "ProvID": "province_id",
            "Provinsi": "province_name",
            "Tanggal": "price_date",
            "Komoditas": "commodity_name",
            "Nilai": "price",
            "NilaiDiff": "price_change_text",
            "Percentage": "percentage_change",
            "TanggalLast": "previous_date_text",
        }
    )

    df["price_date"] = df["price_date"].apply(parse_indonesian_date)
    df["price_change"] = df["price_change_text"].apply(clean_rupiah)
    df["source"] = "PIHPS Bank Indonesia"

    return df[
        [
            "price_date",
            "province_id",
            "province_name",
            "commodity_name",
            "price",
            "price_change",
            "price_change_text",
            "percentage_change",
            "previous_date_text",
            "source",
        ]
    ]


def main():
    all_data = []

    files = sorted(RAW_DIR.glob("pihps_grid_commodity_*.json"))

    for file_path in files:
        print(f"Normalizing: {file_path.name}")

        df = normalize_file(file_path)

        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("No data found.")
        return

    final_df = pd.concat(all_data, ignore_index=True)
    final_df = final_df.sort_values(["commodity_name", "province_name", "price_date"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved normalized grid history to: {OUTPUT_PATH}")
    print(final_df.head())


if __name__ == "__main__":
    main()