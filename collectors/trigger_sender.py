"""
触发信号发送器
负责将监控系统的触发信号发送给Window 6和其他窗口
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeliveryMethod(Enum):
    """传递方式枚举"""
    HTTP_POST = "http_post"
    REDIS_QUEUE = "redis_queue"
    FILE_BACKUP = "file_backup"
    WEBSOCKET = "websocket"


class PriorityLevel(Enum):
    """优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TriggerMessage:
    """触发消息数据类"""
    id: str
    source_window: int
    target_window: int
    trigger_level: int
    message_type: str
    data: Dict[str, Any]
    priority: int = 2
    timestamp: str = ""
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id:
            self.id = f"{self.source_window}_{self.target_window}_{int(datetime.now().timestamp() * 1000)}"


class TriggerSender:
    """触发信号发送器"""
    
    def __init__(self):
        # 目标窗口配置
        self.target_endpoints = {
            6: {  # Window 6 - AI决策大脑
                "http": "http://localhost:8006/api/trigger",
                "redis_queue": "window6_triggers",
                "priority": PriorityLevel.HIGH
            },
            7: {  # Window 7 - 风控执行
                "http": "http://localhost:8007/api/trigger",
                "redis_queue": "window7_triggers", 
                "priority": PriorityLevel.CRITICAL
            },
            8: {  # Window 8 - 通知系统
                "http": "http://localhost:8008/api/trigger",
                "redis_queue": "window8_triggers",
                "priority": PriorityLevel.MEDIUM
            },
            9: {  # Window 9 - 学习系统
                "http": "http://localhost:8009/api/trigger",
                "redis_queue": "window9_triggers",
                "priority": PriorityLevel.LOW
            }
        }
        
        # Redis连接
        self.redis_client = None
        
        # 发送统计
        self.stats = {
            "total_sent": 0,
            "success_sent": 0,
            "failed_sent": 0,
            "retries": 0,
            "last_send_time": None,
            "window_stats": {}
        }
        
        # 失败消息队列
        self.failed_messages = []
        
        # 备份目录
        self.backup_dir = Path("/tmp/trigger_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # WebSocket连接池
        self.websocket_connections = {}
        
        # 初始化标志
        self.initialized = False
    
    async def initialize(self):
        """初始化发送器"""
        if self.initialized:
            logger.warning("TriggerSender已经初始化")
            return
        
        logger.info("正在初始化触发信号发送器...")
        
        try:
            # 初始化Redis连接
            await self._initialize_redis()
            
            # 初始化WebSocket连接
            await self._initialize_websockets()
            
            # 启动重试任务
            asyncio.create_task(self._retry_failed_messages())
            
            # 启动统计任务
            asyncio.create_task(self._periodic_stats())
            
            self.initialized = True
            logger.info("触发信号发送器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    async def _initialize_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接成功")
            
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，将使用文件备份")
            self.redis_client = None
    
    async def _initialize_websockets(self):
        """初始化WebSocket连接"""
        # 这里可以初始化WebSocket连接
        # 暂时留空，未来可以扩展
        pass
    
    async def send_trigger_signal(self, source_window: int, target_window: int,
                                 trigger_level: int, message_type: str,
                                 data: Dict[str, Any], priority: int = 2) -> bool:
        """
        发送触发信号
        
        参数:
            source_window: 源窗口号
            target_window: 目标窗口号
            trigger_level: 触发级别 (1-3)
            message_type: 消息类型
            data: 消息数据
            priority: 优先级 (1-4)
        
        返回:
            bool: 是否发送成功
        """
        if not self.initialized:
            await self.initialize()
        
        # 创建触发消息
        message = TriggerMessage(
            id="",  # 将在__post_init__中生成
            source_window=source_window,
            target_window=target_window,
            trigger_level=trigger_level,
            message_type=message_type,
            data=data,
            priority=priority
        )
        
        logger.info(f"准备发送触发信号: {message.id} -> Window{target_window}")
        
        # 根据目标窗口和优先级选择发送方式
        success = await self._send_message(message)
        
        # 更新统计
        self._update_stats(target_window, success)
        
        return success
    
    async def _send_message(self, message: TriggerMessage) -> bool:
        """发送消息（支持多种方式）"""
        target_window = message.target_window
        
        if target_window not in self.target_endpoints:
            logger.error(f"未知的目标窗口: {target_window}")
            return False
        
        config = self.target_endpoints[target_window]
        
        # 根据优先级和可用性选择发送方式
        methods = self._get_delivery_methods(message, config)
        
        for method in methods:
            try:
                success = await self._send_by_method(message, method, config)
                if success:
                    logger.info(f"消息 {message.id} 通过 {method.value} 发送成功")
                    return True
                else:
                    logger.warning(f"消息 {message.id} 通过 {method.value} 发送失败")
            
            except Exception as e:
                logger.error(f"发送方法 {method.value} 出错: {e}")
                continue
        
        # 所有方法都失败，加入重试队列
        message.retry_count += 1
        if message.retry_count <= message.max_retries:
            self.failed_messages.append(message)
            logger.warning(f"消息 {message.id} 发送失败，已加入重试队列")
        else:
            logger.error(f"消息 {message.id} 超过最大重试次数，丢弃")
        
        return False
    
    def _get_delivery_methods(self, message: TriggerMessage, 
                             config: Dict[str, Any]) -> List[DeliveryMethod]:
        """根据优先级和配置获取发送方式"""
        methods = []
        
        # 高优先级和关键优先级优先使用HTTP
        if message.priority >= PriorityLevel.HIGH.value:
            methods.append(DeliveryMethod.HTTP_POST)
            if self.redis_client:
                methods.append(DeliveryMethod.REDIS_QUEUE)
            methods.append(DeliveryMethod.FILE_BACKUP)
        
        # 中等优先级优先使用Redis
        elif message.priority == PriorityLevel.MEDIUM.value:
            if self.redis_client:
                methods.append(DeliveryMethod.REDIS_QUEUE)
            methods.append(DeliveryMethod.HTTP_POST)
            methods.append(DeliveryMethod.FILE_BACKUP)
        
        # 低优先级使用文件备份
        else:
            methods.append(DeliveryMethod.FILE_BACKUP)
            if self.redis_client:
                methods.append(DeliveryMethod.REDIS_QUEUE)
            methods.append(DeliveryMethod.HTTP_POST)
        
        return methods
    
    async def _send_by_method(self, message: TriggerMessage, 
                             method: DeliveryMethod, 
                             config: Dict[str, Any]) -> bool:
        """按指定方式发送消息"""
        
        if method == DeliveryMethod.HTTP_POST:
            return await self._send_by_http(message, config)
        
        elif method == DeliveryMethod.REDIS_QUEUE:
            return await self._send_by_redis(message, config)
        
        elif method == DeliveryMethod.FILE_BACKUP:
            return await self._send_by_file(message, config)
        
        elif method == DeliveryMethod.WEBSOCKET:
            return await self._send_by_websocket(message, config)
        
        else:
            logger.error(f"未支持的发送方式: {method}")
            return False
    
    async def _send_by_http(self, message: TriggerMessage, 
                           config: Dict[str, Any]) -> bool:
        """通过HTTP POST发送"""
        try:
            endpoint = config.get("http")
            if not endpoint:
                return False
            
            message_data = asdict(message)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=message_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"HTTP发送失败: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"HTTP发送异常: {e}")
            return False
    
    async def _send_by_redis(self, message: TriggerMessage, 
                            config: Dict[str, Any]) -> bool:
        """通过Redis队列发送"""
        if not self.redis_client:
            return False
        
        try:
            queue_name = config.get("redis_queue")
            if not queue_name:
                return False
            
            message_json = json.dumps(asdict(message), ensure_ascii=False)
            
            # 根据优先级选择队列操作
            if message.priority >= PriorityLevel.HIGH.value:
                # 高优先级消息放在队列前面
                await self.redis_client.lpush(queue_name, message_json)
            else:
                # 普通消息放在队列后面
                await self.redis_client.rpush(queue_name, message_json)
            
            # 设置TTL
            await self.redis_client.expire(queue_name, 3600)  # 1小时过期
            
            return True
        
        except Exception as e:
            logger.error(f"Redis发送异常: {e}")
            return False
    
    async def _send_by_file(self, message: TriggerMessage, 
                           config: Dict[str, Any]) -> bool:
        """通过文件备份发送"""
        try:
            # 按窗口和日期创建文件
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"window{message.target_window}_triggers_{date_str}.jsonl"
            filepath = self.backup_dir / filename
            
            message_json = json.dumps(asdict(message), ensure_ascii=False)
            
            # 追加写入文件
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(message_json + '\n')
            
            return True
        
        except Exception as e:
            logger.error(f"文件备份异常: {e}")
            return False
    
    async def _send_by_websocket(self, message: TriggerMessage, 
                                config: Dict[str, Any]) -> bool:
        """通过WebSocket发送"""
        # 暂未实现WebSocket发送
        # 可以在未来扩展
        return False
    
    async def send_broadcast(self, source_window: int, trigger_level: int,
                            message_type: str, data: Dict[str, Any],
                            target_windows: List[int] = None) -> Dict[int, bool]:
        """
        广播发送到多个窗口
        
        参数:
            source_window: 源窗口号
            trigger_level: 触发级别
            message_type: 消息类型
            data: 消息数据
            target_windows: 目标窗口列表，None表示所有窗口
        
        返回:
            Dict[int, bool]: 每个窗口的发送结果
        """
        if target_windows is None:
            target_windows = list(self.target_endpoints.keys())
        
        results = {}
        tasks = []
        
        for target_window in target_windows:
            task = asyncio.create_task(
                self.send_trigger_signal(
                    source_window=source_window,
                    target_window=target_window,
                    trigger_level=trigger_level,
                    message_type=message_type,
                    data=data,
                    priority=trigger_level  # 触发级别作为优先级
                )
            )
            tasks.append((target_window, task))
        
        # 等待所有发送任务完成
        for target_window, task in tasks:
            try:
                success = await task
                results[target_window] = success
            except Exception as e:
                logger.error(f"广播到Window{target_window}失败: {e}")
                results[target_window] = False
        
        return results
    
    async def _retry_failed_messages(self):
        """重试失败的消息"""
        while True:
            try:
                if self.failed_messages:
                    logger.info(f"正在重试 {len(self.failed_messages)} 条失败消息")
                    
                    # 复制列表以避免并发修改
                    messages_to_retry = self.failed_messages.copy()
                    self.failed_messages.clear()
                    
                    for message in messages_to_retry:
                        success = await self._send_message(message)
                        if success:
                            self.stats["retries"] += 1
                            logger.info(f"消息 {message.id} 重试成功")
                        # 失败的消息会在_send_message中重新加入队列
                
                await asyncio.sleep(30)  # 每30秒重试一次
                
            except Exception as e:
                logger.error(f"重试任务异常: {e}")
                await asyncio.sleep(30)
    
    async def _periodic_stats(self):
        """定期输出统计信息"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟输出一次
                stats = self.get_statistics()
                logger.info(f"发送统计: {stats}")
                
            except Exception as e:
                logger.error(f"统计任务异常: {e}")
    
    def _update_stats(self, target_window: int, success: bool):
        """更新统计信息"""
        self.stats["total_sent"] += 1
        self.stats["last_send_time"] = datetime.now().isoformat()
        
        if success:
            self.stats["success_sent"] += 1
        else:
            self.stats["failed_sent"] += 1
        
        # 按窗口统计
        if target_window not in self.stats["window_stats"]:
            self.stats["window_stats"][target_window] = {
                "total": 0,
                "success": 0,
                "failed": 0
            }
        
        window_stats = self.stats["window_stats"][target_window]
        window_stats["total"] += 1
        
        if success:
            window_stats["success"] += 1
        else:
            window_stats["failed"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "failed_messages_count": len(self.failed_messages),
            "target_windows": list(self.target_endpoints.keys()),
            "redis_available": self.redis_client is not None,
            "initialized": self.initialized
        }
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        if not self.redis_client:
            return {"error": "Redis不可用"}
        
        queue_status = {}
        
        for window, config in self.target_endpoints.items():
            queue_name = config.get("redis_queue")
            if queue_name:
                try:
                    length = await self.redis_client.llen(queue_name)
                    queue_status[f"window{window}"] = {
                        "queue_name": queue_name,
                        "length": length
                    }
                except Exception as e:
                    queue_status[f"window{window}"] = {
                        "queue_name": queue_name,
                        "error": str(e)
                    }
        
        return queue_status
    
    async def clear_failed_messages(self):
        """清空失败消息队列"""
        count = len(self.failed_messages)
        self.failed_messages.clear()
        logger.info(f"已清空 {count} 条失败消息")
        return count
    
    async def shutdown(self):
        """关闭发送器"""
        logger.info("正在关闭触发信号发送器...")
        
        # 关闭Redis连接
        if self.redis_client:
            await self.redis_client.close()
        
        # 关闭WebSocket连接
        for conn in self.websocket_connections.values():
            await conn.close()
        
        logger.info("触发信号发送器已关闭")


# 全局发送器实例
trigger_sender = TriggerSender()


async def send_window6_trigger(trigger_level: int, message_type: str, 
                              data: Dict[str, Any]) -> bool:
    """
    便捷函数：发送触发信号给Window 6
    
    参数:
        trigger_level: 触发级别 (1-3)
        message_type: 消息类型
        data: 消息数据
    
    返回:
        bool: 是否发送成功
    """
    if not trigger_sender.initialized:
        await trigger_sender.initialize()
    
    return await trigger_sender.send_trigger_signal(
        source_window=3,
        target_window=6,
        trigger_level=trigger_level,
        message_type=message_type,
        data=data,
        priority=trigger_level
    )


async def broadcast_trigger(trigger_level: int, message_type: str, 
                           data: Dict[str, Any]) -> Dict[int, bool]:
    """
    便捷函数：广播触发信号到所有窗口
    
    参数:
        trigger_level: 触发级别 (1-3)
        message_type: 消息类型
        data: 消息数据
    
    返回:
        Dict[int, bool]: 每个窗口的发送结果
    """
    if not trigger_sender.initialized:
        await trigger_sender.initialize()
    
    return await trigger_sender.send_broadcast(
        source_window=3,
        trigger_level=trigger_level,
        message_type=message_type,
        data=data
    )


async def main():
    """主函数 - 用于测试"""
    sender = TriggerSender()
    
    try:
        # 初始化
        await sender.initialize()
        
        # 测试发送触发信号
        test_data = {
            "symbol": "BTC",
            "trigger_type": "price_surge",
            "value": 0.05,
            "description": "BTC价格上涨5%"
        }
        
        # 发送给Window 6
        logger.info("测试发送到Window 6...")
        success = await sender.send_trigger_signal(
            source_window=3,
            target_window=6,
            trigger_level=2,
            message_type="price_alert",
            data=test_data,
            priority=3
        )
        logger.info(f"发送结果: {success}")
        
        # 测试广播
        logger.info("测试广播...")
        results = await sender.send_broadcast(
            source_window=3,
            trigger_level=1,
            message_type="market_update",
            data=test_data
        )
        logger.info(f"广播结果: {results}")
        
        # 输出统计
        logger.info(f"统计信息: {sender.get_statistics()}")
        
        # 输出队列状态
        queue_status = await sender.get_queue_status()
        logger.info(f"队列状态: {queue_status}")
        
        # 等待重试任务运行
        await asyncio.sleep(5)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
    finally:
        await sender.shutdown()


if __name__ == "__main__":
    asyncio.run(main())