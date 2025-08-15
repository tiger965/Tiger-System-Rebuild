"""Base Data Access Layer"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json

logger = logging.getLogger(__name__)

class BaseDAL:
    """基础数据访问层"""
    
    def __init__(self, db_config: dict, redis_config: dict):
        """初始化DAL
        
        Args:
            db_config: PostgreSQL配置
            redis_config: Redis配置
        """
        self.db_config = db_config
        self.redis_config = redis_config
        self._db_conn = None
        self._redis_conn = None
    
    @property
    def db_conn(self):
        """获取数据库连接"""
        if not self._db_conn or self._db_conn.closed:
            self._db_conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
        return self._db_conn
    
    @property
    def redis_conn(self):
        """获取Redis连接"""
        if not self._redis_conn:
            self._redis_conn = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                decode_responses=True
            )
        return self._redis_conn
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.db_conn.rollback()
            raise
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[str]:
        """执行插入
        
        Args:
            query: SQL插入语句
            params: 插入参数
            
        Returns:
            插入的ID
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(query + " RETURNING id", params)
                result = cursor.fetchone()
                self.db_conn.commit()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Insert execution failed: {e}")
            self.db_conn.rollback()
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(query, params)
                affected = cursor.rowcount
                self.db_conn.commit()
                return affected
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            self.db_conn.rollback()
            raise
    
    def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.redis_conn.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
    
    def cache_get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        try:
            value = self.redis_conn.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def close(self):
        """关闭连接"""
        if self._db_conn:
            self._db_conn.close()
        if self._redis_conn:
            self._redis_conn.close()