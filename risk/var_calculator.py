"""
Tiger系统 - VaR（在险价值）计算器
窗口：7号
功能：计算投资组合的风险价值，评估潜在最大损失
作者：Window-7 Risk Control Officer
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    amount: float
    entry_price: float
    current_price: float
    leverage: float = 1.0
    direction: str = "long"  # long or short


@dataclass
class VaRResult:
    """VaR计算结果"""
    var_95: float  # 95%置信度VaR
    var_99: float  # 99%置信度VaR
    cvar_95: float  # 95%条件VaR (CVaR/ES)
    cvar_99: float  # 99%条件VaR
    method: str  # 计算方法
    time_horizon: int  # 时间跨度（天）
    confidence_levels: Dict[float, float]  # 各置信度的VaR


class VaRCalculator:
    """
    VaR（Value at Risk）计算器
    支持多种计算方法：历史模拟法、参数法、蒙特卡洛模拟法
    """
    
    def __init__(self):
        """初始化VaR计算器"""
        self.default_confidence_levels = [0.90, 0.95, 0.99]
        self.default_time_horizon = 1  # 默认1天
        self.min_samples = 30  # 最少历史数据要求
        
    def calculate_historical_var(self, returns: np.ndarray, 
                                confidence_level: float = 0.95,
                                time_horizon: int = 1) -> float:
        """
        历史模拟法计算VaR
        
        Args:
            returns: 历史收益率数组
            confidence_level: 置信水平
            time_horizon: 时间跨度（天）
            
        Returns:
            VaR值
        """
        if len(returns) < self.min_samples:
            logger.warning(f"历史数据不足: {len(returns)} < {self.min_samples}")
            return 0
        
        # 调整到指定时间跨度
        scaled_returns = returns * np.sqrt(time_horizon)
        
        # 计算分位数
        var = np.percentile(scaled_returns, (1 - confidence_level) * 100)
        
        return abs(var)
    
    def calculate_parametric_var(self, returns: np.ndarray,
                                confidence_level: float = 0.95,
                                time_horizon: int = 1) -> float:
        """
        参数法（方差-协方差法）计算VaR
        假设收益率服从正态分布
        
        Args:
            returns: 历史收益率数组
            confidence_level: 置信水平
            time_horizon: 时间跨度（天）
            
        Returns:
            VaR值
        """
        if len(returns) < self.min_samples:
            return 0
        
        # 计算均值和标准差
        mean = np.mean(returns)
        std = np.std(returns)
        
        # 计算z值
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # 计算VaR
        var = -(mean * time_horizon + z_score * std * np.sqrt(time_horizon))
        
        return abs(var)
    
    def calculate_monte_carlo_var(self, returns: np.ndarray,
                                 confidence_level: float = 0.95,
                                 time_horizon: int = 1,
                                 simulations: int = 10000) -> float:
        """
        蒙特卡洛模拟法计算VaR
        
        Args:
            returns: 历史收益率数组
            confidence_level: 置信水平
            time_horizon: 时间跨度（天）
            simulations: 模拟次数
            
        Returns:
            VaR值
        """
        if len(returns) < self.min_samples:
            return 0
        
        # 计算参数
        mean = np.mean(returns)
        std = np.std(returns)
        
        # 生成模拟路径
        simulated_returns = np.random.normal(
            mean * time_horizon,
            std * np.sqrt(time_horizon),
            simulations
        )
        
        # 计算VaR
        var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
        
        return abs(var)
    
    def calculate_portfolio_var(self, positions: List[Position],
                               price_data: Dict[str, List[float]],
                               method: str = "historical",
                               confidence_level: float = 0.95) -> VaRResult:
        """
        计算投资组合VaR
        
        Args:
            positions: 持仓列表
            price_data: 各资产历史价格数据
            method: 计算方法 (historical/parametric/monte_carlo)
            confidence_level: 置信水平
            
        Returns:
            VaR计算结果
        """
        if not positions:
            logger.warning("无持仓，VaR为0")
            return self._empty_result()
        
        # 计算组合收益率
        portfolio_returns = self._calculate_portfolio_returns(positions, price_data)
        
        if len(portfolio_returns) < self.min_samples:
            logger.warning("历史数据不足，返回估算值")
            return self._estimate_var(positions)
        
        # 根据方法计算VaR
        var_values = {}
        for conf in self.default_confidence_levels:
            if method == "historical":
                var = self.calculate_historical_var(portfolio_returns, conf)
            elif method == "parametric":
                var = self.calculate_parametric_var(portfolio_returns, conf)
            elif method == "monte_carlo":
                var = self.calculate_monte_carlo_var(portfolio_returns, conf)
            else:
                logger.error(f"未知方法: {method}")
                var = 0
            
            var_values[conf] = var
        
        # 计算CVaR（条件VaR）
        cvar_95 = self._calculate_cvar(portfolio_returns, 0.95)
        cvar_99 = self._calculate_cvar(portfolio_returns, 0.99)
        
        # 转换为金额
        total_value = sum(p.amount * p.current_price for p in positions)
        
        return VaRResult(
            var_95=var_values.get(0.95, 0) * total_value,
            var_99=var_values.get(0.99, 0) * total_value,
            cvar_95=cvar_95 * total_value,
            cvar_99=cvar_99 * total_value,
            method=method,
            time_horizon=1,
            confidence_levels={k: v * total_value for k, v in var_values.items()}
        )
    
    def calculate_marginal_var(self, positions: List[Position],
                              price_data: Dict[str, List[float]],
                              target_position: Position) -> float:
        """
        计算边际VaR（增加某个持仓对组合VaR的影响）
        
        Args:
            positions: 当前持仓列表
            price_data: 价格数据
            target_position: 目标持仓
            
        Returns:
            边际VaR
        """
        # 计算当前组合VaR
        current_var = self.calculate_portfolio_var(positions, price_data)
        
        # 计算加入新仓位后的VaR
        new_positions = positions + [target_position]
        new_var = self.calculate_portfolio_var(new_positions, price_data)
        
        # 边际VaR
        marginal_var = new_var.var_95 - current_var.var_95
        
        logger.info(f"边际VaR: {target_position.symbol} = {marginal_var:.2f}")
        
        return marginal_var
    
    def calculate_incremental_var(self, positions: List[Position],
                                 price_data: Dict[str, List[float]],
                                 position_change: Dict[str, float]) -> float:
        """
        计算增量VaR（仓位变化对VaR的影响）
        
        Args:
            positions: 当前持仓
            price_data: 价格数据
            position_change: 仓位变化 {symbol: change_amount}
            
        Returns:
            增量VaR
        """
        # 当前VaR
        current_var = self.calculate_portfolio_var(positions, price_data)
        
        # 更新仓位
        updated_positions = []
        for pos in positions:
            new_pos = Position(
                symbol=pos.symbol,
                amount=pos.amount + position_change.get(pos.symbol, 0),
                entry_price=pos.entry_price,
                current_price=pos.current_price,
                leverage=pos.leverage,
                direction=pos.direction
            )
            updated_positions.append(new_pos)
        
        # 新VaR
        new_var = self.calculate_portfolio_var(updated_positions, price_data)
        
        return new_var.var_95 - current_var.var_95
    
    def stress_test_var(self, positions: List[Position],
                       scenarios: List[Dict[str, float]]) -> List[Dict]:
        """
        压力测试VaR
        
        Args:
            positions: 持仓列表
            scenarios: 压力场景列表 [{symbol: price_change_percent}]
            
        Returns:
            各场景下的损失
        """
        results = []
        
        for i, scenario in enumerate(scenarios):
            total_loss = 0
            
            for pos in positions:
                if pos.symbol in scenario:
                    price_change = scenario[pos.symbol]
                    
                    if pos.direction == "long":
                        loss = pos.amount * pos.current_price * price_change * pos.leverage
                    else:  # short
                        loss = -pos.amount * pos.current_price * price_change * pos.leverage
                    
                    total_loss += loss
            
            results.append({
                "scenario": f"Scenario_{i+1}",
                "loss": abs(total_loss),
                "loss_percent": abs(total_loss) / sum(p.amount * p.current_price for p in positions),
                "details": scenario
            })
        
        return results
    
    def calculate_correlation_matrix(self, price_data: Dict[str, List[float]]) -> pd.DataFrame:
        """
        计算资产相关性矩阵
        
        Args:
            price_data: 各资产价格数据
            
        Returns:
            相关性矩阵
        """
        # 转换为DataFrame
        df = pd.DataFrame(price_data)
        
        # 计算收益率
        returns = df.pct_change().dropna()
        
        # 计算相关性
        correlation = returns.corr()
        
        return correlation
    
    def risk_decomposition(self, positions: List[Position],
                          price_data: Dict[str, List[float]]) -> Dict:
        """
        风险分解（各资产对总VaR的贡献）
        
        Args:
            positions: 持仓列表
            price_data: 价格数据
            
        Returns:
            风险分解结果
        """
        total_var = self.calculate_portfolio_var(positions, price_data)
        
        contributions = {}
        
        for pos in positions:
            # 计算去掉该资产后的VaR
            other_positions = [p for p in positions if p.symbol != pos.symbol]
            
            if other_positions:
                var_without = self.calculate_portfolio_var(other_positions, price_data)
                contribution = total_var.var_95 - var_without.var_95
            else:
                contribution = total_var.var_95
            
            contributions[pos.symbol] = {
                "absolute_contribution": contribution,
                "percentage_contribution": contribution / total_var.var_95 if total_var.var_95 > 0 else 0,
                "position_value": pos.amount * pos.current_price
            }
        
        return {
            "total_var": total_var.var_95,
            "contributions": contributions,
            "correlation_matrix": self.calculate_correlation_matrix(price_data).to_dict()
        }
    
    def _calculate_portfolio_returns(self, positions: List[Position],
                                    price_data: Dict[str, List[float]]) -> np.ndarray:
        """计算组合收益率"""
        if not price_data:
            return np.array([])
        
        # 计算各资产收益率
        returns_dict = {}
        for symbol, prices in price_data.items():
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                returns_dict[symbol] = returns
        
        if not returns_dict:
            return np.array([])
        
        # 计算权重
        total_value = sum(p.amount * p.current_price for p in positions)
        weights = {}
        for pos in positions:
            weight = (pos.amount * pos.current_price) / total_value
            weights[pos.symbol] = weight * pos.leverage
        
        # 计算组合收益率
        min_length = min(len(r) for r in returns_dict.values())
        portfolio_returns = np.zeros(min_length)
        
        for symbol, weight in weights.items():
            if symbol in returns_dict:
                asset_returns = returns_dict[symbol][:min_length]
                portfolio_returns += weight * asset_returns
        
        return portfolio_returns
    
    def _calculate_cvar(self, returns: np.ndarray, confidence_level: float) -> float:
        """计算条件VaR（CVaR/Expected Shortfall）"""
        if len(returns) == 0:
            return 0
        
        var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
        conditional_returns = returns[returns <= var_threshold]
        
        if len(conditional_returns) > 0:
            cvar = np.mean(conditional_returns)
        else:
            cvar = var_threshold
        
        return abs(cvar)
    
    def _empty_result(self) -> VaRResult:
        """返回空结果"""
        return VaRResult(
            var_95=0,
            var_99=0,
            cvar_95=0,
            cvar_99=0,
            method="none",
            time_horizon=1,
            confidence_levels={0.95: 0, 0.99: 0}
        )
    
    def _estimate_var(self, positions: List[Position]) -> VaRResult:
        """估算VaR（数据不足时）"""
        total_value = sum(p.amount * p.current_price for p in positions)
        
        # 使用经验值估算
        estimated_volatility = 0.02  # 假设2%日波动率
        
        return VaRResult(
            var_95=total_value * estimated_volatility * 1.65,  # 95%置信度
            var_99=total_value * estimated_volatility * 2.33,  # 99%置信度
            cvar_95=total_value * estimated_volatility * 2.06,
            cvar_99=total_value * estimated_volatility * 2.67,
            method="estimated",
            time_horizon=1,
            confidence_levels={
                0.95: total_value * estimated_volatility * 1.65,
                0.99: total_value * estimated_volatility * 2.33
            }
        )
    
    def get_risk_metrics(self, positions: List[Position],
                        price_data: Dict[str, List[float]]) -> Dict:
        """
        获取完整的风险指标
        
        Args:
            positions: 持仓列表
            price_data: 价格数据
            
        Returns:
            风险指标汇总
        """
        # 计算三种方法的VaR
        historical_var = self.calculate_portfolio_var(positions, price_data, "historical")
        parametric_var = self.calculate_portfolio_var(positions, price_data, "parametric")
        monte_carlo_var = self.calculate_portfolio_var(positions, price_data, "monte_carlo")
        
        # 压力测试场景
        stress_scenarios = [
            {"BTC": -0.20, "ETH": -0.25},  # 加密货币暴跌
            {"BTC": -0.10, "ETH": -0.10},  # 温和下跌
            {"BTC": -0.30, "ETH": -0.35},  # 极端下跌
        ]
        stress_results = self.stress_test_var(positions, stress_scenarios)
        
        # 风险分解
        decomposition = self.risk_decomposition(positions, price_data)
        
        # 总价值
        total_value = sum(p.amount * p.current_price for p in positions)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_portfolio_value": total_value,
            "var_metrics": {
                "historical": {
                    "var_95": historical_var.var_95,
                    "var_99": historical_var.var_99,
                    "cvar_95": historical_var.cvar_95,
                    "cvar_99": historical_var.cvar_99
                },
                "parametric": {
                    "var_95": parametric_var.var_95,
                    "var_99": parametric_var.var_99
                },
                "monte_carlo": {
                    "var_95": monte_carlo_var.var_95,
                    "var_99": monte_carlo_var.var_99
                }
            },
            "var_as_percent_of_portfolio": {
                "var_95": (historical_var.var_95 / total_value) if total_value > 0 else 0,
                "var_99": (historical_var.var_99 / total_value) if total_value > 0 else 0
            },
            "stress_test_results": stress_results,
            "risk_decomposition": decomposition,
            "risk_limits": {
                "var_95_limit": total_value * 0.10,  # 10% VaR限制
                "var_99_limit": total_value * 0.15,  # 15% VaR限制
                "within_limits": historical_var.var_95 < total_value * 0.10
            }
        }


if __name__ == "__main__":
    # 测试代码
    calculator = VaRCalculator()
    
    # 创建测试持仓
    positions = [
        Position("BTC", 1.0, 50000, 51000, leverage=2.0),
        Position("ETH", 10.0, 3000, 3100, leverage=1.5),
    ]
    
    # 模拟价格数据
    np.random.seed(42)
    price_data = {
        "BTC": [50000 + np.random.randn() * 1000 for _ in range(100)],
        "ETH": [3000 + np.random.randn() * 100 for _ in range(100)]
    }
    
    # 计算VaR
    var_result = calculator.calculate_portfolio_var(positions, price_data)
    print(f"95% VaR: ${var_result.var_95:,.2f}")
    print(f"99% VaR: ${var_result.var_99:,.2f}")
    print(f"95% CVaR: ${var_result.cvar_95:,.2f}")
    
    # 获取完整风险指标
    metrics = calculator.get_risk_metrics(positions, price_data)
    print(f"\n风险指标汇总:")
    print(f"组合总价值: ${metrics['total_portfolio_value']:,.2f}")
    print(f"VaR占比: {metrics['var_as_percent_of_portfolio']['var_95']:.2%}")
    print(f"风险限制内: {metrics['risk_limits']['within_limits']}")