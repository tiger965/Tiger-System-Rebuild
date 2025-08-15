"""
决策跟踪记录系统 - 记录和评估AI决策准确率
多维度评分：准确性、时机、风险控制
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import statistics

logger = logging.getLogger(__name__)


class DecisionResult(Enum):
    """决策结果"""
    WIN = "win"          # 盈利
    LOSS = "loss"        # 亏损
    PENDING = "pending"  # 待定
    TIMEOUT = "timeout"  # 超时


class TriggerSource(Enum):
    """触发来源"""
    TECHNICAL = "technical"     # 技术指标
    MARKET = "market"          # 市场情绪
    SOCIAL = "social"          # 社交媒体
    NEWS = "news"              # 新闻事件
    WHALE = "whale"            # 巨鲸动向
    PATTERN = "pattern"        # 模式识别


@dataclass
class DecisionRecord:
    """决策记录"""
    decision_id: str
    timestamp: str
    symbol: str
    action: str  # "buy", "sell", "hold"
    confidence: float  # 置信度
    reasoning: str  # 决策理由
    trigger_source: TriggerSource
    
    # 交易相关
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None
    
    # 结果相关
    result: DecisionResult = DecisionResult.PENDING
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    
    # 评分相关
    accuracy_score: Optional[float] = None  # 准确性评分
    timing_score: Optional[float] = None    # 时机评分
    risk_score: Optional[float] = None      # 风险控制评分
    overall_score: Optional[float] = None   # 总体评分


class DecisionTracker:
    """
    决策跟踪记录系统
    功能：
    1. 记录每个AI决策
    2. 跟踪决策结果
    3. 多维度评分
    4. 学习和优化
    """
    
    def __init__(self):
        """初始化跟踪器"""
        # 待定决策（尚未有结果）
        self.pending_decisions: Dict[str, DecisionRecord] = {}
        
        # 已完成决策
        self.completed_decisions: List[DecisionRecord] = []
        
        # 准确率统计
        self.accuracy_stats = {
            "total_decisions": 0,
            "correct_predictions": 0,
            "accuracy_rate": 0.0,
            "by_trigger_source": {},
            "by_symbol": {},
            "by_time_period": {}
        }
        
        # 评分权重
        self.scoring_weights = {
            "accuracy": 0.4,    # 准确性权重
            "timing": 0.3,      # 时机权重
            "risk": 0.3         # 风险控制权重
        }
        
        # 学习数据
        self.pattern_performance = {}  # 不同模式的表现
        self.market_condition_performance = {}  # 不同市场条件下的表现
        
        logger.info("决策跟踪系统初始化完成")
    
    def record_decision(self, decision_data: Dict) -> str:
        """
        记录新的决策
        
        Args:
            decision_data: 决策数据字典
                {
                    "symbol": "BTCUSDT",
                    "action": "buy",
                    "confidence": 0.8,
                    "reasoning": "技术突破",
                    "trigger_source": "technical",
                    "entry_price": 50000,
                    "target_price": 55000,
                    "stop_loss": 47500,
                    "position_size": 0.02
                }
        
        Returns:
            decision_id: 决策ID
        """
        # 生成唯一决策ID
        decision_id = self._generate_decision_id(decision_data)
        
        # 创建决策记录
        record = DecisionRecord(
            decision_id=decision_id,
            timestamp=datetime.now().isoformat(),
            symbol=decision_data["symbol"],
            action=decision_data["action"],
            confidence=decision_data["confidence"],
            reasoning=decision_data.get("reasoning", ""),
            trigger_source=TriggerSource(decision_data.get("trigger_source", "technical")),
            entry_price=decision_data["entry_price"],
            target_price=decision_data.get("target_price"),
            stop_loss=decision_data.get("stop_loss"),
            position_size=decision_data.get("position_size")
        )
        
        # 存储到待定决策
        self.pending_decisions[decision_id] = record
        
        logger.info(f"记录决策: {record.action} {record.symbol} @{record.entry_price:.4f} "
                   f"(置信度: {record.confidence:.2f})")
        
        return decision_id
    
    def update_result(self, decision_id: str, result_data: Dict):
        """
        更新决策结果
        
        Args:
            result_data: 结果数据
                {
                    "result": "win",  # "win", "loss", "timeout"
                    "exit_price": 55000,
                    "exit_time": "2025-08-15T10:00:00",
                    "pnl": 1000,
                    "pnl_pct": 0.1
                }
        """
        if decision_id not in self.pending_decisions:
            logger.warning(f"决策ID不存在: {decision_id}")
            return
        
        record = self.pending_decisions[decision_id]
        
        # 更新结果信息
        record.result = DecisionResult(result_data["result"])
        record.exit_price = result_data.get("exit_price")
        record.exit_time = result_data.get("exit_time", datetime.now().isoformat())
        record.pnl = result_data.get("pnl", 0)
        record.pnl_pct = result_data.get("pnl_pct", 0)
        
        # 计算评分
        self._calculate_scores(record)
        
        # 移动到已完成列表
        self.completed_decisions.append(record)
        del self.pending_decisions[decision_id]
        
        # 更新统计
        self._update_accuracy_stats(record)
        
        logger.info(f"更新决策结果: {decision_id} -> {record.result.value} "
                   f"(总评分: {record.overall_score:.2f})")
    
    def _generate_decision_id(self, decision_data: Dict) -> str:
        """生成唯一决策ID"""
        data_str = f"{decision_data['symbol']}_{decision_data['action']}_{datetime.now().isoformat()}"
        return "DEC_" + hashlib.md5(data_str.encode()).hexdigest()[:8]
    
    def _calculate_scores(self, record: DecisionRecord):
        """计算多维度评分"""
        # 1. 准确性评分
        if record.result in [DecisionResult.WIN, DecisionResult.LOSS]:
            if record.pnl_pct is not None:
                # 基于盈亏百分比的准确性评分
                if record.pnl_pct > 0:
                    record.accuracy_score = min(1.0, 0.5 + record.pnl_pct * 2)  # 盈利时评分较高
                else:
                    record.accuracy_score = max(0.0, 0.5 + record.pnl_pct * 2)  # 亏损时评分较低
            else:
                record.accuracy_score = 1.0 if record.result == DecisionResult.WIN else 0.0
        else:
            record.accuracy_score = 0.3  # 超时给予较低评分
        
        # 2. 时机评分
        record.timing_score = self._calculate_timing_score(record)
        
        # 3. 风险控制评分
        record.risk_score = self._calculate_risk_score(record)
        
        # 4. 总体评分
        record.overall_score = (
            record.accuracy_score * self.scoring_weights["accuracy"] +
            record.timing_score * self.scoring_weights["timing"] +
            record.risk_score * self.scoring_weights["risk"]
        )
    
    def _calculate_timing_score(self, record: DecisionRecord) -> float:
        """计算时机评分"""
        if not record.exit_time:
            return 0.5
        
        # 计算持仓时间
        start_time = datetime.fromisoformat(record.timestamp)
        end_time = datetime.fromisoformat(record.exit_time)
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        # 理想持仓时间：4-24小时
        if 4 <= duration_hours <= 24:
            timing_score = 1.0
        elif duration_hours < 4:
            timing_score = 0.6 + (duration_hours / 4) * 0.4  # 过快
        else:
            timing_score = max(0.2, 1.0 - (duration_hours - 24) / 72)  # 过慢
        
        # 如果是盈利且时间合理，加分
        if record.result == DecisionResult.WIN and 2 <= duration_hours <= 48:
            timing_score = min(1.0, timing_score + 0.1)
        
        return timing_score
    
    def _calculate_risk_score(self, record: DecisionRecord) -> float:
        """计算风险控制评分"""
        risk_score = 0.5  # 基础分
        
        # 检查是否设置了止损
        if record.stop_loss is not None:
            risk_score += 0.2
            
            # 计算风险回报比
            if record.target_price is not None:
                if record.action == "buy":
                    profit_potential = record.target_price - record.entry_price
                    loss_potential = record.entry_price - record.stop_loss
                elif record.action == "sell":
                    profit_potential = record.entry_price - record.target_price
                    loss_potential = record.stop_loss - record.entry_price
                else:
                    profit_potential = loss_potential = 1
                
                if loss_potential > 0:
                    risk_reward_ratio = profit_potential / loss_potential
                    if risk_reward_ratio >= 2:
                        risk_score += 0.2  # 好的风险回报比
                    elif risk_reward_ratio >= 1.5:
                        risk_score += 0.1
        
        # 检查仓位大小
        if record.position_size is not None:
            if record.position_size <= 0.05:  # 单仓<=5%
                risk_score += 0.1
        
        # 基于实际结果调整
        if record.result == DecisionResult.LOSS and record.pnl_pct is not None:
            if record.pnl_pct > -0.05:  # 亏损控制在5%以内
                risk_score += 0.1
            elif record.pnl_pct < -0.1:  # 亏损超过10%
                risk_score -= 0.2
        
        return max(0.0, min(1.0, risk_score))
    
    def _update_accuracy_stats(self, record: DecisionRecord):
        """更新准确率统计"""
        self.accuracy_stats["total_decisions"] += 1
        
        if record.result == DecisionResult.WIN:
            self.accuracy_stats["correct_predictions"] += 1
        
        # 计算总体准确率
        total = self.accuracy_stats["total_decisions"]
        correct = self.accuracy_stats["correct_predictions"]
        self.accuracy_stats["accuracy_rate"] = correct / total if total > 0 else 0
        
        # 按触发源统计
        source = record.trigger_source.value
        if source not in self.accuracy_stats["by_trigger_source"]:
            self.accuracy_stats["by_trigger_source"][source] = {"total": 0, "correct": 0}
        
        self.accuracy_stats["by_trigger_source"][source]["total"] += 1
        if record.result == DecisionResult.WIN:
            self.accuracy_stats["by_trigger_source"][source]["correct"] += 1
        
        # 按币种统计
        symbol = record.symbol
        if symbol not in self.accuracy_stats["by_symbol"]:
            self.accuracy_stats["by_symbol"][symbol] = {"total": 0, "correct": 0}
        
        self.accuracy_stats["by_symbol"][symbol]["total"] += 1
        if record.result == DecisionResult.WIN:
            self.accuracy_stats["by_symbol"][symbol]["correct"] += 1
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.completed_decisions:
            return {"message": "暂无已完成的决策记录"}
        
        # 基础统计
        total_decisions = len(self.completed_decisions)
        winning_decisions = sum(1 for d in self.completed_decisions if d.result == DecisionResult.WIN)
        losing_decisions = sum(1 for d in self.completed_decisions if d.result == DecisionResult.LOSS)
        timeout_decisions = sum(1 for d in self.completed_decisions if d.result == DecisionResult.TIMEOUT)
        
        # 评分统计
        overall_scores = [d.overall_score for d in self.completed_decisions if d.overall_score is not None]
        accuracy_scores = [d.accuracy_score for d in self.completed_decisions if d.accuracy_score is not None]
        timing_scores = [d.timing_score for d in self.completed_decisions if d.timing_score is not None]
        risk_scores = [d.risk_score for d in self.completed_decisions if d.risk_score is not None]
        
        # 盈亏统计
        pnl_values = [d.pnl for d in self.completed_decisions if d.pnl is not None]
        pnl_pct_values = [d.pnl_pct for d in self.completed_decisions if d.pnl_pct is not None]
        
        return {
            "summary": {
                "total_decisions": total_decisions,
                "pending_decisions": len(self.pending_decisions),
                "win_rate": winning_decisions / total_decisions * 100,
                "loss_rate": losing_decisions / total_decisions * 100,
                "timeout_rate": timeout_decisions / total_decisions * 100
            },
            "scores": {
                "average_overall": statistics.mean(overall_scores) if overall_scores else 0,
                "average_accuracy": statistics.mean(accuracy_scores) if accuracy_scores else 0,
                "average_timing": statistics.mean(timing_scores) if timing_scores else 0,
                "average_risk": statistics.mean(risk_scores) if risk_scores else 0,
                "score_distribution": self._get_score_distribution(overall_scores)
            },
            "financial": {
                "total_pnl": sum(pnl_values) if pnl_values else 0,
                "average_pnl_pct": statistics.mean(pnl_pct_values) if pnl_pct_values else 0,
                "max_win": max(pnl_pct_values) if pnl_pct_values else 0,
                "max_loss": min(pnl_pct_values) if pnl_pct_values else 0,
                "sharpe_ratio": self._calculate_sharpe_ratio(pnl_pct_values)
            },
            "by_trigger_source": self._get_performance_by_trigger_source(),
            "recent_trend": self._analyze_recent_trend()
        }
    
    def _get_score_distribution(self, scores: List[float]) -> Dict:
        """获取评分分布"""
        if not scores:
            return {}
        
        ranges = {
            "excellent": (0.8, 1.0),
            "good": (0.6, 0.8),
            "average": (0.4, 0.6),
            "poor": (0.0, 0.4)
        }
        
        distribution = {}
        for category, (min_score, max_score) in ranges.items():
            count = sum(1 for score in scores if min_score <= score < max_score)
            distribution[category] = {
                "count": count,
                "percentage": count / len(scores) * 100
            }
        
        return distribution
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """计算夏普比率"""
        if len(returns) < 2:
            return 0
        
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        return avg_return / std_return if std_return > 0 else 0
    
    def _get_performance_by_trigger_source(self) -> Dict:
        """按触发源分析性能"""
        performance = {}
        
        for record in self.completed_decisions:
            source = record.trigger_source.value
            if source not in performance:
                performance[source] = {
                    "total": 0,
                    "wins": 0,
                    "losses": 0,
                    "timeouts": 0,
                    "avg_score": 0,
                    "total_pnl_pct": 0
                }
            
            perf = performance[source]
            perf["total"] += 1
            
            if record.result == DecisionResult.WIN:
                perf["wins"] += 1
            elif record.result == DecisionResult.LOSS:
                perf["losses"] += 1
            elif record.result == DecisionResult.TIMEOUT:
                perf["timeouts"] += 1
            
            if record.overall_score is not None:
                perf["avg_score"] = (perf["avg_score"] * (perf["total"] - 1) + record.overall_score) / perf["total"]
            
            if record.pnl_pct is not None:
                perf["total_pnl_pct"] += record.pnl_pct
        
        # 计算胜率
        for source, perf in performance.items():
            perf["win_rate"] = perf["wins"] / perf["total"] * 100 if perf["total"] > 0 else 0
        
        return performance
    
    def _analyze_recent_trend(self, days: int = 7) -> Dict:
        """分析最近趋势"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_decisions = [
            d for d in self.completed_decisions
            if datetime.fromisoformat(d.timestamp) > cutoff_date
        ]
        
        if not recent_decisions:
            return {"message": f"最近{days}天无决策记录"}
        
        recent_wins = sum(1 for d in recent_decisions if d.result == DecisionResult.WIN)
        recent_scores = [d.overall_score for d in recent_decisions if d.overall_score is not None]
        
        return {
            "period_days": days,
            "total_decisions": len(recent_decisions),
            "win_rate": recent_wins / len(recent_decisions) * 100,
            "average_score": statistics.mean(recent_scores) if recent_scores else 0,
            "trend": "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
        }
    
    def get_decision_details(self, decision_id: str) -> Optional[Dict]:
        """获取决策详情"""
        # 检查待定决策
        if decision_id in self.pending_decisions:
            record = self.pending_decisions[decision_id]
            return self._record_to_dict(record)
        
        # 检查已完成决策
        for record in self.completed_decisions:
            if record.decision_id == decision_id:
                return self._record_to_dict(record)
        
        return None
    
    def _record_to_dict(self, record: DecisionRecord) -> Dict:
        """将记录转换为字典"""
        return {
            "decision_id": record.decision_id,
            "timestamp": record.timestamp,
            "symbol": record.symbol,
            "action": record.action,
            "confidence": record.confidence,
            "reasoning": record.reasoning,
            "trigger_source": record.trigger_source.value,
            "entry_price": record.entry_price,
            "target_price": record.target_price,
            "stop_loss": record.stop_loss,
            "position_size": record.position_size,
            "result": record.result.value,
            "exit_price": record.exit_price,
            "exit_time": record.exit_time,
            "pnl": record.pnl,
            "pnl_pct": record.pnl_pct,
            "scores": {
                "accuracy": record.accuracy_score,
                "timing": record.timing_score,
                "risk": record.risk_score,
                "overall": record.overall_score
            }
        }
    
    def adjust_scoring_weights(self, accuracy: float = None, timing: float = None, risk: float = None):
        """调整评分权重"""
        if accuracy is not None:
            self.scoring_weights["accuracy"] = max(0.0, min(1.0, accuracy))
        if timing is not None:
            self.scoring_weights["timing"] = max(0.0, min(1.0, timing))
        if risk is not None:
            self.scoring_weights["risk"] = max(0.0, min(1.0, risk))
        
        # 标准化权重
        total_weight = sum(self.scoring_weights.values())
        if total_weight > 0:
            for key in self.scoring_weights:
                self.scoring_weights[key] /= total_weight
        
        logger.info(f"评分权重已调整: {self.scoring_weights}")
    
    def export_decisions(self, include_pending: bool = False) -> List[Dict]:
        """导出决策记录"""
        records = []
        
        # 已完成的决策
        for record in self.completed_decisions:
            records.append(self._record_to_dict(record))
        
        # 待定的决策（可选）
        if include_pending:
            for record in self.pending_decisions.values():
                records.append(self._record_to_dict(record))
        
        return records
    
    def cleanup_old_records(self, days: int = 30):
        """清理旧记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 清理已完成的决策
        original_count = len(self.completed_decisions)
        self.completed_decisions = [
            d for d in self.completed_decisions
            if datetime.fromisoformat(d.timestamp) > cutoff_date
        ]
        
        cleaned_count = original_count - len(self.completed_decisions)
        
        logger.info(f"清理了{cleaned_count}条超过{days}天的决策记录")