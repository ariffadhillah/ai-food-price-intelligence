import plotly.express as px
import streamlit as st


def show_commodity_explorer(
    prices,
    metrics,
    scores,
):
    st.title("📈 Commodity Explorer")
    st.caption("Analisis historis harga komoditas per provinsi.")

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
        key="commodity_explorer_commodity",
    )

    selected_province = col2.selectbox(
        "Pilih Provinsi",
        province_options,
        key="commodity_explorer_province",
    )

    filtered = prices[
        (prices["commodity_name"] == selected_commodity)
        & (prices["province_name"] == selected_province)
    ].copy()

    if filtered.empty:
        st.warning("Data tidak tersedia untuk pilihan ini.")
        return

    metric_row = metrics[
        (metrics["commodity_name"] == selected_commodity)
        & (metrics["province_name"] == selected_province)
    ]

    score_row = scores[
        (scores["commodity_name"] == selected_commodity)
        & (scores["province_name"] == selected_province)
    ]

    filtered = filtered.sort_values("price_date")
    latest_price = filtered.iloc[-1]["price"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Latest Price",
        f"Rp {latest_price:,.0f}",
    )

    if not metric_row.empty:
        metric = metric_row.iloc[0]

        c2.metric(
            "1M Change",
            f"{metric['change_1m']:.2f}%",
        )
        c3.metric(
            "3M Change",
            f"{metric['change_3m']:.2f}%",
        )
        c4.metric(
            "6M Change",
            f"{metric['change_6m']:.2f}%",
        )
    else:
        c2.metric("1M Change", "-")
        c3.metric("3M Change", "-")
        c4.metric("6M Change", "-")

    fig_price = px.line(
        filtered,
        x="price_date",
        y="price",
        markers=True,
        title=(
            f"Historical Price Trend: "
            f"{selected_commodity} - {selected_province}"
        ),
    )

    fig_price.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (Rp)",
    )

    st.plotly_chart(
        fig_price,
        use_container_width=True,
    )

    if not score_row.empty:
        score = score_row.iloc[0]

        st.subheader("🧠 Commodity Intelligence")

        st.info(
            f"**{selected_commodity} di {selected_province}** "
            f"memiliki risk score **{score['score']:.2f}** "
            f"dengan level **{score['risk_level']}**. "
            f"Perubahan harga dalam 1 bulan terakhir adalah "
            f"**{score['change_1m']:.2f}%**, "
            f"3 bulan **{score['change_3m']:.2f}%**, dan "
            f"6 bulan **{score['change_6m']:.2f}%**."
        )

    st.subheader("Raw Historical Data")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )