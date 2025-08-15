"""
多级触发机制系统 - 精准控制AI调用时机
关键设计思想：
1. 避免频繁调用AI，降低成本
2. 确保重要信号不遗漏
3. 动态调整触发阈值
4. 智能冷却防止重复触发
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class TriggerLevel(Enum):
    """触发级别枚举"""
    NONE = 0      # 不触发
    LEVEL_1 = 1   # 本地处理
    LEVEL_2 = 2   # 标准AI分析
    LEVEL_3 = 3   # 紧急深度分析


@dataclass
class TriggerSignal:
    """触发信号数据结构"""
    symbol: str
    level: TriggerLevel
    trigger_type: str
    trigger_reason: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # 优先级 0-10
    confidence: float = 0.0  # 置信度 0-1


@dataclass
class TriggerThresholds:
    """动态触发阈值"""
    # 价格变化阈值
    price_change_level_1: float = 1.5  # %
    price_change_level_2: float = 3.0
    price_change_level_3: float = 10.0
    
    # 成交量阈值
    volume_spike_level_1: float = 2.0  # 倍数
    volume_spike_level_2: float = 3.0
    volume_spike_level_3: float = 5.0
    
    # 技术指标阈值
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    rsi_extreme: float = 15.0  # 极端超卖
    rsi_extreme_high: float = 85.0  # 极端超买
    
    # 鲸鱼转账阈值
    whale_transfer_small: float = 1_000_000  # USDT
    whale_transfer_medium: float = 10_000_000
    whale_transfer_large: float = 50_000_000
    
    # 清算阈值
    liquidation_small: float = 10_000_000
    liquidation_medium: float = 50_000_000
    liquidation_large: float = 100_000_000
    
    # 社交媒体阈值
    social_mention_spike: float = 3.0  # 倍数
    sentiment_change: float = 20.0  # %


class TriggerCooldown:
    """冷却机制管理器"""
    
    def __init__(self):
        self.cooldowns: Dict[str, datetime] = {}
        self.trigger_history: Dict[str, List[datetime]] = defaultdict(list)
        self.api_calls: List[datetime] = []
        
        # 冷却时间配置（秒）
        self.same_signal_cooldown = 300  # 5分钟
        self.same_coin_cooldown = 120    # 2分钟
        self.api_rate_limit = 100        # 每小时限制
        
    def can_trigger(self, symbol: str, signal_type: str) -> Tuple[bool, str]:
        """
        检查是否可以触发
        返回: (是否可以触发, 原因)
        """
        now = datetime.now()
        
        # 检查API调用限制
        hour_ago = now - timedelta(hours=1)
        recent_calls = [t for t in self.api_calls if t > hour_ago]
        if len(recent_calls) >= self.api_rate_limit:
            return False, f"API rate limit reached ({len(recent_calls)}/{self.api_rate_limit})"
        
        # 检查相同信号冷却
        signal_key = f"{symbol}:{signal_type}"
        if signal_key in self.cooldowns:
            time_since = (now - self.cooldowns[signal_key]).total_seconds()
            if time_since < self.same_signal_cooldown:
                remaining = self.same_signal_cooldown - time_since
                return False, f"Signal cooldown ({remaining:.0f}s remaining)"
        
        # 检查币种冷却
        coin_key = symbol
        if coin_key in self.cooldowns:
            time_since = (now - self.cooldowns[coin_key]).total_seconds()
            if time_since < self.same_coin_cooldown:
                remaining = self.same_coin_cooldown - time_since
                return False, f"Coin cooldown ({remaining:.0f}s remaining)"
        
        return True, "OK"
    
    def record_trigger(self, symbol: str, signal_type: str):
        """记录触发事件"""
        now = datetime.now()
        signal_key = f"{symbol}:{signal_type}"
        
        self.cooldowns[signal_key] = now
        self.cooldowns[symbol] = now
        self.trigger_history[symbol].append(now)
        self.api_calls.append(now)
        
        # 清理旧记录
        self._cleanup_old_records()
    
    def _cleanup_old_records(self):
        """清理超过1小时的记录"""
        cutoff = datetime.now() - timedelta(hours=1)
        self.api_calls = [t for t in self.api_calls if t > cutoff]
        
        for symbol in list(self.trigger_history.keys()):
            self.trigger_history[symbol] = [
                t for t in self.trigger_history[symbol] if t > cutoff
            ]
            if not self.trigger_history[symbol]:
                del self.trigger_history[symbol]


class TriggerSystem:
    """多级触发机制核心系统"""
    
    def __init__(self):
        self.thresholds = TriggerThresholds()
        self.cooldown = TriggerCooldown()
        self.trigger_queue: List[TriggerSignal] = []
        self.processing = False
        
        # 市场状态跟踪
        self.market_state = {
            'trend': 'neutral',  # bull/bear/neutral
            'volatility': 'normal',  # low/normal/high/extreme
            'volume': 'normal',  # low/normal/high
            'fear_greed': 50  # 0-100
        }
        
        # 性能统计
        self.stats = {
            'total_triggers': 0,
            'level_1_count': 0,
            'level_2_count': 0,
            'level_3_count': 0,
            'false_positives': 0,
            'missed_opportunities': 0
        }
        
    async def evaluate_trigger(self, market_data: Dict[str, Any]) -> Optional[TriggerSignal]:
        """
        评估市场数据，决定触发级别
        这是系统的核心决策逻辑
        """
        symbol = market_data.get('symbol', 'UNKNOWN')
        
        # 提取关键指标
        price_change = abs(market_data.get('price_change_24h', 0))
        volume_ratio = market_data.get('volume_ratio', 1.0)
        rsi = market_data.get('rsi', 50)
        whale_transfer = market_data.get('whale_transfer', 0)
        liquidations = market_data.get('liquidations', 0)
        top_traders = market_data.get('top_traders_action', [])
        social_spike = market_data.get('social_mention_spike', 1.0)
        news_importance = market_data.get('news_importance', 0)
        
        # 计算触发分数
        trigger_score = 0
        trigger_reasons = []
        trigger_data = {}
        
        # Level 3 检查 - 最高优先级
        if self._check_black_swan_conditions(market_data):
            trigger_score = 100
            trigger_reasons.append("Black swan event detected")
            level = TriggerLevel.LEVEL_3
            priority = 10
            
        elif price_change >= self.thresholds.price_change_level_3:
            trigger_score += 50
            trigger_reasons.append(f"Extreme price change: {price_change:.1f}%")
            level = TriggerLevel.LEVEL_3
            priority = 9
            
        elif liquidations >= self.thresholds.liquidation_large:
            trigger_score += 45
            trigger_reasons.append(f"Massive liquidations: ${liquidations/1e6:.1f}M")
            level = TriggerLevel.LEVEL_3
            priority = 9
            
        # Level 2 检查
        elif self._check_level_2_conditions(market_data):
            level = TriggerLevel.LEVEL_2
            priority = 5
            
            if price_change >= self.thresholds.price_change_level_2:
                trigger_score += 30
                trigger_reasons.append(f"Significant price change: {price_change:.1f}%")
                
            if volume_ratio >= self.thresholds.volume_spike_level_2:
                trigger_score += 25
                trigger_reasons.append(f"Volume spike: {volume_ratio:.1f}x")
                
            if len(top_traders) >= 2:
                trigger_score += 30
                trigger_reasons.append(f"Top traders action: {len(top_traders)} traders")
                
            if whale_transfer >= self.thresholds.whale_transfer_medium:
                trigger_score += 20
                trigger_reasons.append(f"Whale transfer: ${whale_transfer/1e6:.1f}M")
                
        # Level 1 检查
        elif self._check_level_1_conditions(market_data):
            level = TriggerLevel.LEVEL_1
            priority = 2
            
            if price_change >= self.thresholds.price_change_level_1:
                trigger_score += 10
                trigger_reasons.append(f"Price change: {price_change:.1f}%")
                
            if volume_ratio >= self.thresholds.volume_spike_level_1:
                trigger_score += 10
                trigger_reasons.append(f"Volume increase: {volume_ratio:.1f}x")
                
        else:
            # 不触发
            return None
        
        # 检查冷却
        can_trigger, reason = self.cooldown.can_trigger(symbol, trigger_reasons[0] if trigger_reasons else "general")
        if not can_trigger:
            logger.debug(f"Trigger blocked for {symbol}: {reason}")
            return None
        
        # 创建触发信号
        signal = TriggerSignal(
            symbol=symbol,
            level=level,
            trigger_type=self._determine_trigger_type(market_data),
            trigger_reason="; ".join(trigger_reasons),
            data=market_data,
            priority=priority,
            confidence=min(trigger_score / 100, 1.0)
        )
        
        # 记录触发
        self.cooldown.record_trigger(symbol, signal.trigger_type)
        self.stats['total_triggers'] += 1
        self.stats[f'level_{level.value}_count'] += 1
        
        logger.info(f"Trigger generated: {symbol} - Level {level.value} - {signal.trigger_reason}")
        
        return signal
    
    def _check_black_swan_conditions(self, data: Dict) -> bool:
        """检查黑天鹅事件条件"""
        # 多重极端条件同时满足
        conditions = [
            data.get('price_change_24h', 0) > 20,  # 价格暴涨暴跌
            data.get('liquidations', 0) > 100_000_000,  # 巨额爆仓
            data.get('news_importance', 0) >= 9,  # 重大新闻
            data.get('panic_selling', False),  # 恐慌性抛售
            data.get('exchange_issue', False),  # 交易所问题
        ]
        
        # 至少2个条件满足
        return sum(conditions) >= 2
    
    def _check_level_2_conditions(self, data: Dict) -> bool:
        """检查Level 2触发条件"""
        conditions = [
            abs(data.get('price_change_24h', 0)) >= self.thresholds.price_change_level_2,
            data.get('volume_ratio', 1) >= self.thresholds.volume_spike_level_2,
            len(data.get('top_traders_action', [])) >= 1,
            data.get('whale_transfer', 0) >= self.thresholds.whale_transfer_small,
            data.get('technical_signals_count', 0) >= 3,
            data.get('social_mention_spike', 1) >= self.thresholds.social_mention_spike,
        ]
        
        # 至少2个条件满足
        return sum(conditions) >= 2
    
    def _check_level_1_conditions(self, data: Dict) -> bool:
        """检查Level 1触发条件"""
        price_change = abs(data.get('price_change_24h', 0))
        volume_ratio = data.get('volume_ratio', 1)
        rsi = data.get('rsi', 50)
        
        # 基础条件检查
        return (
            price_change >= self.thresholds.price_change_level_1 or
            volume_ratio >= self.thresholds.volume_spike_level_1 or
            rsi <= self.thresholds.rsi_oversold or
            rsi >= self.thresholds.rsi_overbought
        )
    
    def _determine_trigger_type(self, data: Dict) -> str:
        """确定触发类型"""
        # 根据主要触发因素分类
        if data.get('news_importance', 0) >= 7:
            return 'news_driven'
        elif len(data.get('top_traders_action', [])) >= 2:
            return 'trader_driven'
        elif data.get('whale_transfer', 0) > 0:
            return 'whale_activity'
        elif abs(data.get('price_change_24h', 0)) >= 5:
            return 'price_movement'
        elif data.get('volume_ratio', 1) >= 3:
            return 'volume_spike'
        elif data.get('liquidations', 0) > 0:
            return 'liquidation_cascade'
        else:
            return 'technical_signal'
    
    async def process_queue(self):
        """处理触发队列"""
        if self.processing:
            return
        
        self.processing = True
        try:
            # 按优先级排序
            self.trigger_queue.sort(key=lambda x: (-x.priority, x.timestamp))
            
            while self.trigger_queue:
                signal = self.trigger_queue.pop(0)
                
                # 处理信号
                await self._process_signal(signal)
                
                # 避免过于频繁
                await asyncio.sleep(1)
                
        finally:
            self.processing = False
    
    async def _process_signal(self, signal: TriggerSignal):
        """处理单个触发信号"""
        logger.info(f"Processing signal: {signal.symbol} - Level {signal.level.value}")
        
        # 这里将与AI客户端集成
        # 根据不同级别采取不同处理策略
        if signal.level == TriggerLevel.LEVEL_1:
            # 本地处理，记录日志
            logger.info(f"Level 1 - Local processing for {signal.symbol}")
            
        elif signal.level == TriggerLevel.LEVEL_2:
            # 调用标准AI分析
            logger.info(f"Level 2 - Standard AI analysis for {signal.symbol}")
            
        elif signal.level == TriggerLevel.LEVEL_3:
            # 紧急深度分析
            logger.warning(f"Level 3 - URGENT deep analysis for {signal.symbol}")
    
    def update_thresholds(self, market_state: Dict):
        """根据市场状态动态调整阈值"""
        # 牛市降低触发阈值
        if market_state.get('trend') == 'bull':
            self.thresholds.price_change_level_2 = 2.5
            self.thresholds.price_change_level_3 = 8.0
            
        # 熊市提高触发阈值
        elif market_state.get('trend') == 'bear':
            self.thresholds.price_change_level_2 = 4.0
            self.thresholds.price_change_level_3 = 12.0
            
        # 高波动市场
        if market_state.get('volatility') == 'high':
            self.thresholds.price_change_level_1 = 2.0
            self.thresholds.price_change_level_2 = 5.0
            
        logger.info(f"Thresholds updated for {market_state.get('trend')} market")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'api_calls_last_hour': len(self.cooldown.api_calls),
            'queue_size': len(self.trigger_queue),
            'active_cooldowns': len(self.cooldown.cooldowns)
        }