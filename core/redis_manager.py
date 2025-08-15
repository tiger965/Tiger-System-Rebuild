"""Redis manager for Tiger System"""

import redis
import json
import asyncio
import aioredis
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class RedisManager:
    """Manage Redis connections and operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Redis manager"""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'redis.yaml'
        self.config = self._load_config()
        self.client = None
        self.pubsub = None
        self.async_client = None
        self._connect()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Redis configuration"""
        default_config = {
            'host': 'localhost',
            'port': 6379,
            'password': 'tiger_redis_2024',
            'db': 0,
            'decode_responses': True,
            'max_connections': 50,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Could not load Redis config: {e}")
        
        return default_config
    
    def _connect(self):
        """Establish Redis connection"""
        try:
            pool = redis.ConnectionPool(
                host=self.config['host'],
                port=self.config['port'],
                password=self.config.get('password'),
                db=self.config['db'],
                decode_responses=self.config['decode_responses'],
                max_connections=self.config['max_connections']
            )
            self.client = redis.Redis(connection_pool=pool)
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def _async_connect(self):
        """Establish async Redis connection"""
        try:
            self.async_client = await aioredis.from_url(
                f"redis://{self.config['host']}:{self.config['port']}",
                password=self.config.get('password'),
                db=self.config['db'],
                decode_responses=self.config['decode_responses']
            )
            await self.async_client.ping()
            logger.info("Async Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect async Redis: {e}")
            raise
    
    # Cache operations
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = 3600) -> bool:
        """Set cache value with TTL"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.setex(key, ttl, value)
        except redis.RedisError as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to get cache: {e}")
            return None
    
    def delete_cache(self, pattern: str) -> int:
        """Delete cache keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Failed to delete cache: {e}")
            return 0
    
    # Hash operations for real-time market data
    def set_market_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store market data in hash"""
        key = f"market:{symbol}"
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Convert numeric values to strings for Redis
            hash_data = {k: str(v) for k, v in data.items()}
            self.client.hset(key, mapping=hash_data)
            self.client.expire(key, 300)  # 5 minutes TTL
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to set market data: {e}")
            return False
    
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data from hash"""
        key = f"market:{symbol}"
        try:
            data = self.client.hgetall(key)
            return data if data else None
        except redis.RedisError as e:
            logger.error(f"Failed to get market data: {e}")
            return None
    
    # Message queue operations
    def push_message(self, queue: str, message: Dict[str, Any]) -> bool:
        """Push message to queue"""
        try:
            message['timestamp'] = datetime.now().isoformat()
            return self.client.lpush(queue, json.dumps(message)) > 0
        except redis.RedisError as e:
            logger.error(f"Failed to push message: {e}")
            return False
    
    def pop_message(self, queue: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """Pop message from queue with blocking"""
        try:
            result = self.client.brpop(queue, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to pop message: {e}")
            return None
    
    def get_queue_length(self, queue: str) -> int:
        """Get number of messages in queue"""
        try:
            return self.client.llen(queue)
        except redis.RedisError as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0
    
    # Stream operations for more advanced message queuing
    def add_to_stream(self, stream: str, data: Dict[str, Any], max_length: int = 10000) -> Optional[str]:
        """Add message to Redis Stream"""
        try:
            # Convert all values to strings
            stream_data = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                          for k, v in data.items()}
            message_id = self.client.xadd(stream, stream_data, maxlen=max_length)
            return message_id
        except redis.RedisError as e:
            logger.error(f"Failed to add to stream: {e}")
            return None
    
    def read_from_stream(self, stream: str, last_id: str = '0', count: int = 10) -> List[Dict[str, Any]]:
        """Read messages from Redis Stream"""
        try:
            messages = self.client.xread({stream: last_id}, count=count, block=100)
            result = []
            for stream_name, stream_messages in messages:
                for message_id, data in stream_messages:
                    # Parse JSON fields back
                    parsed_data = {}
                    for k, v in data.items():
                        try:
                            parsed_data[k] = json.loads(v)
                        except json.JSONDecodeError:
                            parsed_data[k] = v
                    parsed_data['_id'] = message_id
                    result.append(parsed_data)
            return result
        except redis.RedisError as e:
            logger.error(f"Failed to read from stream: {e}")
            return []
    
    # Pub/Sub operations
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to channel"""
        try:
            message['timestamp'] = datetime.now().isoformat()
            return self.client.publish(channel, json.dumps(message)) > 0
        except redis.RedisError as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def subscribe(self, channels: List[str], callback: Callable) -> None:
        """Subscribe to channels with callback"""
        try:
            self.pubsub = self.client.pubsub()
            self.pubsub.subscribe(*channels)
            
            # Start listening in a separate thread
            import threading
            thread = threading.Thread(target=self._listen, args=(callback,))
            thread.daemon = True
            thread.start()
            
            logger.info(f"Subscribed to channels: {channels}")
        except redis.RedisError as e:
            logger.error(f"Failed to subscribe: {e}")
    
    def _listen(self, callback: Callable):
        """Listen for messages (runs in separate thread)"""
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        callback(message['channel'], data)
                    except json.JSONDecodeError:
                        callback(message['channel'], message['data'])
        except Exception as e:
            logger.error(f"Error in pubsub listener: {e}")
    
    # Channel definitions for Tiger System
    CHANNELS = {
        'MARKET_UPDATES': 'market_updates',
        'SIGNALS': 'signals',
        'ALERTS': 'alerts',
        'SYSTEM_STATUS': 'system_status',
        'CHAIN_DATA': 'chain_data',
        'SOCIAL_SENTIMENT': 'social_sentiment',
        'NEWS_EVENTS': 'news_events',
        'TRADER_ACTIONS': 'trader_actions'
    }
    
    # Queue definitions
    QUEUES = {
        'TRADE_EXECUTION': 'queue:trade_execution',
        'DATA_PROCESSING': 'queue:data_processing',
        'NOTIFICATION': 'queue:notification',
        'ANALYSIS': 'queue:analysis'
    }
    
    # Stream definitions
    STREAMS = {
        'MARKET_DATA': 'stream:market_data',
        'SIGNALS': 'stream:signals',
        'SYSTEM_LOGS': 'stream:system_logs'
    }
    
    def set_signal(self, signal_id: str, signal_data: Dict[str, Any]) -> bool:
        """Store signal in Redis with expiration"""
        key = f"signal:{signal_id}"
        try:
            self.client.setex(
                key,
                timedelta(hours=24),
                json.dumps(signal_data)
            )
            # Also add to signals list for quick access
            self.client.lpush("signals:active", signal_id)
            self.client.ltrim("signals:active", 0, 999)  # Keep last 1000
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to set signal: {e}")
            return False
    
    def get_active_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of active signals"""
        try:
            signal_ids = self.client.lrange("signals:active", 0, limit - 1)
            signals = []
            for signal_id in signal_ids:
                signal_data = self.client.get(f"signal:{signal_id}")
                if signal_data:
                    signals.append(json.loads(signal_data))
            return signals
        except redis.RedisError as e:
            logger.error(f"Failed to get active signals: {e}")
            return []
    
    def cleanup_expired(self) -> int:
        """Clean up expired keys"""
        try:
            # Redis automatically handles expiration
            # This method can be used for custom cleanup logic
            return 0
        except redis.RedisError as e:
            logger.error(f"Failed to cleanup: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis health status"""
        try:
            info = self.client.info()
            return {
                'status': 'healthy',
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0),
                'total_commands': info.get('total_commands_processed', 0)
            }
        except redis.RedisError as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    def close(self):
        """Close Redis connections"""
        try:
            if self.pubsub:
                self.pubsub.close()
            if self.client:
                self.client.close()
            if self.async_client:
                asyncio.create_task(self.async_client.close())
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")