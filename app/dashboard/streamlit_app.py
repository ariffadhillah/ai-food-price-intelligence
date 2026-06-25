import pandas as pd
import streamlit as st
import plotly.express as px

from app.database.db import engine
from app.ai.price_forecaster import forecast_price, generate_prediction_summary


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

    top_commodity = highest["commodity_name"]
    top_province = highest["province_name"]
    top_score = highest["score"]

    high_count = len(scores[scores["risk_level"] == "HIGH"])
    market_status, risk_level, icon = generate_market_health(scores)

    return {
        "market_status": market_status,
        "risk_level": risk_level,
        "icon": icon,
        "top_commodity": top_commodity,
        "top_province": top_province,
        "top_score": top_score,
        "high_count": high_count,
    }


@st.cache_data
def load_data():
    prices = pd.read_sql("SELECT * FROM commodity_prices", engine)
    metrics = pd.read_sql("SELECT * FROM market_metrics", engine)
    scores = pd.read_sql("SELECT * FROM commodity_scores", engine)

    prices["price_date"] = pd.to_datetime(prices["price_date"])
    scores["latest_date"] = pd.to_datetime(scores["latest_date"])

    return prices, metrics, scores


prices, metrics, scores = load_data()


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
    st.title("Data Explorer")

    st.subheader("Commodity Prices")
    st.dataframe(prices, use_container_width=True)

    st.subheader("Market Metrics")
    st.dataframe(metrics, use_container_width=True)

    st.subheader("Commodity Scores")
    st.dataframe(scores, use_container_width=True)

    st.stop()


if page == "Forecast Analysis":
    st.title("🔮 Forecast Analysis")
    st.caption("Prediksi harga komoditas berbasis data historis PIHPS dan model Linear Regression.")

    commodity_options = sorted(prices["commodity_name"].dropna().unique())
    province_options = sorted(prices["province_name"].dropna().unique())

    col1, col2 = st.columns(2)

    selected_commodity = col1.selectbox("Pilih Komoditas", commodity_options)
    selected_province = col2.selectbox("Pilih Provinsi", province_options)

    filtered = prices[
        (prices["commodity_name"] == selected_commodity)
        & (prices["province_name"] == selected_province)
    ].copy()

    forecast_df = forecast_price(
        commodity_name=selected_commodity,
        province_name=selected_province,
        periods=3,
    )

    if forecast_df is None or filtered.empty:
        st.warning("Data belum cukup untuk membuat forecast.")
        st.stop()

    latest_price = filtered.sort_values("price_date").iloc[-1]["price"]

    prediction = generate_prediction_summary(
        commodity_name=selected_commodity,
        province_name=selected_province,
        latest_price=latest_price,
        forecast_df=forecast_df,
    )

    p1, p2, p3, p4 = st.columns(4)

    p1.metric("Latest Price", f"Rp {latest_price:,.0f}")
    p2.metric("Predicted Price", f"Rp {prediction['final_forecast_price']:,.0f}")
    p3.metric("Expected Change", f"{prediction['expected_change']:.2f}%")
    p4.metric("Confidence", prediction["confidence"])

    st.info(
        f"**Trend:** {prediction['trend']}  \n\n"
        f"{prediction['summary']}  \n\n"
        f"**Recommendation:** {prediction['recommendation']}"
    )


    summary = generate_ai_executive_summary(scores)

    st.subheader("🤖 AI Executive Summary")

    s1, s2, s3, s4 = st.columns(4)

    s1.metric("Market Health", f"{summary['icon']} {summary['market_status']}")
    s2.metric("Overall Risk", summary["risk_level"])
    s3.metric("Most Critical Commodity", summary["top_commodity"])
    s4.metric("Highest Risk Province", summary["top_province"])

    st.warning(
        f"AI Summary: Market condition is **{summary['market_status']}**. "
        f"The most critical commodity is **{summary['top_commodity']}** in "
        f"**{summary['top_province']}** with risk score **{summary['top_score']:.2f}**. "
        f"There are **{summary['high_count']}** high-risk commodity-province combinations."
    )


    forecast_display = forecast_df.copy()
    forecast_display["predicted_price"] = forecast_display["predicted_price"].apply(
        lambda x: f"Rp {x:,.0f}"
    )

    st.subheader("Forecast Table")
    st.dataframe(forecast_display, use_container_width=True)

    historical_chart = filtered[["price_date", "price"]].copy()
    historical_chart = historical_chart.rename(
        columns={
            "price_date": "date",
            "price": "price",
        }
    )
    historical_chart["type"] = "Historical"

    last_historical = historical_chart.sort_values("date").iloc[-1:].copy()
    last_historical["type"] = "Forecast"

    forecast_chart = forecast_df[["forecast_date", "predicted_price"]].copy()
    forecast_chart = forecast_chart.rename(
        columns={
            "forecast_date": "date",
            "predicted_price": "price",
        }
    )
    forecast_chart["date"] = pd.to_datetime(forecast_chart["date"])
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
        title=f"Forecast Harga {selected_commodity} - {selected_province}",
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

    st.stop()


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


st.subheader("🔮 Price Forecast")

forecast_df = forecast_price(
    commodity_name=selected_commodity,
    province_name=selected_province,
    periods=3,
)

if forecast_df is not None:
    latest_price = filtered.sort_values("price_date").iloc[-1]["price"]

    prediction = generate_prediction_summary(
        commodity_name=selected_commodity,
        province_name=selected_province,
        latest_price=latest_price,
        forecast_df=forecast_df,
    )

    p1, p2, p3 = st.columns(3)

    p1.metric("Predicted Price", f"Rp {prediction['final_forecast_price']:,.0f}")
    p2.metric("Expected Change", f"{prediction['expected_change']:.2f}%")
    p3.metric("Confidence", prediction["confidence"])

    st.info(
        f"**Trend:** {prediction['trend']}  \n\n"
        f"{prediction['summary']}  \n\n"
        f"**Recommendation:** {prediction['recommendation']}"
    )

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

    last_historical = historical_chart.sort_values("date").iloc[-1:].copy()
    last_historical["type"] = "Forecast"

    forecast_chart = forecast_df[["forecast_date", "predicted_price"]].copy()
    forecast_chart = forecast_chart.rename(
        columns={
            "forecast_date": "date",
            "predicted_price": "price",
        }
    )
    forecast_chart["date"] = pd.to_datetime(forecast_chart["date"])
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
        title=f"Forecast Harga {selected_commodity} - {selected_province}",
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

else:
    st.warning("Data belum cukup untuk membuat forecast.")