"""
Telegram Bot集成模块
负责所有Telegram消息推送
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
from collections import deque
import threading
import time

@dataclass
class TelegramMessage:
    """Telegram消息数据类"""
    chat_id: str
    text: str
    parse_mode: str = "Markdown"
    disable_notification: bool = False
    reply_markup: Optional[Dict] = None

class TelegramBot:
    """Telegram Bot处理器"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        初始化Telegram Bot
        
        Args:
            bot_token: Bot令牌
            chat_id: 默认聊天ID
        """
        self.logger = logging.getLogger(__name__)
        
        # Bot配置
        self.config = {
            "bot_token": bot_token or "",
            "chat_id": chat_id or "",
            "parse_mode": "Markdown",
            "api_base": "https://api.telegram.org"
        }
        
        # 消息模板
        self.message_templates = {
            "signal": """
🎯 *交易信号*
━━━━━━━━━━━━━━━
📊 币种：`{symbol}`
📈 方向：*{direction}*
💰 入场：`{entry}`
🛑 止损：`{stop}`
🎯 目标：`{targets}`
📦 仓位：`{size}`
⭐ 置信度：*{confidence}/10*
⏰ 时间：`{timestamp}`
━━━━━━━━━━━━━━━""",
            
            "opportunity": """
💎 *机会发现*
━━━━━━━━━━━━━━━
🔍 类型：`{opportunity_type}`
📊 币种：`{symbol}`
⚡ 触发：{trigger}
💼 建议仓位：`{size}` _(最大5%)_
🛡️ 止损：`{stop}` _(最大2%)_
🎯 目标：`{targets}`
⏳ 时限：`{time_limit}`
⚠️ 风险：*{risk_level}*
━━━━━━━━━━━━━━━
_⚠️ 独立仓位，严格管理_""",
            
            "alert": """
⚠️ *风险预警*
━━━━━━━━━━━━━━━
🚨 类型：*{alert_type}*
📊 币种：`{symbol}`
💵 当前价：`{price}`
📉 风险等级：*{risk_level}*
⚡ 建议操作：
{action}
⏰ 时间：`{timestamp}`
━━━━━━━━━━━━━━━""",
            
            "report": """
📊 *{report_type}报告*
━━━━━━━━━━━━━━━
📅 周期：`{period}`
💰 盈亏：*{pnl}*
📈 胜率：`{win_rate}`
📉 最大回撤：`{drawdown}`
🔄 交易次数：`{trades}`
⭐ 最佳交易：`{best_trade}`
━━━━━━━━━━━━━━━
[查看详情]({link})""",
            
            "system": """
🤖 *系统通知*
━━━━━━━━━━━━━━━
📢 {title}
━━━━━━━━━━━━━━━
{content}
━━━━━━━━━━━━━━━
⏰ `{timestamp}`""",

            "blackswan": """
🦢⚠️ *黑天鹅预警*
━━━━━━━━━━━━━━━
🚨 严重程度：*{severity}*
📊 影响币种：`{symbols}`
📉 预期影响：*{impact}*
⚡ 触发因素：
{triggers}
🛡️ 建议措施：
{actions}
⏰ 检测时间：`{timestamp}`
━━━━━━━━━━━━━━━
_⚠️ 立即执行风控措施_"""
        }
        
        # 发送控制
        self.rate_limit = {
            "max_per_minute": 10,
            "max_per_hour": 100,
            "current_minute_count": 0,
            "current_hour_count": 0,
            "last_minute_reset": datetime.now(),
            "last_hour_reset": datetime.now(),
            "cooldown_seconds": 30
        }
        
        # 消息队列
        self.message_queue = deque(maxlen=100)
        self.failed_queue = deque(maxlen=50)
        
        # 统计信息
        self.stats = {
            "sent": 0,
            "failed": 0,
            "queued": 0,
            "rate_limited": 0,
            "by_type": {}
        }
        
        # 异步事件循环
        self.loop = None
        self.session = None
        self.running = False
        
        # 初始化
        if bot_token:
            self.initialize()
    
    def initialize(self):
        """初始化Bot"""
        if not self.config["bot_token"]:
            self.logger.warning("Bot token未配置")
            return False
        
        # 启动异步处理线程
        self.running = True
        self.process_thread = threading.Thread(target=self._run_async_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        self.logger.info("Telegram Bot初始化成功")
        return True
    
    def _run_async_loop(self):
        """运行异步事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_processor())
    
    async def _async_processor(self):
        """异步消息处理器"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            while self.running:
                try:
                    if self.message_queue:
                        message = self.message_queue.popleft()
                        await self._send_message_async(message)
                    else:
                        await asyncio.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"异步处理错误: {e}")
    
    def send(self, message: str, notification: Any = None) -> bool:
        """
        发送消息（同步接口）
        
        Args:
            message: 消息内容
            notification: 通知对象（可选）
            
        Returns:
            是否成功加入队列
        """
        # 检查配置
        if not self.config["bot_token"] or not self.config["chat_id"]:
            self.logger.error("Telegram未配置")
            return False
        
        # 检查限流
        if not self._check_rate_limit():
            self.stats["rate_limited"] += 1
            self.logger.warning("Telegram消息被限流")
            return False
        
        # 创建消息对象
        telegram_message = TelegramMessage(
            chat_id=self.config["chat_id"],
            text=message,
            parse_mode=self.config["parse_mode"]
        )
        
        # 加入队列
        self.message_queue.append(telegram_message)
        self.stats["queued"] += 1
        
        return True
    
    def send_formatted(self, 
                      message_type: str,
                      data: Dict[str, Any],
                      chat_id: Optional[str] = None) -> bool:
        """
        发送格式化消息
        
        Args:
            message_type: 消息类型
            data: 模板数据
            chat_id: 聊天ID（可选）
            
        Returns:
            是否成功
        """
        # 获取模板
        template = self.message_templates.get(message_type)
        if not template:
            self.logger.error(f"未知消息类型: {message_type}")
            return False
        
        # 添加时间戳
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 格式化消息
        try:
            message = template.format(**data)
        except KeyError as e:
            self.logger.error(f"模板数据缺失: {e}")
            return False
        
        # 创建消息对象
        telegram_message = TelegramMessage(
            chat_id=chat_id or self.config["chat_id"],
            text=message,
            parse_mode=self.config["parse_mode"]
        )
        
        # 加入队列
        self.message_queue.append(telegram_message)
        self.stats["queued"] += 1
        
        # 更新统计
        self.stats["by_type"][message_type] = self.stats["by_type"].get(message_type, 0) + 1
        
        return True
    
    async def _send_message_async(self, message: TelegramMessage) -> bool:
        """
        异步发送消息
        
        Args:
            message: Telegram消息对象
            
        Returns:
            是否成功
        """
        url = f"{self.config['api_base']}/bot{self.config['bot_token']}/sendMessage"
        
        payload = {
            "chat_id": message.chat_id,
            "text": message.text,
            "parse_mode": message.parse_mode,
            "disable_notification": message.disable_notification
        }
        
        if message.reply_markup:
            payload["reply_markup"] = json.dumps(message.reply_markup)
        
        try:
            async with self.session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    self.stats["sent"] += 1
                    self.logger.debug(f"Telegram消息发送成功")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Telegram API错误: {response.status} - {error_text}")
                    self.failed_queue.append(message)
                    self.stats["failed"] += 1
                    return False
        except asyncio.TimeoutError:
            self.logger.error("Telegram发送超时")
            self.failed_queue.append(message)
            self.stats["failed"] += 1
            return False
        except Exception as e:
            self.logger.error(f"Telegram发送失败: {e}")
            self.failed_queue.append(message)
            self.stats["failed"] += 1
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
    
    def send_signal(self, symbol: str, direction: str, entry: float, 
                   stop: float, targets: List[float], size: float, 
                   confidence: int) -> bool:
        """发送交易信号"""
        data = {
            "symbol": symbol,
            "direction": "🔴 做空" if direction.lower() == "short" else "🟢 做多",
            "entry": f"${entry:,.2f}",
            "stop": f"${stop:,.2f}",
            "targets": " / ".join([f"${t:,.2f}" for t in targets]),
            "size": f"{size}%",
            "confidence": confidence
        }
        return self.send_formatted("signal", data)
    
    def send_alert(self, alert_type: str, symbol: str, price: float,
                  risk_level: str, action: str) -> bool:
        """发送风险预警"""
        data = {
            "alert_type": alert_type,
            "symbol": symbol,
            "price": f"${price:,.2f}",
            "risk_level": risk_level,
            "action": action
        }
        return self.send_formatted("alert", data)
    
    def send_report(self, report_type: str, period: str, pnl: float,
                   win_rate: float, drawdown: float, trades: int,
                   best_trade: str, link: str = "#") -> bool:
        """发送报告"""
        data = {
            "report_type": report_type,
            "period": period,
            "pnl": f"${pnl:+,.2f}" if pnl != 0 else "$0",
            "win_rate": f"{win_rate:.1f}%",
            "drawdown": f"{drawdown:.1f}%",
            "trades": trades,
            "best_trade": best_trade,
            "link": link
        }
        return self.send_formatted("report", data)
    
    def send_blackswan_alert(self, severity: str, symbols: List[str],
                           impact: str, triggers: List[str], 
                           actions: List[str]) -> bool:
        """发送黑天鹅预警"""
        data = {
            "severity": severity,
            "symbols": ", ".join(symbols),
            "impact": impact,
            "triggers": "\n".join([f"• {t}" for t in triggers]),
            "actions": "\n".join([f"• {a}" for a in actions]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.send_formatted("blackswan", data)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def retry_failed(self) -> int:
        """重试失败的消息"""
        retry_count = 0
        while self.failed_queue:
            message = self.failed_queue.popleft()
            self.message_queue.append(message)
            retry_count += 1
        
        if retry_count > 0:
            self.logger.info(f"重新加入{retry_count}条失败消息到队列")
        
        return retry_count
    
    def shutdown(self):
        """关闭Bot"""
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            self.process_thread.join(timeout=2)
        self.logger.info("Telegram Bot已关闭")