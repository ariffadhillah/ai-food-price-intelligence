import pandas as pd
import streamlit as st

from app.database.db import engine


@st.cache_data
def load_data():
    prices = pd.read_sql("SELECT * FROM commodity_prices", engine)
    metrics = pd.read_sql("SELECT * FROM market_metrics", engine)
    scores = pd.read_sql("SELECT * FROM commodity_scores", engine)
    analytics = pd.read_sql("SELECT * FROM commodity_analytics", engine)
    provinces = pd.read_sql("SELECT * FROM province_analytics", engine)

    prices["price_date"] = pd.to_datetime(prices["price_date"])
    scores["latest_date"] = pd.to_datetime(scores["latest_date"])

    return prices, metrics, scores, analytics, provinces