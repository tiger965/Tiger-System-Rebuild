"""
Telegram纯通知执行工具 - Window 8
只负责执行发送，不做任何判断
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiofiles
import aiohttp
from pathlib import Path


class TelegramNotifier:
    """Telegram消息发送工具 - 纯执行"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        初始化Telegram通知器
        
        Args:
            bot_token: Telegram Bot Token
            chat_id: 目标聊天ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
        
        # 执行统计
        self.stats = {
            "messages_sent": 0,
            "photos_sent": 0,
            "documents_sent": 0,
            "failed": 0,
            "total_time_ms": 0
        }
    
    async def send_message(self, 
                          message: str, 
                          chat_id: Optional[str] = None,
                          parse_mode: str = "HTML",
                          disable_notification: bool = False) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            message: 消息内容
            chat_id: 可选的目标聊天ID（覆盖默认）
            parse_mode: 消息格式 (HTML/Markdown)
            disable_notification: 是否静音发送
            
        Returns:
            发送结果
        """
        start_time = datetime.now()
        
        try:
            target_chat = chat_id or self.chat_id
            
            payload = {
                "chat_id": target_chat,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        self.stats["messages_sent"] += 1
                        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                        self.stats["total_time_ms"] += elapsed_ms
                        
                        return {
                            "status": "success",
                            "channel": "telegram",
                            "type": "message",
                            "sent_at": datetime.now().isoformat(),
                            "elapsed_ms": elapsed_ms,
                            "message_id": result["result"]["message_id"]
                        }
                    else:
                        self.stats["failed"] += 1
                        return {
                            "status": "failed",
                            "channel": "telegram",
                            "type": "message",
                            "error": result.get("description", "Unknown error"),
                            "sent_at": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"发送Telegram消息失败: {e}")
            return {
                "status": "failed",
                "channel": "telegram",
                "type": "message",
                "error": str(e),
                "sent_at": datetime.now().isoformat()
            }
    
    async def send_photo(self, 
                        photo_path: str, 
                        caption: Optional[str] = None,
                        chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送图片
        
        Args:
            photo_path: 图片文件路径
            caption: 图片说明
            chat_id: 可选的目标聊天ID
            
        Returns:
            发送结果
        """
        start_time = datetime.now()
        
        try:
            target_chat = chat_id or self.chat_id
            photo_file = Path(photo_path)
            
            if not photo_file.exists():
                return {
                    "status": "failed",
                    "channel": "telegram",
                    "type": "photo",
                    "error": f"文件不存在: {photo_path}",
                    "sent_at": datetime.now().isoformat()
                }
            
            async with aiofiles.open(photo_path, 'rb') as f:
                photo_data = await f.read()
            
            data = aiohttp.FormData()
            data.add_field('chat_id', target_chat)
            data.add_field('photo', photo_data, 
                          filename=photo_file.name,
                          content_type='image/jpeg')
            if caption:
                data.add_field('caption', caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendPhoto",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        self.stats["photos_sent"] += 1
                        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                        self.stats["total_time_ms"] += elapsed_ms
                        
                        return {
                            "status": "success",
                            "channel": "telegram",
                            "type": "photo",
                            "sent_at": datetime.now().isoformat(),
                            "elapsed_ms": elapsed_ms,
                            "message_id": result["result"]["message_id"]
                        }
                    else:
                        self.stats["failed"] += 1
                        return {
                            "status": "failed",
                            "channel": "telegram",
                            "type": "photo",
                            "error": result.get("description", "Unknown error"),
                            "sent_at": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"发送Telegram图片失败: {e}")
            return {
                "status": "failed",
                "channel": "telegram",
                "type": "photo",
                "error": str(e),
                "sent_at": datetime.now().isoformat()
            }
    
    async def send_document(self, 
                           file_path: str,
                           caption: Optional[str] = None,
                           chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送文档
        
        Args:
            file_path: 文档文件路径
            caption: 文档说明
            chat_id: 可选的目标聊天ID
            
        Returns:
            发送结果
        """
        start_time = datetime.now()
        
        try:
            target_chat = chat_id or self.chat_id
            doc_file = Path(file_path)
            
            if not doc_file.exists():
                return {
                    "status": "failed",
                    "channel": "telegram",
                    "type": "document",
                    "error": f"文件不存在: {file_path}",
                    "sent_at": datetime.now().isoformat()
                }
            
            async with aiofiles.open(file_path, 'rb') as f:
                doc_data = await f.read()
            
            data = aiohttp.FormData()
            data.add_field('chat_id', target_chat)
            data.add_field('document', doc_data, 
                          filename=doc_file.name)
            if caption:
                data.add_field('caption', caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/sendDocument",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        self.stats["documents_sent"] += 1
                        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                        self.stats["total_time_ms"] += elapsed_ms
                        
                        return {
                            "status": "success",
                            "channel": "telegram",
                            "type": "document",
                            "sent_at": datetime.now().isoformat(),
                            "elapsed_ms": elapsed_ms,
                            "message_id": result["result"]["message_id"]
                        }
                    else:
                        self.stats["failed"] += 1
                        return {
                            "status": "failed",
                            "channel": "telegram",
                            "type": "document",
                            "error": result.get("description", "Unknown error"),
                            "sent_at": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"发送Telegram文档失败: {e}")
            return {
                "status": "failed",
                "channel": "telegram",
                "type": "document",
                "error": str(e),
                "sent_at": datetime.now().isoformat()
            }
    
    async def send_batch(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量发送消息
        
        Args:
            messages: 消息列表，每个消息包含type和content
            
        Returns:
            发送结果列表
        """
        results = []
        
        for msg in messages:
            msg_type = msg.get("type", "message")
            
            if msg_type == "message":
                result = await self.send_message(
                    msg.get("content", ""),
                    msg.get("chat_id"),
                    msg.get("parse_mode", "HTML"),
                    msg.get("disable_notification", False)
                )
            elif msg_type == "photo":
                result = await self.send_photo(
                    msg.get("photo_path", ""),
                    msg.get("caption"),
                    msg.get("chat_id")
                )
            elif msg_type == "document":
                result = await self.send_document(
                    msg.get("file_path", ""),
                    msg.get("caption"),
                    msg.get("chat_id")
                )
            else:
                result = {
                    "status": "failed",
                    "error": f"未知消息类型: {msg_type}"
                }
            
            results.append(result)
            
            # 避免触发Telegram限流
            await asyncio.sleep(0.1)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取发送统计"""
        total_sent = (self.stats["messages_sent"] + 
                     self.stats["photos_sent"] + 
                     self.stats["documents_sent"])
        
        avg_time_ms = 0
        if total_sent > 0:
            avg_time_ms = self.stats["total_time_ms"] / total_sent
        
        return {
            "total_sent": total_sent,
            "messages": self.stats["messages_sent"],
            "photos": self.stats["photos_sent"],
            "documents": self.stats["documents_sent"],
            "failed": self.stats["failed"],
            "average_time_ms": avg_time_ms,
            "success_rate": total_sent / (total_sent + self.stats["failed"]) * 100 if total_sent + self.stats["failed"] > 0 else 0
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "messages_sent": 0,
            "photos_sent": 0,
            "documents_sent": 0,
            "failed": 0,
            "total_time_ms": 0
        }