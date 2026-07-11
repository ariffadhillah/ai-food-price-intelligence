import pandas as pd
import streamlit as st
import plotly.express as px

from app.dashboard.data_loader import load_data
from app.dashboard.utils import (
    generate_insight,
    generate_national_report,
    generate_ai_executive_summary,
)

from app.dashboard.pages.forecast import show_forecast_analysis
from app.dashboard.pages.explorer import show_data_explorer

st.set_page_config(
    page_title="AI Food Price Intelligence",
    page_icon="📊",
    layout="wide",
)



prices, metrics, scores, analytics, provinces = load_data()


page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Commodity Explorer",
        "Forecast Analysis",
        "Data Explorer",
    ],
)


if page == "Data Explorer":
    show_data_explorer(
        prices,
        metrics,
        scores,
    )
    st.stop()

    # end of data explorer page


if page == "Forecast Analysis":
    show_forecast_analysis(prices)
    st.stop()

    # end of forecast analysis page

if page == "Commodity Explorer":
    st.title("📈 Commodity Explorer")
    st.caption("Analisis historis harga komoditas per provinsi.")

    commodity_options = sorted(prices["commodity_name"].dropna().unique())
    province_options = sorted(prices["province_name"].dropna().unique())

    col1, col2 = st.columns(2)

    selected_commodity = col1.selectbox("Pilih Komoditas", commodity_options)
    selected_province = col2.selectbox("Pilih Provinsi", province_options)

    filtered = prices[
        (prices["commodity_name"] == selected_commodity)
        & (prices["province_name"] == selected_province)
    ].copy()

    metric_row = metrics[
        (metrics["commodity_name"] == selected_commodity)
        & (metrics["province_name"] == selected_province)
    ]

    score_row = scores[
        (scores["commodity_name"] == selected_commodity)
        & (scores["province_name"] == selected_province)
    ]

    if filtered.empty:
        st.warning("Data tidak tersedia untuk pilihan ini.")
        st.stop()

    latest_price = filtered.sort_values("price_date").iloc[-1]["price"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Latest Price", f"Rp {latest_price:,.0f}")

    if not metric_row.empty:
        row = metric_row.iloc[0]
        c2.metric("1M Change", f"{row['change_1m']:.2f}%")
        c3.metric("3M Change", f"{row['change_3m']:.2f}%")
        c4.metric("6M Change", f"{row['change_6m']:.2f}%")
    else:
        c2.metric("1M Change", "-")
        c3.metric("3M Change", "-")
        c4.metric("6M Change", "-")

    fig_price = px.line(
        filtered,
        x="price_date",
        y="price",
        markers=True,
        title=f"Historical Price Trend: {selected_commodity} - {selected_province}",
    )

    st.plotly_chart(fig_price, use_container_width=True)

    if not score_row.empty:
        score = score_row.iloc[0]

        st.subheader("🧠 Commodity Intelligence")

        st.info(
            f"**{selected_commodity} di {selected_province}** memiliki risk score "
            f"**{score['score']:.2f}** dengan level **{score['risk_level']}**. "
            f"Perubahan harga dalam 1 bulan terakhir adalah **{score['change_1m']:.2f}%**, "
            f"3 bulan **{score['change_3m']:.2f}%**, dan "
            f"6 bulan **{score['change_6m']:.2f}%**."
        )

    st.subheader("Raw Historical Data")
    st.dataframe(filtered, use_container_width=True)

    st.stop()


st.title("AI Food Price Intelligence Dashboard")
st.caption("Indonesia basic goods price intelligence using PIHPS + PostgreSQL + Analytics")


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

summary = generate_ai_executive_summary(scores)

st.subheader("🤖 AI Executive Summary")

s1, s2, s3, s4 = st.columns(4)

s1.metric("Market Health", f"{summary['icon']} {summary['market_status']}")
s2.metric("Overall Risk", summary["risk_level"])
s3.metric("Most Critical Commodity", summary["top_commodity"])
s4.metric("Highest Risk Province", summary["top_province"])

st.warning(
    f"AI Summary: Market condition is **{summary['market_status']}**. "
    f"The most critical commodity is **{summary['top_commodity']}** "
    f"in **{summary['top_province']}** "
    f"with risk score **{summary['top_score']:.2f}**. "
    f"There are **{summary['high_count']}** high-risk commodity-province combinations."
)

st.info(
    f"Highest current risk: **{highest_risk['commodity_name']}** "
    f"in **{highest_risk['province_name']}** "
    f"with risk score **{highest_risk['score']:.2f}**."
)


st.subheader("📈 Biggest Movers")

col_up, col_down = st.columns(2)

top_gainers = scores.sort_values("change_1m", ascending=False).head(5)
top_losers = scores.sort_values("change_1m", ascending=True).head(5)

with col_up:
    st.markdown("### Top Price Increases")
    for _, row in top_gainers.iterrows():
        st.metric(
            f"{row['commodity_name']} - {row['province_name']}",
            f"{row['change_1m']:.2f}%",
            f"Rp {row['latest_price']:,.0f}",
        )

with col_down:
    st.markdown("### Top Price Decreases")
    for _, row in top_losers.iterrows():
        st.metric(
            f"{row['commodity_name']} - {row['province_name']}",
            f"{row['change_1m']:.2f}%",
            f"Rp {row['latest_price']:,.0f}",
        )


st.subheader("🌊 Volatility & Trend Intelligence")

col_vol, col_trend = st.columns(2)

top_volatility = analytics.sort_values(
    "std_price",
    ascending=False,
).head(10).copy()

# Tambahkan label gabungan
top_volatility["label"] = (
    top_volatility["commodity_name"]
    + " - "
    + top_volatility["province_name"]
)

top_trend = analytics[
    analytics["trend_strength"].isin(
        ["STRONG_UPTREND", "STRONG_DOWNTREND"]
    )
].head(10)

with col_vol:
    st.markdown("### Most Volatile Commodities")

    vol_display = top_volatility[
        [
            "commodity_name",
            "province_name",
            "avg_price",
            "std_price",
            "volatility_level",
        ]
    ].copy()

    vol_display["avg_price"] = vol_display["avg_price"].apply(lambda x: f"Rp {x:,.0f}")
    vol_display["std_price"] = vol_display["std_price"].apply(lambda x: f"Rp {x:,.0f}")

    st.dataframe(vol_display, use_container_width=True)

with col_trend:
    st.markdown("### Strongest Trends")

    trend_display = top_trend[
        [
            "commodity_name",
            "province_name",
            "latest_price",
            "trend_strength",
            "price_range",
        ]
    ].copy()

    trend_display["latest_price"] = trend_display["latest_price"].apply(lambda x: f"Rp {x:,.0f}")
    trend_display["price_range"] = trend_display["price_range"].apply(lambda x: f"Rp {x:,.0f}")

    st.dataframe(trend_display, use_container_width=True)


fig_volatility = px.bar(
    top_volatility.sort_values("std_price", ascending=True),
    x="std_price",
    y="label",
    color="volatility_level",
    orientation="h",
    title="Top Volatility by Commodity and Province",
    hover_data=[
        "avg_price",
        "min_price",
        "max_price",
        "volatility_level",
    ],
)

fig_volatility.update_layout(
    xaxis_title="Standard Deviation (Price Volatility)",
    yaxis_title="Commodity - Province",
)

st.plotly_chart(fig_volatility, use_container_width=True)

# end of volatility chart


st.subheader("🗺️ Province Risk Intelligence")

top_provinces = provinces.sort_values(
    "avg_risk_score",
    ascending=False
).head(10).copy()

province_display = top_provinces.copy()
province_display["avg_risk_score"] = province_display["avg_risk_score"].apply(lambda x: f"{x:.2f}")
province_display["max_risk_score"] = province_display["max_risk_score"].apply(lambda x: f"{x:.2f}")
province_display["top_risk_price"] = province_display["top_risk_price"].apply(lambda x: f"Rp {x:,.0f}")

st.dataframe(
    province_display[
        [
            "province_name",
            "avg_risk_score",
            "max_risk_score",
            "high_risk_count",
            "top_risk_commodity",
            "top_risk_price",
            "top_risk_level",
        ]
    ],
    use_container_width=True,
)

fig_province = px.bar(
    top_provinces.sort_values("avg_risk_score", ascending=True),
    x="avg_risk_score",
    y="province_name",
    color="top_risk_level",
    orientation="h",
    hover_data=[
        "top_risk_commodity",
        "max_risk_score",
        "high_risk_count",
        "avg_change_1m",
        "avg_change_3m",
        "avg_change_6m",
    ],
    title="Top 10 Highest Risk Provinces",
)

fig_province.update_layout(
    xaxis_title="Average Risk Score",
    yaxis_title="Province",
)

st.plotly_chart(fig_province, use_container_width=True)
# end of province risk chart



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


