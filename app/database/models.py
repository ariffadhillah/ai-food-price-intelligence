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