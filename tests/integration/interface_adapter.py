#!/usr/bin/env python3
"""
Tiger系统 - 接口适配层
10号窗口 - 统一接口管理
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import redis
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""
    MARKET_DATA = "market_data"
    CHAIN_DATA = "chain_data"
    SOCIAL_DATA = "social_data"
    NEWS_DATA = "news_data"
    INDICATOR_SIGNAL = "indicator_signal"
    AI_DECISION = "ai_decision"
    RISK_ALERT = "risk_alert"
    NOTIFICATION = "notification"
    SYSTEM_EVENT = "system_event"


class DataFlow:
    """数据流定义"""
    
    FLOWS = {
        "collector_to_db": {
            "source": ["exchange", "chain_social", "bicoin"],
            "target": "database",
            "description": "采集器→数据库"
        },
        "db_to_analyzer": {
            "source": "database",
            "target": ["indicators", "ai"],
            "description": "数据库→分析器"
        },
        "analyzer_to_ai": {
            "source": "indicators",
            "target": "ai",
            "description": "分析器→AI"
        },
        "ai_to_risk": {
            "source": "ai",
            "target": "risk",
            "description": "AI→风控"
        },
        "risk_to_notification": {
            "source": "risk",
            "target": "notification",
            "description": "风控→通知"
        },
        "learning_feedback": {
            "source": "learning",
            "target": ["ai", "indicators", "risk"],
            "description": "学习反馈→各模块"
        }
    }


class BaseAdapter(ABC):
    """基础适配器接口"""
    
    @abstractmethod
    async def send(self, data: Dict[str, Any]):
        """发送数据"""
        pass
        
    @abstractmethod
    async def receive(self) -> Optional[Dict[str, Any]]:
        """接收数据"""
        pass
        
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        pass


class MessageBus:
    """消息总线 - 使用Redis Pub/Sub"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """
        初始化消息总线
        
        Args:
            redis_host: Redis主机
            redis_port: Redis端口
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            self.subscribers = {}
            logger.info(f"消息总线初始化成功 - Redis {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"消息总线初始化失败: {e}")
            self.redis_client = None
            self.pubsub = None
            
    def publish(self, channel: str, message: Dict[str, Any]):
        """
        发布消息
        
        Args:
            channel: 频道名称
            message: 消息内容
        """
        if not self.redis_client:
            logger.warning("Redis未连接，消息发布失败")
            return False
            
        try:
            # 添加时间戳
            message["timestamp"] = datetime.now().isoformat()
            
            # 序列化消息
            message_str = json.dumps(message, ensure_ascii=False)
            
            # 发布
            self.redis_client.publish(channel, message_str)
            logger.debug(f"消息发布到 {channel}: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"消息发布失败: {e}")
            return False
            
    def subscribe(self, channel: str, callback: Callable):
        """
        订阅频道
        
        Args:
            channel: 频道名称
            callback: 回调函数
        """
        if not self.pubsub:
            logger.warning("Redis未连接，无法订阅")
            return False
            
        try:
            self.pubsub.subscribe(channel)
            self.subscribers[channel] = callback
            logger.info(f"已订阅频道: {channel}")
            return True
            
        except Exception as e:
            logger.error(f"订阅失败: {e}")
            return False
            
    async def listen(self):
        """监听消息"""
        if not self.pubsub:
            logger.warning("Redis未连接，无法监听")
            return
            
        logger.info("开始监听消息...")
        
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                data = json.loads(message['data'])
                
                # 调用对应的回调函数
                if channel in self.subscribers:
                    callback = self.subscribers[channel]
                    asyncio.create_task(callback(data))


class InterfaceAdapter:
    """统一接口适配器"""
    
    def __init__(self):
        """初始化接口适配器"""
        self.message_bus = MessageBus()
        self.api_gateway = APIGateway()
        self.data_transformer = DataTransformer()
        
        # 注册数据流
        self.data_flows = DataFlow.FLOWS
        
        logger.info("接口适配器初始化完成")
        
    def setup_data_flows(self):
        """设置数据流转"""
        for flow_name, flow_config in self.data_flows.items():
            logger.info(f"配置数据流: {flow_config['description']}")
            
            # 这里可以设置具体的数据流转逻辑
            # 例如：订阅源频道，处理后发布到目标频道
            
    async def route_message(self, message: Dict[str, Any]):
        """
        路由消息到正确的目标
        
        Args:
            message: 消息内容
        """
        msg_type = message.get("type")
        source = message.get("source")
        
        # 根据消息类型和来源确定目标
        if msg_type == MessageType.MARKET_DATA.value:
            # 市场数据 → 数据库、指标分析
            await self.send_to_database(message)
            await self.send_to_indicators(message)
            
        elif msg_type == MessageType.INDICATOR_SIGNAL.value:
            # 指标信号 → AI决策
            await self.send_to_ai(message)
            
        elif msg_type == MessageType.AI_DECISION.value:
            # AI决策 → 风控
            await self.send_to_risk(message)
            
        elif msg_type == MessageType.RISK_ALERT.value:
            # 风控警报 → 通知
            await self.send_to_notification(message)
            
    async def send_to_database(self, message: Dict[str, Any]):
        """发送到数据库"""
        self.message_bus.publish("database_channel", message)
        
    async def send_to_indicators(self, message: Dict[str, Any]):
        """发送到指标分析"""
        self.message_bus.publish("indicators_channel", message)
        
    async def send_to_ai(self, message: Dict[str, Any]):
        """发送到AI决策"""
        self.message_bus.publish("ai_channel", message)
        
    async def send_to_risk(self, message: Dict[str, Any]):
        """发送到风控"""
        self.message_bus.publish("risk_channel", message)
        
    async def send_to_notification(self, message: Dict[str, Any]):
        """发送到通知"""
        self.message_bus.publish("notification_channel", message)


class APIGateway:
    """API网关"""
    
    def __init__(self):
        """初始化API网关"""
        self.internal_apis = {}
        self.external_apis = {}
        self.rate_limiters = {}
        self.auth_manager = AuthManager()
        
    def register_internal_api(self, name: str, handler: Callable):
        """注册内部API"""
        self.internal_apis[name] = handler
        logger.info(f"注册内部API: {name}")
        
    def register_external_api(self, name: str, config: Dict[str, Any]):
        """注册外部API"""
        self.external_apis[name] = config
        logger.info(f"注册外部API: {name}")
        
    async def call_internal(self, api_name: str, params: Dict[str, Any]) -> Any:
        """调用内部API"""
        if api_name not in self.internal_apis:
            raise ValueError(f"未知的内部API: {api_name}")
            
        handler = self.internal_apis[api_name]
        return await handler(**params)
        
    async def call_external(self, api_name: str, params: Dict[str, Any]) -> Any:
        """调用外部API"""
        if api_name not in self.external_apis:
            raise ValueError(f"未知的外部API: {api_name}")
            
        # 检查限流
        if not self.check_rate_limit(api_name):
            raise Exception(f"API {api_name} 触发限流")
            
        # 这里实现具体的外部API调用逻辑
        config = self.external_apis[api_name]
        # ... 调用逻辑 ...
        
    def check_rate_limit(self, api_name: str) -> bool:
        """检查API限流"""
        # 实现限流逻辑
        return True


class DataTransformer:
    """数据转换器"""
    
    def __init__(self):
        """初始化数据转换器"""
        self.transformers = {}
        
    def register_transformer(self, 
                            source_format: str, 
                            target_format: str, 
                            transformer: Callable):
        """注册转换器"""
        key = f"{source_format}_to_{target_format}"
        self.transformers[key] = transformer
        logger.info(f"注册数据转换器: {key}")
        
    def transform(self, 
                 data: Any, 
                 source_format: str, 
                 target_format: str) -> Any:
        """转换数据格式"""
        key = f"{source_format}_to_{target_format}"
        
        if key not in self.transformers:
            logger.warning(f"无转换器: {key}")
            return data
            
        transformer = self.transformers[key]
        return transformer(data)


class AuthManager:
    """认证授权管理器"""
    
    def __init__(self):
        """初始化认证管理器"""
        self.tokens = {}
        self.permissions = {}
        
    def authenticate(self, token: str) -> bool:
        """认证token"""
        return token in self.tokens
        
    def authorize(self, token: str, resource: str) -> bool:
        """授权访问资源"""
        if token not in self.tokens:
            return False
            
        user_permissions = self.permissions.get(token, [])
        return resource in user_permissions
        
    def register_token(self, token: str, permissions: List[str]):
        """注册token和权限"""
        self.tokens[token] = True
        self.permissions[token] = permissions


class ModuleConnector:
    """模块连接器 - 用于连接各个窗口的模块"""
    
    def __init__(self, adapter: InterfaceAdapter):
        """
        初始化模块连接器
        
        Args:
            adapter: 接口适配器
        """
        self.adapter = adapter
        self.connections = {}
        
    async def connect_modules(self, source: str, target: str):
        """
        连接两个模块
        
        Args:
            source: 源模块
            target: 目标模块
        """
        connection_key = f"{source}_to_{target}"
        
        if connection_key in self.connections:
            logger.warning(f"连接已存在: {connection_key}")
            return
            
        # 创建连接
        self.connections[connection_key] = {
            "source": source,
            "target": target,
            "created_at": datetime.now(),
            "message_count": 0
        }
        
        logger.info(f"模块连接建立: {source} → {target}")
        
    async def send_between_modules(self, 
                                   source: str, 
                                   target: str, 
                                   data: Dict[str, Any]):
        """
        在模块间发送数据
        
        Args:
            source: 源模块
            target: 目标模块
            data: 数据
        """
        connection_key = f"{source}_to_{target}"
        
        if connection_key not in self.connections:
            await self.connect_modules(source, target)
            
        # 更新统计
        self.connections[connection_key]["message_count"] += 1
        
        # 添加路由信息
        data["_routing"] = {
            "source": source,
            "target": target,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送消息
        await self.adapter.route_message(data)
        
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        stats = {
            "total_connections": len(self.connections),
            "connections": []
        }
        
        for key, conn in self.connections.items():
            stats["connections"].append({
                "route": key,
                "message_count": conn["message_count"],
                "created_at": conn["created_at"].isoformat()
            })
            
        return stats


def create_interface_system():
    """创建接口系统"""
    # 创建适配器
    adapter = InterfaceAdapter()
    
    # 设置数据流
    adapter.setup_data_flows()
    
    # 创建模块连接器
    connector = ModuleConnector(adapter)
    
    # 建立核心连接
    asyncio.run(connector.connect_modules("exchange", "database"))
    asyncio.run(connector.connect_modules("chain_social", "database"))
    asyncio.run(connector.connect_modules("database", "indicators"))
    asyncio.run(connector.connect_modules("indicators", "ai"))
    asyncio.run(connector.connect_modules("ai", "risk"))
    asyncio.run(connector.connect_modules("risk", "notification"))
    
    logger.info("接口系统创建完成")
    
    return adapter, connector


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建接口系统
    adapter, connector = create_interface_system()
    
    # 获取连接统计
    stats = connector.get_connection_stats()
    print(f"\n连接统计: {json.dumps(stats, indent=2)}")