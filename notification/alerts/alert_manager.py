"""
告警管理系统
管理各类告警的生成、过滤和分发
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import threading
import time

class AlertType(Enum):
    """告警类型"""
    PRICE_ALERT = "price_alert"          # 价格告警
    PATTERN_ALERT = "pattern_alert"      # 形态告警
    RISK_ALERT = "risk_alert"            # 风险告警
    NEWS_ALERT = "news_alert"            # 新闻告警
    TRADER_ALERT = "trader_alert"        # 交易员动态
    SYSTEM_ALERT = "system_alert"        # 系统告警
    BLACKSWAN_ALERT = "blackswan_alert"  # 黑天鹅告警

class AlertLevel(Enum):
    """告警级别"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class Alert:
    """告警数据类"""
    alert_id: str
    alert_type: AlertType
    alert_level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    is_active: bool = True
    acknowledged: bool = False
    action_required: bool = False
    
    def to_dict(self):
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['alert_level'] = self.alert_level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class AlertManager:
    """告警管理器"""
    
    def __init__(self, notification_system=None):
        """
        初始化告警管理器
        
        Args:
            notification_system: 通知系统实例
        """
        self.logger = logging.getLogger(__name__)
        self.notification_system = notification_system
        
        # 告警存储
        self.active_alerts = {}  # alert_id -> Alert
        self.alert_history = deque(maxlen=1000)
        
        # 告警规则
        self.alert_rules = {
            AlertType.PRICE_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 300,  # 5分钟冷却
                "max_per_hour": 20
            },
            AlertType.PATTERN_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 600,  # 10分钟冷却
                "max_per_hour": 10
            },
            AlertType.RISK_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 60,   # 1分钟冷却
                "max_per_hour": 50
            },
            AlertType.NEWS_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 1800, # 30分钟冷却
                "max_per_hour": 5
            },
            AlertType.TRADER_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 900,  # 15分钟冷却
                "max_per_hour": 10
            },
            AlertType.SYSTEM_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 30,   # 30秒冷却
                "max_per_hour": 100
            },
            AlertType.BLACKSWAN_ALERT: {
                "enabled": True,
                "conditions": [],
                "cooldown": 0,    # 无冷却
                "max_per_hour": 999
            }
        }
        
        # 告警条件
        self.price_conditions = []  # 价格条件列表
        self.pattern_conditions = [] # 形态条件列表
        
        # 去重和限流
        self.deduplication = {
            "enabled": True,
            "window_seconds": 300,  # 5分钟窗口
            "recent_hashes": deque(maxlen=200)
        }
        
        self.throttling = defaultdict(lambda: {
            "count": 0,
            "last_reset": datetime.now(),
            "last_alert": datetime.now()
        })
        
        # 免打扰模式
        self.quiet_hours = {
            "enabled": False,
            "start_hour": 23,
            "end_hour": 7,
            "exceptions": [AlertLevel.CRITICAL, AlertLevel.HIGH]
        }
        
        # 告警分组
        self.alert_groups = defaultdict(list)  # group_key -> [alert_ids]
        
        # 统计信息
        self.stats = {
            "total_generated": 0,
            "total_sent": 0,
            "total_suppressed": 0,
            "by_type": {t.value: 0 for t in AlertType},
            "by_level": {l.value: 0 for l in AlertLevel}
        }
        
        # 黑天鹅检测
        self.blackswan_detector = BlackSwanDetector()
        
        # 启动处理线程
        self.running = True
        self.process_thread = threading.Thread(target=self._process_alerts)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def create_alert(self,
                    alert_type: AlertType,
                    alert_level: AlertLevel,
                    title: str,
                    message: str,
                    source: str = "System",
                    data: Dict[str, Any] = None,
                    action_required: bool = False) -> Optional[str]:
        """
        创建告警
        
        Args:
            alert_type: 告警类型
            alert_level: 告警级别
            title: 标题
            message: 消息内容
            source: 来源
            data: 附加数据
            action_required: 是否需要行动
            
        Returns:
            告警ID或None
        """
        # 检查是否启用
        if not self.alert_rules[alert_type]["enabled"]:
            self.logger.debug(f"告警类型{alert_type.value}已禁用")
            return None
        
        # 检查免打扰
        if self._is_quiet_hours(alert_level):
            self.logger.debug(f"告警在免打扰时间被屏蔽: {title}")
            self.stats["total_suppressed"] += 1
            return None
        
        # 检查去重
        if self._is_duplicate(alert_type, title, message):
            self.logger.debug(f"重复告警被过滤: {title}")
            self.stats["total_suppressed"] += 1
            return None
        
        # 检查限流
        if not self._check_throttling(alert_type):
            self.logger.warning(f"告警被限流: {title}")
            self.stats["total_suppressed"] += 1
            return None
        
        # 生成告警ID
        alert_id = self._generate_alert_id(alert_type, title)
        
        # 创建告警对象
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            alert_level=alert_level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            data=data or {},
            action_required=action_required
        )
        
        # 存储告警
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # 更新统计
        self.stats["total_generated"] += 1
        self.stats["by_type"][alert_type.value] += 1
        self.stats["by_level"][alert_level.value] += 1
        
        # 分组
        self._group_alert(alert)
        
        # 发送通知
        self._send_alert_notification(alert)
        
        self.logger.info(f"告警创建: [{alert_level.value}] {title}")
        
        return alert_id
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        确认告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否成功
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.logger.info(f"告警已确认: {alert_id}")
            return True
        return False
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """
        关闭告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否成功
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].is_active = False
            self.logger.info(f"告警已关闭: {alert_id}")
            return True
        return False
    
    def add_price_condition(self, symbol: str, price_type: str, 
                           threshold: float, direction: str = "above"):
        """
        添加价格条件
        
        Args:
            symbol: 币种
            price_type: 价格类型（current, high, low）
            threshold: 阈值
            direction: 方向（above, below）
        """
        condition = {
            "symbol": symbol,
            "price_type": price_type,
            "threshold": threshold,
            "direction": direction,
            "created_at": datetime.now()
        }
        self.price_conditions.append(condition)
        self.logger.info(f"添加价格条件: {symbol} {price_type} {direction} {threshold}")
    
    def check_price_conditions(self, market_data: Dict[str, float]):
        """
        检查价格条件
        
        Args:
            market_data: 市场数据
        """
        for condition in self.price_conditions:
            symbol = condition["symbol"]
            if symbol not in market_data:
                continue
            
            current_price = market_data[symbol]
            threshold = condition["threshold"]
            direction = condition["direction"]
            
            triggered = False
            if direction == "above" and current_price > threshold:
                triggered = True
            elif direction == "below" and current_price < threshold:
                triggered = True
            
            if triggered:
                self.create_alert(
                    alert_type=AlertType.PRICE_ALERT,
                    alert_level=AlertLevel.MEDIUM,
                    title=f"{symbol}价格触发",
                    message=f"{symbol}价格{current_price}已{direction}{threshold}",
                    data={"symbol": symbol, "price": current_price, "threshold": threshold}
                )
    
    def detect_blackswan(self, market_data: Dict, news_data: List, social_data: Dict):
        """
        检测黑天鹅事件
        
        Args:
            market_data: 市场数据
            news_data: 新闻数据
            social_data: 社交数据
        """
        # 使用黑天鹅检测器
        blackswan_event = self.blackswan_detector.detect(market_data, news_data, social_data)
        
        if blackswan_event:
            self.create_alert(
                alert_type=AlertType.BLACKSWAN_ALERT,
                alert_level=AlertLevel.CRITICAL,
                title="🦢 黑天鹅事件检测",
                message=blackswan_event["description"],
                data=blackswan_event,
                action_required=True
            )
    
    def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        if not self.notification_system:
            return
        
        # 根据告警级别映射到通知级别
        notification_level_map = {
            AlertLevel.LOW: "INFO",
            AlertLevel.MEDIUM: "IMPORTANT",
            AlertLevel.HIGH: "URGENT",
            AlertLevel.CRITICAL: "CRITICAL"
        }
        
        # 发送通知
        from ..notification_system import NotificationLevel
        
        level = NotificationLevel[notification_level_map[alert.alert_level]]
        
        self.notification_system.send(
            level=level,
            title=alert.title,
            content=alert.message,
            source=f"AlertManager/{alert.source}",
            metadata=alert.data
        )
        
        self.stats["total_sent"] += 1
    
    def _is_quiet_hours(self, alert_level: AlertLevel) -> bool:
        """检查是否在免打扰时间"""
        if not self.quiet_hours["enabled"]:
            return False
        
        if alert_level in self.quiet_hours["exceptions"]:
            return False
        
        current_hour = datetime.now().hour
        start = self.quiet_hours["start_hour"]
        end = self.quiet_hours["end_hour"]
        
        if start > end:
            return current_hour >= start or current_hour < end
        else:
            return start <= current_hour < end
    
    def _is_duplicate(self, alert_type: AlertType, title: str, message: str) -> bool:
        """检查是否重复"""
        if not self.deduplication["enabled"]:
            return False
        
        # 生成哈希
        alert_hash = hash(f"{alert_type.value}:{title}:{message}")
        
        if alert_hash in self.deduplication["recent_hashes"]:
            return True
        
        self.deduplication["recent_hashes"].append(alert_hash)
        return False
    
    def _check_throttling(self, alert_type: AlertType) -> bool:
        """检查限流"""
        rule = self.alert_rules[alert_type]
        throttle_info = self.throttling[alert_type]
        
        now = datetime.now()
        
        # 重置小时计数
        if (now - throttle_info["last_reset"]).seconds >= 3600:
            throttle_info["count"] = 0
            throttle_info["last_reset"] = now
        
        # 检查冷却时间
        if (now - throttle_info["last_alert"]).seconds < rule["cooldown"]:
            return False
        
        # 检查小时限制
        if throttle_info["count"] >= rule["max_per_hour"]:
            return False
        
        # 更新计数
        throttle_info["count"] += 1
        throttle_info["last_alert"] = now
        
        return True
    
    def _generate_alert_id(self, alert_type: AlertType, title: str) -> str:
        """生成告警ID"""
        import hashlib
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        content = f"{alert_type.value}:{title}:{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _group_alert(self, alert: Alert):
        """告警分组"""
        # 按类型和级别分组
        group_key = f"{alert.alert_type.value}:{alert.alert_level.value}"
        self.alert_groups[group_key].append(alert.alert_id)
        
        # 限制每组大小
        if len(self.alert_groups[group_key]) > 100:
            self.alert_groups[group_key] = self.alert_groups[group_key][-100:]
    
    def _process_alerts(self):
        """处理告警（后台线程）"""
        while self.running:
            try:
                # 清理过期告警
                self._cleanup_old_alerts()
                
                # 检查告警条件
                # 这里可以添加定期检查逻辑
                
                time.sleep(10)  # 每10秒处理一次
            except Exception as e:
                self.logger.error(f"处理告警时出错: {e}")
    
    def _cleanup_old_alerts(self):
        """清理过期告警"""
        now = datetime.now()
        to_remove = []
        
        for alert_id, alert in self.active_alerts.items():
            # 超过24小时的告警自动关闭
            if (now - alert.timestamp).days >= 1:
                to_remove.append(alert_id)
        
        for alert_id in to_remove:
            del self.active_alerts[alert_id]
        
        if to_remove:
            self.logger.info(f"清理了{len(to_remove)}个过期告警")
    
    def get_active_alerts(self, alert_type: Optional[AlertType] = None,
                         alert_level: Optional[AlertLevel] = None) -> List[Alert]:
        """获取活跃告警"""
        alerts = []
        
        for alert in self.active_alerts.values():
            if alert.is_active:
                if alert_type and alert.alert_type != alert_type:
                    continue
                if alert_level and alert.alert_level != alert_level:
                    continue
                alerts.append(alert)
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def shutdown(self):
        """关闭告警管理器"""
        self.running = False
        if self.process_thread.is_alive():
            self.process_thread.join(timeout=2)
        self.logger.info("告警管理器已关闭")


class BlackSwanDetector:
    """黑天鹅事件检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 检测阈值
        self.thresholds = {
            "price_drop": -10,      # 价格跌幅超过10%
            "volume_spike": 5,       # 成交量激增5倍
            "volatility_spike": 3,   # 波动率激增3倍
            "news_sentiment": -0.8,  # 新闻情绪极度负面
            "social_panic": 0.9      # 社交恐慌指数
        }
    
    def detect(self, market_data: Dict, news_data: List, social_data: Dict) -> Optional[Dict]:
        """
        检测黑天鹅事件
        
        Returns:
            黑天鹅事件信息或None
        """
        triggers = []
        affected_symbols = []
        severity = "LOW"
        
        # 检查价格暴跌
        for symbol, data in market_data.items():
            if "change_24h" in data and data["change_24h"] < self.thresholds["price_drop"]:
                triggers.append(f"{symbol}暴跌{data['change_24h']:.1f}%")
                affected_symbols.append(symbol)
                severity = "HIGH"
        
        # 检查成交量异常
        # ... 省略具体实现
        
        # 检查新闻情绪
        # ... 省略具体实现
        
        # 如果有触发条件
        if triggers:
            return {
                "severity": severity,
                "triggers": triggers,
                "affected_symbols": affected_symbols,
                "description": f"检测到潜在黑天鹅事件: {', '.join(triggers)}",
                "recommended_actions": [
                    "立即检查所有持仓",
                    "考虑降低仓位",
                    "启动紧急风控措施"
                ],
                "timestamp": datetime.now().isoformat()
            }
        
        return None