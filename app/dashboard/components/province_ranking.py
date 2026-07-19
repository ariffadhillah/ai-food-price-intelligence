import plotly.express as px
import streamlit as st


def classify_province_risk(score):
    if score >= 20:
        return "HIGH"

    if score >= 10:
        return "MEDIUM"

    return "LOW"


def show_province_ranking(provinces):
    st.subheader("🏆 Province Risk Ranking")

    st.caption(
        "Peringkat provinsi berdasarkan rata-rata risk score "
        "seluruh komoditas yang tersedia."
    )

    if provinces.empty:
        st.warning("Data province analytics belum tersedia.")
        return

    ranking = (
        provinces.sort_values(
            "avg_risk_score",
            ascending=False,
        )
        .reset_index(drop=True)
        .copy()
    )

    ranking["rank"] = ranking.index + 1

    ranking["risk_category"] = ranking[
        "avg_risk_score"
    ].apply(classify_province_risk)

    top_province = ranking.iloc[0]
    lowest_province = ranking.iloc[-1]

    total_high_risk = int(
        ranking["high_risk_count"].sum()
    )

    average_national_risk = ranking[
        "avg_risk_score"
    ].mean()

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Highest Risk Province",
        top_province["province_name"],
        f"Score {top_province['avg_risk_score']:.2f}",
    )

    k2.metric(
        "Most Stable Province",
        lowest_province["province_name"],
        f"Score {lowest_province['avg_risk_score']:.2f}",
    )

    k3.metric(
        "National Average Risk",
        f"{average_national_risk:.2f}",
    )

    k4.metric(
        "Total High-Risk Alerts",
        f"{total_high_risk:,}",
    )

    top_ranking = ranking.head(10).copy()

    ranking_display = top_ranking[
        [
            "rank",
            "province_name",
            "avg_risk_score",
            "max_risk_score",
            "high_risk_count",
            "top_risk_commodity",
            "top_risk_price",
            "risk_category",
        ]
    ].copy()

    ranking_display["avg_risk_score"] = (
        ranking_display["avg_risk_score"]
        .apply(lambda value: f"{value:.2f}")
    )

    ranking_display["max_risk_score"] = (
        ranking_display["max_risk_score"]
        .apply(lambda value: f"{value:.2f}")
    )

    ranking_display["top_risk_price"] = (
        ranking_display["top_risk_price"]
        .apply(lambda value: f"Rp {value:,.0f}")
    )

    st.markdown("### Top 10 Highest Risk Provinces")

    st.dataframe(
        ranking_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn(
                "Rank",
                format="%d",
            ),
            "province_name": "Province",
            "avg_risk_score": "Average Risk",
            "max_risk_score": "Maximum Risk",
            "high_risk_count": "High-Risk Items",
            "top_risk_commodity": "Critical Commodity",
            "top_risk_price": "Commodity Price",
            "risk_category": "Risk Category",
        },
    )

    chart_data = top_ranking.sort_values(
        "avg_risk_score",
        ascending=True,
    )

    fig = px.bar(
        chart_data,
        x="avg_risk_score",
        y="province_name",
        color="risk_category",
        orientation="h",
        text="avg_risk_score",
        hover_data={
            "province_name": True,
            "avg_risk_score": ":.2f",
            "max_risk_score": ":.2f",
            "high_risk_count": True,
            "top_risk_commodity": True,
            "top_risk_price": ":,.0f",
            "avg_change_1m": ":.2f",
            "avg_change_3m": ":.2f",
            "avg_change_6m": ":.2f",
            "risk_category": True,
        },
        category_orders={
            "risk_category": [
                "HIGH",
                "MEDIUM",
                "LOW",
            ]
        },
        color_discrete_map={
            "HIGH": "#dc2626",
            "MEDIUM": "#f59e0b",
            "LOW": "#22c55e",
        },
        title="Top 10 Province Risk Ranking",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=560,
        xaxis_title="Average Risk Score",
        yaxis_title="Province",
        legend_title="Risk Category",
        margin={
            "l": 0,
            "r": 30,
            "t": 60,
            "b": 0,
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )