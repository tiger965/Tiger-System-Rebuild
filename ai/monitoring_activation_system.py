"""
三级触发系统 - 监控市场变化并决定激活级别
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class MonitoringActivationSystem:
    """三级触发监控系统"""
    
    def __init__(self):
        """初始化监控系统"""
        # 触发阈值
        self.trigger_thresholds = {
            1: 0.003,  # 0.3% - 一级触发
            2: 0.005,  # 0.5% - 二级触发
            3: 0.010   # 1.0% - 三级触发
        }
        
        # 监控的主要币种
        self.monitored_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", 
            "SOLUSDT", "XRPUSDT", "ADAUSDT"
        ]
        
        # 价格缓存（用于计算变化率）
        self.price_cache = {}
        self.last_check_time = {}
        
        # 触发历史记录
        self.trigger_history = []
        self.max_history = 100
        
        # 冷却时间（防止频繁触发）
        self.cooldown_periods = {
            1: timedelta(minutes=5),   # 一级5分钟冷却
            2: timedelta(minutes=15),  # 二级15分钟冷却
            3: timedelta(minutes=30)   # 三级30分钟冷却
        }
        self.last_trigger_time = {}
        
        logger.info("三级触发系统初始化完成")
    
    def check_trigger_level(self, market_data: Dict) -> int:
        """
        检查触发级别
        返回: 0=无触发, 1=一级, 2=二级, 3=三级
        """
        try:
            # 提取价格数据
            current_prices = self._extract_prices(market_data)
            if not current_prices:
                return 0
            
            # 计算价格变化率
            price_changes = self._calculate_price_changes(current_prices)
            
            # 检查成交量异常
            volume_spike = self._check_volume_spike(market_data)
            
            # 检查市场情绪
            sentiment_extreme = self._check_sentiment(market_data)
            
            # 综合判断触发级别
            trigger_level = self._determine_trigger_level(
                price_changes, 
                volume_spike, 
                sentiment_extreme
            )
            
            # 检查冷却时间
            if trigger_level > 0 and not self._check_cooldown(trigger_level):
                logger.info(f"触发级别{trigger_level}在冷却期内，跳过")
                return 0
            
            # 记录触发
            if trigger_level > 0:
                self._record_trigger(trigger_level, price_changes, market_data)
            
            return trigger_level
            
        except Exception as e:
            logger.error(f"检查触发级别失败: {e}")
            return 0
    
    def _extract_prices(self, market_data: Dict) -> Dict[str, float]:
        """提取价格数据"""
        prices = {}
        
        # 从市场数据中提取价格
        if "btc_price" in market_data:
            btc_data = market_data["btc_price"]
            if isinstance(btc_data, dict) and "price" in btc_data:
                prices["BTCUSDT"] = float(btc_data["price"])
        
        # 从热门币种中提取
        if "hot_coins" in market_data:
            for coin in market_data["hot_coins"]:
                if isinstance(coin, dict):
                    symbol = coin.get("symbol")
                    price = coin.get("price")
                    if symbol and price:
                        prices[symbol] = float(price)
        
        return prices
    
    def _calculate_price_changes(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """计算价格变化率"""
        changes = {}
        
        for symbol, current_price in current_prices.items():
            if symbol in self.price_cache:
                previous_price = self.price_cache[symbol]
                if previous_price > 0:
                    change_rate = abs((current_price - previous_price) / previous_price)
                    changes[symbol] = change_rate
                    
                    if change_rate > 0.001:  # 超过0.1%才记录
                        logger.debug(f"{symbol}: {previous_price:.2f} -> {current_price:.2f} "
                                   f"({change_rate:.2%})")
            
            # 更新缓存
            self.price_cache[symbol] = current_price
        
        return changes
    
    def _check_volume_spike(self, market_data: Dict) -> bool:
        """检查成交量是否异常"""
        # 检查成交量是否突增
        if "hot_coins" in market_data:
            for coin in market_data["hot_coins"]:
                if isinstance(coin, dict):
                    volume_change = coin.get("volume_change_24h", 0)
                    if abs(volume_change) > 50:  # 成交量变化超过50%
                        logger.info(f"检测到成交量异常: {coin.get('symbol')} "
                                  f"变化 {volume_change}%")
                        return True
        return False
    
    def _check_sentiment(self, market_data: Dict) -> bool:
        """检查市场情绪是否极端"""
        # 这里可以集成社交媒体情绪分析
        # 暂时返回False
        return False
    
    def _determine_trigger_level(self, 
                                price_changes: Dict[str, float],
                                volume_spike: bool,
                                sentiment_extreme: bool) -> int:
        """综合判断触发级别"""
        if not price_changes:
            return 0
        
        # 找出最大变化率
        max_change = max(price_changes.values()) if price_changes else 0
        triggered_symbols = [s for s, c in price_changes.items() 
                           if c >= self.trigger_thresholds[1]]
        
        # 根据变化率判断基础级别
        base_level = 0
        for level in [3, 2, 1]:  # 从高到低检查
            if max_change >= self.trigger_thresholds[level]:
                base_level = level
                break
        
        # 根据其他因素调整级别
        if base_level > 0:
            # 多个币种同时触发，提升级别
            if len(triggered_symbols) >= 3:
                base_level = min(base_level + 1, 3)
                logger.info(f"多币种同时触发: {triggered_symbols}")
            
            # 成交量异常，提升级别
            if volume_spike:
                base_level = min(base_level + 1, 3)
                logger.info("成交量异常，提升触发级别")
            
            # 情绪极端，提升级别
            if sentiment_extreme:
                base_level = min(base_level + 1, 3)
                logger.info("市场情绪极端，提升触发级别")
        
        if base_level > 0:
            logger.info(f"触发级别判定: {base_level}级 "
                       f"(最大变化: {max_change:.2%})")
        
        return base_level
    
    def _check_cooldown(self, trigger_level: int) -> bool:
        """检查是否在冷却期"""
        if trigger_level not in self.last_trigger_time:
            return True
        
        last_time = self.last_trigger_time[trigger_level]
        cooldown = self.cooldown_periods[trigger_level]
        
        if datetime.now() - last_time < cooldown:
            remaining = cooldown - (datetime.now() - last_time)
            logger.debug(f"级别{trigger_level}冷却中，剩余: {remaining}")
            return False
        
        return True
    
    def _record_trigger(self, level: int, price_changes: Dict, market_data: Dict):
        """记录触发事件"""
        trigger_event = {
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "price_changes": price_changes,
            "max_change": max(price_changes.values()) if price_changes else 0,
            "triggered_symbols": [s for s, c in price_changes.items() 
                                 if c >= self.trigger_thresholds[1]],
            "market_snapshot": {
                "btc_price": market_data.get("btc_price", {}).get("price"),
                "hot_coins_count": len(market_data.get("hot_coins", []))
            }
        }
        
        # 添加到历史
        self.trigger_history.append(trigger_event)
        
        # 限制历史记录数量
        if len(self.trigger_history) > self.max_history:
            self.trigger_history = self.trigger_history[-self.max_history:]
        
        # 更新最后触发时间
        self.last_trigger_time[level] = datetime.now()
        
        # 记录日志
        logger.info(f"触发事件记录: {json.dumps(trigger_event, ensure_ascii=False)}")
    
    def get_trigger_stats(self) -> Dict:
        """获取触发统计"""
        if not self.trigger_history:
            return {
                "total_triggers": 0,
                "level_distribution": {1: 0, 2: 0, 3: 0},
                "last_trigger": None
            }
        
        level_counts = {1: 0, 2: 0, 3: 0}
        for event in self.trigger_history:
            level = event["level"]
            if level in level_counts:
                level_counts[level] += 1
        
        return {
            "total_triggers": len(self.trigger_history),
            "level_distribution": level_counts,
            "last_trigger": self.trigger_history[-1] if self.trigger_history else None,
            "triggers_last_hour": len([
                e for e in self.trigger_history
                if datetime.fromisoformat(e["timestamp"]) > 
                   datetime.now() - timedelta(hours=1)
            ])
        }
    
    def adjust_sensitivity(self, factor: float):
        """调整触发灵敏度"""
        logger.info(f"调整触发灵敏度: {factor}x")
        
        for level in self.trigger_thresholds:
            self.trigger_thresholds[level] *= factor
        
        logger.info(f"新的触发阈值: {self.trigger_thresholds}")
    
    def reset_cooldowns(self):
        """重置所有冷却时间"""
        self.last_trigger_time.clear()
        logger.info("所有触发冷却时间已重置")