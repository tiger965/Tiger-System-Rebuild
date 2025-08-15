"""
三级预警通知系统
黄色、橙色、红色分级预警
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import threading
import time
import json

# 导入其他模块
from .telegram.telegram_bot import TelegramBot
from .email.email_sender import EmailSender
from .notification_system import NotificationSystem, NotificationLevel

class AlertLevel(Enum):
    """预警级别"""
    LEVEL_1_YELLOW = "🟡 黄色预警"     # 一级预警
    LEVEL_2_ORANGE = "🟠 橙色预警"     # 二级预警
    LEVEL_3_RED = "🔴 红色紧急"        # 三级紧急

class AlertNotifier:
    """分级预警通知系统"""
    
    def __init__(self, 
                 telegram_bot: Optional[TelegramBot] = None,
                 email_sender: Optional[EmailSender] = None,
                 notification_system: Optional[NotificationSystem] = None):
        """
        初始化预警通知器
        
        Args:
            telegram_bot: Telegram Bot实例
            email_sender: 邮件发送器实例
            notification_system: 通知系统实例
        """
        self.logger = logging.getLogger(__name__)
        
        # 通知渠道
        self.telegram_bot = telegram_bot or TelegramBot()
        self.email_sender = email_sender or EmailSender()
        self.notification_system = notification_system or NotificationSystem()
        
        # 短信和电话配置（需要实际服务提供商）
        self.sms_config = {
            "enabled": False,
            "provider": "twilio",  # 可以使用Twilio等服务
            "account_sid": "",
            "auth_token": "",
            "from_number": "",
            "to_numbers": []
        }
        
        self.phone_config = {
            "enabled": False,
            "provider": "twilio",
            "account_sid": "",
            "auth_token": "",
            "from_number": "",
            "emergency_numbers": []
        }
        
        # 预警统计
        self.stats = {
            "yellow_count": 0,
            "orange_count": 0,
            "red_count": 0,
            "opportunity_count": 0,
            "last_red_alert": None
        }
        
        # 预警历史
        self.alert_history = []
        
    def send_level_1_alert(self, warning_data: Dict[str, Any]) -> bool:
        """
        发送一级黄色预警
        
        Args:
            warning_data: 预警数据
                - trigger: 触发信号
                - details: 异常详情
                - timestamp: 时间戳
                - symbol: 相关币种（可选）
                
        Returns:
            是否发送成功
        """
        self.logger.info("发送一级黄色预警")
        
        # 构建消息
        message = self._format_level_1_message(warning_data)
        
        # 仅通过Telegram发送（一级预警不紧急）
        success = False
        
        # 1. Telegram通知
        if self.telegram_bot:
            telegram_msg = f"""
🟡 **一级预警（黄色）**
━━━━━━━━━━━━━━━
⚡ 触发信号：{warning_data.get('trigger', 'N/A')}
📝 异常详情：{warning_data.get('details', 'N/A')}
📊 相关币种：{warning_data.get('symbol', 'N/A')}
⏰ 时间：{datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━
💡 建议：提高警惕，暂不采取行动
"""
            success = self.telegram_bot.send(telegram_msg)
        
        # 2. 通知系统记录
        if self.notification_system:
            self.notification_system.send(
                level=NotificationLevel.INFO,
                title="🟡 黄色预警",
                content=message,
                source="AlertNotifier",
                metadata=warning_data
            )
        
        # 更新统计
        self.stats["yellow_count"] += 1
        
        # 记录历史
        self._record_alert(AlertLevel.LEVEL_1_YELLOW, warning_data)
        
        return success
        
    def send_level_2_alert(self, strategy_data: Dict[str, Any]) -> bool:
        """
        发送二级橙色预警
        
        Args:
            strategy_data: 策略数据
                - action: AI建议动作
                - reduce_pct: 减仓百分比
                - hedge_size: 对冲规模
                - reason: 原因说明
                - urgency: 紧急程度
                
        Returns:
            是否发送成功
        """
        self.logger.warning("发送二级橙色预警")
        
        # 构建消息
        message = self._format_level_2_message(strategy_data)
        
        success_count = 0
        
        # 1. Telegram紧急通知
        if self.telegram_bot:
            telegram_msg = f"""
🟠🟠🟠 **二级预警（橙色）** 🟠🟠🟠
━━━━━━━━━━━━━━━
⚠️ **多重信号确认！需要立即行动！**
━━━━━━━━━━━━━━━
🤖 AI建议：{strategy_data.get('action', 'N/A')}
📉 减仓建议：{strategy_data.get('reduce_pct', 0)}%
🛡️ 对冲规模：{strategy_data.get('hedge_size', 'N/A')}
❓ 原因：{strategy_data.get('reason', 'N/A')}
⚡ 紧急度：{strategy_data.get('urgency', 'HIGH')}
━━━━━━━━━━━━━━━
⚠️ **立即执行防御措施！**
"""
            if self.telegram_bot.send(telegram_msg):
                success_count += 1
        
        # 2. 邮件通知
        if self.email_sender:
            self.email_sender.send_alert_email(
                alert_type="二级预警",
                alert_level="ORANGE",
                title="橙色预警 - 需要立即行动",
                message=message,
                actions=[
                    f"减仓{strategy_data.get('reduce_pct', 0)}%",
                    f"建立对冲仓位",
                    "密切关注市场动向"
                ],
                to_emails=["alert@example.com"]
            )
            success_count += 1
        
        # 3. 通知系统记录
        if self.notification_system:
            self.notification_system.send(
                level=NotificationLevel.URGENT,
                title="🟠 橙色预警",
                content=message,
                source="AlertNotifier",
                metadata=strategy_data
            )
        
        # 更新统计
        self.stats["orange_count"] += 1
        
        # 记录历史
        self._record_alert(AlertLevel.LEVEL_2_ORANGE, strategy_data)
        
        return success_count > 0
        
    def send_level_3_emergency(self, emergency_data: Dict[str, Any]) -> bool:
        """
        发送三级红色紧急预警
        
        Args:
            emergency_data: 紧急数据
                - action_1: 紧急行动1
                - action_2: 紧急行动2
                - action_3: 紧急行动3
                - threat_level: 威胁等级
                - affected_positions: 受影响仓位
                - estimated_loss: 预估损失
                
        Returns:
            是否发送成功
        """
        self.logger.critical("发送三级红色紧急预警！！！")
        
        # 构建消息
        message = self._format_level_3_message(emergency_data)
        
        success_count = 0
        
        # 1. Telegram紧急通知（最高优先级）
        if self.telegram_bot:
            telegram_msg = f"""
🔴🔴🔴 **三级紧急预警** 🔴🔴🔴
⚠️⚠️⚠️ **黑天鹅事件可能发生！** ⚠️⚠️⚠️
━━━━━━━━━━━━━━━
🚨 威胁等级：{emergency_data.get('threat_level', 'EXTREME')}
💀 预估损失：{emergency_data.get('estimated_loss', 'N/A')}
📊 受影响仓位：{emergency_data.get('affected_positions', 'ALL')}
━━━━━━━━━━━━━━━
⚡ **立即执行以下行动：**
1️⃣ {emergency_data.get('action_1', '立即平仓50%以上')}
2️⃣ {emergency_data.get('action_2', '启动紧急对冲')}
3️⃣ {emergency_data.get('action_3', '暂停所有新开仓')}
━━━━━━━━━━━━━━━
🔴 **生存第一，不计成本！**
🔴 **这不是演习！立即行动！**
━━━━━━━━━━━━━━━
"""
            # 连续发送3次确保收到
            for i in range(3):
                if self.telegram_bot.send(telegram_msg):
                    success_count += 1
                time.sleep(1)
        
        # 2. 邮件紧急通知
        if self.email_sender:
            self.email_sender.send_alert_email(
                alert_type="三级紧急",
                alert_level="RED",
                title="🔴 红色紧急预警 - 立即行动！",
                message=message,
                actions=[
                    emergency_data.get('action_1', '立即平仓50%以上'),
                    emergency_data.get('action_2', '启动紧急对冲'),
                    emergency_data.get('action_3', '暂停所有新开仓')
                ],
                to_emails=["emergency@example.com"]
            )
            success_count += 1
        
        # 3. 短信通知
        if self.sms_config["enabled"]:
            self._send_sms(f"🔴紧急！黑天鹅预警！{message[:100]}")
            success_count += 1
        
        # 4. 电话呼叫（最紧急）
        if self.phone_config["enabled"]:
            self._make_phone_call(emergency_data)
            success_count += 1
        else:
            # 模拟电话呼叫
            self.logger.critical("📞 模拟电话呼叫：拨打紧急联系人...")
            print("\n" + "="*50)
            print("📞📞📞 紧急电话呼叫模拟 📞📞📞")
            print("="*50)
            print(f"呼叫号码：{self.phone_config.get('emergency_numbers', ['13800138000'])}")
            print(f"语音内容：紧急！Tiger系统检测到黑天鹅事件，请立即查看交易系统！")
            print("="*50 + "\n")
        
        # 5. 通知系统记录（最高级别）
        if self.notification_system:
            self.notification_system.send(
                level=NotificationLevel.CRITICAL,
                title="🔴 红色紧急预警",
                content=message,
                source="AlertNotifier",
                metadata=emergency_data,
                force=True  # 强制发送，跳过所有限制
            )
        
        # 更新统计
        self.stats["red_count"] += 1
        self.stats["last_red_alert"] = datetime.now()
        
        # 记录历史
        self._record_alert(AlertLevel.LEVEL_3_RED, emergency_data)
        
        # 启动持续监控
        self._start_emergency_monitoring(emergency_data)
        
        return success_count > 0
    
    def send_opportunity_alert(self, opp_data: Dict[str, Any]) -> bool:
        """
        发送机会提醒
        
        Args:
            opp_data: 机会数据
                - type: 类型（short/bottom_fishing）
                - level: 机会级别
                - size: 建议仓位
                - target: 目标收益
                - panic_index: 恐慌指数（抄底时）
                
        Returns:
            是否发送成功
        """
        self.logger.info(f"发送机会提醒：{opp_data.get('type')}")
        
        success = False
        
        if opp_data.get('type') == 'short':
            # 做空机会
            message = f"""
📉 **做空机会提醒**
━━━━━━━━━━━━━━━
📊 币种：{opp_data.get('symbol', 'N/A')}
⚡ 预警级别：{opp_data.get('level', 'MEDIUM')}
💼 建议仓位：{opp_data.get('size', 5)}%
📉 预期跌幅：{opp_data.get('target', 10)}%
⏰ 有效期：{opp_data.get('valid_time', '4小时')}
━━━━━━━━━━━━━━━
⚠️ 风险提示：做空需谨慎，严格止损
"""
        else:  # bottom_fishing
            # 抄底机会
            message = f"""
📈 **抄底机会提醒**
━━━━━━━━━━━━━━━
📊 币种：{opp_data.get('symbol', 'N/A')}
😱 恐慌指数：{opp_data.get('panic_index', 0)}/100
💼 建议仓位：{opp_data.get('size', 3)}%
📈 预期反弹：{opp_data.get('target', 15)}%
⏰ 建仓时机：{opp_data.get('timing', '分批建仓')}
━━━━━━━━━━━━━━━
💡 策略：分批进场，控制风险
"""
        
        # 通过Telegram发送
        if self.telegram_bot:
            success = self.telegram_bot.send(message)
        
        # 通知系统记录
        if self.notification_system:
            self.notification_system.send(
                level=NotificationLevel.IMPORTANT,
                title=f"💰 {opp_data.get('type', 'opportunity')}机会",
                content=message,
                source="AlertNotifier",
                metadata=opp_data
            )
        
        # 更新统计
        self.stats["opportunity_count"] += 1
        
        return success
    
    def _format_level_1_message(self, data: Dict) -> str:
        """格式化一级预警消息"""
        return (f"黄色预警 - 触发信号：{data.get('trigger')}，"
                f"详情：{data.get('details')}，"
                f"建议：提高警惕")
    
    def _format_level_2_message(self, data: Dict) -> str:
        """格式化二级预警消息"""
        return (f"橙色预警 - AI建议：{data.get('action')}，"
                f"减仓{data.get('reduce_pct')}%，"
                f"立即执行防御措施")
    
    def _format_level_3_message(self, data: Dict) -> str:
        """格式化三级预警消息"""
        return (f"红色紧急 - 黑天鹅事件！"
                f"威胁等级：{data.get('threat_level')}，"
                f"立即执行紧急措施")
    
    def _send_sms(self, message: str) -> bool:
        """
        发送短信（需要配置短信服务）
        
        Args:
            message: 短信内容
            
        Returns:
            是否成功
        """
        if not self.sms_config["enabled"]:
            self.logger.info(f"短信模拟发送：{message[:50]}...")
            return False
        
        # 这里需要集成实际的短信服务（如Twilio）
        # 示例代码：
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=message,
        #     from_=from_number,
        #     to=to_number
        # )
        
        return True
    
    def _make_phone_call(self, emergency_data: Dict) -> bool:
        """
        拨打紧急电话（需要配置电话服务）
        
        Args:
            emergency_data: 紧急数据
            
        Returns:
            是否成功
        """
        if not self.phone_config["enabled"]:
            self.logger.critical("电话呼叫服务未启用（需要配置Twilio等服务）")
            return False
        
        # 这里需要集成实际的电话服务（如Twilio）
        # 示例代码：
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # call = client.calls.create(
        #     twiml='<Response><Say>紧急！Tiger系统检测到黑天鹅事件</Say></Response>',
        #     from_=from_number,
        #     to=emergency_number
        # )
        
        return True
    
    def _record_alert(self, level: AlertLevel, data: Dict):
        """记录预警历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "data": data
        }
        self.alert_history.append(record)
        
        # 保持最近100条记录
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def _start_emergency_monitoring(self, emergency_data: Dict):
        """启动紧急监控（红色预警后持续监控）"""
        def monitor():
            self.logger.info("启动紧急监控模式...")
            for i in range(10):  # 监控10分钟
                time.sleep(60)  # 每分钟检查一次
                self.logger.info(f"紧急监控中... {i+1}/10分钟")
                # 这里可以添加实际的监控逻辑
        
        # 在后台线程运行监控
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def get_stats(self) -> Dict:
        """获取预警统计"""
        return self.stats.copy()
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """获取最近的预警记录"""
        return self.alert_history[-count:] if self.alert_history else []
    
    def test_all_levels(self):
        """测试所有预警级别"""
        print("\n" + "="*60)
        print("测试三级预警系统")
        print("="*60)
        
        # 测试黄色预警
        print("\n1. 测试黄色预警...")
        self.send_level_1_alert({
            "trigger": "RSI超买信号",
            "details": "BTC RSI达到75，进入超买区域",
            "symbol": "BTC"
        })
        time.sleep(2)
        
        # 测试橙色预警
        print("\n2. 测试橙色预警...")
        self.send_level_2_alert({
            "action": "立即减仓",
            "reduce_pct": 30,
            "hedge_size": "开空单$10000",
            "reason": "多重技术指标显示顶部",
            "urgency": "HIGH"
        })
        time.sleep(2)
        
        # 测试红色紧急
        print("\n3. 测试红色紧急预警...")
        self.send_level_3_emergency({
            "action_1": "立即平仓70%多单",
            "action_2": "开空单对冲$50000",
            "action_3": "停止所有自动交易",
            "threat_level": "EXTREME",
            "affected_positions": "BTC, ETH, SOL",
            "estimated_loss": "$100,000+"
        })
        time.sleep(2)
        
        # 测试机会提醒
        print("\n4. 测试做空机会...")
        self.send_opportunity_alert({
            "type": "short",
            "symbol": "DOGE",
            "level": "HIGH",
            "size": 5,
            "target": 15,
            "valid_time": "4小时"
        })
        time.sleep(1)
        
        print("\n5. 测试抄底机会...")
        self.send_opportunity_alert({
            "type": "bottom_fishing",
            "symbol": "ETH",
            "panic_index": 85,
            "size": 3,
            "target": 20,
            "timing": "分3批建仓"
        })
        
        # 显示统计
        print("\n" + "="*60)
        print("预警统计：")
        stats = self.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("="*60)