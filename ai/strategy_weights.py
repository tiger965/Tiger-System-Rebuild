"""
策略权重系统 - 动态调整决策权重
根据市场环境、历史表现、交易员信号等因素
智能调整不同策略和信号源的权重
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """策略类型"""
    TREND_FOLLOWING = "trend_following"      # 趋势跟随
    MEAN_REVERSION = "mean_reversion"        # 均值回归
    BREAKOUT = "breakout"                    # 突破交易
    MOMENTUM = "momentum"                     # 动量交易
    ARBITRAGE = "arbitrage"                  # 套利交易
    SCALPING = "scalping"                    # 剥头皮
    SWING = "swing"                          # 波段交易
    CONTRARIAN = "contrarian"                # 逆向交易


class MarketCondition(Enum):
    """市场状况"""
    STRONG_BULL = "strong_bull"      # 强牛市
    BULL = "bull"                     # 牛市
    SIDEWAYS_UP = "sideways_up"      # 震荡上行
    SIDEWAYS = "sideways"             # 震荡
    SIDEWAYS_DOWN = "sideways_down"  # 震荡下行
    BEAR = "bear"                     # 熊市
    STRONG_BEAR = "strong_bear"      # 强熊市
    VOLATILE = "volatile"             # 高波动
    CRASH = "crash"                   # 崩盘


@dataclass
class TraderProfile:
    """交易员档案"""
    name: str
    platform: str
    overall_winrate: float
    recent_winrate: float  # 最近30天
    avg_pnl: float
    total_trades: int
    specialties: List[str]  # 擅长的币种
    best_market: MarketCondition  # 最佳市场环境
    current_weight: float = 0.2
    performance_history: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class StrategyPerformance:
    """策略表现"""
    strategy_type: StrategyType
    market_condition: MarketCondition
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    trade_count: int
    last_updated: datetime


class StrategyWeights:
    """策略权重管理系统"""
    
    def __init__(self):
        # 策略权重表（根据市场状况）
        self.strategy_weights = self._initialize_strategy_weights()
        
        # 交易员权重
        self.trader_profiles = self._initialize_trader_profiles()
        
        # 信号源权重
        self.signal_weights = {
            'technical': 0.3,      # 技术分析
            'fundamental': 0.2,    # 基本面
            'sentiment': 0.15,     # 市场情绪
            'onchain': 0.15,       # 链上数据
            'trader': 0.2          # 交易员信号
        }
        
        # 历史表现记录
        self.performance_history: Dict[StrategyType, List[StrategyPerformance]] = defaultdict(list)
        
        # 当前市场状况
        self.current_market = MarketCondition.SIDEWAYS
        
        # 自适应参数
        self.adaptation_rate = 0.1  # 权重调整速率
        self.performance_window = 30  # 性能评估窗口（天）
        self.min_weight = 0.05  # 最小权重
        self.max_weight = 0.5   # 最大权重
        
        # 权重调整历史
        self.weight_history = deque(maxlen=100)
    
    def _initialize_strategy_weights(self) -> Dict[MarketCondition, Dict[StrategyType, float]]:
        """初始化策略权重矩阵"""
        return {
            MarketCondition.STRONG_BULL: {
                StrategyType.TREND_FOLLOWING: 0.35,
                StrategyType.MOMENTUM: 0.30,
                StrategyType.BREAKOUT: 0.20,
                StrategyType.MEAN_REVERSION: 0.05,
                StrategyType.SWING: 0.05,
                StrategyType.CONTRARIAN: 0.05
            },
            MarketCondition.BULL: {
                StrategyType.TREND_FOLLOWING: 0.30,
                StrategyType.MOMENTUM: 0.25,
                StrategyType.BREAKOUT: 0.20,
                StrategyType.SWING: 0.10,
                StrategyType.MEAN_REVERSION: 0.10,
                StrategyType.CONTRARIAN: 0.05
            },
            MarketCondition.SIDEWAYS_UP: {
                StrategyType.SWING: 0.25,
                StrategyType.MEAN_REVERSION: 0.25,
                StrategyType.BREAKOUT: 0.20,
                StrategyType.MOMENTUM: 0.15,
                StrategyType.TREND_FOLLOWING: 0.10,
                StrategyType.CONTRARIAN: 0.05
            },
            MarketCondition.SIDEWAYS: {
                StrategyType.MEAN_REVERSION: 0.35,
                StrategyType.SWING: 0.25,
                StrategyType.SCALPING: 0.15,
                StrategyType.ARBITRAGE: 0.10,
                StrategyType.BREAKOUT: 0.10,
                StrategyType.TREND_FOLLOWING: 0.05
            },
            MarketCondition.SIDEWAYS_DOWN: {
                StrategyType.MEAN_REVERSION: 0.30,
                StrategyType.CONTRARIAN: 0.20,
                StrategyType.SWING: 0.20,
                StrategyType.SCALPING: 0.15,
                StrategyType.ARBITRAGE: 0.10,
                StrategyType.TREND_FOLLOWING: 0.05
            },
            MarketCondition.BEAR: {
                StrategyType.CONTRARIAN: 0.25,
                StrategyType.MEAN_REVERSION: 0.25,
                StrategyType.TREND_FOLLOWING: 0.20,  # 做空趋势
                StrategyType.SCALPING: 0.15,
                StrategyType.SWING: 0.10,
                StrategyType.MOMENTUM: 0.05
            },
            MarketCondition.STRONG_BEAR: {
                StrategyType.TREND_FOLLOWING: 0.30,  # 做空趋势
                StrategyType.CONTRARIAN: 0.25,
                StrategyType.MEAN_REVERSION: 0.20,
                StrategyType.SCALPING: 0.15,
                StrategyType.ARBITRAGE: 0.05,
                StrategyType.MOMENTUM: 0.05
            },
            MarketCondition.VOLATILE: {
                StrategyType.SCALPING: 0.25,
                StrategyType.BREAKOUT: 0.20,
                StrategyType.MOMENTUM: 0.20,
                StrategyType.MEAN_REVERSION: 0.15,
                StrategyType.ARBITRAGE: 0.10,
                StrategyType.CONTRARIAN: 0.10
            },
            MarketCondition.CRASH: {
                StrategyType.CONTRARIAN: 0.40,  # 抄底
                StrategyType.MEAN_REVERSION: 0.30,
                StrategyType.SCALPING: 0.20,
                StrategyType.ARBITRAGE: 0.10,
                StrategyType.TREND_FOLLOWING: 0.0,
                StrategyType.MOMENTUM: 0.0
            }
        }
    
    def _initialize_trader_profiles(self) -> Dict[str, TraderProfile]:
        """初始化交易员档案"""
        return {
            "如果我不懂": TraderProfile(
                name="如果我不懂",
                platform="Binance",
                overall_winrate=0.68,
                recent_winrate=0.72,
                avg_pnl=15.5,
                total_trades=1250,
                specialties=["BTC", "ETH", "SOL"],
                best_market=MarketCondition.BULL,
                current_weight=0.30
            ),
            "熬鹰": TraderProfile(
                name="熬鹰",
                platform="Binance",
                overall_winrate=0.65,
                recent_winrate=0.68,
                avg_pnl=12.3,
                total_trades=980,
                specialties=["BTC", "BNB", "ARB"],
                best_market=MarketCondition.SIDEWAYS,
                current_weight=0.25
            ),
            "以予": TraderProfile(
                name="以予",
                platform="OKX",
                overall_winrate=0.70,
                recent_winrate=0.75,
                avg_pnl=18.2,
                total_trades=850,
                specialties=["ETH", "MATIC", "LINK"],
                best_market=MarketCondition.VOLATILE,
                current_weight=0.25
            ),
            "梭哈哥": TraderProfile(
                name="梭哈哥",
                platform="Bybit",
                overall_winrate=0.58,
                recent_winrate=0.62,
                avg_pnl=25.5,  # 高风险高收益
                total_trades=450,
                specialties=["DOGE", "SHIB", "PEPE"],
                best_market=MarketCondition.STRONG_BULL,
                current_weight=0.10
            ),
            "稳健派": TraderProfile(
                name="稳健派",
                platform="Binance",
                overall_winrate=0.75,
                recent_winrate=0.73,
                avg_pnl=8.5,  # 低风险稳定
                total_trades=2100,
                specialties=["BTC", "ETH"],
                best_market=MarketCondition.BEAR,
                current_weight=0.10
            )
        }
    
    def update_market_condition(self, indicators: Dict[str, Any]) -> MarketCondition:
        """
        根据指标更新市场状况
        
        Args:
            indicators: 市场指标
                - trend_strength: -1到1
                - volatility: 波动率
                - fear_greed: 恐惧贪婪指数
                - volume_trend: 成交量趋势
        """
        trend = indicators.get('trend_strength', 0)
        volatility = indicators.get('volatility', 'normal')
        fear_greed = indicators.get('fear_greed', 50)
        volume = indicators.get('volume_trend', 'normal')
        
        # 判断市场状况
        if volatility == 'extreme':
            if fear_greed < 20:
                new_market = MarketCondition.CRASH
            else:
                new_market = MarketCondition.VOLATILE
        elif trend > 0.7:
            if fear_greed > 80:
                new_market = MarketCondition.STRONG_BULL
            else:
                new_market = MarketCondition.BULL
        elif trend < -0.7:
            if fear_greed < 20:
                new_market = MarketCondition.STRONG_BEAR
            else:
                new_market = MarketCondition.BEAR
        elif -0.3 <= trend <= 0.3:
            if trend > 0:
                new_market = MarketCondition.SIDEWAYS_UP
            elif trend < 0:
                new_market = MarketCondition.SIDEWAYS_DOWN
            else:
                new_market = MarketCondition.SIDEWAYS
        else:
            new_market = MarketCondition.SIDEWAYS
        
        # 记录变化
        if new_market != self.current_market:
            logger.info(f"Market condition changed: {self.current_market.value} -> {new_market.value}")
            self.current_market = new_market
            self._record_weight_change("market_change", self.get_current_weights())
        
        return new_market
    
    def get_strategy_weight(self, strategy: StrategyType) -> float:
        """获取特定策略的当前权重"""
        weights = self.strategy_weights.get(self.current_market, {})
        return weights.get(strategy, 0.1)
    
    def get_trader_weight(self, trader_name: str) -> float:
        """获取特定交易员的权重"""
        profile = self.trader_profiles.get(trader_name)
        if not profile:
            return 0.05  # 未知交易员的默认权重
        
        # 根据市场环境调整权重
        market_bonus = 1.0
        if profile.best_market == self.current_market:
            market_bonus = 1.2  # 在最佳市场环境下增加20%权重
        
        # 根据近期表现调整
        performance_bonus = 1.0
        if profile.recent_winrate > profile.overall_winrate:
            performance_bonus = 1.1  # 近期表现好增加10%
        elif profile.recent_winrate < profile.overall_winrate * 0.8:
            performance_bonus = 0.9  # 近期表现差减少10%
        
        adjusted_weight = profile.current_weight * market_bonus * performance_bonus
        
        # 限制在合理范围内
        return max(self.min_weight, min(self.max_weight, adjusted_weight))
    
    def update_strategy_performance(self,
                                   strategy: StrategyType,
                                   win_rate: float,
                                   avg_return: float,
                                   trades: int):
        """更新策略表现"""
        performance = StrategyPerformance(
            strategy_type=strategy,
            market_condition=self.current_market,
            win_rate=win_rate,
            avg_return=avg_return,
            sharpe_ratio=self._calculate_sharpe(avg_return, 0),  # 简化计算
            max_drawdown=0,  # 需要另外计算
            trade_count=trades,
            last_updated=datetime.now()
        )
        
        self.performance_history[strategy].append(performance)
        
        # 自适应调整权重
        self._adapt_weights(strategy, win_rate, avg_return)
    
    def update_trader_performance(self,
                                 trader_name: str,
                                 trade_result: bool,
                                 pnl: float):
        """更新交易员表现"""
        profile = self.trader_profiles.get(trader_name)
        if not profile:
            return
        
        # 更新历史记录
        profile.performance_history.append({
            'timestamp': datetime.now(),
            'success': trade_result,
            'pnl': pnl
        })
        
        # 更新近期胜率
        recent_trades = list(profile.performance_history)[-30:]
        if recent_trades:
            wins = sum(1 for t in recent_trades if t['success'])
            profile.recent_winrate = wins / len(recent_trades)
        
        # 自适应调整权重
        self._adapt_trader_weight(trader_name)
    
    def _adapt_weights(self, strategy: StrategyType, win_rate: float, avg_return: float):
        """自适应调整策略权重"""
        current_weights = self.strategy_weights[self.current_market]
        current_weight = current_weights.get(strategy, 0.1)
        
        # 计算性能分数
        performance_score = win_rate * 0.6 + min(avg_return / 20, 1.0) * 0.4
        
        # 计算权重调整
        if performance_score > 0.6:  # 表现好
            adjustment = self.adaptation_rate * (performance_score - 0.6)
            new_weight = current_weight * (1 + adjustment)
        elif performance_score < 0.4:  # 表现差
            adjustment = self.adaptation_rate * (0.4 - performance_score)
            new_weight = current_weight * (1 - adjustment)
        else:
            new_weight = current_weight
        
        # 限制权重范围
        new_weight = max(self.min_weight, min(self.max_weight, new_weight))
        
        # 更新权重
        current_weights[strategy] = new_weight
        
        # 归一化权重
        self._normalize_weights(current_weights)
        
        logger.debug(f"Adjusted {strategy.value} weight: {current_weight:.3f} -> {new_weight:.3f}")
    
    def _adapt_trader_weight(self, trader_name: str):
        """自适应调整交易员权重"""
        profile = self.trader_profiles.get(trader_name)
        if not profile:
            return
        
        # 计算性能分数
        performance_score = (
            profile.recent_winrate * 0.5 +
            min(profile.avg_pnl / 30, 1.0) * 0.3 +
            min(profile.total_trades / 1000, 1.0) * 0.2
        )
        
        # 调整权重
        if performance_score > 0.6:
            adjustment = self.adaptation_rate * (performance_score - 0.6)
            profile.current_weight *= (1 + adjustment)
        elif performance_score < 0.4:
            adjustment = self.adaptation_rate * (0.4 - performance_score)
            profile.current_weight *= (1 - adjustment)
        
        # 限制范围
        profile.current_weight = max(0.05, min(0.4, profile.current_weight))
        
        # 归一化所有交易员权重
        self._normalize_trader_weights()
    
    def _normalize_weights(self, weights: Dict):
        """归一化权重使总和为1"""
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] /= total
    
    def _normalize_trader_weights(self):
        """归一化交易员权重"""
        total = sum(p.current_weight for p in self.trader_profiles.values())
        if total > 0:
            for profile in self.trader_profiles.values():
                profile.current_weight /= total
    
    def _calculate_sharpe(self, returns: float, std: float) -> float:
        """计算夏普比率（简化版）"""
        risk_free_rate = 0.02  # 2%无风险利率
        if std == 0:
            std = 0.15  # 默认标准差
        return (returns - risk_free_rate) / std if std > 0 else 0
    
    def _record_weight_change(self, reason: str, weights: Dict):
        """记录权重变化"""
        self.weight_history.append({
            'timestamp': datetime.now(),
            'reason': reason,
            'market': self.current_market.value,
            'weights': weights.copy()
        })
    
    def get_current_weights(self) -> Dict[str, Any]:
        """获取当前所有权重"""
        return {
            'market_condition': self.current_market.value,
            'strategies': self.strategy_weights.get(self.current_market, {}),
            'traders': {
                name: profile.current_weight 
                for name, profile in self.trader_profiles.items()
            },
            'signals': self.signal_weights
        }
    
    def calculate_composite_score(self, signals: Dict[str, float]) -> float:
        """
        计算综合评分
        
        Args:
            signals: 各种信号的评分(0-1)
                - technical_score
                - sentiment_score
                - trader_score
                - onchain_score
                
        Returns:
            综合评分(0-1)
        """
        composite = 0.0
        
        # 应用信号权重
        for signal_type, weight in self.signal_weights.items():
            score = signals.get(f"{signal_type}_score", 0.5)
            composite += score * weight
        
        return min(1.0, max(0.0, composite))
    
    def recommend_position_size(self, 
                               confidence: float,
                               risk_level: str,
                               account_balance: float) -> float:
        """
        推荐仓位大小
        
        Args:
            confidence: 置信度(0-10)
            risk_level: 风险等级
            account_balance: 账户余额
            
        Returns:
            推荐仓位(USDT)
        """
        # 基础仓位比例
        base_ratio = 0.1  # 10%
        
        # 根据置信度调整
        confidence_multiplier = confidence / 10
        
        # 根据风险等级调整
        risk_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'extreme': 0.3  # 极高风险反而要降低仓位
        }
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        # 根据市场状况调整
        market_multipliers = {
            MarketCondition.STRONG_BULL: 1.2,
            MarketCondition.BULL: 1.1,
            MarketCondition.SIDEWAYS: 0.8,
            MarketCondition.BEAR: 0.6,
            MarketCondition.STRONG_BEAR: 0.4,
            MarketCondition.CRASH: 0.2,
            MarketCondition.VOLATILE: 0.7
        }
        market_multiplier = market_multipliers.get(self.current_market, 1.0)
        
        # 计算最终仓位
        position_ratio = base_ratio * confidence_multiplier * risk_multiplier * market_multiplier
        
        # 限制最大仓位
        max_position_ratio = 0.3  # 最多30%
        position_ratio = min(position_ratio, max_position_ratio)
        
        return account_balance * position_ratio
    
    def get_strategy_recommendation(self) -> Dict[str, Any]:
        """获取策略推荐"""
        current_weights = self.strategy_weights.get(self.current_market, {})
        
        # 排序策略
        sorted_strategies = sorted(
            current_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'market_condition': self.current_market.value,
            'primary_strategy': sorted_strategies[0][0].value if sorted_strategies else None,
            'secondary_strategy': sorted_strategies[1][0].value if len(sorted_strategies) > 1 else None,
            'avoid_strategies': [s[0].value for s in sorted_strategies if s[1] < 0.1],
            'top_traders': sorted(
                self.trader_profiles.items(),
                key=lambda x: x[1].current_weight,
                reverse=True
            )[:3]
        }