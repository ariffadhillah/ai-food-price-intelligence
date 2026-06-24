import pandas as pd
import streamlit as st
import plotly.express as px
from app.database.db import engine


st.set_page_config(
    page_title="AI Food Price Intelligence",
    page_icon="📊",
    layout="wide",
)


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

st.subheader("🔥 Top Risk Commodities")

top_risk = scores.sort_values("score", ascending=False).head(10)

top_risk_display = top_risk.copy()
top_risk_display["latest_price"] = top_risk_display["latest_price"].apply(lambda x: f"Rp {x:,.0f}")
top_risk_display["change_1m"] = top_risk_display["change_1m"].apply(lambda x: f"{x:.2f}%")
top_risk_display["change_3m"] = top_risk_display["change_3m"].apply(lambda x: f"{x:.2f}%")
top_risk_display["change_6m"] = top_risk_display["change_6m"].apply(lambda x: f"{x:.2f}%")
top_risk_display["score"] = top_risk_display["score"].apply(lambda x: f"{x:.2f}")

st.dataframe(
    top_risk[
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

# fig_risk = px.bar(
#     top_risk,
#     x="score",
#     y="commodity_name",
#     color="risk_level",
#     orientation="h",
#     hover_data=["province_name", "latest_price", "change_1m", "change_3m", "change_6m"],
#     title="Top 10 Commodity Risk Score",
# )

# top_risk["label"] = top_risk["commodity_name"] + " - " + top_risk["province_name"]

top_risk = scores.sort_values("score", ascending=False).head(10).copy()
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