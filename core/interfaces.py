"""Standard data interfaces for Tiger System"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from enum import Enum
import json

# Enums for type safety
class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    ALERT = "alert"
    HOLD = "hold"

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TradeStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class TimeHorizon(str, Enum):
    SHORT = "short"  # < 1 day
    MEDIUM = "medium"  # 1-7 days
    LONG = "long"  # > 7 days

class Importance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Base interface
@dataclass
class BaseInterface:
    """Base interface with common fields"""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, Enum):
                result[key] = value.value
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary"""
        return cls(**data)

# Market Data Interface
@dataclass
class MarketData(BaseInterface):
    """Market data from exchanges"""
    symbol: str
    price: float
    volume: float
    source: str
    exchange: Optional[str] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    open_24h: Optional[float] = None
    change_24h: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    
    def validate(self) -> bool:
        """Validate market data"""
        return (
            self.symbol and 
            self.price > 0 and 
            self.volume >= 0 and
            self.source
        )

# Chain Data Interface
@dataclass
class ChainData(BaseInterface):
    """Blockchain transaction data"""
    chain: str
    block_number: int
    transaction_hash: str
    from_address: str
    to_address: str
    token_symbol: Optional[str] = None
    amount: Optional[float] = None
    gas_used: Optional[int] = None
    gas_price: Optional[float] = None
    transaction_type: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate chain data"""
        return (
            self.chain and
            self.block_number > 0 and
            self.transaction_hash and
            self.from_address and
            self.to_address
        )

# Social Sentiment Interface
@dataclass
class SocialSentiment(BaseInterface):
    """Social media sentiment data"""
    source: str  # twitter, reddit, telegram, etc
    content: str
    sentiment_score: float  # -1 to 1
    symbol: Optional[str] = None
    author: Optional[str] = None
    engagement_score: Optional[int] = None
    reach: Optional[int] = None
    url: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate sentiment data"""
        return (
            self.source and
            self.content and
            -1 <= self.sentiment_score <= 1
        )

# News Event Interface
@dataclass
class NewsEvent(BaseInterface):
    """News and event data"""
    source: str
    title: str
    importance: Importance
    content: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    
    def validate(self) -> bool:
        """Validate news event"""
        return (
            self.source and
            self.title and
            self.importance
        )

# Trader Action Interface
@dataclass
class TraderAction(BaseInterface):
    """Top trader action data"""
    trader_address: str
    action_type: str  # buy, sell, stake, unstake, etc
    symbol: str
    amount: float
    trader_label: Optional[str] = None  # whale, smart_money, etc
    price: Optional[float] = None
    chain: Optional[str] = None
    transaction_hash: Optional[str] = None
    profit_loss: Optional[float] = None
    
    def validate(self) -> bool:
        """Validate trader action"""
        return (
            self.trader_address and
            self.action_type and
            self.symbol and
            self.amount > 0
        )

# Signal Interface
@dataclass
class Signal(BaseInterface):
    """Trading signal"""
    signal_type: SignalType
    symbol: str
    confidence: float  # 0 to 1
    trigger_reason: str
    source: str  # technical, sentiment, whale_alert, etc
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_horizon: Optional[TimeHorizon] = None
    status: str = "active"  # active, expired, executed
    
    def validate(self) -> bool:
        """Validate signal"""
        return (
            self.signal_type and
            self.symbol and
            0 <= self.confidence <= 1 and
            self.trigger_reason and
            self.source
        )
    
    def is_active(self) -> bool:
        """Check if signal is still active"""
        return self.status == "active"

# Trade Interface
@dataclass
class Trade(BaseInterface):
    """Trade execution data"""
    symbol: str
    trade_type: str  # buy, sell
    status: TradeStatus
    signal_id: Optional[str] = None
    suggested_price: Optional[float] = None
    suggested_amount: Optional[float] = None
    actual_price: Optional[float] = None
    actual_amount: Optional[float] = None
    exchange: Optional[str] = None
    profit_loss: Optional[float] = None
    fees: Optional[float] = None
    executed_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate trade"""
        return (
            self.symbol and
            self.trade_type and
            self.status
        )
    
    def is_profitable(self) -> bool:
        """Check if trade is profitable"""
        return self.profit_loss and self.profit_loss > 0

# System Log Interface
@dataclass
class SystemLog(BaseInterface):
    """System log entry"""
    window_id: int  # 1-10
    log_level: LogLevel
    component: str
    message: str
    error_trace: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate log entry"""
        return (
            1 <= self.window_id <= 10 and
            self.log_level and
            self.component and
            self.message
        )

# Learning Data Interface
@dataclass
class LearningData(BaseInterface):
    """Machine learning training data"""
    model_name: str
    model_version: str
    training_data: Dict[str, Any]
    status: str  # training, completed, failed
    performance_metrics: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    
    def validate(self) -> bool:
        """Validate learning data"""
        return (
            self.model_name and
            self.model_version and
            self.training_data and
            self.status
        )

# Aggregated Data Interface
@dataclass
class AggregatedMarketData(BaseInterface):
    """Aggregated market data from multiple sources"""
    symbol: str
    avg_price: float
    total_volume: float
    price_sources: List[Dict[str, float]]
    confidence: float  # 0 to 1, based on source agreement
    
    def validate(self) -> bool:
        """Validate aggregated data"""
        return (
            self.symbol and
            self.avg_price > 0 and
            self.total_volume >= 0 and
            0 <= self.confidence <= 1
        )

# Alert Interface
@dataclass
class Alert(BaseInterface):
    """System alert"""
    alert_type: str  # price_alert, volume_spike, whale_movement, etc
    severity: Importance
    title: str
    message: str
    symbol: Optional[str] = None
    action_required: bool = False
    
    def validate(self) -> bool:
        """Validate alert"""
        return (
            self.alert_type and
            self.severity and
            self.title and
            self.message
        )

# Performance Metrics Interface
@dataclass
class PerformanceMetrics(BaseInterface):
    """System performance metrics"""
    window_id: int
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    throughput: int  # operations per second
    error_rate: float
    uptime_seconds: int
    
    def validate(self) -> bool:
        """Validate metrics"""
        return (
            1 <= self.window_id <= 10 and
            0 <= self.cpu_usage <= 100 and
            0 <= self.memory_usage <= 100 and
            self.latency_ms >= 0 and
            self.throughput >= 0 and
            0 <= self.error_rate <= 1 and
            self.uptime_seconds >= 0
        )

# Message Interface for inter-window communication
@dataclass
class WindowMessage(BaseInterface):
    """Message between windows"""
    from_window: int
    to_window: int
    message_type: str
    payload: Dict[str, Any]
    priority: int = 0  # Higher number = higher priority
    requires_response: bool = False
    correlation_id: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate message"""
        return (
            1 <= self.from_window <= 10 and
            1 <= self.to_window <= 10 and
            self.message_type and
            self.payload is not None
        )

# Batch Data Interface
@dataclass
class BatchData(BaseInterface):
    """Batch of data for bulk operations"""
    data_type: str
    items: List[BaseInterface]
    batch_id: str
    total_count: int
    
    def validate(self) -> bool:
        """Validate batch"""
        return (
            self.data_type and
            self.items and
            self.batch_id and
            self.total_count > 0
        )
    
    def validate_all_items(self) -> bool:
        """Validate all items in batch"""
        return all(item.validate() for item in self.items)

# Configuration Interface
@dataclass
class SystemConfig(BaseInterface):
    """System configuration"""
    window_id: int
    config_version: str
    settings: Dict[str, Any]
    enabled_features: List[str]
    
    def validate(self) -> bool:
        """Validate configuration"""
        return (
            1 <= self.window_id <= 10 and
            self.config_version and
            self.settings is not None
        )

# Response Interface
@dataclass
class APIResponse(BaseInterface):
    """Standard API response"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    request_id: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate response"""
        return isinstance(self.success, bool)

# Factory class for creating interfaces
class InterfaceFactory:
    """Factory for creating interface instances"""
    
    @staticmethod
    def create_market_data(**kwargs) -> MarketData:
        """Create MarketData instance"""
        return MarketData(**kwargs)
    
    @staticmethod
    def create_signal(**kwargs) -> Signal:
        """Create Signal instance"""
        return Signal(**kwargs)
    
    @staticmethod
    def create_trade(**kwargs) -> Trade:
        """Create Trade instance"""
        return Trade(**kwargs)
    
    @staticmethod
    def create_alert(**kwargs) -> Alert:
        """Create Alert instance"""
        return Alert(**kwargs)
    
    @staticmethod
    def create_log(**kwargs) -> SystemLog:
        """Create SystemLog instance"""
        return SystemLog(**kwargs)

# Validation utilities
def validate_data(data: BaseInterface) -> tuple[bool, Optional[str]]:
    """Validate any data interface"""
    try:
        if hasattr(data, 'validate'):
            is_valid = data.validate()
            if not is_valid:
                return False, f"Validation failed for {type(data).__name__}"
            return True, None
        return False, "No validate method found"
    except Exception as e:
        return False, str(e)

# Type hints for common operations
DataType = MarketData | ChainData | SocialSentiment | NewsEvent | TraderAction | Signal | Trade | SystemLog | LearningData