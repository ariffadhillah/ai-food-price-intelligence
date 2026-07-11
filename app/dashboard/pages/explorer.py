import streamlit as st


def show_data_explorer(
    prices,
    metrics,
    scores,
):
    st.title("Data Explorer")

    st.subheader("Commodity Prices")
    st.dataframe(
        prices,
        use_container_width=True,
    )

    st.subheader("Market Metrics")
    st.dataframe(
        metrics,
        use_container_width=True,
    )

    st.subheader("Commodity Scores")
    st.dataframe(
        scores,
        use_container_width=True,
    )