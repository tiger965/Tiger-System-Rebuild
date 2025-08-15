"""
预警管理器
配合高频监控，实时触发预警
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """预警级别"""
    CRITICAL = 0  # 紧急
    HIGH = 1      # 高
    MEDIUM = 2    # 中
    LOW = 3       # 低
    INFO = 4      # 信息

@dataclass
class Alert:
    """预警数据"""
    id: str
    type: str
    level: AlertLevel
    symbol: str
    message: str
    data: Dict
    timestamp: datetime
    triggered_at: datetime = None
    resolved_at: datetime = None
    
class AlertManager:
    """预警管理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.active_alerts = {}  # 活跃预警
        self.alert_history = []  # 历史预警
        self.alert_callbacks = []  # 预警回调
        self.alert_counters = {}  # 预警计数器
        self.rate_limiter = {}  # 速率限制
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "enabled": True,
            "max_alerts_per_minute": 10,
            "alert_ttl": 3600,  # 预警保留1小时
            "dedup_window": 60,  # 去重窗口60秒
            "escalation_enabled": True,
            "notification_channels": ["log", "redis"]
        }
    
    def register_callback(self, callback: Callable):
        """注册预警回调"""
        self.alert_callbacks.append(callback)
        logger.info(f"注册预警回调: {callback.__name__}")
    
    async def check_price_alert(self, symbol: str, price: float, 
                               config: Dict = None) -> Optional[Alert]:
        """检查价格预警"""
        config = config or {}
        alerts = []
        
        # 检查绝对价格阈值
        if "high" in config and price >= config["high"]:
            alert = await self._create_alert(
                type="price_high",
                level=AlertLevel.HIGH,
                symbol=symbol,
                message=f"{symbol}价格突破上限: ${price:.2f} >= ${config['high']}",
                data={"price": price, "threshold": config["high"]}
            )
            alerts.append(alert)
        
        if "low" in config and price <= config["low"]:
            alert = await self._create_alert(
                type="price_low",
                level=AlertLevel.HIGH,
                symbol=symbol,
                message=f"{symbol}价格跌破下限: ${price:.2f} <= ${config['low']}",
                data={"price": price, "threshold": config["low"]}
            )
            alerts.append(alert)
        
        return alerts[0] if alerts else None
    
    async def check_price_change_alert(self, symbol: str, current_price: float,
                                      previous_price: float, window: int = 60) -> Optional[Alert]:
        """检查价格变化预警"""
        if previous_price <= 0:
            return None
        
        change = (current_price - previous_price) / previous_price
        change_percent = change * 100
        
        # 根据变化幅度确定预警级别
        level = AlertLevel.INFO
        if abs(change_percent) >= 5:
            level = AlertLevel.CRITICAL
        elif abs(change_percent) >= 3:
            level = AlertLevel.HIGH
        elif abs(change_percent) >= 2:
            level = AlertLevel.MEDIUM
        elif abs(change_percent) >= 1:
            level = AlertLevel.LOW
        else:
            return None
        
        direction = "暴涨" if change > 0 else "暴跌"
        
        return await self._create_alert(
            type=f"price_{direction.lower()}",
            level=level,
            symbol=symbol,
            message=f"{symbol}{direction}{abs(change_percent):.2f}% (${previous_price:.2f} -> ${current_price:.2f})",
            data={
                "current_price": current_price,
                "previous_price": previous_price,
                "change_percent": change_percent,
                "window_seconds": window
            }
        )
    
    async def check_volume_alert(self, symbol: str, current_volume: float,
                                avg_volume: float, multiplier: float = 3.0) -> Optional[Alert]:
        """检查成交量预警"""
        if avg_volume <= 0:
            return None
        
        ratio = current_volume / avg_volume
        
        if ratio >= multiplier:
            level = AlertLevel.HIGH if ratio >= 5 else AlertLevel.MEDIUM
            
            return await self._create_alert(
                type="volume_spike",
                level=level,
                symbol=symbol,
                message=f"{symbol}成交量激增{ratio:.1f}倍",
                data={
                    "current_volume": current_volume,
                    "average_volume": avg_volume,
                    "ratio": ratio,
                    "threshold": multiplier
                }
            )
        
        return None
    
    async def check_whale_alert(self, symbol: str, trade: Dict,
                               threshold: float = 500000) -> Optional[Alert]:
        """检查巨鲸交易预警"""
        value = trade.get("price", 0) * trade.get("size", 0)
        
        if value >= threshold:
            level = AlertLevel.CRITICAL if value >= 5000000 else \
                   AlertLevel.HIGH if value >= 1000000 else AlertLevel.MEDIUM
            
            side = "买入" if trade.get("side") == "buy" else "卖出"
            
            return await self._create_alert(
                type="whale_trade",
                level=level,
                symbol=symbol,
                message=f"巨鲸{side}: {symbol} ${value:,.0f}",
                data={
                    "trade": trade,
                    "value": value,
                    "threshold": threshold
                }
            )
        
        return None
    
    async def check_funding_rate_alert(self, symbol: str, funding_rate: float,
                                      threshold: float = 0.0005) -> Optional[Alert]:
        """检查资金费率预警"""
        if abs(funding_rate) >= threshold:
            level = AlertLevel.HIGH if abs(funding_rate) >= 0.001 else AlertLevel.MEDIUM
            
            direction = "正向" if funding_rate > 0 else "负向"
            
            return await self._create_alert(
                type="funding_rate",
                level=level,
                symbol=symbol,
                message=f"{symbol}资金费率异常{direction}: {funding_rate:.4%}",
                data={
                    "funding_rate": funding_rate,
                    "threshold": threshold,
                    "direction": direction
                }
            )
        
        return None
    
    async def check_liquidation_alert(self, symbol: str, liquidations: List[Dict],
                                     threshold: float = 1000000) -> Optional[Alert]:
        """检查爆仓预警"""
        total_value = sum(liq.get("value", 0) for liq in liquidations)
        
        if total_value >= threshold:
            level = AlertLevel.CRITICAL if total_value >= 10000000 else \
                   AlertLevel.HIGH if total_value >= 5000000 else AlertLevel.MEDIUM
            
            return await self._create_alert(
                type="liquidation_cascade",
                level=level,
                symbol=symbol,
                message=f"{symbol}连环爆仓: ${total_value:,.0f}",
                data={
                    "liquidations": liquidations,
                    "total_value": total_value,
                    "count": len(liquidations),
                    "threshold": threshold
                }
            )
        
        return None
    
    async def check_arbitrage_alert(self, symbol: str, okx_price: float,
                                   binance_price: float, threshold: float = 0.003) -> Optional[Alert]:
        """检查套利机会预警"""
        price_diff = abs(okx_price - binance_price)
        price_diff_percent = price_diff / min(okx_price, binance_price)
        
        if price_diff_percent >= threshold:
            direction = "OKX→Binance" if okx_price < binance_price else "Binance→OKX"
            profit = price_diff_percent * 100
            
            return await self._create_alert(
                type="arbitrage_opportunity",
                level=AlertLevel.HIGH,
                symbol=symbol,
                message=f"套利机会 {symbol}: {direction} 利润{profit:.2f}%",
                data={
                    "okx_price": okx_price,
                    "binance_price": binance_price,
                    "difference": price_diff,
                    "difference_percent": price_diff_percent,
                    "direction": direction,
                    "potential_profit": profit
                }
            )
        
        return None
    
    async def _create_alert(self, type: str, level: AlertLevel, symbol: str,
                           message: str, data: Dict) -> Alert:
        """创建预警"""
        # 生成预警ID
        alert_id = f"{type}_{symbol}_{datetime.now(timezone.utc).timestamp()}"
        
        # 检查去重
        if self._is_duplicate(type, symbol):
            logger.debug(f"预警去重: {type} {symbol}")
            return None
        
        # 检查速率限制
        if not self._check_rate_limit():
            logger.warning("预警速率限制")
            return None
        
        # 创建预警对象
        alert = Alert(
            id=alert_id,
            type=type,
            level=level,
            symbol=symbol,
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc),
            triggered_at=datetime.now(timezone.utc)
        )
        
        # 存储预警
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # 更新计数器
        self._update_counters(type, symbol)
        
        # 触发回调
        await self._trigger_callbacks(alert)
        
        # 记录日志
        self._log_alert(alert)
        
        return alert
    
    def _is_duplicate(self, type: str, symbol: str) -> bool:
        """检查是否重复预警"""
        key = f"{type}_{symbol}"
        now = datetime.now(timezone.utc)
        
        # 检查去重窗口内是否有相同预警
        for alert in self.alert_history[-100:]:  # 只检查最近100条
            if alert.type == type and alert.symbol == symbol:
                time_diff = (now - alert.triggered_at).total_seconds()
                if time_diff < self.config["dedup_window"]:
                    return True
        
        return False
    
    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        now = datetime.now(timezone.utc)
        minute_key = now.strftime("%Y%m%d%H%M")
        
        if minute_key not in self.rate_limiter:
            self.rate_limiter = {minute_key: 0}  # 清理旧数据
        
        if self.rate_limiter[minute_key] >= self.config["max_alerts_per_minute"]:
            return False
        
        self.rate_limiter[minute_key] += 1
        return True
    
    def _update_counters(self, type: str, symbol: str):
        """更新计数器"""
        # 更新类型计数
        if type not in self.alert_counters:
            self.alert_counters[type] = 0
        self.alert_counters[type] += 1
        
        # 更新币种计数
        symbol_key = f"symbol_{symbol}"
        if symbol_key not in self.alert_counters:
            self.alert_counters[symbol_key] = 0
        self.alert_counters[symbol_key] += 1
    
    async def _trigger_callbacks(self, alert: Alert):
        """触发回调"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"预警回调失败: {e}")
    
    def _log_alert(self, alert: Alert):
        """记录预警日志"""
        level_map = {
            AlertLevel.CRITICAL: logging.CRITICAL,
            AlertLevel.HIGH: logging.ERROR,
            AlertLevel.MEDIUM: logging.WARNING,
            AlertLevel.LOW: logging.INFO,
            AlertLevel.INFO: logging.DEBUG
        }
        
        log_level = level_map.get(alert.level, logging.INFO)
        logger.log(log_level, f"[{alert.level.name}] {alert.message}")
    
    def resolve_alert(self, alert_id: str):
        """解决预警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now(timezone.utc)
            del self.active_alerts[alert_id]
            logger.info(f"预警已解决: {alert_id}")
    
    def get_active_alerts(self, symbol: str = None, type: str = None) -> List[Alert]:
        """获取活跃预警"""
        alerts = list(self.active_alerts.values())
        
        if symbol:
            alerts = [a for a in alerts if a.symbol == symbol]
        if type:
            alerts = [a for a in alerts if a.type == type]
        
        return alerts
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "counters": self.alert_counters,
            "rate_limit_status": self.rate_limiter
        }
    
    def clear_old_alerts(self):
        """清理过期预警"""
        now = datetime.now(timezone.utc)
        ttl = timedelta(seconds=self.config["alert_ttl"])
        
        # 清理活跃预警
        expired = []
        for alert_id, alert in self.active_alerts.items():
            if now - alert.triggered_at > ttl:
                expired.append(alert_id)
        
        for alert_id in expired:
            self.resolve_alert(alert_id)
        
        # 清理历史记录
        self.alert_history = [
            a for a in self.alert_history
            if now - a.triggered_at <= ttl
        ]
        
        logger.info(f"清理过期预警: {len(expired)}个")


# 测试函数
async def test_alert_manager():
    """测试预警管理器"""
    manager = AlertManager()
    
    # 注册回调
    def alert_handler(alert: Alert):
        print(f"收到预警: [{alert.level.name}] {alert.message}")
    
    manager.register_callback(alert_handler)
    
    # 测试价格预警
    print("测试价格预警...")
    alert = await manager.check_price_alert("BTC-USDT", 100001, {"high": 100000, "low": 50000})
    
    # 测试价格变化预警
    print("\n测试价格变化预警...")
    alert = await manager.check_price_change_alert("ETH-USDT", 3800, 3500)
    
    # 测试巨鲸交易预警
    print("\n测试巨鲸交易预警...")
    trade = {"price": 67000, "size": 20, "side": "buy"}
    alert = await manager.check_whale_alert("BTC-USDT", trade)
    
    # 测试套利预警
    print("\n测试套利预警...")
    alert = await manager.check_arbitrage_alert("BTC-USDT", 67000, 67300)
    
    # 获取统计信息
    stats = manager.get_statistics()
    print(f"\n预警统计: {stats}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_alert_manager())