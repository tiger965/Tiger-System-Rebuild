"""
Tiger系统 - 资金管理模块
窗口：7号
功能：严格的资金管理规则，保护账户安全
作者：Window-7 Risk Control Officer
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradingRecord:
    """交易记录"""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: float
    risk_taken: float
    position_size: float


@dataclass
class AccountStatus:
    """账户状态"""
    total_capital: float
    available_capital: float
    used_capital: float
    daily_pnl: float = 0
    weekly_pnl: float = 0
    monthly_pnl: float = 0
    trades_today: int = 0
    winning_trades: int = 0
    losing_trades: int = 0


class MoneyManagement:
    """资金管理系统 - 纪律的守护者"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.account_status = AccountStatus(
            total_capital=initial_capital,
            available_capital=initial_capital,
            used_capital=0
        )
        
        # 交易记录
        self.trades_history = []
        self.daily_trades = []
        
        # 限制规则
        self.limits = {
            "daily": {
                "max_loss_ratio": 0.10,  # 10%日亏损限制
                "max_loss_amount": initial_capital * 0.10,
                "max_trades": 10,
                "max_risk_per_trade": 0.03,  # 3%单笔风险
                "circuit_breaker": False  # 熔断标志
            },
            "weekly": {
                "max_loss_ratio": 0.20,  # 20%周亏损限制
                "max_loss_amount": initial_capital * 0.20,
                "review_trigger_ratio": 0.15,  # 15%触发审查
                "position_reduction": False  # 减仓标志
            },
            "monthly": {
                "max_loss_ratio": 0.40,  # 40%月亏损限制
                "max_loss_amount": initial_capital * 0.40,
                "circuit_breaker_ratio": 0.30,  # 30%熔断
                "absolute_stop": False  # 绝对停止标志
            }
        }
        
        # 盈利管理规则
        self.profit_rules = {
            "monthly_target": 0.20,  # 月目标20%
            "take_profit_ratio": 0.50,  # 达到目标提取50%
            "compound_ratio": 0.30,  # 30%复投
            "reserve_ratio": 0.20  # 20%储备
        }
        
        # 状态记录
        self.last_check_time = datetime.now()
        self.alerts = []
        
    def check_daily_limits(self) -> Dict:
        """
        检查日限制
        
        Returns:
            检查结果
        """
        result = {
            "can_trade": True,
            "warnings": [],
            "restrictions": []
        }
        
        # 检查日亏损
        if self.account_status.daily_pnl < 0:
            loss_ratio = abs(self.account_status.daily_pnl) / self.initial_capital
            
            if loss_ratio >= self.limits["daily"]["max_loss_ratio"]:
                result["can_trade"] = False
                result["restrictions"].append("日亏损达到10%，停止开仓")
                self.limits["daily"]["circuit_breaker"] = True
                logger.critical(f"日亏损熔断: {loss_ratio:.1%}")
            elif loss_ratio >= 0.07:
                result["warnings"].append(f"日亏损接近限制: {loss_ratio:.1%}")
        
        # 检查交易次数
        if self.account_status.trades_today >= self.limits["daily"]["max_trades"]:
            result["can_trade"] = False
            result["restrictions"].append(f"已达日交易次数上限({self.limits['daily']['max_trades']})")
        elif self.account_status.trades_today >= 8:
            result["warnings"].append(f"接近日交易次数上限: {self.account_status.trades_today}/{self.limits['daily']['max_trades']}")
        
        return result
    
    def check_weekly_limits(self) -> Dict:
        """
        检查周限制
        
        Returns:
            检查结果
        """
        result = {
            "position_adjustment": None,
            "warnings": [],
            "actions": []
        }
        
        # 检查周亏损
        if self.account_status.weekly_pnl < 0:
            loss_ratio = abs(self.account_status.weekly_pnl) / self.initial_capital
            
            if loss_ratio >= self.limits["weekly"]["max_loss_ratio"]:
                result["position_adjustment"] = "reduce_50"
                result["actions"].append("周亏损达到20%，强制减仓50%")
                self.limits["weekly"]["position_reduction"] = True
                logger.critical(f"周亏损触发减仓: {loss_ratio:.1%}")
            elif loss_ratio >= self.limits["weekly"]["review_trigger_ratio"]:
                result["position_adjustment"] = "review"
                result["actions"].append("周亏损达到15%，触发策略审查")
                result["warnings"].append("需要审查交易策略")
        
        return result
    
    def check_monthly_limits(self) -> Dict:
        """
        检查月限制
        
        Returns:
            检查结果
        """
        result = {
            "emergency_action": None,
            "warnings": [],
            "critical": []
        }
        
        # 检查月亏损
        if self.account_status.monthly_pnl < 0:
            loss_ratio = abs(self.account_status.monthly_pnl) / self.initial_capital
            
            if loss_ratio >= self.limits["monthly"]["max_loss_ratio"]:
                result["emergency_action"] = "ABSOLUTE_STOP"
                result["critical"].append("月亏损达到40%红线，系统停止")
                self.limits["monthly"]["absolute_stop"] = True
                logger.critical(f"触发绝对红线: {loss_ratio:.1%}")
            elif loss_ratio >= self.limits["monthly"]["circuit_breaker_ratio"]:
                result["emergency_action"] = "CIRCUIT_BREAKER"
                result["critical"].append("月亏损达到30%，触发熔断")
                result["warnings"].append("立即降低所有风险")
        
        return result
    
    def calculate_position_size(self, risk_per_trade: float, stop_loss_points: float) -> float:
        """
        计算仓位大小
        
        Args:
            risk_per_trade: 单笔风险金额
            stop_loss_points: 止损点数
            
        Returns:
            建议仓位大小
        """
        # 检查是否可以交易
        daily_check = self.check_daily_limits()
        if not daily_check["can_trade"]:
            logger.warning("触发日限制，不能开仓")
            return 0
        
        # 检查单笔风险限制
        max_risk = self.current_capital * self.limits["daily"]["max_risk_per_trade"]
        risk_amount = min(risk_per_trade, max_risk)
        
        # 计算仓位
        if stop_loss_points > 0:
            position_size = risk_amount / stop_loss_points
        else:
            position_size = 0
        
        # 检查可用资金
        if position_size > self.account_status.available_capital:
            position_size = self.account_status.available_capital * 0.9  # 保留10%缓冲
        
        logger.info(f"计算仓位: 风险={risk_amount:.2f}, 止损点={stop_loss_points:.2f}, 仓位={position_size:.2f}")
        
        return position_size
    
    def update_trade(self, trade: TradingRecord) -> bool:
        """
        更新交易记录
        
        Args:
            trade: 交易记录
            
        Returns:
            是否成功
        """
        try:
            self.trades_history.append(trade)
            
            # 更新日交易
            if trade.entry_time.date() == datetime.now().date():
                self.daily_trades.append(trade)
                self.account_status.trades_today += 1
                
                # 更新日盈亏
                self.account_status.daily_pnl += trade.pnl
                
                # 更新胜负统计
                if trade.pnl > 0:
                    self.account_status.winning_trades += 1
                else:
                    self.account_status.losing_trades += 1
            
            # 更新资金
            self.current_capital += trade.pnl
            self.account_status.total_capital = self.current_capital
            
            # 检查限制
            self._check_all_limits()
            
            return True
        except Exception as e:
            logger.error(f"更新交易失败: {e}")
            return False
    
    def profit_management(self) -> Dict:
        """
        盈利管理
        
        Returns:
            盈利处理建议
        """
        monthly_profit = self.account_status.monthly_pnl
        
        if monthly_profit <= 0:
            return {"action": "none", "reason": "无盈利"}
        
        profit_ratio = monthly_profit / self.initial_capital
        
        result = {
            "total_profit": monthly_profit,
            "profit_ratio": profit_ratio,
            "actions": []
        }
        
        # 达到月目标
        if profit_ratio >= self.profit_rules["monthly_target"]:
            take_amount = monthly_profit * self.profit_rules["take_profit_ratio"]
            compound_amount = monthly_profit * self.profit_rules["compound_ratio"]
            reserve_amount = monthly_profit * self.profit_rules["reserve_ratio"]
            
            result["actions"] = [
                {"type": "take_profit", "amount": take_amount, "reason": "达到月目标，提取利润"},
                {"type": "compound", "amount": compound_amount, "reason": "复投扩大本金"},
                {"type": "reserve", "amount": reserve_amount, "reason": "建立风险准备金"}
            ]
            
            logger.info(f"盈利管理: 提取={take_amount:.2f}, 复投={compound_amount:.2f}, 储备={reserve_amount:.2f}")
        
        return result
    
    def get_risk_capacity(self) -> Dict:
        """
        获取当前风险容量
        
        Returns:
            风险容量信息
        """
        daily_remaining = self.limits["daily"]["max_loss_amount"] + self.account_status.daily_pnl
        trades_remaining = self.limits["daily"]["max_trades"] - self.account_status.trades_today
        
        return {
            "timestamp": datetime.now().isoformat(),
            "daily_risk_remaining": max(0, daily_remaining),
            "trades_remaining": max(0, trades_remaining),
            "max_position_size": self.account_status.available_capital * 0.3,  # 最大30%
            "suggested_risk_per_trade": min(
                daily_remaining * 0.3,  # 剩余日风险的30%
                self.current_capital * self.limits["daily"]["max_risk_per_trade"]
            ),
            "circuit_breaker_active": self.limits["daily"]["circuit_breaker"],
            "position_reduction_active": self.limits["weekly"]["position_reduction"],
            "absolute_stop_active": self.limits["monthly"]["absolute_stop"]
        }
    
    def _check_all_limits(self):
        """检查所有限制"""
        # 日限制
        daily_result = self.check_daily_limits()
        if daily_result["warnings"]:
            self.alerts.extend(daily_result["warnings"])
        
        # 周限制
        weekly_result = self.check_weekly_limits()
        if weekly_result["warnings"]:
            self.alerts.extend(weekly_result["warnings"])
        
        # 月限制
        monthly_result = self.check_monthly_limits()
        if monthly_result["critical"]:
            self.alerts.extend(monthly_result["critical"])
    
    def reset_daily_stats(self):
        """重置日统计"""
        self.account_status.daily_pnl = 0
        self.account_status.trades_today = 0
        self.daily_trades.clear()
        self.limits["daily"]["circuit_breaker"] = False
        logger.info("日统计已重置")
    
    def reset_weekly_stats(self):
        """重置周统计"""
        self.account_status.weekly_pnl = 0
        self.limits["weekly"]["position_reduction"] = False
        logger.info("周统计已重置")
    
    def reset_monthly_stats(self):
        """重置月统计"""
        self.account_status.monthly_pnl = 0
        self.account_status.winning_trades = 0
        self.account_status.losing_trades = 0
        self.limits["monthly"]["absolute_stop"] = False
        logger.info("月统计已重置")
    
    def get_status(self) -> Dict:
        """获取资金管理状态"""
        win_rate = 0
        if self.account_status.winning_trades + self.account_status.losing_trades > 0:
            win_rate = self.account_status.winning_trades / (
                self.account_status.winning_trades + self.account_status.losing_trades
            )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "capital": {
                "initial": self.initial_capital,
                "current": self.current_capital,
                "available": self.account_status.available_capital,
                "used": self.account_status.used_capital
            },
            "pnl": {
                "daily": self.account_status.daily_pnl,
                "weekly": self.account_status.weekly_pnl,
                "monthly": self.account_status.monthly_pnl
            },
            "statistics": {
                "trades_today": self.account_status.trades_today,
                "win_rate": win_rate,
                "winning_trades": self.account_status.winning_trades,
                "losing_trades": self.account_status.losing_trades
            },
            "limits_status": {
                "daily_breaker": self.limits["daily"]["circuit_breaker"],
                "weekly_reduction": self.limits["weekly"]["position_reduction"],
                "monthly_stop": self.limits["monthly"]["absolute_stop"]
            },
            "alerts": self.alerts[-5:] if self.alerts else []
        }


if __name__ == "__main__":
    # 测试代码
    mm = MoneyManagement(initial_capital=100000)
    
    # 模拟交易
    trade1 = TradingRecord(
        symbol="BTC",
        entry_time=datetime.now(),
        exit_time=datetime.now(),
        pnl=-1000,
        risk_taken=3000,
        position_size=10000
    )
    mm.update_trade(trade1)
    
    # 检查限制
    daily_check = mm.check_daily_limits()
    print(f"日限制检查: {daily_check}")
    
    # 获取风险容量
    risk_capacity = mm.get_risk_capacity()
    print(f"风险容量: {json.dumps(risk_capacity, indent=2)}")
    
    # 获取状态
    status = mm.get_status()
    print(f"资金管理状态: {json.dumps(status, indent=2)}")