"""
虚拟交易模拟器 - 纯算术计算，不涉及真实资金
风险控制：单仓5%，总敞口25%，24小时强制平仓
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """交易状态"""
    ACTIVE = "active"       # 持仓中
    WIN = "win"            # 盈利平仓
    LOSS = "loss"          # 亏损平仓
    TIMEOUT = "timeout"    # 超时平仓


@dataclass
class VirtualPosition:
    """虚拟持仓"""
    symbol: str
    signal_type: str  # "buy", "sell"
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float  # 持仓比例
    entry_time: datetime
    status: TradeStatus
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    duration_hours: float = 0.0


@dataclass
class PerformanceReport:
    """性能报告"""
    current_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    max_drawdown: float
    sharpe_ratio: float
    active_positions: int
    average_hold_time: float  # 小时


class SimpleSimulator:
    """
    虚拟交易模拟器
    核心特性：
    1. 纯算术计算，不接触真实资金
    2. 严格风险控制
    3. 24小时强制平仓
    4. 完整的性能统计
    """
    
    def __init__(self, initial_balance: float = 100000):
        """初始化模拟器"""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # 风险控制参数
        self.max_position_size = 0.05    # 单仓最大5%
        self.max_total_exposure = 0.25   # 总敞口最大25%
        self.max_hold_hours = 24         # 最长持仓24小时
        
        # 当前持仓
        self.positions: Dict[str, VirtualPosition] = {}
        
        # 历史交易
        self.completed_trades: List[VirtualPosition] = []
        
        # 性能统计
        self.performance_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "timeout_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "peak_balance": initial_balance
        }
        
        logger.info(f"虚拟交易模拟器初始化完成，初始资金: ${initial_balance:,.2f}")
    
    def virtual_buy(self, symbol: str, entry_price: float, target_price: float, 
                   stop_loss: float, position_size_pct: float) -> bool:
        """
        虚拟买入
        
        Args:
            symbol: 交易对
            entry_price: 入场价格
            target_price: 目标价格
            stop_loss: 止损价格
            position_size_pct: 仓位大小百分比
        """
        return self._open_position("buy", symbol, entry_price, target_price, 
                                  stop_loss, position_size_pct)
    
    def virtual_sell(self, symbol: str, entry_price: float, target_price: float,
                    stop_loss: float, position_size_pct: float) -> bool:
        """虚拟卖出"""
        return self._open_position("sell", symbol, entry_price, target_price,
                                  stop_loss, position_size_pct)
    
    def _open_position(self, signal_type: str, symbol: str, entry_price: float,
                      target_price: float, stop_loss: float, position_size_pct: float) -> bool:
        """开仓逻辑"""
        # 检查是否已有该币种的持仓
        if symbol in self.positions:
            logger.warning(f"币种 {symbol} 已有持仓，跳过")
            return False
        
        # 风险控制：单仓大小限制
        if position_size_pct > self.max_position_size:
            position_size_pct = self.max_position_size
            logger.info(f"仓位大小调整到最大限制: {self.max_position_size*100}%")
        
        # 风险控制：总敞口限制
        current_exposure = sum(pos.position_size for pos in self.positions.values())
        if current_exposure + position_size_pct > self.max_total_exposure:
            available_exposure = self.max_total_exposure - current_exposure
            if available_exposure <= 0:
                logger.warning(f"总敞口已达上限 {self.max_total_exposure*100}%，无法开新仓")
                return False
            position_size_pct = available_exposure
            logger.info(f"仓位大小调整为可用敞口: {position_size_pct*100:.1f}%")
        
        # 创建虚拟持仓
        position = VirtualPosition(
            symbol=symbol,
            signal_type=signal_type,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=position_size_pct,
            entry_time=datetime.now(),
            status=TradeStatus.ACTIVE
        )
        
        self.positions[symbol] = position
        
        logger.info(f"虚拟{signal_type}: {symbol} @{entry_price:.4f}, "
                   f"目标: {target_price:.4f}, 止损: {stop_loss:.4f}, "
                   f"仓位: {position_size_pct*100:.1f}%")
        
        return True
    
    def check_exits(self, current_prices: Dict[str, float]):
        """检查出场条件"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            should_exit, reason = self._should_exit_position(position, current_price)
            
            if should_exit:
                positions_to_close.append((symbol, current_price, reason))
        
        # 执行平仓
        for symbol, exit_price, reason in positions_to_close:
            self._close_position(symbol, exit_price, reason)
    
    def _should_exit_position(self, position: VirtualPosition, current_price: float) -> Tuple[bool, str]:
        """判断是否应该平仓"""
        # 检查超时
        duration = datetime.now() - position.entry_time
        if duration.total_seconds() / 3600 > self.max_hold_hours:
            return True, "timeout"
        
        if position.signal_type == "buy":
            # 买入信号：价格上涨到目标或下跌到止损
            if current_price >= position.target_price:
                return True, "target_hit"
            elif current_price <= position.stop_loss:
                return True, "stop_loss_hit"
        
        elif position.signal_type == "sell":
            # 卖出信号：价格下跌到目标或上涨到止损
            if current_price <= position.target_price:
                return True, "target_hit"
            elif current_price >= position.stop_loss:
                return True, "stop_loss_hit"
        
        return False, ""
    
    def _close_position(self, symbol: str, exit_price: float, reason: str):
        """平仓"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        position.duration_hours = (position.exit_time - position.entry_time).total_seconds() / 3600
        
        # 计算盈亏
        if position.signal_type == "buy":
            position.pnl_pct = (exit_price - position.entry_price) / position.entry_price
        elif position.signal_type == "sell":
            position.pnl_pct = (position.entry_price - exit_price) / position.entry_price
        
        # 计算实际盈亏金额
        position.pnl = self.current_balance * position.position_size * position.pnl_pct
        
        # 更新余额
        self.current_balance += position.pnl
        
        # 设置状态
        if reason == "target_hit":
            position.status = TradeStatus.WIN
        elif reason == "stop_loss_hit":
            position.status = TradeStatus.LOSS
        elif reason == "timeout":
            position.status = TradeStatus.TIMEOUT
        
        # 记录到历史交易
        self.completed_trades.append(position)
        
        # 移除当前持仓
        del self.positions[symbol]
        
        # 更新统计
        self._update_performance_stats(position)
        
        logger.info(f"平仓 {symbol}: {position.signal_type} @{exit_price:.4f}, "
                   f"盈亏: {position.pnl_pct*100:+.2f}% (${position.pnl:+.2f}), "
                   f"原因: {reason}, 余额: ${self.current_balance:,.2f}")
    
    def _update_performance_stats(self, position: VirtualPosition):
        """更新性能统计"""
        self.performance_stats["total_trades"] += 1
        
        if position.status == TradeStatus.WIN:
            self.performance_stats["winning_trades"] += 1
        elif position.status == TradeStatus.LOSS:
            self.performance_stats["losing_trades"] += 1
        elif position.status == TradeStatus.TIMEOUT:
            self.performance_stats["timeout_trades"] += 1
        
        self.performance_stats["total_pnl"] += position.pnl
        
        # 更新最大回撤
        if self.current_balance > self.performance_stats["peak_balance"]:
            self.performance_stats["peak_balance"] = self.current_balance
        
        drawdown = (self.performance_stats["peak_balance"] - self.current_balance) / self.performance_stats["peak_balance"]
        if drawdown > self.performance_stats["max_drawdown"]:
            self.performance_stats["max_drawdown"] = drawdown
    
    def force_close_all(self, current_prices: Dict[str, float], reason: str = "force_close"):
        """强制平仓所有持仓"""
        symbols_to_close = list(self.positions.keys())
        
        for symbol in symbols_to_close:
            if symbol in current_prices:
                self._close_position(symbol, current_prices[symbol], reason)
            else:
                # 如果没有当前价格，使用入场价格平仓
                position = self.positions[symbol]
                self._close_position(symbol, position.entry_price, reason)
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        total_trades = self.performance_stats["total_trades"]
        winning_trades = self.performance_stats["winning_trades"]
        
        # 计算胜率
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 计算总收益率
        total_return_pct = (self.current_balance - self.initial_balance) / self.initial_balance
        
        # 计算平均持仓时间
        avg_hold_time = 0
        if self.completed_trades:
            avg_hold_time = sum(trade.duration_hours for trade in self.completed_trades) / len(self.completed_trades)
        
        # 计算夏普比率（简化版本）
        sharpe_ratio = 0
        if self.completed_trades:
            returns = [trade.pnl_pct for trade in self.completed_trades]
            if len(returns) > 1:
                import statistics
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns)
                if std_return > 0:
                    sharpe_ratio = avg_return / std_return
        
        return {
            "balance": {
                "initial": self.initial_balance,
                "current": self.current_balance,
                "total_pnl": self.current_balance - self.initial_balance,
                "total_return_pct": total_return_pct * 100
            },
            "positions": {
                "active": len(self.positions),
                "completed": len(self.completed_trades)
            },
            "statistics": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": self.performance_stats["losing_trades"],
                "timeout_trades": self.performance_stats["timeout_trades"],
                "win_rate": win_rate * 100,
                "max_drawdown": self.performance_stats["max_drawdown"] * 100,
                "sharpe_ratio": sharpe_ratio,
                "average_hold_time_hours": avg_hold_time
            },
            "risk_metrics": {
                "current_exposure": sum(pos.position_size for pos in self.positions.values()) * 100,
                "max_exposure_limit": self.max_total_exposure * 100,
                "single_position_limit": self.max_position_size * 100,
                "max_hold_hours": self.max_hold_hours
            }
        }
    
    def get_active_positions_summary(self) -> List[Dict]:
        """获取当前持仓摘要"""
        positions = []
        for symbol, position in self.positions.items():
            duration = (datetime.now() - position.entry_time).total_seconds() / 3600
            
            positions.append({
                "symbol": symbol,
                "signal_type": position.signal_type,
                "entry_price": position.entry_price,
                "target_price": position.target_price,
                "stop_loss": position.stop_loss,
                "position_size_pct": position.position_size * 100,
                "duration_hours": duration,
                "time_remaining_hours": max(0, self.max_hold_hours - duration)
            })
        
        return positions
    
    def adjust_risk_parameters(self, max_position_size: float = None,
                              max_total_exposure: float = None,
                              max_hold_hours: float = None):
        """调整风险参数"""
        if max_position_size is not None:
            self.max_position_size = max(0.01, min(0.2, max_position_size))  # 1%-20%
        
        if max_total_exposure is not None:
            self.max_total_exposure = max(0.05, min(0.5, max_total_exposure))  # 5%-50%
        
        if max_hold_hours is not None:
            self.max_hold_hours = max(1, min(168, max_hold_hours))  # 1小时-7天
        
        logger.info(f"风险参数已调整: 单仓={self.max_position_size*100}%, "
                   f"总敞口={self.max_total_exposure*100}%, "
                   f"最长持仓={self.max_hold_hours}小时")
    
    def reset_simulator(self, new_balance: float = None):
        """重置模拟器"""
        if new_balance is not None:
            self.initial_balance = new_balance
        
        self.current_balance = self.initial_balance
        self.positions.clear()
        self.completed_trades.clear()
        
        self.performance_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "timeout_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "peak_balance": self.initial_balance
        }
        
        logger.info(f"模拟器已重置，资金: ${self.initial_balance:,.2f}")
    
    def export_trade_history(self) -> List[Dict]:
        """导出交易历史"""
        history = []
        for trade in self.completed_trades:
            history.append({
                "symbol": trade.symbol,
                "signal_type": trade.signal_type,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "target_price": trade.target_price,
                "stop_loss": trade.stop_loss,
                "position_size_pct": trade.position_size * 100,
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                "duration_hours": trade.duration_hours,
                "pnl": trade.pnl,
                "pnl_pct": trade.pnl_pct * 100,
                "status": trade.status.value
            })
        
        return history