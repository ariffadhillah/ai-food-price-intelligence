import plotly.express as px
import streamlit as st


def show_province_comparison(provinces):
    st.subheader("⚖️ Province Comparison")

    st.caption(
        "Bandingkan kondisi harga pangan antara dua provinsi."
    )

    province_names = sorted(
        provinces["province_name"].unique()
    )

    col1, col2 = st.columns(2)

    province_a = col1.selectbox(
        "Province A",
        province_names,
        key="province_a",
    )

    province_b = col2.selectbox(
        "Province B",
        province_names,
        index=1,
        key="province_b",
    )

    row_a = provinces[
        provinces["province_name"] == province_a
    ].iloc[0]

    row_b = provinces[
        provinces["province_name"] == province_b
    ].iloc[0]

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        province_a,
        f"{row_a['avg_risk_score']:.2f}",
        "Average Risk",
    )

    c2.metric(
        province_b,
        f"{row_b['avg_risk_score']:.2f}",
        "Average Risk",
    )

    c3.metric(
        "Difference",
        f"{abs(row_a['avg_risk_score']-row_b['avg_risk_score']):.2f}",
    )

    higher = (
        province_a
        if row_a["avg_risk_score"] > row_b["avg_risk_score"]
        else province_b
    )

    c4.metric(
        "Higher Risk",
        higher,
    )

    compare = provinces[
        provinces["province_name"].isin(
            [province_a, province_b]
        )
    ].copy()

    fig = px.bar(
        compare,
        x="province_name",
        y="avg_risk_score",
        color="province_name",
        text="avg_risk_score",
        title="Average Risk Score",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    metric_df = compare[
        [
            "province_name",
            "avg_risk_score",
            "max_risk_score",
            "high_risk_count",
            "top_risk_commodity",
            "top_risk_price",
            "avg_change_1m",
            "avg_change_3m",
            "avg_change_6m",
        ]
    ].copy()

    metric_df["top_risk_price"] = (
        metric_df["top_risk_price"]
        .apply(lambda x: f"Rp {x:,.0f}")
    )

    metric_df["avg_risk_score"] = (
        metric_df["avg_risk_score"]
        .apply(lambda x: f"{x:.2f}")
    )

    metric_df["max_risk_score"] = (
        metric_df["max_risk_score"]
        .apply(lambda x: f"{x:.2f}")
    )

    metric_df["avg_change_1m"] = (
        metric_df["avg_change_1m"]
        .apply(lambda x: f"{x:.2f}%")
    )

    metric_df["avg_change_3m"] = (
        metric_df["avg_change_3m"]
        .apply(lambda x: f"{x:.2f}%")
    )

    metric_df["avg_change_6m"] = (
        metric_df["avg_change_6m"]
        .apply(lambda x: f"{x:.2f}%")
    )

    st.markdown("### Detailed Comparison")

    st.dataframe(
        metric_df,
        use_container_width=True,
        hide_index=True,
    )

    winner = (
        row_a
        if row_a["avg_risk_score"] > row_b["avg_risk_score"]
        else row_b
    )

    loser = (
        row_b
        if row_a["avg_risk_score"] > row_b["avg_risk_score"]
        else row_a
    )

    diff = (
        winner["avg_risk_score"]
        - loser["avg_risk_score"]
    )

    st.info(
        f"""
### AI Comparison Summary

**{winner['province_name']}** memiliki tingkat risiko rata-rata
lebih tinggi sebesar **{diff:.2f} poin** dibanding
**{loser['province_name']}**.

Komoditas paling kritis di provinsi tersebut adalah
**{winner['top_risk_commodity']}**
dengan skor maksimum
**{winner['max_risk_score']:.2f}**.

Perubahan harga rata-rata dalam tiga bulan terakhir mencapai
**{winner['avg_change_3m']:.2f}%**.
"""
    )