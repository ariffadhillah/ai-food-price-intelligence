import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path


PRICE_PATH = Path("data/processed/pihps_prices_normalized.csv")
SUMMARY_PATH = Path("data/processed/pihps_price_summary.csv")


st.set_page_config(
    page_title="AI Food Price Intelligence",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    prices = pd.read_csv(PRICE_PATH)
    summary = pd.read_csv(SUMMARY_PATH)

    prices["price_date"] = pd.to_datetime(prices["price_date"])

    return prices, summary


prices, summary = load_data()


st.title("AI Food Price Intelligence Dashboard")
st.caption("Market price monitoring for Indonesian basic goods using PIHPS Bank Indonesia data.")


commodity_options = sorted(prices["commodity_name"].unique())

selected_commodity = st.selectbox(
    "Pilih Komoditas",
    commodity_options,
)


commodity_prices = prices[prices["commodity_name"] == selected_commodity].copy()
commodity_summary = summary[summary["commodity_name"] == selected_commodity].iloc[0]


latest_price = commodity_summary["latest_price"]
start_price = commodity_summary["start_price"]
price_change = commodity_summary["price_change"]
percentage_change = commodity_summary["percentage_change"]
unit = commodity_summary["unit"]


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label=f"Harga Terbaru / {unit}",
    value=f"Rp {latest_price:,.0f}",
)

col2.metric(
    label="Perubahan Harga",
    value=f"Rp {price_change:,.0f}",
)

col3.metric(
    label="Perubahan Persen",
    value=f"{percentage_change:.2f}%",
)

col4.metric(
    label=f"Harga Awal / {unit}",
    value=f"Rp {start_price:,.0f}",
)


fig = px.line(
    commodity_prices,
    x="price_date",
    y="price",
    markers=True,
    title=f"Tren Harga {selected_commodity}",
)

fig.update_layout(
    xaxis_title="Tanggal",
    yaxis_title=f"Harga per {unit}",
)

st.plotly_chart(fig, use_container_width=True)


st.subheader("Ringkasan Semua Komoditas")

summary_display = summary.copy()
summary_display["latest_price"] = summary_display["latest_price"].apply(lambda x: f"Rp {x:,.0f}")
summary_display["start_price"] = summary_display["start_price"].apply(lambda x: f"Rp {x:,.0f}")
summary_display["price_change"] = summary_display["price_change"].apply(lambda x: f"Rp {x:,.0f}")
summary_display["percentage_change"] = summary_display["percentage_change"].apply(lambda x: f"{x:.2f}%")

st.dataframe(summary_display, use_container_width=True)