"""
Tiger系统 - 止损系统
窗口：7号
功能：多重止损机制，确保损失可控
作者：Window-7 Risk Control Officer
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Position:
    """仓位数据结构"""
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    entry_time: datetime
    unrealized_pnl: float
    atr: float  # Average True Range
    support_level: float
    resistance_level: float


class StopLossSystem:
    """止损系统 - 铁律执行，绝不妥协"""
    
    def __init__(self):
        self.active_stops = {}  # 活跃的止损订单
        self.stop_history = []  # 止损历史记录
        self.protection_mode = False  # 保护模式标志
        
        # 止损参数配置
        self.config = {
            "technical": {
                "support_break_buffer": 0.002,  # 支撑位下方0.2%触发
                "pattern_fail_threshold": 0.03,  # 形态失败3%止损
                "indicator_reverse_confirm": 2  # 需要2个指标确认
            },
            "fixed": {
                "percentage_stop": 0.05,  # 5%固定止损
                "max_percentage": 0.08,  # 最大8%止损
                "atr_multiplier": 2.0,  # 2倍ATR止损
                "dollar_stop": 1000  # 单笔最大损失$1000
            },
            "time": {
                "no_profit_days": 3,  # 3天不盈利止损
                "sideways_days": 7,  # 横盘7天止损
                "news_event_hours": 4  # 重大事件前4小时平仓
            },
            "trailing": {
                "activation_profit": 0.10,  # 盈利10%激活
                "trail_distance": 0.05,  # 追踪距离5%
                "breakeven_buffer": 0.002  # 成本价上方0.2%保护
            }
        }
        
    def calculate_technical_stop(self, position: Position) -> Tuple[float, str]:
        """
        技术止损计算
        
        Args:
            position: 仓位信息
            
        Returns:
            (止损价格, 止损原因)
        """
        stops = []
        
        # 支撑位止损
        support_stop = position.support_level * (1 - self.config["technical"]["support_break_buffer"])
        stops.append((support_stop, "支撑位跌破"))
        
        # 形态失败止损
        pattern_stop = position.entry_price * (1 - self.config["technical"]["pattern_fail_threshold"])
        stops.append((pattern_stop, "形态失败"))
        
        # 选择最高的止损价（最保守）
        stop_price, reason = max(stops, key=lambda x: x[0])
        
        logger.info(f"{position.symbol} 技术止损: {stop_price:.2f} ({reason})")
        return stop_price, reason
    
    def calculate_fixed_stop(self, position: Position) -> Tuple[float, str]:
        """
        固定止损计算
        
        Args:
            position: 仓位信息
            
        Returns:
            (止损价格, 止损原因)
        """
        stops = []
        
        # 百分比止损
        percentage_stop = position.entry_price * (1 - self.config["fixed"]["percentage_stop"])
        stops.append((percentage_stop, f"{self.config['fixed']['percentage_stop']*100}%固定止损"))
        
        # ATR止损
        if position.atr > 0:
            atr_stop = position.entry_price - (position.atr * self.config["fixed"]["atr_multiplier"])
            stops.append((atr_stop, f"{self.config['fixed']['atr_multiplier']}倍ATR止损"))
        
        # 美元止损
        dollar_stop_price = position.entry_price - (self.config["fixed"]["dollar_stop"] / position.quantity)
        stops.append((dollar_stop_price, f"${self.config['fixed']['dollar_stop']}固定止损"))
        
        # 选择最高的止损价（最保守）
        stop_price, reason = max(stops, key=lambda x: x[0])
        
        # 确保不超过最大止损
        max_stop = position.entry_price * (1 - self.config["fixed"]["max_percentage"])
        if stop_price < max_stop:
            stop_price = max_stop
            reason = f"最大{self.config['fixed']['max_percentage']*100}%止损"
        
        logger.info(f"{position.symbol} 固定止损: {stop_price:.2f} ({reason})")
        return stop_price, reason
    
    def calculate_time_stop(self, position: Position, market_events: List[Dict] = None) -> Tuple[bool, str]:
        """
        时间止损判断
        
        Args:
            position: 仓位信息
            market_events: 市场事件列表
            
        Returns:
            (是否触发止损, 止损原因)
        """
        current_time = datetime.now()
        holding_days = (current_time - position.entry_time).days
        
        # 无盈利时间止损
        if position.unrealized_pnl <= 0 and holding_days >= self.config["time"]["no_profit_days"]:
            return True, f"持仓{holding_days}天无盈利"
        
        # 横盘时间止损
        if self._is_sideways(position) and holding_days >= self.config["time"]["sideways_days"]:
            return True, f"横盘{holding_days}天"
        
        # 重大事件止损
        if market_events:
            for event in market_events:
                event_time = datetime.fromisoformat(event["time"])
                hours_to_event = (event_time - current_time).total_seconds() / 3600
                if 0 < hours_to_event <= self.config["time"]["news_event_hours"]:
                    return True, f"重大事件{event['name']}即将发生"
        
        return False, ""
    
    def calculate_trailing_stop(self, position: Position, highest_price: float) -> Tuple[float, str]:
        """
        追踪止损计算
        
        Args:
            position: 仓位信息
            highest_price: 持仓期间最高价
            
        Returns:
            (止损价格, 止损原因)
        """
        profit_ratio = (highest_price - position.entry_price) / position.entry_price
        
        # 未达到激活条件
        if profit_ratio < self.config["trailing"]["activation_profit"]:
            # 返回成本保护价
            breakeven_stop = position.entry_price * (1 + self.config["trailing"]["breakeven_buffer"])
            if position.current_price > breakeven_stop:
                return breakeven_stop, "成本保护"
            return 0, "未激活追踪止损"
        
        # 计算追踪止损价
        trail_stop = highest_price * (1 - self.config["trailing"]["trail_distance"])
        
        # 动态调整追踪距离
        if profit_ratio > 0.20:  # 盈利超过20%
            trail_stop = highest_price * (1 - self.config["trailing"]["trail_distance"] * 0.5)  # 收紧止损
            return trail_stop, f"盈利{profit_ratio:.1%}动态追踪"
        
        return trail_stop, f"追踪止损(距高点{self.config['trailing']['trail_distance']*100}%)"
    
    def get_combined_stop(self, 
                         position: Position, 
                         highest_price: float,
                         market_events: List[Dict] = None) -> Dict:
        """
        综合止损计算 - 最严格的生效
        
        Args:
            position: 仓位信息
            highest_price: 最高价
            market_events: 市场事件
            
        Returns:
            止损决策
        """
        stops = []
        
        # 技术止损
        tech_stop, tech_reason = self.calculate_technical_stop(position)
        stops.append({"price": tech_stop, "type": "technical", "reason": tech_reason})
        
        # 固定止损
        fixed_stop, fixed_reason = self.calculate_fixed_stop(position)
        stops.append({"price": fixed_stop, "type": "fixed", "reason": fixed_reason})
        
        # 时间止损
        time_trigger, time_reason = self.calculate_time_stop(position, market_events)
        if time_trigger:
            stops.append({"price": position.current_price * 0.995, "type": "time", "reason": time_reason})
        
        # 追踪止损
        trail_stop, trail_reason = self.calculate_trailing_stop(position, highest_price)
        if trail_stop > 0:
            stops.append({"price": trail_stop, "type": "trailing", "reason": trail_reason})
        
        # 选择最高的止损价（最保守）
        final_stop = max(stops, key=lambda x: x["price"])
        
        # 检查是否触发
        triggered = position.current_price <= final_stop["price"]
        
        return {
            "symbol": position.symbol,
            "stop_price": final_stop["price"],
            "current_price": position.current_price,
            "stop_type": final_stop["type"],
            "reason": final_stop["reason"],
            "triggered": triggered,
            "distance": (position.current_price - final_stop["price"]) / position.current_price,
            "all_stops": stops
        }
    
    def emergency_stop_all(self, reason: str = "紧急止损") -> List[Dict]:
        """
        紧急止损所有仓位
        
        Args:
            reason: 止损原因
            
        Returns:
            止损执行列表
        """
        logger.critical(f"紧急止损触发: {reason}")
        
        stop_orders = []
        for symbol, stop_info in self.active_stops.items():
            stop_orders.append({
                "symbol": symbol,
                "action": "EMERGENCY_CLOSE",
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
        
        # 记录到历史
        self.stop_history.extend(stop_orders)
        
        # 清空活跃止损
        self.active_stops.clear()
        
        # 启动保护模式
        self.protection_mode = True
        
        return stop_orders
    
    def update_stop(self, symbol: str, new_stop: Dict) -> bool:
        """
        更新止损订单
        
        Args:
            symbol: 币种
            new_stop: 新止损信息
            
        Returns:
            是否成功
        """
        try:
            old_stop = self.active_stops.get(symbol)
            
            # 止损只能上移，不能下移（保护利润）
            if old_stop and new_stop["stop_price"] < old_stop["stop_price"]:
                logger.warning(f"{symbol} 止损价不能下移: {old_stop['stop_price']} -> {new_stop['stop_price']}")
                return False
            
            self.active_stops[symbol] = new_stop
            logger.info(f"{symbol} 止损更新: {new_stop['stop_price']:.2f} ({new_stop['reason']})")
            
            return True
        except Exception as e:
            logger.error(f"止损更新失败: {e}")
            return False
    
    def check_stop_triggers(self, market_data: Dict) -> List[Dict]:
        """
        检查止损触发
        
        Args:
            market_data: 市场数据
            
        Returns:
            触发的止损列表
        """
        triggered_stops = []
        
        for symbol, stop_info in self.active_stops.items():
            current_price = market_data.get(symbol, {}).get("price")
            if not current_price:
                continue
            
            if current_price <= stop_info["stop_price"]:
                triggered_stops.append({
                    "symbol": symbol,
                    "stop_price": stop_info["stop_price"],
                    "trigger_price": current_price,
                    "reason": stop_info["reason"],
                    "type": stop_info["stop_type"],
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.warning(f"止损触发: {symbol} @ {current_price:.2f} (止损价: {stop_info['stop_price']:.2f})")
        
        return triggered_stops
    
    def _is_sideways(self, position: Position) -> bool:
        """判断是否横盘"""
        # 简化判断：价格在入场价±3%范围内
        return abs(position.current_price - position.entry_price) / position.entry_price < 0.03
    
    def get_stop_status(self) -> Dict:
        """获取止损系统状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_stops": len(self.active_stops),
            "protection_mode": self.protection_mode,
            "stops": self.active_stops.copy(),
            "recent_triggers": self.stop_history[-10:] if self.stop_history else []
        }


if __name__ == "__main__":
    # 测试代码
    sl = StopLossSystem()
    
    # 创建测试仓位
    test_position = Position(
        symbol="BTC",
        entry_price=70000,
        current_price=68000,
        quantity=0.1,
        entry_time=datetime.now() - timedelta(days=2),
        unrealized_pnl=-200,
        atr=1500,
        support_level=67000,
        resistance_level=72000
    )
    
    # 测试综合止损
    stop_decision = sl.get_combined_stop(test_position, highest_price=71000)
    print(f"止损决策: {stop_decision}")
    
    # 更新止损
    sl.update_stop("BTC", stop_decision)
    
    # 检查触发
    triggers = sl.check_stop_triggers({"BTC": {"price": 67500}})
    print(f"触发的止损: {triggers}")
    
    # 获取状态
    status = sl.get_stop_status()
    print(f"止损系统状态: {status}")