"""
异常检测机制
监控价格波动、成交量异常、深度变化等
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from collections import deque
import statistics
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # 历史数据缓存
        self.price_history = {}  # symbol -> deque of prices
        self.volume_history = {}  # symbol -> deque of volumes
        self.depth_history = {}  # symbol -> deque of depth snapshots
        self.funding_history = {}  # symbol -> deque of funding rates
        
        # 异常事件回调
        self.anomaly_callbacks = []
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "price_change_threshold": 0.03,  # 3%价格变化阈值
            "volume_multiplier": 5,  # 成交量异常倍数
            "depth_change_threshold": 0.5,  # 50%深度变化阈值
            "large_order_usdt": 1000000,  # 大单阈值（USDT）
            "funding_rate_threshold": 0.001,  # 0.1%资金费率阈值
            "history_window": 300,  # 历史数据窗口（秒）
            "min_samples": 10  # 最小样本数
        }
    
    def register_callback(self, callback):
        """注册异常事件回调"""
        self.anomaly_callbacks.append(callback)
    
    async def detect_price_anomaly(self, symbol: str, price: float, timestamp: datetime = None) -> Optional[Dict]:
        """检测价格异常"""
        timestamp = timestamp or datetime.now(timezone.utc)
        
        # 初始化历史记录
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.config["history_window"])
        
        history = self.price_history[symbol]
        
        # 添加新价格
        history.append((timestamp, price))
        
        # 样本数不足
        if len(history) < self.config["min_samples"]:
            return None
        
        # 计算1分钟前的价格
        one_minute_ago = timestamp - timedelta(seconds=60)
        old_prices = [p for t, p in history if t >= one_minute_ago and t < timestamp - timedelta(seconds=50)]
        
        if not old_prices:
            return None
        
        old_price = statistics.mean(old_prices)
        price_change = (price - old_price) / old_price
        
        # 检测异常
        if abs(price_change) > self.config["price_change_threshold"]:
            anomaly = {
                "type": "price_anomaly",
                "symbol": symbol,
                "current_price": price,
                "old_price": old_price,
                "change_percent": price_change * 100,
                "threshold": self.config["price_change_threshold"] * 100,
                "direction": "surge" if price_change > 0 else "plunge",
                "timestamp": timestamp,
                "severity": self._calculate_severity(abs(price_change), self.config["price_change_threshold"])
            }
            
            await self._trigger_anomaly(anomaly)
            return anomaly
        
        return None
    
    async def detect_volume_anomaly(self, symbol: str, volume: float, timestamp: datetime = None) -> Optional[Dict]:
        """检测成交量异常"""
        timestamp = timestamp or datetime.now(timezone.utc)
        
        # 初始化历史记录
        if symbol not in self.volume_history:
            self.volume_history[symbol] = deque(maxlen=self.config["history_window"])
        
        history = self.volume_history[symbol]
        
        # 添加新成交量
        history.append((timestamp, volume))
        
        # 样本数不足
        if len(history) < self.config["min_samples"]:
            return None
        
        # 计算5分钟平均成交量
        five_minutes_ago = timestamp - timedelta(seconds=300)
        recent_volumes = [v for t, v in history if t >= five_minutes_ago and t < timestamp]
        
        if len(recent_volumes) < 5:
            return None
        
        avg_volume = statistics.mean(recent_volumes)
        
        # 检测异常
        if volume > avg_volume * self.config["volume_multiplier"]:
            anomaly = {
                "type": "volume_anomaly",
                "symbol": symbol,
                "current_volume": volume,
                "average_volume": avg_volume,
                "multiplier": volume / avg_volume if avg_volume > 0 else 0,
                "threshold": self.config["volume_multiplier"],
                "timestamp": timestamp,
                "severity": self._calculate_severity(volume / avg_volume, self.config["volume_multiplier"])
            }
            
            await self._trigger_anomaly(anomaly)
            return anomaly
        
        return None
    
    async def detect_depth_anomaly(self, symbol: str, depth: Dict, timestamp: datetime = None) -> Optional[Dict]:
        """检测深度异常（买卖墙）"""
        timestamp = timestamp or datetime.now(timezone.utc)
        
        # 初始化历史记录
        if symbol not in self.depth_history:
            self.depth_history[symbol] = deque(maxlen=30)  # 保留30个快照
        
        history = self.depth_history[symbol]
        
        # 计算当前深度特征
        current_bid_volume = sum(float(bid["size"]) for bid in depth.get("bids", [])[:10])
        current_ask_volume = sum(float(ask["size"]) for ask in depth.get("asks", [])[:10])
        
        # 添加到历史
        history.append({
            "timestamp": timestamp,
            "bid_volume": current_bid_volume,
            "ask_volume": current_ask_volume
        })
        
        # 样本数不足
        if len(history) < 3:
            return None
        
        # 获取之前的深度
        prev_snapshot = history[-2]
        prev_bid_volume = prev_snapshot["bid_volume"]
        prev_ask_volume = prev_snapshot["ask_volume"]
        
        # 计算变化率
        bid_change = abs(current_bid_volume - prev_bid_volume) / prev_bid_volume if prev_bid_volume > 0 else 0
        ask_change = abs(current_ask_volume - prev_ask_volume) / prev_ask_volume if prev_ask_volume > 0 else 0
        
        anomalies = []
        
        # 检测买墙
        if bid_change > self.config["depth_change_threshold"]:
            if current_bid_volume > prev_bid_volume:
                anomalies.append({
                    "type": "depth_anomaly",
                    "subtype": "bid_wall_appeared",
                    "symbol": symbol,
                    "current_volume": current_bid_volume,
                    "previous_volume": prev_bid_volume,
                    "change_percent": bid_change * 100,
                    "timestamp": timestamp,
                    "severity": self._calculate_severity(bid_change, self.config["depth_change_threshold"])
                })
            else:
                anomalies.append({
                    "type": "depth_anomaly",
                    "subtype": "bid_wall_removed",
                    "symbol": symbol,
                    "current_volume": current_bid_volume,
                    "previous_volume": prev_bid_volume,
                    "change_percent": bid_change * 100,
                    "timestamp": timestamp,
                    "severity": self._calculate_severity(bid_change, self.config["depth_change_threshold"])
                })
        
        # 检测卖墙
        if ask_change > self.config["depth_change_threshold"]:
            if current_ask_volume > prev_ask_volume:
                anomalies.append({
                    "type": "depth_anomaly",
                    "subtype": "ask_wall_appeared",
                    "symbol": symbol,
                    "current_volume": current_ask_volume,
                    "previous_volume": prev_ask_volume,
                    "change_percent": ask_change * 100,
                    "timestamp": timestamp,
                    "severity": self._calculate_severity(ask_change, self.config["depth_change_threshold"])
                })
            else:
                anomalies.append({
                    "type": "depth_anomaly",
                    "subtype": "ask_wall_removed",
                    "symbol": symbol,
                    "current_volume": current_ask_volume,
                    "previous_volume": prev_ask_volume,
                    "change_percent": ask_change * 100,
                    "timestamp": timestamp,
                    "severity": self._calculate_severity(ask_change, self.config["depth_change_threshold"])
                })
        
        # 触发异常
        for anomaly in anomalies:
            await self._trigger_anomaly(anomaly)
        
        return anomalies[0] if anomalies else None
    
    async def detect_large_trade(self, symbol: str, trade: Dict) -> Optional[Dict]:
        """检测大单成交"""
        price = float(trade.get("price", 0))
        size = float(trade.get("size", 0))
        value = price * size
        
        if value > self.config["large_order_usdt"]:
            anomaly = {
                "type": "large_trade",
                "symbol": symbol,
                "price": price,
                "size": size,
                "value": value,
                "side": trade.get("side", "unknown"),
                "threshold": self.config["large_order_usdt"],
                "timestamp": trade.get("timestamp", datetime.now(timezone.utc)),
                "severity": self._calculate_severity(value, self.config["large_order_usdt"])
            }
            
            await self._trigger_anomaly(anomaly)
            return anomaly
        
        return None
    
    async def detect_funding_rate_anomaly(self, symbol: str, funding_rate: float, 
                                        timestamp: datetime = None) -> Optional[Dict]:
        """检测资金费率异常"""
        timestamp = timestamp or datetime.now(timezone.utc)
        
        # 初始化历史记录
        if symbol not in self.funding_history:
            self.funding_history[symbol] = deque(maxlen=30)  # 保留30个记录
        
        history = self.funding_history[symbol]
        history.append((timestamp, funding_rate))
        
        # 检测异常
        if abs(funding_rate) > self.config["funding_rate_threshold"]:
            anomaly = {
                "type": "funding_rate_anomaly",
                "symbol": symbol,
                "funding_rate": funding_rate,
                "threshold": self.config["funding_rate_threshold"],
                "direction": "positive" if funding_rate > 0 else "negative",
                "timestamp": timestamp,
                "severity": self._calculate_severity(abs(funding_rate), self.config["funding_rate_threshold"])
            }
            
            await self._trigger_anomaly(anomaly)
            return anomaly
        
        return None
    
    async def detect_cross_exchange_anomaly(self, symbol: str, okx_price: float, 
                                           binance_price: float) -> Optional[Dict]:
        """检测交易所间价差异常"""
        price_diff = abs(okx_price - binance_price)
        price_diff_percent = price_diff / min(okx_price, binance_price)
        
        # 价差超过0.5%视为异常
        if price_diff_percent > 0.005:
            anomaly = {
                "type": "cross_exchange_anomaly",
                "symbol": symbol,
                "okx_price": okx_price,
                "binance_price": binance_price,
                "difference": price_diff,
                "difference_percent": price_diff_percent * 100,
                "arbitrage_direction": "OKX->Binance" if okx_price < binance_price else "Binance->OKX",
                "timestamp": datetime.now(timezone.utc),
                "severity": self._calculate_severity(price_diff_percent, 0.005)
            }
            
            await self._trigger_anomaly(anomaly)
            return anomaly
        
        return None
    
    def _calculate_severity(self, value: float, threshold: float) -> str:
        """计算异常严重程度"""
        ratio = value / threshold if threshold > 0 else 0
        
        if ratio < 1.5:
            return "low"
        elif ratio < 3:
            return "medium"
        elif ratio < 5:
            return "high"
        else:
            return "critical"
    
    async def _trigger_anomaly(self, anomaly: Dict):
        """触发异常事件"""
        logger.warning(f"检测到异常: {anomaly}")
        
        # 调用所有回调函数
        for callback in self.anomaly_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(anomaly)
                else:
                    callback(anomaly)
            except Exception as e:
                logger.error(f"异常回调失败: {e}")
    
    def get_statistics(self, symbol: str = None) -> Dict:
        """获取检测统计信息"""
        if symbol:
            return {
                "symbol": symbol,
                "price_samples": len(self.price_history.get(symbol, [])),
                "volume_samples": len(self.volume_history.get(symbol, [])),
                "depth_samples": len(self.depth_history.get(symbol, [])),
                "funding_samples": len(self.funding_history.get(symbol, []))
            }
        else:
            return {
                "total_symbols": len(set(list(self.price_history.keys()) + 
                                       list(self.volume_history.keys()))),
                "price_monitoring": list(self.price_history.keys()),
                "volume_monitoring": list(self.volume_history.keys()),
                "depth_monitoring": list(self.depth_history.keys()),
                "funding_monitoring": list(self.funding_history.keys())
            }
    
    def clear_history(self, symbol: str = None):
        """清除历史数据"""
        if symbol:
            self.price_history.pop(symbol, None)
            self.volume_history.pop(symbol, None)
            self.depth_history.pop(symbol, None)
            self.funding_history.pop(symbol, None)
        else:
            self.price_history.clear()
            self.volume_history.clear()
            self.depth_history.clear()
            self.funding_history.clear()


# 测试函数
async def test_detector():
    """测试异常检测器"""
    detector = AnomalyDetector()
    
    # 注册回调
    def anomaly_handler(anomaly):
        print(f"[异常告警] {anomaly['type']}: {anomaly}")
    
    detector.register_callback(anomaly_handler)
    
    # 测试价格异常
    print("测试价格异常检测...")
    symbol = "BTCUSDT"
    
    # 模拟正常价格
    for i in range(15):
        await detector.detect_price_anomaly(symbol, 67000 + i * 10)
        await asyncio.sleep(0.1)
    
    # 模拟价格暴涨
    anomaly = await detector.detect_price_anomaly(symbol, 70000)
    if anomaly:
        print(f"检测到价格异常: {anomaly}")
    
    # 测试成交量异常
    print("\n测试成交量异常检测...")
    
    # 模拟正常成交量
    for i in range(10):
        await detector.detect_volume_anomaly(symbol, 100 + i * 5)
    
    # 模拟成交量激增
    anomaly = await detector.detect_volume_anomaly(symbol, 1000)
    if anomaly:
        print(f"检测到成交量异常: {anomaly}")
    
    # 测试大单检测
    print("\n测试大单检测...")
    trade = {
        "price": 67000,
        "size": 20,
        "side": "buy"
    }
    anomaly = await detector.detect_large_trade(symbol, trade)
    if anomaly:
        print(f"检测到大单: {anomaly}")
    
    # 获取统计信息
    stats = detector.get_statistics()
    print(f"\n检测统计: {stats}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_detector())