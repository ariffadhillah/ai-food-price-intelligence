import pandas as pd
from sklearn.linear_model import LinearRegression
from app.database.db import engine


def forecast_price(commodity_name, province_name, periods=3):
    query = """
        SELECT price_date, commodity_name, province_name, price
        FROM commodity_prices
        WHERE commodity_name = %(commodity_name)s
        AND province_name = %(province_name)s
        ORDER BY price_date
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "commodity_name": commodity_name,
            "province_name": province_name,
        },
    )

    if len(df) < 3:
        return None

    df["price_date"] = pd.to_datetime(df["price_date"])
    df["month_index"] = range(len(df))

    X = df[["month_index"]]
    y = df["price"]

    model = LinearRegression()
    model.fit(X, y)

    future_rows = []

    last_date = df["price_date"].max()
    last_index = df["month_index"].max()

    for i in range(1, periods + 1):
        future_index = last_index + i
        future_date = last_date + pd.DateOffset(months=i)

        future_df = pd.DataFrame(
            {"month_index": [future_index]}
        )

        predicted_price = model.predict(future_df)[0]

        future_rows.append(
            {
                "forecast_date": future_date.date(),
                "commodity_name": commodity_name,
                "province_name": province_name,
                "predicted_price": round(predicted_price, 2),
            }
        )

    return pd.DataFrame(future_rows)


def generate_prediction_summary(
    commodity_name,
    province_name,
    latest_price,
    forecast_df,
):
    if forecast_df is None or forecast_df.empty:
        return {
            "trend": "Insufficient Data",
            "confidence": "Low",
            "summary": "Data belum cukup untuk membuat prediksi harga.",
            "recommendation": "Tambahkan lebih banyak data historis untuk meningkatkan akurasi prediksi.",
        }

    final_forecast_price = forecast_df.iloc[-1]["predicted_price"]

    expected_change = (
        (final_forecast_price - latest_price) / latest_price
    ) * 100

    if expected_change >= 10:
        trend = "Increasing"
        confidence = "High"
        recommendation = "Perlu pemantauan serius terhadap pasokan, distribusi, dan potensi kenaikan lanjutan."
    elif expected_change >= 3:
        trend = "Slightly Increasing"
        confidence = "Medium"
        recommendation = "Perlu dipantau secara berkala karena ada indikasi kenaikan harga."
    elif expected_change <= -10:
        trend = "Decreasing"
        confidence = "High"
        recommendation = "Harga diperkirakan turun, tetapi tetap perlu memantau volatilitas pasar."
    elif expected_change <= -3:
        trend = "Slightly Decreasing"
        confidence = "Medium"
        recommendation = "Harga menunjukkan potensi penurunan ringan dalam beberapa bulan ke depan."
    else:
        trend = "Stable"
        confidence = "Medium"
        recommendation = "Harga relatif stabil berdasarkan tren historis saat ini."

    summary = (
        f"Forecast menunjukkan harga {commodity_name} di {province_name} "
        f"diperkirakan menjadi Rp {final_forecast_price:,.0f} dalam 3 bulan ke depan. "
        f"Perubahan estimasi dari harga terbaru adalah {expected_change:.2f}%."
    )

    return {
        "trend": trend,
        "confidence": confidence,
        "expected_change": round(expected_change, 2),
        "final_forecast_price": round(final_forecast_price, 2),
        "summary": summary,
        "recommendation": recommendation,
    }


def main():
    result = forecast_price(
        commodity_name="Cabai Merah",
        province_name="Sulawesi Tenggara",
        periods=3,
    )

    if result is None:
        print("Not enough data for forecasting.")
    else:
        print(result)


if __name__ == "__main__":
    main()