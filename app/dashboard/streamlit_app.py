import pandas as pd
import streamlit as st
import plotly.express as px
from app.database.db import engine
from app.ai.price_forecaster import forecast_price

st.set_page_config(
    page_title="AI Food Price Intelligence",
    page_icon="📊",
    layout="wide",
)


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


@st.cache_data
def load_data():
    prices = pd.read_sql("SELECT * FROM commodity_prices", engine)
    metrics = pd.read_sql("SELECT * FROM market_metrics", engine)
    scores = pd.read_sql("SELECT * FROM commodity_scores", engine)

    prices["price_date"] = pd.to_datetime(prices["price_date"])
    scores["latest_date"] = pd.to_datetime(scores["latest_date"])

    return prices, metrics, scores


prices, metrics, scores = load_data()

st.title("AI Food Price Intelligence Dashboard")
st.caption("Indonesia basic goods price intelligence using PIHPS + PostgreSQL + Analytics")

# Executive KPI Cards
total_records = len(prices)
total_commodities = scores["commodity_name"].nunique()
total_provinces = scores["province_name"].nunique()
high_risk_count = len(scores[scores["risk_level"] == "HIGH"])

highest_risk = scores.sort_values("score", ascending=False).iloc[0]

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Price Records", f"{total_records:,}")
k2.metric("Commodities", total_commodities)
k3.metric("Provinces", total_provinces)
k4.metric("High Risk Items", high_risk_count)

st.info(
    f"Highest current risk: **{highest_risk['commodity_name']}** "
    f"in **{highest_risk['province_name']}** "
    f"with risk score **{highest_risk['score']:.2f}**."
)

st.subheader("📋 National Market Report")
st.markdown(generate_national_report(scores))

st.subheader("🔥 Top Risk Commodities")

top_risk = scores.sort_values("score", ascending=False).head(10).copy()

top_risk_display = top_risk.copy()
top_risk_display["latest_price"] = top_risk_display["latest_price"].apply(lambda x: f"Rp {x:,.0f}")
top_risk_display["change_1m"] = top_risk_display["change_1m"].apply(lambda x: f"{x:.2f}%")
top_risk_display["change_3m"] = top_risk_display["change_3m"].apply(lambda x: f"{x:.2f}%")
top_risk_display["change_6m"] = top_risk_display["change_6m"].apply(lambda x: f"{x:.2f}%")
top_risk_display["score"] = top_risk_display["score"].apply(lambda x: f"{x:.2f}")

st.dataframe(
    top_risk_display[
        [
            "commodity_name",
            "province_name",
            "latest_price",
            "change_1m",
            "change_3m",
            "change_6m",
            "score",
            "risk_level",
        ]
    ],
    use_container_width=True,
)

top_risk["label"] = top_risk["commodity_name"] + " - " + top_risk["province_name"]

fig_risk = px.bar(
    top_risk.sort_values("score", ascending=True),
    x="score",
    y="label",
    color="risk_level",
    orientation="h",
    hover_data=["latest_price", "change_1m", "change_3m", "change_6m"],
    title="Top 10 Commodity Risk Score",
)

fig_risk.update_layout(
    yaxis_title="Commodity - Province",
    xaxis_title="Risk Score",
)

st.plotly_chart(fig_risk, use_container_width=True)

st.subheader("🧠 AI Market Insights")

top_insights = scores.sort_values("score", ascending=False).head(5)

for _, row in top_insights.iterrows():
    st.markdown(generate_insight(row))

st.subheader("📈 Commodity Price Trend")

commodity_options = sorted(prices["commodity_name"].dropna().unique())
province_options = sorted(prices["province_name"].dropna().unique())

col1, col2 = st.columns(2)

selected_commodity = col1.selectbox("Pilih Komoditas", commodity_options)
selected_province = col2.selectbox("Pilih Provinsi", province_options)

filtered = prices[
    (prices["commodity_name"] == selected_commodity)
    & (prices["province_name"] == selected_province)
].copy()

fig_price = px.line(
    filtered,
    x="price_date",
    y="price",
    markers=True,
    title=f"Tren Harga {selected_commodity} - {selected_province}",
)

st.plotly_chart(fig_price, use_container_width=True)

st.subheader("📊 Market Metrics")


st.subheader("🔮 Price Forecast")

forecast_df = forecast_price(
    commodity_name=selected_commodity,
    province_name=selected_province,
    periods=3,
)

if forecast_df is not None:
    forecast_display = forecast_df.copy()
    forecast_display["predicted_price"] = forecast_display["predicted_price"].apply(
        lambda x: f"Rp {x:,.0f}"
    )

    st.dataframe(
        forecast_display[
            [
                "forecast_date",
                "commodity_name",
                "province_name",
                "predicted_price",
            ]
        ],
        use_container_width=True,
    )

    historical_chart = filtered[["price_date", "price"]].copy()
    historical_chart = historical_chart.rename(
        columns={
            "price_date": "date",
            "price": "price",
        }
    )
    historical_chart["type"] = "Historical"

    forecast_chart = forecast_df[["forecast_date", "predicted_price"]].copy()
    forecast_chart = forecast_chart.rename(
        columns={
            "forecast_date": "date",
            "predicted_price": "price",
        }
    )
    forecast_chart["date"] = pd.to_datetime(forecast_chart["date"])
    forecast_chart["type"] = "Forecast"

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
        title=f"Forecast Harga {selected_commodity} - {selected_province}",
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

else:
    st.warning("Data belum cukup untuk membuat forecast.")

metric_row = metrics[
    (metrics["commodity_name"] == selected_commodity)
    & (metrics["province_name"] == selected_province)
]

if not metric_row.empty:
    row = metric_row.iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Latest Price", f"Rp {row['latest_price']:,.0f}")
    c2.metric("1M Change", f"{row['change_1m']:.2f}%")
    c3.metric("3M Change", f"{row['change_3m']:.2f}%")
    c4.metric("6M Change", f"{row['change_6m']:.2f}%")