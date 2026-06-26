from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime
)

from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class CommodityPrice(Base):

    __tablename__ = "commodity_prices"

    id = Column(Integer, primary_key=True)

    price_date = Column(Date)

    commodity_name = Column(String(255))

    province_id = Column(Integer)

    province_name = Column(String(255))

    price = Column(Float)

    price_change = Column(Float)

    percentage_change = Column(Float)

    source = Column(String(255))

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


class MarketMetric(Base):

    __tablename__ = "market_metrics"

    id = Column(Integer, primary_key=True)

    commodity_name = Column(String(255))
    province_name = Column(String(255))

    latest_date = Column(Date)
    latest_price = Column(Float)

    price_1m_ago = Column(Float)
    change_1m = Column(Float)

    price_3m_ago = Column(Float)
    change_3m = Column(Float)

    price_6m_ago = Column(Float)
    change_6m = Column(Float)

    trend = Column(String(50))

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


class CommodityScore(Base):

    __tablename__ = "commodity_scores"

    id = Column(Integer, primary_key=True)

    commodity_name = Column(String(255))
    province_name = Column(String(255))

    latest_date = Column(Date)
    latest_price = Column(Float)

    change_1m = Column(Float)
    change_3m = Column(Float)
    change_6m = Column(Float)

    score = Column(Float)
    risk_level = Column(String(50))

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


class CommodityAnalytics(Base):

    __tablename__ = "commodity_analytics"

    id = Column(Integer, primary_key=True)

    commodity_name = Column(String(255))
    province_name = Column(String(255))

    avg_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    median_price = Column(Float)
    std_price = Column(Float)

    volatility_level = Column(String(50))
    trend_strength = Column(String(50))

    latest_price = Column(Float)
    price_range = Column(Float)
    data_points = Column(Integer)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )