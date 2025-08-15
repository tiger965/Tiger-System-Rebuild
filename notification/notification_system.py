"""
分级通知系统 - 8号窗口核心模块
管理所有通知的分发和控制
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import deque
import asyncio
import threading
from dataclasses import dataclass, asdict

class NotificationLevel(Enum):
    """通知级别枚举"""
    INFO = "INFO"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"

@dataclass
class Notification:
    """通知消息数据类"""
    level: NotificationLevel
    title: str
    content: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        data = asdict(self)
        data['level'] = self.level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class NotificationSystem:
    """分级通知系统主类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化通知系统"""
        self.logger = logging.getLogger(__name__)
        
        # 通知级别配置
        self.levels = {
            NotificationLevel.INFO: {
                "description": "一般信息",
                "action": "仅终端显示",
                "icon": "ℹ️",
                "example": "RSI进入超买区",
                "channels": ["terminal"]
            },
            NotificationLevel.IMPORTANT: {
                "description": "重要信号",
                "action": "Telegram推送",
                "icon": "📊",
                "example": "触发开仓信号",
                "channels": ["terminal", "telegram"]
            },
            NotificationLevel.URGENT: {
                "description": "紧急警报",
                "action": "Telegram + 邮件",
                "icon": "⚠️",
                "example": "止损触发、黑天鹅",
                "channels": ["terminal", "telegram", "email"]
            },
            NotificationLevel.CRITICAL: {
                "description": "危急情况",
                "action": "所有渠道 + 电话",
                "icon": "🚨",
                "example": "爆仓风险、系统故障",
                "channels": ["terminal", "telegram", "email", "webhook", "sms"]
            }
        }
        
        # 推送渠道状态
        self.channels = {
            "terminal": {"enabled": True, "handler": None},
            "telegram": {"enabled": False, "handler": None},
            "email": {"enabled": False, "handler": None},
            "webhook": {"enabled": False, "handler": None},
            "sms": {"enabled": False, "handler": None}
        }
        
        # 消息队列和历史记录
        self.message_queue = deque(maxlen=1000)
        self.sent_history = deque(maxlen=10000)
        
        # 限流控制
        self.rate_limit = {
            "max_per_minute": 10,
            "max_per_hour": 100,
            "current_minute_count": 0,
            "current_hour_count": 0,
            "last_minute_reset": datetime.now(),
            "last_hour_reset": datetime.now()
        }
        
        # 去重机制
        self.deduplication = {
            "enabled": True,
            "window_seconds": 60,
            "recent_hashes": deque(maxlen=100)
        }
        
        # 免打扰模式
        self.quiet_hours = {
            "enabled": True,
            "start_hour": 23,
            "end_hour": 7,
            "exceptions": [NotificationLevel.CRITICAL, NotificationLevel.URGENT]
        }
        
        # 统计信息
        self.stats = {
            "total_sent": 0,
            "by_level": {level.value: 0 for level in NotificationLevel},
            "by_channel": {ch: 0 for ch in self.channels},
            "failed": 0,
            "deduplicated": 0,
            "rate_limited": 0
        }
        
        # 加载配置
        if config_path:
            self.load_config(config_path)
            
        # 启动后台处理线程
        self.running = True
        self.process_thread = threading.Thread(target=self._process_queue)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def send(self, 
             level: NotificationLevel,
             title: str,
             content: str,
             source: str = "System",
             metadata: Dict[str, Any] = None,
             force: bool = False) -> bool:
        """
        发送通知
        
        Args:
            level: 通知级别
            title: 标题
            content: 内容
            source: 来源
            metadata: 附加数据
            force: 强制发送（跳过限流和去重）
            
        Returns:
            是否成功加入队列
        """
        # 创建通知对象
        notification = Notification(
            level=level,
            title=title,
            content=content,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # 检查是否在免打扰时间
        if not force and self._is_quiet_hours(notification):
            self.logger.info(f"通知在免打扰时间被屏蔽: {title}")
            return False
        
        # 检查去重
        if not force and self._is_duplicate(notification):
            self.stats["deduplicated"] += 1
            self.logger.info(f"重复通知被过滤: {title}")
            return False
        
        # 检查限流
        if not force and not self._check_rate_limit():
            self.stats["rate_limited"] += 1
            self.logger.warning(f"触发限流，通知被延迟: {title}")
            # 延迟发送而不是丢弃
            threading.Timer(60, lambda: self.send(
                level, title, content, source, metadata, force=True
            )).start()
            return False
        
        # 加入队列
        self.message_queue.append(notification)
        self.logger.info(f"通知已加入队列: [{level.value}] {title}")
        return True
    
    def _process_queue(self):
        """后台处理消息队列"""
        while self.running:
            try:
                if self.message_queue:
                    notification = self.message_queue.popleft()
                    self._dispatch_notification(notification)
                else:
                    # 队列为空，等待
                    import time
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"处理通知时出错: {e}")
    
    def _dispatch_notification(self, notification: Notification):
        """分发通知到各个渠道"""
        level_config = self.levels[notification.level]
        channels_to_use = level_config["channels"]
        
        # 格式化消息
        formatted_message = self._format_message(notification)
        
        success_count = 0
        for channel in channels_to_use:
            if self.channels[channel]["enabled"]:
                try:
                    if self._send_to_channel(channel, formatted_message, notification):
                        success_count += 1
                        self.stats["by_channel"][channel] += 1
                except Exception as e:
                    self.logger.error(f"发送到{channel}失败: {e}")
                    self.stats["failed"] += 1
        
        if success_count > 0:
            self.stats["total_sent"] += 1
            self.stats["by_level"][notification.level.value] += 1
            self.sent_history.append(notification)
            self.logger.info(f"通知发送成功: {notification.title} (渠道数: {success_count})")
        else:
            self.stats["failed"] += 1
            self.logger.error(f"通知发送失败: {notification.title}")
    
    def _format_message(self, notification: Notification) -> str:
        """格式化消息"""
        icon = self.levels[notification.level]["icon"]
        timestamp = notification.timestamp.strftime("%H:%M:%S")
        
        message = f"{icon} [{notification.level.value}] {timestamp}\n"
        message += f"📌 {notification.title}\n"
        message += f"📝 {notification.content}\n"
        message += f"🔍 来源: {notification.source}"
        
        if notification.metadata:
            message += f"\n📊 附加信息: {json.dumps(notification.metadata, ensure_ascii=False, indent=2)}"
        
        return message
    
    def _send_to_channel(self, channel: str, message: str, notification: Notification) -> bool:
        """发送到指定渠道"""
        if channel == "terminal":
            # 终端输出
            self._print_to_terminal(message, notification.level)
            return True
        
        # 其他渠道需要对应的handler
        handler = self.channels[channel].get("handler")
        if handler:
            return handler.send(message, notification)
        
        # 如果没有handler，记录日志
        self.logger.warning(f"{channel}渠道未配置handler")
        return False
    
    def _print_to_terminal(self, message: str, level: NotificationLevel):
        """输出到终端（带颜色）"""
        colors = {
            NotificationLevel.INFO: "\033[94m",      # 蓝色
            NotificationLevel.IMPORTANT: "\033[93m",  # 黄色
            NotificationLevel.URGENT: "\033[91m",     # 红色
            NotificationLevel.CRITICAL: "\033[95m"    # 紫色
        }
        reset = "\033[0m"
        
        color = colors.get(level, "")
        print(f"{color}{message}{reset}")
        print("-" * 50)
    
    def _is_quiet_hours(self, notification: Notification) -> bool:
        """检查是否在免打扰时间"""
        if not self.quiet_hours["enabled"]:
            return False
        
        # 检查是否是例外级别
        if notification.level in self.quiet_hours["exceptions"]:
            return False
        
        current_hour = datetime.now().hour
        start = self.quiet_hours["start_hour"]
        end = self.quiet_hours["end_hour"]
        
        # 处理跨天的情况
        if start > end:
            return current_hour >= start or current_hour < end
        else:
            return start <= current_hour < end
    
    def _is_duplicate(self, notification: Notification) -> bool:
        """检查是否重复"""
        if not self.deduplication["enabled"]:
            return False
        
        # 生成消息哈希
        msg_hash = hash(f"{notification.level.value}:{notification.title}:{notification.content}")
        
        if msg_hash in self.deduplication["recent_hashes"]:
            return True
        
        self.deduplication["recent_hashes"].append(msg_hash)
        return False
    
    def _check_rate_limit(self) -> bool:
        """检查限流"""
        now = datetime.now()
        
        # 重置分钟计数器
        if (now - self.rate_limit["last_minute_reset"]).seconds >= 60:
            self.rate_limit["current_minute_count"] = 0
            self.rate_limit["last_minute_reset"] = now
        
        # 重置小时计数器
        if (now - self.rate_limit["last_hour_reset"]).seconds >= 3600:
            self.rate_limit["current_hour_count"] = 0
            self.rate_limit["last_hour_reset"] = now
        
        # 检查限制
        if self.rate_limit["current_minute_count"] >= self.rate_limit["max_per_minute"]:
            return False
        if self.rate_limit["current_hour_count"] >= self.rate_limit["max_per_hour"]:
            return False
        
        # 增加计数
        self.rate_limit["current_minute_count"] += 1
        self.rate_limit["current_hour_count"] += 1
        
        return True
    
    def register_channel_handler(self, channel: str, handler):
        """注册渠道处理器"""
        if channel in self.channels:
            self.channels[channel]["handler"] = handler
            self.channels[channel]["enabled"] = True
            self.logger.info(f"已注册{channel}渠道处理器")
        else:
            self.logger.error(f"未知渠道: {channel}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_recent_notifications(self, count: int = 10) -> List[Dict]:
        """获取最近的通知"""
        recent = list(self.sent_history)[-count:]
        return [n.to_dict() for n in recent]
    
    def load_config(self, config_path: str):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 更新配置
                if "rate_limit" in config:
                    self.rate_limit.update(config["rate_limit"])
                if "quiet_hours" in config:
                    self.quiet_hours.update(config["quiet_hours"])
                if "deduplication" in config:
                    self.deduplication.update(config["deduplication"])
                self.logger.info(f"配置加载成功: {config_path}")
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
    
    def shutdown(self):
        """关闭通知系统"""
        self.running = False
        if self.process_thread.is_alive():
            self.process_thread.join(timeout=2)
        self.logger.info("通知系统已关闭")