"""
Tiger系统 - Window 7 API接口
窗口：7号
功能：提供风控和执行服务的RESTful API接口
作者：Window-7 Risk Control Officer
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uvicorn
import logging
import asyncio

# 导入内部模块
from kelly_calculator import KellyCalculator
from var_calculator import VaRCalculator, Position
from execution_engine import ExecutionEngine, Order, OrderType, ExecutionAlgorithm, OrderStatus
from money.money_management import MoneyManagement, TradingRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Tiger Window-7 Risk Control API",
    description="风控执行工具API接口",
    version="7.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
kelly_calculator = KellyCalculator()
var_calculator = VaRCalculator()
execution_engine = ExecutionEngine()
money_manager = MoneyManagement(initial_capital=100000)


# ==================== 请求模型 ====================

class KellyRequest(BaseModel):
    """凯利公式请求"""
    win_rate: float = Field(..., ge=0, le=1, description="胜率")
    win_loss_ratio: float = Field(..., gt=0, description="盈亏比")
    capital: float = Field(..., gt=0, description="账户资金")
    trades: Optional[List[Dict]] = Field(None, description="历史交易")
    market_conditions: Optional[Dict] = Field(None, description="市场条件")


class VaRRequest(BaseModel):
    """VaR计算请求"""
    positions: List[Dict] = Field(..., description="持仓列表")
    price_data: Dict[str, List[float]] = Field(..., description="价格数据")
    method: str = Field("historical", description="计算方法")
    confidence_level: float = Field(0.95, description="置信水平")


class PositionSizeRequest(BaseModel):
    """仓位计算请求"""
    capital: float = Field(..., gt=0, description="账户资金")
    risk_percent: float = Field(..., ge=0, le=1, description="风险比例")
    entry_price: float = Field(..., gt=0, description="入场价格")
    stop_price: float = Field(..., gt=0, description="止损价格")
    leverage: Optional[float] = Field(1.0, description="杠杆倍数")


class OrderRequest(BaseModel):
    """订单请求"""
    symbol: str = Field(..., description="交易对")
    side: str = Field(..., pattern="^(buy|sell)$", description="方向")
    amount: float = Field(..., gt=0, description="数量")
    order_type: str = Field("limit", description="订单类型")
    price: Optional[float] = Field(None, description="价格")
    algorithm: Optional[str] = Field("immediate", description="执行算法")
    urgency: Optional[str] = Field("medium", description="紧急程度")


class StopLossRequest(BaseModel):
    """止损设置请求"""
    symbol: str = Field(..., description="交易对")
    entry_price: float = Field(..., gt=0, description="入场价格")
    method: str = Field("percent", description="止损方法")
    params: Dict = Field(..., description="止损参数")


class RiskCheckRequest(BaseModel):
    """风险检查请求"""
    symbol: str = Field(..., description="交易对")
    amount: float = Field(..., description="数量")
    leverage: float = Field(1.0, description="杠杆")
    side: str = Field(..., pattern="^(buy|sell)$", description="方向")


# ==================== API端点 ====================

@app.get("/")
async def root():
    """API根路径"""
    return {
        "service": "Tiger Window-7 Risk Control",
        "version": "7.1.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "components": {
            "kelly_calculator": "ok",
            "var_calculator": "ok",
            "execution_engine": "ok",
            "money_manager": "ok",
            "stoploss_system": "ok"
        },
        "timestamp": datetime.now().isoformat()
    }


# ==================== 凯利公式相关 ====================

@app.post("/kelly/calculate")
async def calculate_kelly(request: KellyRequest):
    """计算凯利公式"""
    try:
        # 基础凯利计算
        kelly_fraction = kelly_calculator.calculate_kelly_fraction(
            request.win_rate,
            request.win_loss_ratio
        )
        
        # 如果有历史交易，计算优化凯利
        if request.trades:
            optimal_kelly = kelly_calculator.calculate_optimal_fraction(request.trades)
        else:
            optimal_kelly = kelly_fraction
        
        # 计算仓位大小
        position_info = kelly_calculator.calculate_position_size(
            request.capital,
            optimal_kelly
        )
        
        # 如果有市场条件，获取完整建议
        if request.market_conditions:
            recommendation = kelly_calculator.get_recommendation(
                request.capital,
                request.trades or [],
                request.market_conditions
            )
        else:
            recommendation = None
        
        return {
            "status": "success",
            "data": {
                "kelly_fraction": kelly_fraction,
                "optimal_kelly": optimal_kelly,
                "position_size": position_info,
                "recommendation": recommendation
            }
        }
    except Exception as e:
        logger.error(f"凯利计算失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kelly/monte_carlo")
async def kelly_monte_carlo(request: KellyRequest):
    """蒙特卡洛优化凯利"""
    try:
        if not request.trades:
            raise HTTPException(status_code=400, detail="需要历史交易数据")
        
        result = kelly_calculator.monte_carlo_kelly(request.trades)
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"蒙特卡洛失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VaR相关 ====================

@app.post("/var/calculate")
async def calculate_var(request: VaRRequest):
    """计算VaR"""
    try:
        # 转换持仓格式
        positions = [
            Position(
                symbol=p["symbol"],
                amount=p["amount"],
                entry_price=p["entry_price"],
                current_price=p["current_price"],
                leverage=p.get("leverage", 1.0),
                direction=p.get("direction", "long")
            )
            for p in request.positions
        ]
        
        # 计算VaR
        var_result = var_calculator.calculate_portfolio_var(
            positions,
            request.price_data,
            request.method,
            request.confidence_level
        )
        
        return {
            "status": "success",
            "data": {
                "var_95": var_result.var_95,
                "var_99": var_result.var_99,
                "cvar_95": var_result.cvar_95,
                "cvar_99": var_result.cvar_99,
                "method": var_result.method,
                "confidence_levels": var_result.confidence_levels
            }
        }
    except Exception as e:
        logger.error(f"VaR计算失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/var/stress_test")
async def var_stress_test(request: VaRRequest):
    """VaR压力测试"""
    try:
        positions = [
            Position(
                symbol=p["symbol"],
                amount=p["amount"],
                entry_price=p["entry_price"],
                current_price=p["current_price"],
                leverage=p.get("leverage", 1.0),
                direction=p.get("direction", "long")
            )
            for p in request.positions
        ]
        
        # 定义压力场景
        scenarios = [
            {"BTC": -0.10, "ETH": -0.15},  # 温和下跌
            {"BTC": -0.20, "ETH": -0.25},  # 中度下跌
            {"BTC": -0.30, "ETH": -0.35},  # 严重下跌
        ]
        
        results = var_calculator.stress_test_var(positions, scenarios)
        
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        logger.error(f"压力测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/var/risk_metrics")
async def get_risk_metrics(request: VaRRequest):
    """获取完整风险指标"""
    try:
        positions = [
            Position(
                symbol=p["symbol"],
                amount=p["amount"],
                entry_price=p["entry_price"],
                current_price=p["current_price"],
                leverage=p.get("leverage", 1.0),
                direction=p.get("direction", "long")
            )
            for p in request.positions
        ]
        
        metrics = var_calculator.get_risk_metrics(positions, request.price_data)
        
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 仓位管理相关 ====================

@app.post("/position/calculate")
async def calculate_position_size(request: PositionSizeRequest):
    """计算仓位大小"""
    try:
        # 计算止损距离
        stop_distance = abs(request.entry_price - request.stop_price)
        stop_percent = stop_distance / request.entry_price
        
        # 计算风险金额
        risk_amount = request.capital * request.risk_percent
        
        # 计算仓位大小
        position_size = risk_amount / stop_distance
        
        # 考虑杠杆
        actual_capital_needed = position_size * request.entry_price / request.leverage
        
        return {
            "status": "success",
            "data": {
                "position_size": position_size,
                "position_value": position_size * request.entry_price,
                "risk_amount": risk_amount,
                "stop_distance": stop_distance,
                "stop_percent": stop_percent,
                "capital_needed": actual_capital_needed,
                "leverage": request.leverage
            }
        }
    except Exception as e:
        logger.error(f"仓位计算失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/position/check_limit")
async def check_position_limit(request: RiskCheckRequest):
    """检查仓位限制"""
    try:
        # 使用money_manager检查
        daily_check = money_manager.check_daily_limits()
        weekly_check = money_manager.check_weekly_limits()
        
        # 计算仓位占比
        position_value = request.amount * request.leverage
        position_percent = position_value / money_manager.current_capital
        
        # 综合判断
        can_trade = daily_check["can_trade"] and position_percent <= 0.3
        
        return {
            "status": "success",
            "data": {
                "can_trade": can_trade,
                "position_percent": position_percent,
                "daily_status": daily_check,
                "weekly_status": weekly_check,
                "risk_capacity": money_manager.get_risk_capacity()
            }
        }
    except Exception as e:
        logger.error(f"检查仓位限制失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 订单执行相关 ====================

@app.post("/order/submit")
async def submit_order(request: OrderRequest, background_tasks: BackgroundTasks):
    """提交订单"""
    try:
        # 创建订单
        order = Order(
            order_id=f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            symbol=request.symbol,
            side=request.side,
            amount=request.amount,
            order_type=OrderType[request.order_type.upper()],
            price=request.price
        )
        
        # 选择执行算法
        algorithm = ExecutionAlgorithm[request.algorithm.upper()]
        
        # 提交订单（异步执行）
        order_id = await execution_engine.submit_order(order, algorithm)
        
        if not order_id:
            raise HTTPException(status_code=400, detail="订单提交失败")
        
        return {
            "status": "success",
            "data": {
                "order_id": order_id,
                "status": "submitted",
                "algorithm": algorithm.value
            }
        }
    except Exception as e:
        logger.error(f"提交订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/order/{order_id}")
async def cancel_order(order_id: str):
    """取消订单"""
    try:
        success = await execution_engine.cancel_order(order_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="订单不存在或无法取消")
        
        return {
            "status": "success",
            "message": f"订单 {order_id} 已取消"
        }
    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/order/{order_id}")
async def get_order_status(order_id: str):
    """查询订单状态"""
    try:
        order = execution_engine.get_order_status(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        return {
            "status": "success",
            "data": {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "amount": order.amount,
                "filled_amount": order.filled_amount,
                "average_price": order.average_price,
                "status": order.status.value,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"查询订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/active")
async def get_active_orders():
    """获取活动订单"""
    try:
        orders = execution_engine.get_active_orders()
        
        return {
            "status": "success",
            "data": [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "amount": order.amount,
                    "filled_amount": order.filled_amount,
                    "status": order.status.value
                }
                for order in orders
            ]
        }
    except Exception as e:
        logger.error(f"获取活动订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 止损相关 ====================

@app.post("/stoploss/calculate")
async def calculate_stoploss(request: StopLossRequest):
    """计算止损价格"""
    try:
        if request.method == "percent":
            stop_price = request.entry_price * (1 - request.params.get("percent", 0.02))
        elif request.method == "atr":
            # 这里需要历史价格数据计算ATR
            stop_price = request.entry_price - request.params.get("atr_multiplier", 2) * request.params.get("atr", 100)
        elif request.method == "fixed":
            stop_price = request.entry_price - request.params.get("amount", 100)
        else:
            stop_price = request.entry_price * 0.98  # 默认2%
        
        return {
            "status": "success",
            "data": {
                "symbol": request.symbol,
                "entry_price": request.entry_price,
                "stop_price": stop_price,
                "stop_distance": abs(request.entry_price - stop_price),
                "stop_percent": abs(request.entry_price - stop_price) / request.entry_price,
                "method": request.method
            }
        }
    except Exception as e:
        logger.error(f"计算止损失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 资金管理相关 ====================

@app.get("/money/status")
async def get_money_status():
    """获取资金管理状态"""
    try:
        status = money_manager.get_status()
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取资金状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/money/risk_capacity")
async def get_risk_capacity():
    """获取风险容量"""
    try:
        capacity = money_manager.get_risk_capacity()
        return {
            "status": "success",
            "data": capacity
        }
    except Exception as e:
        logger.error(f"获取风险容量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/money/update_trade")
async def update_trade(trade: Dict):
    """更新交易记录"""
    try:
        trading_record = TradingRecord(
            symbol=trade["symbol"],
            entry_time=datetime.fromisoformat(trade["entry_time"]),
            exit_time=datetime.fromisoformat(trade["exit_time"]) if trade.get("exit_time") else None,
            pnl=trade["pnl"],
            risk_taken=trade.get("risk_taken", 0),
            position_size=trade.get("position_size", 0)
        )
        
        success = money_manager.update_trade(trading_record)
        
        return {
            "status": "success" if success else "failed",
            "message": "交易记录已更新" if success else "更新失败"
        }
    except Exception as e:
        logger.error(f"更新交易记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 执行统计 ====================

@app.get("/stats/execution")
async def get_execution_stats():
    """获取执行统计"""
    try:
        stats = execution_engine.get_execution_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取执行统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 综合风控检查 ====================

@app.post("/risk/check")
async def comprehensive_risk_check(decision: Dict):
    """综合风控检查"""
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "can_trade": True,
            "checks": {},
            "warnings": [],
            "restrictions": []
        }
        
        # 1. 检查资金管理限制
        daily_limits = money_manager.check_daily_limits()
        if not daily_limits["can_trade"]:
            results["can_trade"] = False
            results["restrictions"].extend(daily_limits["restrictions"])
        results["checks"]["daily_limits"] = daily_limits
        
        # 2. 检查仓位限制
        if "amount" in decision and "price" in decision:
            position_value = decision["amount"] * decision.get("price", 0)
            position_percent = position_value / money_manager.current_capital
            
            if position_percent > 0.3:
                results["can_trade"] = False
                results["restrictions"].append(f"仓位占比过高: {position_percent:.1%}")
            results["checks"]["position_size"] = {
                "value": position_value,
                "percent": position_percent
            }
        
        # 3. 检查杠杆限制
        leverage = decision.get("leverage", 1)
        if leverage > 5:
            results["can_trade"] = False
            results["restrictions"].append(f"杠杆过高: {leverage}x")
        results["checks"]["leverage"] = leverage
        
        # 4. 检查风险容量
        risk_capacity = money_manager.get_risk_capacity()
        results["checks"]["risk_capacity"] = risk_capacity
        
        # 5. 综合评分
        risk_score = 0
        if daily_limits["can_trade"]:
            risk_score += 25
        if position_percent <= 0.2:
            risk_score += 25
        if leverage <= 3:
            risk_score += 25
        if risk_capacity["daily_risk_remaining"] > 0:
            risk_score += 25
        
        results["risk_score"] = risk_score
        results["risk_level"] = (
            "LOW" if risk_score >= 75 else
            "MEDIUM" if risk_score >= 50 else
            "HIGH"
        )
        
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        logger.error(f"风控检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 启动API服务
    uvicorn.run(
        "api_interface:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    )