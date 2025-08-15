"""
Webhook发送模块
支持Discord、Slack等Webhook推送
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class WebhookConfig:
    """Webhook配置"""
    name: str
    url: str
    webhook_type: str  # discord, slack, custom
    enabled: bool = True

class WebhookSender:
    """Webhook发送器"""
    
    def __init__(self):
        """初始化Webhook发送器"""
        self.logger = logging.getLogger(__name__)
        
        # Webhook配置
        self.webhooks = {}
        
        # 消息格式化器
        self.formatters = {
            "discord": self._format_discord,
            "slack": self._format_slack,
            "custom": self._format_custom
        }
        
        # 统计信息
        self.stats = {
            "sent": 0,
            "failed": 0,
            "by_type": {}
        }
    
    def add_webhook(self, name: str, url: str, webhook_type: str = "custom"):
        """
        添加Webhook
        
        Args:
            name: Webhook名称
            url: Webhook URL
            webhook_type: 类型（discord/slack/custom）
        """
        self.webhooks[name] = WebhookConfig(
            name=name,
            url=url,
            webhook_type=webhook_type,
            enabled=True
        )
        self.logger.info(f"添加Webhook: {name} ({webhook_type})")
    
    def send(self, message: str, notification: Any = None) -> bool:
        """
        发送到所有启用的Webhook
        
        Args:
            message: 消息内容
            notification: 通知对象
            
        Returns:
            是否至少有一个成功
        """
        success_count = 0
        
        for webhook_config in self.webhooks.values():
            if webhook_config.enabled:
                if self.send_to_webhook(webhook_config.name, message, notification):
                    success_count += 1
        
        return success_count > 0
    
    def send_to_webhook(self, webhook_name: str, message: str, 
                       notification: Any = None) -> bool:
        """
        发送到指定Webhook
        
        Args:
            webhook_name: Webhook名称
            message: 消息内容
            notification: 通知对象
            
        Returns:
            是否成功
        """
        if webhook_name not in self.webhooks:
            self.logger.error(f"Webhook不存在: {webhook_name}")
            return False
        
        webhook_config = self.webhooks[webhook_name]
        
        if not webhook_config.enabled:
            self.logger.debug(f"Webhook已禁用: {webhook_name}")
            return False
        
        # 格式化消息
        formatter = self.formatters.get(webhook_config.webhook_type, self._format_custom)
        payload = formatter(message, notification)
        
        # 发送请求
        try:
            response = requests.post(
                webhook_config.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.stats["sent"] += 1
                self.stats["by_type"][webhook_config.webhook_type] = \
                    self.stats["by_type"].get(webhook_config.webhook_type, 0) + 1
                self.logger.debug(f"Webhook发送成功: {webhook_name}")
                return True
            else:
                self.logger.error(f"Webhook发送失败: {webhook_name} - {response.status_code}")
                self.stats["failed"] += 1
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Webhook发送超时: {webhook_name}")
            self.stats["failed"] += 1
            return False
        except Exception as e:
            self.logger.error(f"Webhook发送异常: {webhook_name} - {e}")
            self.stats["failed"] += 1
            return False
    
    def _format_discord(self, message: str, notification: Any) -> Dict:
        """格式化Discord消息"""
        # Discord Webhook格式
        embed = {
            "title": "Tiger系统通知",
            "description": message,
            "color": self._get_color_by_level(notification),
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Tiger Trading System"
            }
        }
        
        # 添加字段
        if notification and hasattr(notification, 'level'):
            embed["fields"] = [
                {
                    "name": "级别",
                    "value": str(notification.level),
                    "inline": True
                },
                {
                    "name": "来源",
                    "value": getattr(notification, 'source', 'System'),
                    "inline": True
                }
            ]
        
        return {
            "embeds": [embed],
            "username": "Tiger System",
            "avatar_url": "https://example.com/tiger-avatar.png"  # 可配置
        }
    
    def _format_slack(self, message: str, notification: Any) -> Dict:
        """格式化Slack消息"""
        # Slack Webhook格式
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Tiger系统通知"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        # 添加上下文
        if notification:
            context_elements = []
            
            if hasattr(notification, 'level'):
                context_elements.append({
                    "type": "mrkdwn",
                    "text": f"*级别:* {notification.level}"
                })
            
            if hasattr(notification, 'timestamp'):
                context_elements.append({
                    "type": "mrkdwn",
                    "text": f"*时间:* {notification.timestamp}"
                })
            
            if context_elements:
                blocks.append({
                    "type": "context",
                    "elements": context_elements
                })
        
        return {
            "blocks": blocks,
            "username": "Tiger System",
            "icon_emoji": ":tiger:"
        }
    
    def _format_custom(self, message: str, notification: Any) -> Dict:
        """格式化自定义消息"""
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "source": "Tiger System"
        }
        
        # 添加通知信息
        if notification:
            if hasattr(notification, 'to_dict'):
                payload["notification"] = notification.to_dict()
            elif hasattr(notification, '__dict__'):
                payload["notification"] = notification.__dict__
        
        return payload
    
    def _get_color_by_level(self, notification: Any) -> int:
        """根据级别获取颜色（Discord）"""
        if not notification or not hasattr(notification, 'level'):
            return 0x808080  # 灰色
        
        level = str(notification.level).upper()
        colors = {
            "INFO": 0x3498db,      # 蓝色
            "IMPORTANT": 0xf39c12, # 橙色
            "URGENT": 0xe74c3c,    # 红色
            "CRITICAL": 0x9b59b6   # 紫色
        }
        
        return colors.get(level, 0x808080)
    
    def enable_webhook(self, webhook_name: str):
        """启用Webhook"""
        if webhook_name in self.webhooks:
            self.webhooks[webhook_name].enabled = True
            self.logger.info(f"Webhook已启用: {webhook_name}")
    
    def disable_webhook(self, webhook_name: str):
        """禁用Webhook"""
        if webhook_name in self.webhooks:
            self.webhooks[webhook_name].enabled = False
            self.logger.info(f"Webhook已禁用: {webhook_name}")
    
    def remove_webhook(self, webhook_name: str):
        """移除Webhook"""
        if webhook_name in self.webhooks:
            del self.webhooks[webhook_name]
            self.logger.info(f"Webhook已移除: {webhook_name}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def test_webhook(self, webhook_name: str) -> bool:
        """测试Webhook连接"""
        test_message = f"测试消息 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return self.send_to_webhook(webhook_name, test_message)