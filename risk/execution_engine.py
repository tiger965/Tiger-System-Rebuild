"""
Tiger系统 - 订单执行引擎
窗口：7号
功能：智能订单执行、滑点控制、执行算法（TWAP/VWAP）
作者：Window-7 Risk Control Officer
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecutionAlgorithm(Enum):
    """执行算法"""
    IMMEDIATE = "immediate"  # 立即执行
    TWAP = "twap"  # 时间加权平均
    VWAP = "vwap"  # 成交量加权平均
    ICEBERG = "iceberg"  # 冰山订单
    ADAPTIVE = "adaptive"  # 自适应执行


@dataclass
class Order:
    """订单信息"""
    order_id: str
    symbol: str
    side: str  # buy/sell
    amount: float
    order_type: OrderType
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # GTC/IOC/FOK
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0
    average_price: float = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """执行计划"""
    algorithm: ExecutionAlgorithm
    total_amount: float
    slices: List[Dict]  # 分片执行计划
    time_window: int  # 执行时间窗口（秒）
    urgency: str  # low/medium/high
    max_slippage: float  # 最大滑点
    estimated_cost: float  # 预估执行成本


class ExecutionEngine:
    """
    订单执行引擎
    负责智能订单路由、执行算法、滑点控制
    """
    
    def __init__(self):
        """初始化执行引擎"""
        self.orders = {}  # 订单缓存
        self.active_orders = {}  # 活动订单
        self.execution_queue = []  # 执行队列
        
        # 执行参数
        self.slippage_model = {
            "base": 0.0005,  # 基础滑点 0.05%
            "impact": 0.0001,  # 冲击成本系数
            "urgency_multiplier": {
                "low": 0.5,
                "medium": 1.0,
                "high": 2.0
            }
        }
        
        # 执行限制
        self.limits = {
            "max_order_size": 100000,  # 最大单笔订单
            "max_slippage": 0.01,  # 最大滑点1%
            "min_slice_size": 100,  # 最小分片大小
            "max_slices": 100  # 最大分片数
        }
        
        # 性能统计
        self.stats = {
            "total_orders": 0,
            "filled_orders": 0,
            "cancelled_orders": 0,
            "total_slippage": 0,
            "average_fill_time": 0
        }
    
    async def submit_order(self, order: Order, 
                          algorithm: ExecutionAlgorithm = ExecutionAlgorithm.IMMEDIATE) -> str:
        """
        提交订单
        
        Args:
            order: 订单对象
            algorithm: 执行算法
            
        Returns:
            订单ID
        """
        try:
            # 验证订单
            if not self._validate_order(order):
                order.status = OrderStatus.REJECTED
                logger.error(f"订单验证失败: {order.order_id}")
                return None
            
            # 存储订单
            self.orders[order.order_id] = order
            self.active_orders[order.order_id] = order
            order.status = OrderStatus.SUBMITTED
            
            # 生成执行计划
            plan = self._create_execution_plan(order, algorithm)
            
            # 执行订单
            asyncio.create_task(self._execute_order(order, plan))
            
            logger.info(f"订单已提交: {order.order_id}, 算法: {algorithm.value}")
            self.stats["total_orders"] += 1
            
            return order.order_id
            
        except Exception as e:
            logger.error(f"提交订单失败: {e}")
            order.status = OrderStatus.REJECTED
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        if order_id not in self.active_orders:
            logger.warning(f"订单不存在或已完成: {order_id}")
            return False
        
        order = self.active_orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            logger.warning(f"订单状态不可取消: {order.status}")
            return False
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        del self.active_orders[order_id]
        
        self.stats["cancelled_orders"] += 1
        logger.info(f"订单已取消: {order_id}")
        
        return True
    
    def calculate_twap(self, total_amount: float, duration: int, 
                      intervals: int = 10) -> List[Dict]:
        """
        计算TWAP（时间加权平均价格）执行计划
        
        Args:
            total_amount: 总数量
            duration: 执行时长（秒）
            intervals: 分片数量
            
        Returns:
            执行计划
        """
        if intervals > self.limits["max_slices"]:
            intervals = self.limits["max_slices"]
        
        slice_amount = total_amount / intervals
        slice_duration = duration / intervals
        
        slices = []
        for i in range(intervals):
            slices.append({
                "index": i,
                "amount": slice_amount,
                "start_time": i * slice_duration,
                "end_time": (i + 1) * slice_duration,
                "priority": "medium"
            })
        
        logger.info(f"TWAP计划: {intervals}片, 每片{slice_amount:.2f}")
        
        return slices
    
    def calculate_vwap(self, total_amount: float, volume_profile: List[float]) -> List[Dict]:
        """
        计算VWAP（成交量加权平均价格）执行计划
        
        Args:
            total_amount: 总数量
            volume_profile: 成交量分布
            
        Returns:
            执行计划
        """
        if not volume_profile:
            # 如果没有成交量数据，退化为TWAP
            return self.calculate_twap(total_amount, 3600)
        
        # 归一化成交量分布
        total_volume = sum(volume_profile)
        weights = [v / total_volume for v in volume_profile]
        
        slices = []
        for i, weight in enumerate(weights):
            slice_amount = total_amount * weight
            
            if slice_amount >= self.limits["min_slice_size"]:
                slices.append({
                    "index": i,
                    "amount": slice_amount,
                    "weight": weight,
                    "priority": "high" if weight > 0.1 else "medium"
                })
        
        logger.info(f"VWAP计划: {len(slices)}片, 基于成交量分布")
        
        return slices
    
    def calculate_iceberg(self, total_amount: float, visible_percent: float = 0.1) -> List[Dict]:
        """
        计算冰山订单执行计划
        
        Args:
            total_amount: 总数量
            visible_percent: 可见比例
            
        Returns:
            执行计划
        """
        visible_amount = total_amount * visible_percent
        hidden_amount = total_amount - visible_amount
        
        # 计算分片数量
        num_slices = int(hidden_amount / visible_amount) + 1
        
        slices = []
        remaining = total_amount
        
        for i in range(num_slices):
            slice_amount = min(visible_amount, remaining)
            slices.append({
                "index": i,
                "amount": slice_amount,
                "visible": i == 0,  # 只有第一片可见
                "priority": "low"
            })
            remaining -= slice_amount
            
            if remaining <= 0:
                break
        
        logger.info(f"冰山计划: {len(slices)}片, 可见{visible_percent:.1%}")
        
        return slices
    
    def estimate_slippage(self, amount: float, liquidity: float, 
                         urgency: str = "medium") -> float:
        """
        估算滑点
        
        Args:
            amount: 订单数量
            liquidity: 市场流动性
            urgency: 紧急程度
            
        Returns:
            预估滑点
        """
        if liquidity <= 0:
            return self.limits["max_slippage"]
        
        # 基础滑点
        base_slippage = self.slippage_model["base"]
        
        # 冲击成本
        impact = self.slippage_model["impact"] * (amount / liquidity)
        
        # 紧急程度调整
        urgency_mult = self.slippage_model["urgency_multiplier"].get(urgency, 1.0)
        
        # 总滑点
        total_slippage = (base_slippage + impact) * urgency_mult
        
        # 限制最大滑点
        total_slippage = min(total_slippage, self.limits["max_slippage"])
        
        logger.debug(f"滑点估算: {total_slippage:.4%} (数量={amount}, 流动性={liquidity})")
        
        return total_slippage
    
    def calculate_optimal_execution(self, order: Order, market_data: Dict) -> ExecutionPlan:
        """
        计算最优执行策略
        
        Args:
            order: 订单
            market_data: 市场数据
            
        Returns:
            执行计划
        """
        # 分析市场条件
        liquidity = market_data.get("liquidity", 1000000)
        volatility = market_data.get("volatility", 0.01)
        spread = market_data.get("spread", 0.001)
        trend = market_data.get("trend", "neutral")
        
        # 选择执行算法
        if order.amount < liquidity * 0.01:
            # 小订单，立即执行
            algorithm = ExecutionAlgorithm.IMMEDIATE
            slices = [{"amount": order.amount, "priority": "high"}]
            time_window = 1
            
        elif order.amount < liquidity * 0.05:
            # 中等订单，使用TWAP
            algorithm = ExecutionAlgorithm.TWAP
            slices = self.calculate_twap(order.amount, 300)  # 5分钟
            time_window = 300
            
        elif order.amount < liquidity * 0.20:
            # 大订单，使用VWAP或冰山
            if volatility < 0.02:
                algorithm = ExecutionAlgorithm.VWAP
                slices = self.calculate_vwap(order.amount, market_data.get("volume_profile", []))
            else:
                algorithm = ExecutionAlgorithm.ICEBERG
                slices = self.calculate_iceberg(order.amount)
            time_window = 1800  # 30分钟
            
        else:
            # 超大订单，自适应执行
            algorithm = ExecutionAlgorithm.ADAPTIVE
            slices = self._adaptive_slicing(order.amount, market_data)
            time_window = 3600  # 1小时
        
        # 计算紧急程度
        if volatility > 0.03 or abs(trend) == "strong":
            urgency = "high"
        elif volatility > 0.015:
            urgency = "medium"
        else:
            urgency = "low"
        
        # 估算执行成本
        estimated_slippage = self.estimate_slippage(order.amount, liquidity, urgency)
        estimated_cost = order.amount * order.price * (estimated_slippage + spread)
        
        return ExecutionPlan(
            algorithm=algorithm,
            total_amount=order.amount,
            slices=slices,
            time_window=time_window,
            urgency=urgency,
            max_slippage=min(estimated_slippage * 2, self.limits["max_slippage"]),
            estimated_cost=estimated_cost
        )
    
    async def _execute_order(self, order: Order, plan: ExecutionPlan):
        """执行订单（内部方法）"""
        start_time = time.time()
        total_filled = 0
        total_cost = 0
        
        try:
            for slice_info in plan.slices:
                if order.status == OrderStatus.CANCELLED:
                    break
                
                # 模拟执行延迟
                await asyncio.sleep(0.1)
                
                # 执行分片
                filled, cost = await self._execute_slice(order, slice_info)
                
                total_filled += filled
                total_cost += cost
                
                # 更新订单状态
                order.filled_amount = total_filled
                order.average_price = total_cost / total_filled if total_filled > 0 else 0
                order.updated_at = datetime.now()
                
                if total_filled >= order.amount * 0.99:  # 99%视为完全成交
                    order.status = OrderStatus.FILLED
                    break
                else:
                    order.status = OrderStatus.PARTIAL
            
            # 完成执行
            if order.status == OrderStatus.FILLED:
                del self.active_orders[order.order_id]
                self.stats["filled_orders"] += 1
                
                execution_time = time.time() - start_time
                self.stats["average_fill_time"] = (
                    self.stats["average_fill_time"] * 0.9 + execution_time * 0.1
                )
                
                logger.info(f"订单执行完成: {order.order_id}, "
                          f"成交量={total_filled:.2f}, "
                          f"均价={order.average_price:.2f}, "
                          f"耗时={execution_time:.1f}秒")
            
        except Exception as e:
            logger.error(f"订单执行失败: {e}")
            order.status = OrderStatus.REJECTED
    
    async def _execute_slice(self, order: Order, slice_info: Dict) -> Tuple[float, float]:
        """执行订单分片（模拟）"""
        # 这里应该调用实际的交易所API
        # 现在使用模拟执行
        
        amount = slice_info.get("amount", 0)
        
        # 模拟成交价格（加入随机滑点）
        slippage = np.random.uniform(-0.001, 0.002)
        if order.side == "buy":
            execution_price = order.price * (1 + slippage)
        else:
            execution_price = order.price * (1 - slippage)
        
        cost = amount * execution_price
        
        self.stats["total_slippage"] += abs(slippage)
        
        return amount, cost
    
    def _validate_order(self, order: Order) -> bool:
        """验证订单"""
        # 检查订单数量
        if order.amount <= 0 or order.amount > self.limits["max_order_size"]:
            logger.error(f"订单数量无效: {order.amount}")
            return False
        
        # 检查价格
        if order.order_type != OrderType.MARKET and (not order.price or order.price <= 0):
            logger.error(f"限价单价格无效: {order.price}")
            return False
        
        # 检查订单类型
        if order.side not in ["buy", "sell"]:
            logger.error(f"订单方向无效: {order.side}")
            return False
        
        return True
    
    def _create_execution_plan(self, order: Order, algorithm: ExecutionAlgorithm) -> ExecutionPlan:
        """创建执行计划"""
        if algorithm == ExecutionAlgorithm.TWAP:
            slices = self.calculate_twap(order.amount, 300)
            time_window = 300
        elif algorithm == ExecutionAlgorithm.VWAP:
            slices = self.calculate_vwap(order.amount, [])
            time_window = 600
        elif algorithm == ExecutionAlgorithm.ICEBERG:
            slices = self.calculate_iceberg(order.amount)
            time_window = 900
        else:
            # 默认立即执行
            slices = [{"amount": order.amount, "priority": "high"}]
            time_window = 1
        
        return ExecutionPlan(
            algorithm=algorithm,
            total_amount=order.amount,
            slices=slices,
            time_window=time_window,
            urgency="medium",
            max_slippage=self.limits["max_slippage"],
            estimated_cost=order.amount * order.price * 1.001
        )
    
    def _adaptive_slicing(self, amount: float, market_data: Dict) -> List[Dict]:
        """自适应分片（根据市场条件动态调整）"""
        volatility = market_data.get("volatility", 0.01)
        liquidity = market_data.get("liquidity", 1000000)
        
        # 根据波动率和流动性调整分片
        if volatility > 0.03:
            # 高波动，更多小片
            num_slices = min(50, int(amount / (liquidity * 0.001)))
        else:
            # 低波动，较少大片
            num_slices = min(20, int(amount / (liquidity * 0.005)))
        
        num_slices = max(5, num_slices)  # 至少5片
        
        # 使用正态分布分配数量（前后小，中间大）
        weights = np.random.normal(0.5, 0.15, num_slices)
        weights = np.abs(weights) / np.sum(np.abs(weights))
        
        slices = []
        for i, weight in enumerate(weights):
            slices.append({
                "index": i,
                "amount": amount * weight,
                "priority": "high" if i < 3 else "medium",
                "adaptive": True
            })
        
        return slices
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取订单状态"""
        return self.orders.get(order_id)
    
    def get_active_orders(self) -> List[Order]:
        """获取活动订单"""
        return list(self.active_orders.values())
    
    def get_execution_stats(self) -> Dict:
        """获取执行统计"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_orders": self.stats["total_orders"],
            "filled_orders": self.stats["filled_orders"],
            "cancelled_orders": self.stats["cancelled_orders"],
            "fill_rate": self.stats["filled_orders"] / self.stats["total_orders"] 
                        if self.stats["total_orders"] > 0 else 0,
            "average_slippage": self.stats["total_slippage"] / self.stats["filled_orders"]
                              if self.stats["filled_orders"] > 0 else 0,
            "average_fill_time": self.stats["average_fill_time"],
            "active_orders": len(self.active_orders)
        }


if __name__ == "__main__":
    # 测试代码
    async def test_execution():
        engine = ExecutionEngine()
        
        # 创建测试订单
        order = Order(
            order_id="TEST001",
            symbol="BTC/USDT",
            side="buy",
            amount=10.0,
            order_type=OrderType.LIMIT,
            price=50000.0
        )
        
        # 提交订单
        order_id = await engine.submit_order(order, ExecutionAlgorithm.TWAP)
        print(f"订单已提交: {order_id}")
        
        # 等待执行
        await asyncio.sleep(2)
        
        # 查询状态
        status = engine.get_order_status(order_id)
        print(f"订单状态: {status.status.value}")
        print(f"成交量: {status.filled_amount:.2f}")
        print(f"均价: {status.average_price:.2f}")
        
        # 执行统计
        stats = engine.get_execution_stats()
        print(f"\n执行统计: {stats}")
    
    # 运行测试
    asyncio.run(test_execution())