import streamlit as st

from app.dashboard.data_loader import load_data
from app.dashboard.pages.commodity import show_commodity_explorer
from app.dashboard.pages.executive import show_executive_overview
from app.dashboard.pages.explorer import show_data_explorer
from app.dashboard.pages.forecast import show_forecast_analysis


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


if page == "Executive Overview":
    show_executive_overview(
        prices,
        metrics,
        scores,
        analytics,
        provinces,
    )

elif page == "Commodity Explorer":
    show_commodity_explorer(
        prices,
        metrics,
        scores,
    )

elif page == "Forecast Analysis":
    show_forecast_analysis(prices)

elif page == "Data Explorer":
    show_data_explorer(
        prices,
        metrics,
        scores,
    )