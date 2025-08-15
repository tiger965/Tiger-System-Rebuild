"""Data Access Layer for Tiger System"""

import asyncio
import asyncpg
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import yaml
import json
from decimal import Decimal
from sqlalchemy import create_engine, pool, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from .interfaces import (
    MarketData, ChainData, SocialSentiment, NewsEvent,
    TraderAction, Signal, Trade, SystemLog, LearningData,
    BaseInterface
)
from .redis_manager import RedisManager

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseInterface)

class DatabasePool:
    """Database connection pool manager"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize connection pool"""
        self.config = config
        self.sync_pool = None
        self.async_pool = None
        self._init_pools()
    
    def _init_pools(self):
        """Initialize connection pools"""
        # Synchronous pool using psycopg2
        dsn = f"host={self.config['host']} port={self.config['port']} " \
              f"dbname={self.config['database']} user={self.config['user']} " \
              f"password={self.config['password']}"
        
        self.sync_pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=dsn
        )
        
        # SQLAlchemy engine for ORM operations
        db_url = f"postgresql://{self.config['user']}:{self.config['password']}@" \
                 f"{self.config['host']}:{self.config['port']}/{self.config['database']}"
        
        self.sync_engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        
        # Async engine for async operations
        async_db_url = f"postgresql+asyncpg://{self.config['user']}:{self.config['password']}@" \
                       f"{self.config['host']}:{self.config['port']}/{self.config['database']}"
        
        self.async_engine = create_async_engine(
            async_db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        
        # Session makers
        self.sync_session_maker = sessionmaker(bind=self.sync_engine)
        self.async_session_maker = async_sessionmaker(bind=self.async_engine, class_=AsyncSession)
    
    def get_connection(self):
        """Get synchronous connection from pool"""
        return self.sync_pool.getconn()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        self.sync_pool.putconn(conn)
    
    @asynccontextmanager
    async def get_async_connection(self):
        """Get async connection"""
        conn = await asyncpg.connect(
            host=self.config['host'],
            port=self.config['port'],
            database=self.config['database'],
            user=self.config['user'],
            password=self.config['password']
        )
        try:
            yield conn
        finally:
            await conn.close()
    
    def close(self):
        """Close all connections"""
        if self.sync_pool:
            self.sync_pool.closeall()
        if self.sync_engine:
            self.sync_engine.dispose()

class DataAccessLayer:
    """Main Data Access Layer class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize DAL"""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'database.yaml'
        self.config = self._load_config()
        self.pool = DatabasePool(self.config)
        self.redis = RedisManager()
        self.batch_size = 1000
    
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        default_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'tiger_system',
            'user': 'tiger_app',
            'password': 'tiger_secure_password_2024'
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Handle environment variable references
                    if loaded_config.get('password') == '${TIGER_DB_PASSWORD}':
                        import os
                        loaded_config['password'] = os.environ.get('TIGER_DB_PASSWORD', default_config['password'])
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        
        return default_config
    
    # ============= Market Data Operations =============
    
    def insert_market_data(self, data: MarketData) -> bool:
        """Insert market data"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO market_data (
                    timestamp, symbol, exchange, price, volume,
                    high_24h, low_24h, open_24h, bid_price, ask_price,
                    bid_volume, ask_volume
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol, exchange) DO UPDATE
                SET price = EXCLUDED.price,
                    volume = EXCLUDED.volume,
                    high_24h = EXCLUDED.high_24h,
                    low_24h = EXCLUDED.low_24h,
                    open_24h = EXCLUDED.open_24h,
                    bid_price = EXCLUDED.bid_price,
                    ask_price = EXCLUDED.ask_price,
                    bid_volume = EXCLUDED.bid_volume,
                    ask_volume = EXCLUDED.ask_volume
            """
            
            cursor.execute(query, (
                data.timestamp, data.symbol, data.exchange or data.source,
                data.price, data.volume, data.high_24h, data.low_24h,
                data.open_24h, data.bid_price, data.ask_price,
                data.bid_volume, data.ask_volume
            ))
            
            conn.commit()
            
            # Update Redis cache
            self.redis.set_market_data(data.symbol, data.to_dict())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert market data: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    async def insert_market_data_batch(self, data_list: List[MarketData]) -> int:
        """Insert batch of market data asynchronously"""
        inserted = 0
        
        async with self.pool.get_async_connection() as conn:
            try:
                # Prepare batch insert
                values = []
                for data in data_list:
                    values.append((
                        data.timestamp, data.symbol, data.exchange or data.source,
                        data.price, data.volume, data.high_24h, data.low_24h,
                        data.open_24h, data.bid_price, data.ask_price,
                        data.bid_volume, data.ask_volume
                    ))
                
                # Execute batch insert
                query = """
                    INSERT INTO market_data (
                        timestamp, symbol, exchange, price, volume,
                        high_24h, low_24h, open_24h, bid_price, ask_price,
                        bid_volume, ask_volume
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (timestamp, symbol, exchange) DO UPDATE
                    SET price = EXCLUDED.price,
                        volume = EXCLUDED.volume
                """
                
                await conn.executemany(query, values)
                inserted = len(values)
                
                # Update Redis cache for latest data
                for data in data_list[-10:]:  # Cache last 10 items
                    self.redis.set_market_data(data.symbol, data.to_dict())
                
            except Exception as e:
                logger.error(f"Failed to insert market data batch: {e}")
        
        return inserted
    
    def get_latest_market_data(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest market data for symbol"""
        # Try Redis cache first
        cached = self.redis.get_market_data(symbol)
        if cached:
            return [cached]
        
        # Query database
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            cursor.execute(query, (symbol, limit))
            results = cursor.fetchall()
            
            # Convert Decimal to float
            for row in results:
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        row[key] = float(value)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    # ============= Signal Operations =============
    
    def insert_signal(self, signal: Signal) -> Optional[str]:
        """Insert new signal and return ID"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO signals (
                    timestamp, signal_type, symbol, source, confidence,
                    trigger_reason, target_price, stop_loss, take_profit,
                    time_horizon, metadata, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            cursor.execute(query, (
                signal.timestamp, signal.signal_type.value, signal.symbol,
                signal.source, signal.confidence, signal.trigger_reason,
                signal.target_price, signal.stop_loss, signal.take_profit,
                signal.time_horizon.value if signal.time_horizon else None,
                json.dumps(signal.metadata), signal.status
            ))
            
            signal_id = cursor.fetchone()[0]
            conn.commit()
            
            # Store in Redis
            self.redis.set_signal(str(signal_id), signal.to_dict())
            
            # Publish to channel
            self.redis.publish(self.redis.CHANNELS['SIGNALS'], {
                'signal_id': str(signal_id),
                'signal': signal.to_dict()
            })
            
            return str(signal_id)
            
        except Exception as e:
            logger.error(f"Failed to insert signal: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    def get_active_signals(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active signals"""
        # Try Redis first
        cached_signals = self.redis.get_active_signals()
        if cached_signals and not symbol:
            return cached_signals
        
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if symbol:
                query = """
                    SELECT * FROM signals
                    WHERE status = 'active' AND symbol = %s
                    AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
                    ORDER BY confidence DESC, timestamp DESC
                """
                cursor.execute(query, (symbol,))
            else:
                query = """
                    SELECT * FROM signals
                    WHERE status = 'active'
                    AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
                    ORDER BY confidence DESC, timestamp DESC
                    LIMIT 100
                """
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            # Convert to dict and handle types
            signals = []
            for row in results:
                signal_dict = dict(row)
                for key, value in signal_dict.items():
                    if isinstance(value, Decimal):
                        signal_dict[key] = float(value)
                    elif isinstance(value, datetime):
                        signal_dict[key] = value.isoformat()
                signals.append(signal_dict)
            
            return signals
            
        except Exception as e:
            logger.error(f"Failed to get active signals: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    # ============= Trade Operations =============
    
    def insert_trade(self, trade: Trade) -> bool:
        """Insert trade record"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO trades (
                    timestamp, signal_id, symbol, trade_type,
                    suggested_price, suggested_amount, actual_price,
                    actual_amount, exchange, status, profit_loss,
                    fees, metadata, executed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                trade.timestamp, trade.signal_id, trade.symbol,
                trade.trade_type, trade.suggested_price,
                trade.suggested_amount, trade.actual_price,
                trade.actual_amount, trade.exchange,
                trade.status.value, trade.profit_loss,
                trade.fees, json.dumps(trade.metadata),
                trade.executed_at
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert trade: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    # ============= Chain Data Operations =============
    
    async def insert_chain_data_batch(self, data_list: List[ChainData]) -> int:
        """Insert batch of chain data"""
        inserted = 0
        
        async with self.pool.get_async_connection() as conn:
            try:
                values = []
                for data in data_list:
                    values.append((
                        data.timestamp, data.chain, data.block_number,
                        data.transaction_hash, data.from_address,
                        data.to_address, data.token_symbol, data.amount,
                        data.gas_used, data.gas_price, data.transaction_type,
                        json.dumps(data.metadata)
                    ))
                
                query = """
                    INSERT INTO chain_data (
                        timestamp, chain, block_number, transaction_hash,
                        from_address, to_address, token_symbol, amount,
                        gas_used, gas_price, transaction_type, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (transaction_hash) DO NOTHING
                """
                
                await conn.executemany(query, values)
                inserted = len(values)
                
            except Exception as e:
                logger.error(f"Failed to insert chain data batch: {e}")
        
        return inserted
    
    # ============= Social Sentiment Operations =============
    
    def insert_social_sentiment(self, sentiment: SocialSentiment) -> bool:
        """Insert social sentiment data"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO social_sentiment (
                    timestamp, source, symbol, content, author,
                    sentiment_score, engagement_score, reach, url, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                sentiment.timestamp, sentiment.source, sentiment.symbol,
                sentiment.content, sentiment.author, sentiment.sentiment_score,
                sentiment.engagement_score, sentiment.reach, sentiment.url,
                json.dumps(sentiment.metadata)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert social sentiment: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    def get_sentiment_summary(self, symbol: str, hours: int = 24) -> Dict[str, Any]:
        """Get sentiment summary for symbol"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as total_mentions,
                    SUM(engagement_score) as total_engagement,
                    MAX(sentiment_score) as max_sentiment,
                    MIN(sentiment_score) as min_sentiment
                FROM social_sentiment
                WHERE symbol = %s
                AND timestamp > CURRENT_TIMESTAMP - INTERVAL '%s hours'
            """
            
            cursor.execute(query, (symbol, hours))
            result = cursor.fetchone()
            
            if result:
                return {
                    'symbol': symbol,
                    'avg_sentiment': float(result['avg_sentiment']) if result['avg_sentiment'] else 0,
                    'total_mentions': result['total_mentions'],
                    'total_engagement': result['total_engagement'] or 0,
                    'max_sentiment': float(result['max_sentiment']) if result['max_sentiment'] else 0,
                    'min_sentiment': float(result['min_sentiment']) if result['min_sentiment'] else 0,
                    'period_hours': hours
                }
            
            return {'symbol': symbol, 'avg_sentiment': 0, 'total_mentions': 0}
            
        except Exception as e:
            logger.error(f"Failed to get sentiment summary: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    # ============= System Log Operations =============
    
    def log(self, window_id: int, level: str, component: str, message: str, 
            error_trace: Optional[str] = None, metadata: Optional[Dict] = None):
        """Write system log"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO system_logs (
                    window_id, log_level, component, message,
                    error_trace, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                window_id, level, component, message,
                error_trace, json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
            
            # Also log to Redis stream for real-time monitoring
            self.redis.add_to_stream(self.redis.STREAMS['SYSTEM_LOGS'], {
                'window_id': window_id,
                'log_level': level,
                'component': component,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    def get_system_health(self) -> List[Dict[str, Any]]:
        """Get system health status"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM system_health
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            health_data = []
            for row in results:
                health_data.append({
                    'window_id': row['window_id'],
                    'log_count': row['log_count'],
                    'error_count': row['error_count'],
                    'warning_count': row['warning_count'],
                    'last_activity': row['last_activity'].isoformat() if row['last_activity'] else None
                })
            
            return health_data
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    # ============= Generic Operations =============
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute custom query"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert special types
            processed_results = []
            for row in results:
                processed_row = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        processed_row[key] = float(value)
                    elif isinstance(value, datetime):
                        processed_row[key] = value.isoformat()
                    else:
                        processed_row[key] = value
                processed_results.append(processed_row)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    async def execute_async_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute async query"""
        async with self.pool.get_async_connection() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Failed to execute async query: {e}")
                return []
    
    # ============= Performance Monitoring =============
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get DAL performance statistics"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get table sizes
            query = """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    n_live_tup as row_count
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            
            cursor.execute(query)
            table_stats = cursor.fetchall()
            
            # Get connection stats
            query = """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
            """
            
            cursor.execute(query)
            conn_stats = cursor.fetchone()
            
            # Get Redis stats
            redis_stats = self.redis.health_check()
            
            return {
                'database': {
                    'tables': table_stats,
                    'connections': conn_stats
                },
                'redis': redis_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
    
    # ============= Cleanup Operations =============
    
    def archive_old_data(self, days: int = 30) -> Dict[str, int]:
        """Archive data older than specified days"""
        archived = {}
        
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            tables = ['market_data', 'chain_data', 'social_sentiment', 
                     'news_events', 'trader_actions', 'system_logs']
            
            for table in tables:
                # Count records to archive
                count_query = f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '{days} days'
                """
                cursor.execute(count_query)
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Archive (in production, would move to archive table)
                    delete_query = f"""
                        DELETE FROM {table}
                        WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '{days} days'
                    """
                    cursor.execute(delete_query)
                    archived[table] = count
            
            conn.commit()
            logger.info(f"Archived old data: {archived}")
            
        except Exception as e:
            logger.error(f"Failed to archive data: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)
        
        return archived
    
    def close(self):
        """Close all connections"""
        try:
            self.pool.close()
            self.redis.close()
            logger.info("DAL connections closed")
        except Exception as e:
            logger.error(f"Error closing DAL: {e}")

# Singleton instance
_dal_instance: Optional[DataAccessLayer] = None

def get_dal() -> DataAccessLayer:
    """Get singleton DAL instance"""
    global _dal_instance
    if _dal_instance is None:
        _dal_instance = DataAccessLayer()
    return _dal_instance