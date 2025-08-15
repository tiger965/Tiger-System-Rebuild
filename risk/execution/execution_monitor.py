"""
Tiger系统 - 执行监控系统
窗口：7号  
功能：监控交易执行质量，跟踪绩效表现
作者：Window-7 Risk Control Officer
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """仓位状态枚举"""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    STOPPED = "stopped"


@dataclass
class ExecutionRecord:
    """执行记录"""
    suggestion_id: str
    symbol: str
    suggested_price: float
    suggested_time: datetime
    actual_price: Optional[float] = None
    actual_time: Optional[datetime] = None
    quantity: float = 0
    status: PositionStatus = PositionStatus.PENDING
    slippage: float = 0
    execution_delay: float = 0  # 秒
    
    def calculate_slippage(self):
        """计算滑点"""
        if self.actual_price and self.suggested_price:
            self.slippage = (self.actual_price - self.suggested_price) / self.suggested_price
            
    def calculate_delay(self):
        """计算执行延迟"""
        if self.actual_time and self.suggested_time:
            self.execution_delay = (self.actual_time - self.suggested_time).total_seconds()


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0
    win_rate: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    profit_factor: float = 0
    sharpe_ratio: float = 0
    max_drawdown: float = 0
    recovery_time: int = 0  # 天数
    
    def calculate_metrics(self, trades: List[Dict]):
        """计算绩效指标"""
        if not trades:
            return
            
        self.total_trades = len(trades)
        
        # 计算胜率
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] < 0]
        
        self.winning_trades = len(wins)
        self.losing_trades = len(losses)
        
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
            
        # 计算平均盈亏
        if wins:
            self.avg_win = sum(t["pnl"] for t in wins) / len(wins)
        if losses:
            self.avg_loss = abs(sum(t["pnl"] for t in losses) / len(losses))
            
        # 计算盈亏比
        if self.avg_loss > 0:
            self.profit_factor = self.avg_win / self.avg_loss
            
        # 计算总盈亏
        self.total_pnl = sum(t["pnl"] for t in trades)
        
        # 计算夏普比率
        self.sharpe_ratio = self._calculate_sharpe_ratio(trades)
        
        # 计算最大回撤
        self.max_drawdown = self._calculate_max_drawdown(trades)
        
        # 计算恢复时间
        self.recovery_time = self._calculate_recovery_time(trades)
    
    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """计算夏普比率"""
        if len(trades) < 2:
            return 0
            
        returns = [t["pnl"] / t.get("capital", 10000) for t in trades]
        
        if not returns:
            return 0
            
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0
        
        if std_return == 0:
            return 0
            
        # 假设无风险利率为0
        sharpe = (avg_return * 252) / (std_return * (252 ** 0.5))  # 年化
        
        return sharpe
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0
            
        cumulative_pnl = []
        cum_sum = 0
        
        for trade in trades:
            cum_sum += trade["pnl"]
            cumulative_pnl.append(cum_sum)
            
        if not cumulative_pnl:
            return 0
            
        peak = cumulative_pnl[0]
        max_dd = 0
        
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
            
        return max_dd
    
    def _calculate_recovery_time(self, trades: List[Dict]) -> int:
        """计算回撤恢复时间"""
        if not trades:
            return 0
            
        # 简化计算：找到最大回撤后恢复到新高的时间
        cumulative_pnl = []
        cum_sum = 0
        
        for i, trade in enumerate(trades):
            cum_sum += trade["pnl"]
            cumulative_pnl.append((i, cum_sum, trade.get("time", datetime.now())))
            
        if not cumulative_pnl:
            return 0
            
        peak_idx = 0
        peak_value = cumulative_pnl[0][1]
        max_dd_idx = 0
        recovery_days = 0
        
        for i, (idx, value, time) in enumerate(cumulative_pnl):
            if value > peak_value:
                peak_value = value
                peak_idx = i
                
                # 计算从最低点恢复的时间
                if max_dd_idx > 0:
                    recovery_time = cumulative_pnl[i][2] - cumulative_pnl[max_dd_idx][2]
                    recovery_days = max(recovery_days, recovery_time.days)
                    
            elif value < peak_value:
                max_dd_idx = i
                
        return recovery_days


class ExecutionMonitor:
    """执行监控系统 - 跟踪每一个建议的执行情况"""
    
    def __init__(self):
        self.active_suggestions = {}  # 活跃的建议
        self.execution_history = []  # 执行历史
        self.performance_metrics = PerformanceMetrics()
        self.slippage_stats = {
            "total_slippage": 0,
            "avg_slippage": 0,
            "max_slippage": 0,
            "slippage_cost": 0
        }
        
    def track_suggestion(self, suggestion: Dict) -> str:
        """
        跟踪新的交易建议
        
        Args:
            suggestion: 交易建议
            
        Returns:
            建议ID
        """
        suggestion_id = f"{suggestion['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution_record = ExecutionRecord(
            suggestion_id=suggestion_id,
            symbol=suggestion["symbol"],
            suggested_price=suggestion["price"],
            suggested_time=datetime.now(),
            quantity=suggestion.get("quantity", 0),
            status=PositionStatus.PENDING
        )
        
        self.active_suggestions[suggestion_id] = execution_record
        
        logger.info(f"跟踪新建议: {suggestion_id} - {suggestion['symbol']} @ {suggestion['price']}")
        
        return suggestion_id
    
    def update_execution(self, suggestion_id: str, execution_data: Dict) -> bool:
        """
        更新执行状态
        
        Args:
            suggestion_id: 建议ID
            execution_data: 执行数据
            
        Returns:
            是否成功
        """
        if suggestion_id not in self.active_suggestions:
            logger.warning(f"建议ID不存在: {suggestion_id}")
            return False
            
        record = self.active_suggestions[suggestion_id]
        
        # 更新执行信息
        record.actual_price = execution_data.get("price")
        record.actual_time = datetime.now()
        record.quantity = execution_data.get("quantity", record.quantity)
        
        # 更新状态
        status_str = execution_data.get("status", "pending")
        try:
            record.status = PositionStatus(status_str)
        except ValueError:
            logger.error(f"无效状态: {status_str}")
            record.status = PositionStatus.PENDING
            
        # 计算滑点和延迟
        record.calculate_slippage()
        record.calculate_delay()
        
        # 更新滑点统计
        self._update_slippage_stats(record)
        
        # 如果已完成，移到历史记录
        if record.status in [PositionStatus.FILLED, PositionStatus.STOPPED, PositionStatus.CANCELLED]:
            self.execution_history.append(record)
            del self.active_suggestions[suggestion_id]
            logger.info(f"执行完成: {suggestion_id} - 状态: {record.status.value}")
            
        return True
    
    def calculate_performance(self, trades: List[Dict]) -> Dict:
        """
        计算绩效指标
        
        Args:
            trades: 交易列表
            
        Returns:
            绩效报告
        """
        self.performance_metrics.calculate_metrics(trades)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_trades": self.performance_metrics.total_trades,
                "win_rate": f"{self.performance_metrics.win_rate:.2%}",
                "winning_trades": self.performance_metrics.winning_trades,
                "losing_trades": self.performance_metrics.losing_trades,
                "total_pnl": self.performance_metrics.total_pnl,
                "avg_win": self.performance_metrics.avg_win,
                "avg_loss": self.performance_metrics.avg_loss,
                "profit_factor": round(self.performance_metrics.profit_factor, 2),
                "sharpe_ratio": round(self.performance_metrics.sharpe_ratio, 2),
                "max_drawdown": f"{self.performance_metrics.max_drawdown:.2%}",
                "recovery_days": self.performance_metrics.recovery_time
            },
            "rating": self._get_performance_rating()
        }
    
    def get_execution_quality_report(self) -> Dict:
        """
        获取执行质量报告
        
        Returns:
            质量报告
        """
        if not self.execution_history:
            return {
                "timestamp": datetime.now().isoformat(),
                "message": "暂无执行记录"
            }
            
        # 计算执行统计
        total_executions = len(self.execution_history)
        filled_executions = sum(1 for r in self.execution_history if r.status == PositionStatus.FILLED)
        cancelled_executions = sum(1 for r in self.execution_history if r.status == PositionStatus.CANCELLED)
        stopped_executions = sum(1 for r in self.execution_history if r.status == PositionStatus.STOPPED)
        
        # 计算平均延迟
        delays = [r.execution_delay for r in self.execution_history if r.execution_delay > 0]
        avg_delay = statistics.mean(delays) if delays else 0
        
        # 计算填充率
        fill_rate = filled_executions / total_executions if total_executions > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "execution_stats": {
                "total": total_executions,
                "filled": filled_executions,
                "cancelled": cancelled_executions,
                "stopped": stopped_executions,
                "fill_rate": f"{fill_rate:.2%}"
            },
            "slippage_stats": {
                "avg_slippage": f"{self.slippage_stats['avg_slippage']:.4%}",
                "max_slippage": f"{self.slippage_stats['max_slippage']:.4%}",
                "total_cost": self.slippage_stats["slippage_cost"]
            },
            "timing_stats": {
                "avg_delay": f"{avg_delay:.2f}秒",
                "max_delay": f"{max(delays) if delays else 0:.2f}秒"
            },
            "quality_score": self._calculate_quality_score()
        }
    
    def get_position_status_summary(self) -> Dict:
        """
        获取仓位状态汇总
        
        Returns:
            状态汇总
        """
        status_count = {}
        for record in self.active_suggestions.values():
            status = record.status.value
            status_count[status] = status_count.get(status, 0) + 1
            
        positions = []
        for record in self.active_suggestions.values():
            positions.append({
                "id": record.suggestion_id,
                "symbol": record.symbol,
                "status": record.status.value,
                "suggested_price": record.suggested_price,
                "actual_price": record.actual_price,
                "slippage": f"{record.slippage:.4%}" if record.slippage else "N/A",
                "delay": f"{record.execution_delay:.1f}s" if record.execution_delay else "N/A"
            })
            
        return {
            "timestamp": datetime.now().isoformat(),
            "active_positions": len(self.active_suggestions),
            "status_distribution": status_count,
            "positions": positions
        }
    
    def check_execution_anomalies(self) -> List[Dict]:
        """
        检查执行异常
        
        Returns:
            异常列表
        """
        anomalies = []
        
        # 检查长时间未执行的建议
        for suggestion_id, record in self.active_suggestions.items():
            time_pending = (datetime.now() - record.suggested_time).total_seconds()
            
            if record.status == PositionStatus.PENDING and time_pending > 300:  # 5分钟
                anomalies.append({
                    "type": "EXECUTION_TIMEOUT",
                    "suggestion_id": suggestion_id,
                    "symbol": record.symbol,
                    "time_pending": f"{time_pending:.0f}秒",
                    "severity": "HIGH"
                })
                
        # 检查异常滑点
        for record in self.execution_history[-10:]:  # 最近10笔
            if abs(record.slippage) > 0.01:  # 滑点超过1%
                anomalies.append({
                    "type": "EXCESSIVE_SLIPPAGE",
                    "suggestion_id": record.suggestion_id,
                    "symbol": record.symbol,
                    "slippage": f"{record.slippage:.4%}",
                    "severity": "MEDIUM"
                })
                
        # 检查连续止损
        recent_stops = sum(1 for r in self.execution_history[-5:] 
                          if r.status == PositionStatus.STOPPED)
        if recent_stops >= 3:
            anomalies.append({
                "type": "CONSECUTIVE_STOPS",
                "count": recent_stops,
                "severity": "HIGH",
                "action": "Review risk parameters"
            })
            
        return anomalies
    
    def _update_slippage_stats(self, record: ExecutionRecord):
        """更新滑点统计"""
        if record.slippage == 0:
            return
            
        # 更新总滑点
        self.slippage_stats["total_slippage"] += abs(record.slippage)
        
        # 更新最大滑点
        self.slippage_stats["max_slippage"] = max(
            self.slippage_stats["max_slippage"],
            abs(record.slippage)
        )
        
        # 计算滑点成本
        if record.actual_price and record.quantity:
            cost = abs(record.slippage) * record.actual_price * record.quantity
            self.slippage_stats["slippage_cost"] += cost
            
        # 更新平均滑点
        executed_count = len(self.execution_history) + 1
        if executed_count > 0:
            self.slippage_stats["avg_slippage"] = (
                self.slippage_stats["total_slippage"] / executed_count
            )
    
    def _get_performance_rating(self) -> str:
        """获取绩效评级"""
        score = 0
        
        # 胜率评分
        if self.performance_metrics.win_rate > 0.6:
            score += 3
        elif self.performance_metrics.win_rate > 0.5:
            score += 2
        elif self.performance_metrics.win_rate > 0.4:
            score += 1
            
        # 盈亏比评分
        if self.performance_metrics.profit_factor > 2:
            score += 3
        elif self.performance_metrics.profit_factor > 1.5:
            score += 2
        elif self.performance_metrics.profit_factor > 1:
            score += 1
            
        # 夏普比率评分
        if self.performance_metrics.sharpe_ratio > 2:
            score += 3
        elif self.performance_metrics.sharpe_ratio > 1:
            score += 2
        elif self.performance_metrics.sharpe_ratio > 0:
            score += 1
            
        # 评级
        if score >= 8:
            return "EXCELLENT"
        elif score >= 6:
            return "GOOD"
        elif score >= 4:
            return "FAIR"
        elif score >= 2:
            return "POOR"
        else:
            return "CRITICAL"
    
    def _calculate_quality_score(self) -> int:
        """计算执行质量分数"""
        score = 100
        
        # 滑点扣分
        if self.slippage_stats["avg_slippage"] > 0.005:  # 0.5%
            score -= 10
        if self.slippage_stats["max_slippage"] > 0.02:  # 2%
            score -= 15
            
        # 填充率加分
        if self.execution_history:
            fill_rate = sum(1 for r in self.execution_history if r.status == PositionStatus.FILLED) / len(self.execution_history)
            if fill_rate > 0.9:
                score += 10
            elif fill_rate < 0.7:
                score -= 10
                
        return max(0, min(100, score))


if __name__ == "__main__":
    # 测试代码
    em = ExecutionMonitor()
    
    # 跟踪建议
    suggestion = {
        "symbol": "BTC",
        "price": 70000,
        "quantity": 0.1,
        "action": "BUY"
    }
    suggestion_id = em.track_suggestion(suggestion)
    
    # 更新执行
    execution = {
        "price": 70050,
        "quantity": 0.1,
        "status": "filled"
    }
    em.update_execution(suggestion_id, execution)
    
    # 模拟交易数据
    test_trades = [
        {"pnl": 1000, "capital": 10000},
        {"pnl": -500, "capital": 10000},
        {"pnl": 800, "capital": 10000},
        {"pnl": -200, "capital": 10000},
        {"pnl": 1500, "capital": 10000}
    ]
    
    # 计算绩效
    performance = em.calculate_performance(test_trades)
    print(f"绩效报告: {json.dumps(performance, indent=2)}")
    
    # 执行质量报告
    quality_report = em.get_execution_quality_report()
    print(f"执行质量: {json.dumps(quality_report, indent=2)}")
    
    # 检查异常
    anomalies = em.check_execution_anomalies()
    print(f"执行异常: {anomalies}")