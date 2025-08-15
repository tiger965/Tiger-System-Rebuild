"""
Tiger系统 - 仓位管理系统
窗口：7号
功能：实施严格的仓位控制规则，确保风险可控
作者：Window-7 Risk Control Officer
"""

import json
import math
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PositionManager:
    """仓位管理核心类 - 铁律执行者"""
    
    def __init__(self):
        self.rules = {
            "initial_position": 0.05,  # 5% 初始仓位
            "max_initial": 0.10,  # 10% 初始仓位上限
            "max_single_coin": 0.30,  # 30% 单币最大
            "max_total_position": 0.70,  # 70% 总仓位上限
            "emergency_reserve": 0.30,  # 30% 应急资金
            "opportunity_reserve": 0.10  # 10% 机会资金（新增）
        }
        
        self.current_positions = {}
        self.total_capital = 0
        self.available_capital = 0
        self.performance_history = []
        
    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        凯利公式计算最优仓位
        f = (p * b - q) / b
        f: 最优仓位比例
        p: 胜率
        b: 平均盈亏比
        q: 败率(1-p)
        """
        if avg_win <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
            
        q = 1 - win_rate
        b = avg_win / avg_loss if avg_loss > 0 else avg_win
        
        # 凯利公式
        f = (win_rate * b - q) / b
        
        # 安全系数：使用1/4凯利
        f = f * 0.25
        
        # 限制范围
        f = max(0, min(f, self.rules["max_initial"]))
        
        logger.info(f"凯利公式计算: 胜率={win_rate:.2%}, 盈亏比={b:.2f}, 建议仓位={f:.2%}")
        return f
    
    def calculate_position_size(self, 
                               signal_strength: float,
                               market_conditions: Dict,
                               risk_score: int) -> Tuple[float, str]:
        """
        计算具体仓位大小
        
        Args:
            signal_strength: 信号强度 (0-10)
            market_conditions: 市场状况
            risk_score: 风险评分 (0-30)
        
        Returns:
            (仓位比例, 决策理由)
        """
        base_position = self.rules["initial_position"]
        
        # 信号强度调整
        signal_multiplier = 1.0
        if signal_strength >= 8:
            signal_multiplier = 1.5
        elif signal_strength >= 6:
            signal_multiplier = 1.2
        elif signal_strength < 4:
            signal_multiplier = 0.5
            
        # 市场条件调整
        market_multiplier = 1.0
        if market_conditions.get("trend") == "strong_uptrend":
            market_multiplier = 1.3
        elif market_conditions.get("trend") == "downtrend":
            market_multiplier = 0.7
            
        if market_conditions.get("volatility") == "high":
            market_multiplier *= 0.8
            
        # 风险调整
        risk_multiplier = 1.0
        if risk_score > 20:
            risk_multiplier = 0.5
        elif risk_score > 15:
            risk_multiplier = 0.7
        elif risk_score < 10:
            risk_multiplier = 1.2
            
        # 计算最终仓位
        position_size = base_position * signal_multiplier * market_multiplier * risk_multiplier
        
        # 检查限制
        position_size = self._apply_position_limits(position_size)
        
        reason = f"信号:{signal_strength}/10, 市场:{market_conditions.get('trend', 'neutral')}, 风险:{risk_score}/30"
        
        return position_size, reason
    
    def _apply_position_limits(self, position_size: float) -> float:
        """应用仓位限制规则"""
        # 不能超过初始仓位上限
        position_size = min(position_size, self.rules["max_initial"])
        
        # 检查总仓位限制
        total_used = sum(self.current_positions.values())
        if total_used + position_size > self.rules["max_total_position"]:
            position_size = self.rules["max_total_position"] - total_used
            
        # 确保保留应急资金
        if total_used + position_size > (1 - self.rules["emergency_reserve"]):
            position_size = (1 - self.rules["emergency_reserve"]) - total_used
            
        return max(0, position_size)
    
    def adjust_position_dynamic(self, symbol: str, performance: Dict) -> Dict:
        """
        动态调整仓位
        
        Args:
            symbol: 币种
            performance: 表现数据
        
        Returns:
            调整建议
        """
        current_position = self.current_positions.get(symbol, 0)
        adjustment = {"action": "hold", "new_position": current_position, "reason": ""}
        
        # 连胜加仓
        if performance.get("winning_streak", 0) >= 3:
            if current_position < self.rules["max_single_coin"] * 0.8:
                adjustment["action"] = "increase"
                adjustment["new_position"] = min(current_position * 1.2, 
                                                self.rules["max_single_coin"])
                adjustment["reason"] = f"连胜{performance['winning_streak']}次，适当加仓"
                
        # 连败减仓
        elif performance.get("losing_streak", 0) >= 2:
            adjustment["action"] = "decrease"
            adjustment["new_position"] = current_position * 0.5
            adjustment["reason"] = f"连败{performance['losing_streak']}次，必须减仓"
            
        # 高波动减仓
        elif performance.get("volatility", 0) > 0.5:
            adjustment["action"] = "decrease"
            adjustment["new_position"] = current_position * 0.7
            adjustment["reason"] = "市场波动过大，降低仓位"
            
        # 黑天鹅风险
        elif performance.get("black_swan_risk", False):
            adjustment["action"] = "emergency_reduce"
            adjustment["new_position"] = current_position * 0.5
            adjustment["reason"] = "黑天鹅风险预警，立即减仓50%"
            
        return adjustment
    
    def rebalance_portfolio(self) -> Dict:
        """
        定期仓位再平衡
        
        Returns:
            再平衡建议
        """
        rebalance_actions = []
        total_position = sum(self.current_positions.values())
        
        for symbol, position in self.current_positions.items():
            # 检查单币限制
            if position > self.rules["max_single_coin"]:
                rebalance_actions.append({
                    "symbol": symbol,
                    "action": "reduce",
                    "target": self.rules["max_single_coin"],
                    "reason": "超过单币限制"
                })
                
            # 检查占比过高
            if total_position > 0 and position / total_position > 0.5:
                rebalance_actions.append({
                    "symbol": symbol,
                    "action": "reduce",
                    "target": total_position * 0.4,
                    "reason": "占比过高，需要分散"
                })
                
        return {
            "timestamp": datetime.now().isoformat(),
            "total_position": total_position,
            "actions": rebalance_actions
        }
    
    def profit_extraction_rules(self, total_profit: float) -> Dict:
        """
        利润提取规则
        
        Args:
            total_profit: 总利润
        
        Returns:
            提取建议
        """
        extraction = {
            "extract_amount": 0,
            "reinvest_amount": 0,
            "reserve_amount": 0,
            "reason": ""
        }
        
        if total_profit <= 0:
            extraction["reason"] = "无利润可提取"
            return extraction
            
        # 利润分配策略
        if total_profit > self.total_capital * 0.5:  # 利润超过本金50%
            extraction["extract_amount"] = total_profit * 0.3  # 提取30%
            extraction["reserve_amount"] = total_profit * 0.2  # 储备20%
            extraction["reinvest_amount"] = total_profit * 0.5  # 复投50%
            extraction["reason"] = "大幅盈利，部分提取"
        elif total_profit > self.total_capital * 0.2:  # 利润超过20%
            extraction["extract_amount"] = total_profit * 0.2  # 提取20%
            extraction["reserve_amount"] = total_profit * 0.3  # 储备30%
            extraction["reinvest_amount"] = total_profit * 0.5  # 复投50%
            extraction["reason"] = "稳定盈利，适度提取"
        else:
            extraction["reinvest_amount"] = total_profit  # 全部复投
            extraction["reason"] = "利润较少，全部复投"
            
        return extraction
    
    def check_loss_compensation_limit(self, symbol: str, loss_amount: float) -> bool:
        """
        检查亏损补仓限制
        
        Args:
            symbol: 币种
            loss_amount: 亏损金额
        
        Returns:
            是否允许补仓
        """
        current_position = self.current_positions.get(symbol, 0)
        
        # 亏损超过20%不允许补仓
        if loss_amount > self.total_capital * 0.2:
            logger.warning(f"{symbol} 亏损超过20%，禁止补仓")
            return False
            
        # 已经补仓2次不允许再补
        if self._get_compensation_count(symbol) >= 2:
            logger.warning(f"{symbol} 已补仓2次，禁止继续补仓")
            return False
            
        # 仓位已达上限
        if current_position >= self.rules["max_single_coin"]:
            logger.warning(f"{symbol} 仓位已达上限，禁止补仓")
            return False
            
        return True
    
    def _get_compensation_count(self, symbol: str) -> int:
        """获取补仓次数（需要连接数据库实现）"""
        # TODO: 从数据库读取补仓记录
        return 0
    
    def update_position(self, symbol: str, new_position: float, action: str) -> bool:
        """
        更新仓位记录
        
        Args:
            symbol: 币种
            new_position: 新仓位
            action: 操作类型
        
        Returns:
            是否成功
        """
        try:
            old_position = self.current_positions.get(symbol, 0)
            self.current_positions[symbol] = new_position
            
            logger.info(f"仓位更新: {symbol} {old_position:.2%} -> {new_position:.2%} ({action})")
            
            # 记录到历史
            self.performance_history.append({
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "old_position": old_position,
                "new_position": new_position,
                "action": action
            })
            
            return True
        except Exception as e:
            logger.error(f"仓位更新失败: {e}")
            return False
    
    def get_position_status(self) -> Dict:
        """获取当前仓位状态"""
        total_used = sum(self.current_positions.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "positions": self.current_positions.copy(),
            "total_used": total_used,
            "available": 1 - total_used,
            "emergency_reserve": self.rules["emergency_reserve"],
            "opportunity_reserve": self.rules["opportunity_reserve"],
            "can_open_new": total_used < self.rules["max_total_position"],
            "risk_level": self._calculate_risk_level(total_used)
        }
    
    def _calculate_risk_level(self, total_used: float) -> str:
        """计算风险等级"""
        if total_used > 0.6:
            return "HIGH"
        elif total_used > 0.4:
            return "MEDIUM"
        else:
            return "LOW"


if __name__ == "__main__":
    # 测试代码
    pm = PositionManager()
    pm.total_capital = 100000  # 10万美元
    
    # 测试凯利公式
    optimal_size = pm.kelly_criterion(0.6, 2.0, 1.0)
    print(f"凯利公式建议仓位: {optimal_size:.2%}")
    
    # 测试仓位计算
    position, reason = pm.calculate_position_size(
        signal_strength=7,
        market_conditions={"trend": "uptrend", "volatility": "medium"},
        risk_score=12
    )
    print(f"计算仓位: {position:.2%}, 原因: {reason}")
    
    # 测试仓位状态
    pm.update_position("BTC", 0.15, "open")
    pm.update_position("ETH", 0.10, "open")
    status = pm.get_position_status()
    print(f"仓位状态: {json.dumps(status, indent=2)}")