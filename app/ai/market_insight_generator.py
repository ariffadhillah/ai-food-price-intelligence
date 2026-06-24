import pandas as pd
from app.database.db import engine


def generate_insight(row):
    commodity = row["commodity_name"]
    province = row["province_name"]
    price = row["latest_price"]
    change_1m = row["change_1m"]
    change_3m = row["change_3m"]
    change_6m = row["change_6m"]
    score = row["score"]
    risk = row["risk_level"]

    if risk == "HIGH":
        risk_text = "memiliki risiko harga tinggi dan perlu dipantau secara serius"
    elif risk == "MEDIUM":
        risk_text = "menunjukkan pergerakan harga sedang"
    else:
        risk_text = "relatif stabil berdasarkan data historis"

    return (
        f"{commodity} di {province} saat ini berada di harga Rp {price:,.0f}. "
        f"Dalam 1 bulan terakhir berubah {change_1m:.2f}%, "
        f"3 bulan {change_3m:.2f}%, dan 6 bulan {change_6m:.2f}%. "
        f"Dengan risk score {score:.2f}, komoditas ini {risk_text}."
    )


def main():
    query = """
        SELECT *
        FROM commodity_scores
        ORDER BY score DESC
        LIMIT 10
    """

    df = pd.read_sql(query, engine)
    df["insight"] = df.apply(generate_insight, axis=1)

    print("\nAI Market Insights\n")

    for _, row in df.iterrows():
        print(f"- {row['insight']}")


if __name__ == "__main__":
    main()