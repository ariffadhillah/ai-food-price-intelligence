def generate_national_ai_report(
    scores,
    provinces,
    analytics,
):
    if scores.empty or provinces.empty or analytics.empty:
        return {
            "market_status": "UNKNOWN",
            "headline": "Data belum cukup untuk menghasilkan analisis nasional.",
            "key_findings": [],
            "critical_provinces": [],
            "critical_commodities": [],
            "recommendations": [],
        }

    top_scores = scores.sort_values(
        "score",
        ascending=False,
    )

    top_provinces = provinces.sort_values(
        "avg_risk_score",
        ascending=False,
    )

    top_volatility = analytics.sort_values(
        "std_price",
        ascending=False,
    )

    high_risk_count = int(
        (scores["risk_level"] == "HIGH").sum()
    )

    total_scores = len(scores)

    high_risk_ratio = (
        high_risk_count / total_scores * 100
        if total_scores
        else 0
    )

    if high_risk_ratio >= 20:
        market_status = "HIGH PRESSURE"
    elif high_risk_ratio >= 10:
        market_status = "WATCHLIST"
    else:
        market_status = "STABLE"

    highest_score = top_scores.iloc[0]
    highest_province = top_provinces.iloc[0]
    highest_volatility = top_volatility.iloc[0]

    critical_provinces = (
        top_provinces.head(5)["province_name"]
        .dropna()
        .tolist()
    )

    critical_commodities = (
        top_scores.head(10)["commodity_name"]
        .dropna()
        .drop_duplicates()
        .head(5)
        .tolist()
    )

    headline = (
        f"Kondisi pasar pangan nasional berada pada kategori "
        f"{market_status}. Risiko tertinggi saat ini berasal dari "
        f"{highest_score['commodity_name']} di "
        f"{highest_score['province_name']} dengan skor "
        f"{highest_score['score']:.2f}."
    )

    key_findings = [
        (
            f"Terdapat {high_risk_count} kombinasi komoditas-provinsi "
            f"dalam kategori HIGH, atau {high_risk_ratio:.2f}% "
            f"dari seluruh data yang dianalisis."
        ),
        (
            f"Provinsi dengan rata-rata risiko tertinggi adalah "
            f"{highest_province['province_name']} dengan skor "
            f"{highest_province['avg_risk_score']:.2f}."
        ),
        (
            f"Komoditas paling volatil adalah "
            f"{highest_volatility['commodity_name']} di "
            f"{highest_volatility['province_name']} dengan standar "
            f"deviasi harga Rp {highest_volatility['std_price']:,.0f}."
        ),
        (
            f"Komoditas paling kritis secara nasional saat ini adalah "
            f"{highest_score['commodity_name']} dengan perubahan "
            f"1 bulan sebesar {highest_score['change_1m']:.2f}%."
        ),
    ]

    recommendations = []

    if high_risk_ratio >= 20:
        recommendations.extend(
            [
                "Tingkatkan frekuensi pemantauan harga dan pasokan pada provinsi berisiko tinggi.",
                "Prioritaskan evaluasi distribusi dan logistik untuk komoditas dengan kenaikan ekstrem.",
                "Siapkan intervensi pasokan untuk wilayah yang menunjukkan volatilitas tinggi.",
            ]
        )
    elif high_risk_ratio >= 10:
        recommendations.extend(
            [
                "Pantau komoditas utama pada provinsi dengan skor risiko tertinggi.",
                "Lakukan evaluasi mingguan terhadap perubahan harga dan distribusi.",
                "Perhatikan komoditas dengan tren kenaikan kuat sebelum masuk kategori HIGH.",
            ]
        )
    else:
        recommendations.extend(
            [
                "Pertahankan pemantauan rutin terhadap harga pangan nasional.",
                "Fokus pada komoditas yang menunjukkan peningkatan volatilitas.",
                "Gunakan hasil forecast untuk mendeteksi risiko kenaikan lebih awal.",
            ]
        )

    return {
        "market_status": market_status,
        "headline": headline,
        "key_findings": key_findings,
        "critical_provinces": critical_provinces,
        "critical_commodities": critical_commodities,
        "recommendations": recommendations,
    }