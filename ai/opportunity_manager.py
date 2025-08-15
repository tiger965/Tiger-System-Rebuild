"""
10币种精准管理系统 - 严格控制交易数量
最多同时管理10个币种：用户5个 + 模拟5个
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AllocationMode(Enum):
    """分配模式"""
    USER = "user"           # 用户真实交易
    SIMULATION = "simulation"  # 虚拟模拟交易


@dataclass
class OpportunitySignal:
    """机会信号数据结构"""
    symbol: str
    signal_type: str  # "buy", "sell", "hold"
    quality_score: float  # 0-1 质量评分
    confidence: float  # 置信度
    entry_price: float
    target_price: float
    stop_loss: float
    source: str  # 信号来源
    timestamp: str
    risk_reward_ratio: float
    timeframe: str
    volume_score: float  # 成交量评分
    technical_score: float  # 技术指标评分
    sentiment_score: float  # 情绪评分


@dataclass
class ManagedPosition:
    """管理中的持仓"""
    symbol: str
    mode: AllocationMode
    signal: OpportunitySignal
    start_time: str
    status: str  # "active", "completed", "stopped"
    current_price: float
    unrealized_pnl: float
    priority_rank: int  # 优先级排名 1-10


class OpportunityManager:
    """
    10币种精准管理系统
    核心规则：永远不超过10个币种
    """
    
    # 硬性限制
    MAX_TOTAL_COINS = 10  # 总计最多10个
    MAX_USER_COINS = 5    # 用户真实交易最多5个
    MAX_SIM_COINS = 5     # 虚拟模拟最多5个
    
    def __init__(self):
        """初始化管理器"""
        # 当前管理的持仓
        self.managed_positions: Dict[str, ManagedPosition] = {}
        
        # 分配统计
        self.allocation_stats = {
            "user_count": 0,
            "simulation_count": 0,
            "total_count": 0,
            "rejected_count": 0  # 被拒绝的信号数量
        }
        
        # 质量阈值
        self.quality_thresholds = {
            "user_min": 0.7,      # 用户交易最低质量要求
            "simulation_min": 0.5,  # 模拟交易最低质量要求
            "replacement_min": 0.8  # 替换现有持仓的最低质量
        }
        
        # 历史记录
        self.allocation_history = []
        self.replacement_history = []
        
        logger.info("10币种精准管理系统初始化完成")
    
    def process_opportunities(self, signals: List[OpportunitySignal]) -> Dict[str, List[OpportunitySignal]]:
        """
        处理机会信号，分配到用户和模拟
        
        Returns:
            {
                "user": [...],      # 分配给用户的信号
                "simulation": [...], # 分配给模拟的信号
                "rejected": [...]   # 被拒绝的信号
            }
        """
        logger.info(f"处理{len(signals)}个机会信号")
        
        # 过滤和排序信号
        qualified_signals = self._filter_and_rank_signals(signals)
        
        # 检查是否有空位
        available_slots = self._get_available_slots()
        
        # 分配信号
        allocation = self._allocate_signals(qualified_signals, available_slots)
        
        # 实际创建持仓
        self._create_positions_from_allocation(allocation)
        
        # 处理替换逻辑
        self._handle_replacements(allocation["rejected"])
        
        # 更新统计
        self._update_allocation_stats(allocation)
        
        # 记录历史
        self._record_allocation_history(allocation)
        
        logger.info(f"分配结果: 用户{len(allocation['user'])}个, "
                   f"模拟{len(allocation['simulation'])}个, "
                   f"拒绝{len(allocation['rejected'])}个")
        
        return allocation
    
    def _filter_and_rank_signals(self, signals: List[OpportunitySignal]) -> List[OpportunitySignal]:
        """过滤和排序信号"""
        # 过滤掉已存在的币种
        filtered = []
        for signal in signals:
            if signal.symbol not in self.managed_positions:
                # 检查最低质量要求
                if signal.quality_score >= self.quality_thresholds["simulation_min"]:
                    filtered.append(signal)
                else:
                    logger.debug(f"信号质量过低，拒绝: {signal.symbol} ({signal.quality_score:.2f})")
        
        # 按质量评分排序
        filtered.sort(key=lambda x: x.quality_score, reverse=True)
        
        return filtered
    
    def _get_available_slots(self) -> Dict[str, int]:
        """获取可用槽位"""
        current_user = sum(1 for pos in self.managed_positions.values() 
                          if pos.mode == AllocationMode.USER)
        current_sim = sum(1 for pos in self.managed_positions.values() 
                         if pos.mode == AllocationMode.SIMULATION)
        
        return {
            "user": max(0, self.MAX_USER_COINS - current_user),
            "simulation": max(0, self.MAX_SIM_COINS - current_sim),
            "total": max(0, self.MAX_TOTAL_COINS - len(self.managed_positions))
        }
    
    def _allocate_signals(self, signals: List[OpportunitySignal], 
                         available_slots: Dict[str, int]) -> Dict[str, List[OpportunitySignal]]:
        """分配信号到不同模式"""
        allocation = {
            "user": [],
            "simulation": [],
            "rejected": []
        }
        
        for signal in signals:
            # 检查总槽位
            if len(allocation["user"]) + len(allocation["simulation"]) >= available_slots["total"]:
                allocation["rejected"].append(signal)
                continue
            
            # 高质量信号优先分配给用户
            if (signal.quality_score >= self.quality_thresholds["user_min"] and 
                len(allocation["user"]) < available_slots["user"]):
                allocation["user"].append(signal)
            
            # 其他信号分配给模拟
            elif len(allocation["simulation"]) < available_slots["simulation"]:
                allocation["simulation"].append(signal)
            
            # 无可用槽位
            else:
                allocation["rejected"].append(signal)
        
        return allocation
    
    def _create_positions_from_allocation(self, allocation: Dict[str, List[OpportunitySignal]]):
        """从分配结果创建实际持仓"""
        # 创建用户持仓
        for signal in allocation["user"]:
            self._add_position(signal, AllocationMode.USER)
        
        # 创建模拟持仓
        for signal in allocation["simulation"]:
            self._add_position(signal, AllocationMode.SIMULATION)
    
    def _handle_replacements(self, rejected_signals: List[OpportunitySignal]):
        """处理高质量信号的替换逻辑"""
        for signal in rejected_signals:
            # 只有特优信号才考虑替换
            if signal.quality_score >= self.quality_thresholds["replacement_min"]:
                success = self._try_replace_position(signal)
                if success:
                    logger.info(f"高质量信号替换成功: {signal.symbol} "
                               f"(质量: {signal.quality_score:.2f})")
    
    def _try_replace_position(self, new_signal: OpportunitySignal) -> bool:
        """尝试用新信号替换现有最低质量持仓"""
        if not self.managed_positions:
            return False
        
        # 找到质量最低的持仓
        lowest_position = min(
            self.managed_positions.values(),
            key=lambda pos: pos.signal.quality_score
        )
        
        # 检查是否值得替换
        if new_signal.quality_score > lowest_position.signal.quality_score + 0.1:  # 至少高10%
            # 执行替换
            old_symbol = lowest_position.symbol
            self._remove_position(old_symbol)
            self._add_position(new_signal, lowest_position.mode)
            
            # 记录替换历史
            self.replacement_history.append({
                "timestamp": datetime.now().isoformat(),
                "replaced_symbol": old_symbol,
                "replaced_quality": lowest_position.signal.quality_score,
                "new_symbol": new_signal.symbol,
                "new_quality": new_signal.quality_score,
                "improvement": new_signal.quality_score - lowest_position.signal.quality_score
            })
            
            return True
        
        return False
    
    def add_position(self, signal: OpportunitySignal, mode: AllocationMode) -> bool:
        """添加新持仓"""
        # 检查容量限制
        if not self._can_add_position(mode):
            logger.warning(f"无法添加持仓: {signal.symbol}, 模式: {mode.value}, 已达上限")
            return False
        
        return self._add_position(signal, mode)
    
    def _add_position(self, signal: OpportunitySignal, mode: AllocationMode) -> bool:
        """内部添加持仓方法"""
        position = ManagedPosition(
            symbol=signal.symbol,
            mode=mode,
            signal=signal,
            start_time=datetime.now().isoformat(),
            status="active",
            current_price=signal.entry_price,
            unrealized_pnl=0.0,
            priority_rank=self._calculate_priority_rank(signal)
        )
        
        self.managed_positions[signal.symbol] = position
        self._update_allocation_stats()
        
        logger.info(f"添加持仓: {signal.symbol} ({mode.value}) "
                   f"质量: {signal.quality_score:.2f}")
        return True
    
    def _can_add_position(self, mode: AllocationMode) -> bool:
        """检查是否可以添加持仓"""
        current_counts = self._count_positions_by_mode()
        
        if mode == AllocationMode.USER:
            return current_counts["user"] < self.MAX_USER_COINS
        elif mode == AllocationMode.SIMULATION:
            return current_counts["simulation"] < self.MAX_SIM_COINS
        
        return False
    
    def _count_positions_by_mode(self) -> Dict[str, int]:
        """统计不同模式的持仓数量"""
        counts = {"user": 0, "simulation": 0}
        
        for position in self.managed_positions.values():
            if position.mode == AllocationMode.USER:
                counts["user"] += 1
            elif position.mode == AllocationMode.SIMULATION:
                counts["simulation"] += 1
        
        return counts
    
    def remove_position(self, symbol: str, reason: str = "completed") -> bool:
        """移除持仓"""
        return self._remove_position(symbol, reason)
    
    def _remove_position(self, symbol: str, reason: str = "completed") -> bool:
        """内部移除持仓方法"""
        if symbol not in self.managed_positions:
            logger.warning(f"尝试移除不存在的持仓: {symbol}")
            return False
        
        position = self.managed_positions[symbol]
        position.status = reason
        
        del self.managed_positions[symbol]
        self._update_allocation_stats()
        
        logger.info(f"移除持仓: {symbol} 原因: {reason}")
        return True
    
    def update_position_price(self, symbol: str, current_price: float):
        """更新持仓当前价格"""
        if symbol in self.managed_positions:
            position = self.managed_positions[symbol]
            position.current_price = current_price
            
            # 计算未实现盈亏
            entry_price = position.signal.entry_price
            if position.signal.signal_type == "buy":
                position.unrealized_pnl = (current_price - entry_price) / entry_price
            elif position.signal.signal_type == "sell":
                position.unrealized_pnl = (entry_price - current_price) / entry_price
    
    def _calculate_priority_rank(self, signal: OpportunitySignal) -> int:
        """计算优先级排名"""
        # 综合质量评分计算排名
        score = (signal.quality_score * 0.4 + 
                signal.confidence * 0.3 + 
                signal.risk_reward_ratio * 0.2 / 5 +  # 假设最大风险回报比为5
                signal.volume_score * 0.1)
        
        # 转换为1-10的排名
        rank = max(1, min(10, int(score * 10)))
        return rank
    
    def _update_allocation_stats(self, allocation: Dict[str, List[OpportunitySignal]] = None):
        """更新分配统计"""
        counts = self._count_positions_by_mode()
        
        self.allocation_stats.update({
            "user_count": counts["user"],
            "simulation_count": counts["simulation"],
            "total_count": len(self.managed_positions)
        })
        
        if allocation:
            self.allocation_stats["rejected_count"] += len(allocation.get("rejected", []))
    
    def _record_allocation_history(self, allocation: Dict[str, List[OpportunitySignal]]):
        """记录分配历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "allocated": {
                "user": [s.symbol for s in allocation["user"]],
                "simulation": [s.symbol for s in allocation["simulation"]],
                "rejected": [s.symbol for s in allocation["rejected"]]
            },
            "counts": self.allocation_stats.copy()
        }
        
        self.allocation_history.append(record)
        
        # 限制历史记录数量
        if len(self.allocation_history) > 1000:
            self.allocation_history = self.allocation_history[-1000:]
    
    def get_portfolio_status(self) -> Dict:
        """获取投资组合状态"""
        user_positions = []
        sim_positions = []
        
        for position in self.managed_positions.values():
            pos_info = {
                "symbol": position.symbol,
                "quality": position.signal.quality_score,
                "confidence": position.signal.confidence,
                "unrealized_pnl": position.unrealized_pnl,
                "priority_rank": position.priority_rank,
                "duration": (datetime.now() - datetime.fromisoformat(position.start_time)).total_seconds() / 3600,  # 小时
                "status": position.status
            }
            
            if position.mode == AllocationMode.USER:
                user_positions.append(pos_info)
            else:
                sim_positions.append(pos_info)
        
        return {
            "summary": {
                "total_positions": len(self.managed_positions),
                "user_positions": len(user_positions),
                "simulation_positions": len(sim_positions),
                "capacity_used": f"{len(self.managed_positions)}/{self.MAX_TOTAL_COINS}",
                "user_capacity": f"{len(user_positions)}/{self.MAX_USER_COINS}",
                "sim_capacity": f"{len(sim_positions)}/{self.MAX_SIM_COINS}"
            },
            "user_portfolio": sorted(user_positions, key=lambda x: x["priority_rank"]),
            "simulation_portfolio": sorted(sim_positions, key=lambda x: x["priority_rank"]),
            "stats": self.allocation_stats,
            "recent_replacements": self.replacement_history[-5:] if self.replacement_history else []
        }
    
    def is_portfolio_full(self) -> bool:
        """检查投资组合是否已满"""
        return len(self.managed_positions) >= self.MAX_TOTAL_COINS
    
    def get_lowest_quality_position(self) -> Optional[ManagedPosition]:
        """获取质量最低的持仓"""
        if not self.managed_positions:
            return None
        
        return min(self.managed_positions.values(), 
                  key=lambda pos: pos.signal.quality_score)
    
    def adjust_quality_thresholds(self, user_min: float = None, 
                                 sim_min: float = None, 
                                 replacement_min: float = None):
        """调整质量阈值"""
        if user_min is not None:
            self.quality_thresholds["user_min"] = max(0.0, min(1.0, user_min))
        if sim_min is not None:
            self.quality_thresholds["simulation_min"] = max(0.0, min(1.0, sim_min))
        if replacement_min is not None:
            self.quality_thresholds["replacement_min"] = max(0.0, min(1.0, replacement_min))
        
        logger.info(f"质量阈值已调整: {self.quality_thresholds}")
    
    def get_allocation_efficiency(self) -> Dict:
        """获取分配效率统计"""
        if not self.allocation_history:
            return {"efficiency": 0, "message": "无历史数据"}
        
        total_processed = sum(
            len(record["allocated"]["user"]) + 
            len(record["allocated"]["simulation"]) + 
            len(record["allocated"]["rejected"])
            for record in self.allocation_history
        )
        
        total_allocated = sum(
            len(record["allocated"]["user"]) + 
            len(record["allocated"]["simulation"])
            for record in self.allocation_history
        )
        
        efficiency = total_allocated / total_processed if total_processed > 0 else 0
        
        return {
            "efficiency": efficiency,
            "total_processed": total_processed,
            "total_allocated": total_allocated,
            "rejection_rate": 1 - efficiency,
            "average_quality": self._calculate_average_quality()
        }
    
    def _calculate_average_quality(self) -> float:
        """计算平均质量评分"""
        if not self.managed_positions:
            return 0.0
        
        total_quality = sum(pos.signal.quality_score for pos in self.managed_positions.values())
        return total_quality / len(self.managed_positions)