"""Market data model"""

from sqlalchemy import Column, String, DateTime, Numeric, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

class MarketData(BaseModel):
    """Market data from exchanges"""
    __tablename__ = 'market_data'
    __table_args__ = (
        UniqueConstraint('timestamp', 'symbol', 'exchange', name='market_data_unique'),
        Index('idx_market_data_timestamp', 'timestamp'),
        Index('idx_market_data_symbol', 'symbol'),
        Index('idx_market_data_exchange', 'exchange'),
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
        {'postgresql_partition_by': 'RANGE (timestamp)'}
    )
    
    timestamp = Column(DateTime(timezone=True), nullable=False)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 8), nullable=False)
    high_24h = Column(Numeric(20, 8))
    low_24h = Column(Numeric(20, 8))
    open_24h = Column(Numeric(20, 8))
    bid_price = Column(Numeric(20, 8))
    ask_price = Column(Numeric(20, 8))
    bid_volume = Column(Numeric(20, 8))
    ask_volume = Column(Numeric(20, 8))