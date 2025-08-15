"""
上下文管理系统 - AI的记忆和知识库
维护对话历史、市场背景、交易经验等关键信息
确保AI决策具有连贯性和学习能力
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class MarketCycle(Enum):
    """市场周期"""
    BULL = "bull"          # 牛市
    BEAR = "bear"          # 熊市
    SIDEWAYS = "sideways"  # 震荡市
    RECOVERY = "recovery"  # 恢复期
    CRASH = "crash"        # 崩盘


class EmotionState(Enum):
    """市场情绪状态"""
    EXTREME_FEAR = "extreme_fear"      # 极度恐惧
    FEAR = "fear"                      # 恐惧
    NEUTRAL = "neutral"                # 中性
    GREED = "greed"                    # 贪婪
    EXTREME_GREED = "extreme_greed"    # 极度贪婪


@dataclass
class Conversation:
    """对话记录"""
    timestamp: datetime
    symbol: str
    prompt_type: str
    question: str
    answer: str
    decision: Optional[str] = None
    confidence: float = 0.0
    outcome: Optional[str] = None  # 事后验证结果


@dataclass
class TradingHistory:
    """交易历史记录"""
    timestamp: datetime
    symbol: str
    action: str  # LONG/SHORT/CLOSE
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    decision_basis: str = ""
    success: Optional[bool] = None


@dataclass
class MarketEvent:
    """市场重大事件"""
    timestamp: datetime
    event_type: str
    description: str
    impact_level: int  # 1-10
    affected_coins: List[str]
    market_reaction: str


@dataclass
class KnowledgeItem:
    """知识库条目"""
    category: str
    subcategory: str
    title: str
    content: str
    source: str
    confidence: float
    last_updated: datetime
    usage_count: int = 0


class ContextManager:
    """上下文管理器主类"""
    
    def __init__(self, max_conversations: int = 100, max_history_days: int = 30):
        # 对话历史管理
        self.conversations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        self.all_conversations = deque(maxlen=max_conversations)
        
        # 交易历史
        self.trading_history: List[TradingHistory] = []
        self.max_history_days = max_history_days
        
        # 市场背景
        self.market_state = {
            'cycle': MarketCycle.SIDEWAYS,
            'emotion': EmotionState.NEUTRAL,
            'volatility': 'normal',
            'trend_strength': 0.5,
            'key_levels': {},
            'dominant_narrative': ""
        }
        
        # 重大事件记录
        self.market_events = deque(maxlen=50)
        
        # 知识库
        self.knowledge_base = self._initialize_knowledge_base()
        
        # 个人偏好和风险配置
        self.trader_profile = {
            'risk_tolerance': 'moderate',  # low/moderate/high
            'preferred_timeframe': '4H',
            'max_position_size': 0.3,
            'preferred_coins': ['BTC', 'ETH'],
            'avoided_coins': [],
            'success_strategies': [],
            'failed_strategies': []
        }
        
        # 性能追踪
        self.performance_metrics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'avg_confidence': 0.0,
            'best_performing_strategy': None,
            'worst_performing_strategy': None
        }
        
        # 缓存的分析结果
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5分钟
    
    def _initialize_knowledge_base(self) -> Dict[str, List[KnowledgeItem]]:
        """初始化知识库"""
        knowledge_base = {
            'technical_analysis': [],
            'fundamental_analysis': [],
            'market_psychology': [],
            'risk_management': [],
            'trading_strategies': [],
            'historical_patterns': []
        }
        
        # 添加基础知识
        base_knowledge = [
            KnowledgeItem(
                category='technical_analysis',
                subcategory='indicators',
                title='RSI Interpretation',
                content='RSI < 30 indicates oversold, > 70 indicates overbought. Divergences are strong signals.',
                source='Classic TA',
                confidence=0.9,
                last_updated=datetime.now()
            ),
            KnowledgeItem(
                category='risk_management',
                subcategory='position_sizing',
                title='Kelly Criterion',
                content='Optimal position size = (p*b - q)/b, where p=win probability, q=loss probability, b=win/loss ratio',
                source='Mathematical Finance',
                confidence=0.85,
                last_updated=datetime.now()
            ),
            KnowledgeItem(
                category='market_psychology',
                subcategory='sentiment',
                title='Contrarian Indicators',
                content='Extreme fear often marks bottoms, extreme greed marks tops. Best opportunities at sentiment extremes.',
                source='Behavioral Finance',
                confidence=0.8,
                last_updated=datetime.now()
            )
        ]
        
        for item in base_knowledge:
            knowledge_base[item.category].append(item)
        
        return knowledge_base
    
    def add_conversation(self, 
                        symbol: str,
                        prompt_type: str,
                        question: str,
                        answer: str,
                        decision: Optional[str] = None,
                        confidence: float = 0.0):
        """添加对话记录"""
        conversation = Conversation(
            timestamp=datetime.now(),
            symbol=symbol,
            prompt_type=prompt_type,
            question=question[:500],  # 限制长度
            answer=answer[:2000],     # 限制长度
            decision=decision,
            confidence=confidence
        )
        
        # 按币种存储
        self.conversations[symbol].append(conversation)
        
        # 总记录
        self.all_conversations.append(conversation)
        
        # 更新统计
        self.performance_metrics['total_decisions'] += 1
        self.performance_metrics['avg_confidence'] = (
            (self.performance_metrics['avg_confidence'] * (self.performance_metrics['total_decisions'] - 1) + confidence)
            / self.performance_metrics['total_decisions']
        )
        
        logger.debug(f"Conversation added for {symbol}: {prompt_type}")
    
    def get_recent_conversations(self, 
                                 symbol: Optional[str] = None,
                                 limit: int = 5) -> List[Conversation]:
        """获取最近的对话"""
        if symbol:
            return list(self.conversations[symbol])[-limit:]
        else:
            return list(self.all_conversations)[-limit:]
    
    def add_trading_record(self,
                          symbol: str,
                          action: str,
                          entry_price: float,
                          decision_basis: str = ""):
        """添加交易记录"""
        record = TradingHistory(
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            entry_price=entry_price,
            decision_basis=decision_basis
        )
        
        self.trading_history.append(record)
        
        # 清理旧记录
        cutoff = datetime.now() - timedelta(days=self.max_history_days)
        self.trading_history = [
            r for r in self.trading_history if r.timestamp > cutoff
        ]
        
        logger.info(f"Trading record added: {symbol} {action} @ {entry_price}")
    
    def close_trading_record(self,
                           symbol: str,
                           exit_price: float) -> Optional[TradingHistory]:
        """关闭交易记录"""
        # 找到最近的未关闭记录
        for record in reversed(self.trading_history):
            if record.symbol == symbol and record.exit_price is None:
                record.exit_price = exit_price
                
                # 计算盈亏
                if record.action == "LONG":
                    record.pnl_percentage = (exit_price - record.entry_price) / record.entry_price * 100
                elif record.action == "SHORT":
                    record.pnl_percentage = (record.entry_price - exit_price) / record.entry_price * 100
                
                record.success = record.pnl_percentage > 0 if record.pnl_percentage else None
                
                # 更新统计
                if record.success:
                    self.performance_metrics['successful_decisions'] += 1
                
                logger.info(f"Trade closed: {symbol} PnL: {record.pnl_percentage:.2f}%")
                return record
        
        return None
    
    def update_market_state(self, updates: Dict[str, Any]):
        """更新市场状态"""
        for key, value in updates.items():
            if key in self.market_state:
                old_value = self.market_state[key]
                self.market_state[key] = value
                
                # 记录重要变化
                if key == 'cycle' and old_value != value:
                    self.add_market_event(
                        event_type='cycle_change',
                        description=f"Market cycle changed from {old_value.value} to {value.value}",
                        impact_level=8,
                        affected_coins=['ALL']
                    )
        
        logger.debug(f"Market state updated: {updates}")
    
    def add_market_event(self,
                        event_type: str,
                        description: str,
                        impact_level: int,
                        affected_coins: List[str],
                        market_reaction: str = ""):
        """添加市场事件"""
        event = MarketEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            impact_level=min(10, max(1, impact_level)),
            affected_coins=affected_coins,
            market_reaction=market_reaction
        )
        
        self.market_events.append(event)
        
        logger.info(f"Market event recorded: {event_type} - Impact: {impact_level}/10")
    
    def get_recent_events(self, hours: int = 24) -> List[MarketEvent]:
        """获取最近的市场事件"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.market_events if e.timestamp > cutoff]
    
    def add_knowledge(self,
                     category: str,
                     subcategory: str,
                     title: str,
                     content: str,
                     source: str = "AI Analysis",
                     confidence: float = 0.7):
        """添加知识条目"""
        if category not in self.knowledge_base:
            self.knowledge_base[category] = []
        
        # 检查是否已存在
        for item in self.knowledge_base[category]:
            if item.title == title:
                # 更新现有条目
                item.content = content
                item.last_updated = datetime.now()
                item.usage_count += 1
                return
        
        # 添加新条目
        knowledge = KnowledgeItem(
            category=category,
            subcategory=subcategory,
            title=title,
            content=content,
            source=source,
            confidence=confidence,
            last_updated=datetime.now()
        )
        
        self.knowledge_base[category].append(knowledge)
        
        logger.debug(f"Knowledge added: {category}/{title}")
    
    def search_knowledge(self, 
                        query: str,
                        category: Optional[str] = None) -> List[KnowledgeItem]:
        """搜索知识库"""
        results = []
        query_lower = query.lower()
        
        categories = [category] if category else self.knowledge_base.keys()
        
        for cat in categories:
            for item in self.knowledge_base.get(cat, []):
                if (query_lower in item.title.lower() or 
                    query_lower in item.content.lower() or
                    query_lower in item.subcategory.lower()):
                    results.append(item)
                    item.usage_count += 1
        
        # 按置信度和使用次数排序
        results.sort(key=lambda x: (x.confidence, x.usage_count), reverse=True)
        
        return results[:10]  # 返回前10个结果
    
    def get_trading_stats(self, symbol: Optional[str] = None) -> Dict:
        """获取交易统计"""
        if symbol:
            records = [r for r in self.trading_history if r.symbol == symbol]
        else:
            records = self.trading_history
        
        if not records:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'best_trade': None,
                'worst_trade': None
            }
        
        completed = [r for r in records if r.pnl_percentage is not None]
        if not completed:
            return {
                'total_trades': len(records),
                'win_rate': 0,
                'avg_pnl': 0,
                'best_trade': None,
                'worst_trade': None
            }
        
        wins = [r for r in completed if r.pnl_percentage > 0]
        
        return {
            'total_trades': len(completed),
            'win_rate': len(wins) / len(completed) * 100,
            'avg_pnl': np.mean([r.pnl_percentage for r in completed]),
            'best_trade': max(completed, key=lambda x: x.pnl_percentage),
            'worst_trade': min(completed, key=lambda x: x.pnl_percentage),
            'current_streak': self._calculate_streak(completed)
        }
    
    def _calculate_streak(self, records: List[TradingHistory]) -> int:
        """计算连胜/连败"""
        if not records:
            return 0
        
        streak = 0
        last_success = records[-1].success
        
        for record in reversed(records):
            if record.success == last_success:
                streak += 1 if last_success else -1
            else:
                break
        
        return streak
    
    def build_context(self, 
                     symbol: str,
                     include_history: bool = True,
                     include_market: bool = True,
                     include_knowledge: bool = True) -> Dict[str, Any]:
        """
        构建完整的上下文
        
        Args:
            symbol: 交易对
            include_history: 是否包含历史对话
            include_market: 是否包含市场背景
            include_knowledge: 是否包含相关知识
            
        Returns:
            完整的上下文字典
        """
        context = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加历史对话
        if include_history:
            recent_convs = self.get_recent_conversations(symbol, limit=3)
            context['recent_conversations'] = [
                {
                    'time': conv.timestamp.isoformat(),
                    'type': conv.prompt_type,
                    'decision': conv.decision,
                    'confidence': conv.confidence
                }
                for conv in recent_convs
            ]
        
        # 添加交易历史
        trading_stats = self.get_trading_stats(symbol)
        context['trading_performance'] = trading_stats
        
        # 添加市场背景
        if include_market:
            context['market_state'] = {
                'cycle': self.market_state['cycle'].value,
                'emotion': self.market_state['emotion'].value,
                'volatility': self.market_state['volatility'],
                'trend_strength': self.market_state['trend_strength']
            }
            
            # 最近事件
            recent_events = self.get_recent_events(24)
            if recent_events:
                context['recent_events'] = [
                    f"{e.event_type}: {e.description}"
                    for e in recent_events[:3]
                ]
        
        # 添加相关知识
        if include_knowledge:
            # 根据市场状态搜索相关知识
            if self.market_state['cycle'] == MarketCycle.BEAR:
                knowledge = self.search_knowledge("bear market", "trading_strategies")
            elif self.market_state['cycle'] == MarketCycle.BULL:
                knowledge = self.search_knowledge("bull market", "trading_strategies")
            else:
                knowledge = self.search_knowledge("sideways", "trading_strategies")
            
            if knowledge:
                context['relevant_knowledge'] = [
                    {'title': k.title, 'content': k.content}
                    for k in knowledge[:2]
                ]
        
        # 添加个人偏好
        context['trader_profile'] = self.trader_profile
        
        return context
    
    def save_state(self, filepath: str):
        """保存状态到文件"""
        state = {
            'conversations': dict(self.conversations),
            'trading_history': self.trading_history,
            'market_state': self.market_state,
            'market_events': list(self.market_events),
            'knowledge_base': self.knowledge_base,
            'trader_profile': self.trader_profile,
            'performance_metrics': self.performance_metrics
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"Context state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """从文件加载状态"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            
            self.conversations = defaultdict(lambda: deque(maxlen=10), state['conversations'])
            self.trading_history = state['trading_history']
            self.market_state = state['market_state']
            self.market_events = deque(state['market_events'], maxlen=50)
            self.knowledge_base = state['knowledge_base']
            self.trader_profile = state['trader_profile']
            self.performance_metrics = state['performance_metrics']
            
            logger.info(f"Context state loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load state: {str(e)}")
    
    def get_summary(self) -> Dict:
        """获取上下文摘要"""
        return {
            'total_conversations': len(self.all_conversations),
            'unique_symbols': len(self.conversations),
            'total_trades': len(self.trading_history),
            'market_cycle': self.market_state['cycle'].value,
            'market_emotion': self.market_state['emotion'].value,
            'recent_events': len(self.get_recent_events(24)),
            'knowledge_items': sum(len(items) for items in self.knowledge_base.values()),
            'performance': {
                'win_rate': self.get_trading_stats()['win_rate'],
                'avg_confidence': self.performance_metrics['avg_confidence']
            }
        }