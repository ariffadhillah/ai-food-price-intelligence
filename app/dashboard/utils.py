def generate_insight(row):
    return (
        f"**{row['commodity_name']} di {row['province_name']}** berada di harga "
        f"**Rp {row['latest_price']:,.0f}**. "
        f"Perubahan 1 bulan **{row['change_1m']:.2f}%**, "
        f"3 bulan **{row['change_3m']:.2f}%**, "
        f"dan 6 bulan **{row['change_6m']:.2f}%**. "
        f"Risk score **{row['score']:.2f}** dengan level **{row['risk_level']}**."
    )


def generate_national_report(scores):
    top = scores.sort_values("score", ascending=False)
    top3 = top.head(3)

    commodities = ", ".join(top3["commodity_name"].unique())
    provinces = ", ".join(top3["province_name"].tolist())
    high_count = len(scores[scores["risk_level"] == "HIGH"])

    return f"""
{commodities} mendominasi daftar komoditas berisiko tinggi di Indonesia.

Provinsi dengan tekanan harga terbesar saat ini adalah {provinces}.

Sebanyak {high_count} kombinasi komoditas-provinsi saat ini berada dalam kategori HIGH risk dan memerlukan pemantauan lebih lanjut.
"""


def generate_market_health(scores):
    high_count = len(scores[scores["risk_level"] == "HIGH"])
    total_count = len(scores)

    high_ratio = (high_count / total_count) * 100 if total_count else 0

    if high_ratio >= 20:
        return "Volatile", "HIGH", "⚠️"
    elif high_ratio >= 10:
        return "Watchlist", "MEDIUM", "🟡"

    return "Stable", "LOW", "🟢"


def generate_ai_executive_summary(scores):
    top = scores.sort_values("score", ascending=False)
    highest = top.iloc[0]

    high_count = len(scores[scores["risk_level"] == "HIGH"])
    market_status, risk_level, icon = generate_market_health(scores)

    return {
        "market_status": market_status,
        "risk_level": risk_level,
        "icon": icon,
        "top_commodity": highest["commodity_name"],
        "top_province": highest["province_name"],
        "top_score": highest["score"],
        "high_count": high_count,
    }