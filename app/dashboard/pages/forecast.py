import pandas as pd
import plotly.express as px
import streamlit as st

from app.ai.price_forecaster import (
    forecast_price,
    generate_prediction_summary,
)


def show_forecast_analysis(prices):
    st.title("🔮 Forecast Analysis")
    st.caption(
        "Prediksi harga komoditas berbasis data historis PIHPS "
        "dan model Linear Regression."
    )

    commodity_options = sorted(
        prices["commodity_name"].dropna().unique()
    )
    province_options = sorted(
        prices["province_name"].dropna().unique()
    )

    col1, col2 = st.columns(2)

    selected_commodity = col1.selectbox(
        "Pilih Komoditas",
        commodity_options,
        key="forecast_commodity",
    )

    selected_province = col2.selectbox(
        "Pilih Provinsi",
        province_options,
        key="forecast_province",
    )

    filtered = prices[
        (prices["commodity_name"] == selected_commodity)
        & (prices["province_name"] == selected_province)
    ].copy()

    if filtered.empty:
        st.warning("Data tidak tersedia untuk pilihan ini.")
        return

    forecast_df = forecast_price(
        commodity_name=selected_commodity,
        province_name=selected_province,
        periods=3,
    )

    if forecast_df is None or forecast_df.empty:
        st.warning("Data belum cukup untuk membuat forecast.")
        return

    latest_price = (
        filtered.sort_values("price_date")
        .iloc[-1]["price"]
    )

    prediction = generate_prediction_summary(
        commodity_name=selected_commodity,
        province_name=selected_province,
        latest_price=latest_price,
        forecast_df=forecast_df,
    )

    p1, p2, p3, p4 = st.columns(4)

    p1.metric(
        "Latest Price",
        f"Rp {latest_price:,.0f}",
    )
    p2.metric(
        "Predicted Price",
        f"Rp {prediction['final_forecast_price']:,.0f}",
    )
    p3.metric(
        "Expected Change",
        f"{prediction['expected_change']:.2f}%",
    )
    p4.metric(
        "Confidence",
        prediction["confidence"],
    )

    st.info(
        f"**Trend:** {prediction['trend']}  \n\n"
        f"{prediction['summary']}  \n\n"
        f"**Recommendation:** {prediction['recommendation']}"
    )

    forecast_display = forecast_df.copy()
    forecast_display["predicted_price"] = (
        forecast_display["predicted_price"]
        .apply(lambda value: f"Rp {value:,.0f}")
    )

    st.subheader("Forecast Table")
    st.dataframe(
        forecast_display,
        use_container_width=True,
        hide_index=True,
    )

    historical_chart = filtered[
        ["price_date", "price"]
    ].copy()

    historical_chart = historical_chart.rename(
        columns={"price_date": "date"}
    )
    historical_chart["type"] = "Historical"

    last_historical = (
        historical_chart
        .sort_values("date")
        .iloc[-1:]
        .copy()
    )
    last_historical["type"] = "Forecast"

    forecast_chart = forecast_df[
        ["forecast_date", "predicted_price"]
    ].copy()

    forecast_chart = forecast_chart.rename(
        columns={
            "forecast_date": "date",
            "predicted_price": "price",
        }
    )

    forecast_chart["date"] = pd.to_datetime(
        forecast_chart["date"]
    )
    forecast_chart["type"] = "Forecast"

    forecast_chart = pd.concat(
        [last_historical, forecast_chart],
        ignore_index=True,
    )

    combined_chart = pd.concat(
        [historical_chart, forecast_chart],
        ignore_index=True,
    )

    fig_forecast = px.line(
        combined_chart,
        x="date",
        y="price",
        color="type",
        markers=True,
        title=(
            f"Forecast Harga {selected_commodity} "
            f"- {selected_province}"
        ),
    )

    fig_forecast.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (Rp)",
        legend_title="Data Type",
    )

    st.plotly_chart(
        fig_forecast,
        use_container_width=True,
    )