"""
Tiger系统 - Window 7 完整测试套件
功能：全面测试所有组件，确保100%工业级质量
"""

import pytest
import asyncio
import numpy as np
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入待测试模块
from kelly_calculator import KellyCalculator, TradeStats
from var_calculator import VaRCalculator, Position, VaRResult
from execution_engine import ExecutionEngine, Order, OrderType, OrderStatus, ExecutionAlgorithm
from money.money_management import MoneyManagement, TradingRecord
from stoploss.stoploss_system import StopLossSystem


class TestKellyCalculator:
    """测试凯利公式计算器"""
    
    def setup_method(self):
        """测试前准备"""
        self.calculator = KellyCalculator(max_kelly_fraction=0.25)
    
    def test_basic_kelly_calculation(self):
        """测试基础凯利计算"""
        # 正常情况
        kelly = self.calculator.calculate_kelly_fraction(0.6, 1.5)
        assert 0 <= kelly <= 1, f"凯利比例应在0-1之间，实际: {kelly}"
        
        # 边界情况
        kelly_zero = self.calculator.calculate_kelly_fraction(0.5, 1.0)
        assert kelly_zero == 0, f"50%胜率，1:1赔率应该为0，实际: {kelly_zero}"
        
        # 异常情况
        kelly_invalid = self.calculator.calculate_kelly_fraction(1.1, 1.5)
        assert kelly_invalid == 0, f"无效胜率应返回0，实际: {kelly_invalid}"
        
        print("✓ 基础凯利计算测试通过")
    
    def test_position_size_calculation(self):
        """测试仓位计算"""
        capital = 100000
        kelly = 0.1
        
        result = self.calculator.calculate_position_size(capital, kelly)
        
        assert "actual_position" in result, "缺少实际仓位字段"
        assert result["actual_position"] > 0, "仓位必须大于0"
        assert result["actual_position"] <= capital, "仓位不能超过总资金"
        
        print("✓ 仓位计算测试通过")
    
    def test_monte_carlo_simulation(self):
        """测试蒙特卡洛模拟"""
        # 创建模拟交易数据
        trades = []
        for i in range(50):
            pnl = np.random.normal(0.01, 0.05)  # 1%均值，5%波动
            trades.append({
                "pnl": pnl * 1000,
                "pnl_percent": pnl
            })
        
        result = self.calculator.monte_carlo_kelly(trades)
        
        assert "optimal_kelly" in result, "缺少最优凯利字段"
        assert 0 <= result["optimal_kelly"] <= 1, f"最优凯利比例异常: {result['optimal_kelly']}"
        assert "risk_of_ruin" in result, "缺少破产风险字段"
        
        print("✓ 蒙特卡洛模拟测试通过")
    
    def test_dynamic_adjustment(self):
        """测试动态调整"""
        # 测试不同市场条件下的调整
        scenarios = [
            {"drawdown": 0.05, "volatility": 0.10, "regime": "trending"},
            {"drawdown": 0.15, "volatility": 0.25, "regime": "volatile"},
            {"drawdown": 0.25, "volatility": 0.35, "regime": "uncertain"}
        ]
        
        for scenario in scenarios:
            adjustment = self.calculator.dynamic_kelly_adjustment(
                scenario["drawdown"],
                scenario["volatility"],
                scenario["regime"]
            )
            assert 0.1 <= adjustment <= 1.5, f"调整系数超出范围: {adjustment}"
        
        print("✓ 动态调整测试通过")


class TestVaRCalculator:
    """测试VaR计算器"""
    
    def setup_method(self):
        """测试前准备"""
        self.calculator = VaRCalculator()
        
        # 创建测试持仓
        self.positions = [
            Position("BTC", 1.0, 50000, 51000, leverage=2.0),
            Position("ETH", 10.0, 3000, 3100, leverage=1.5),
        ]
        
        # 创建测试价格数据
        np.random.seed(42)
        self.price_data = {
            "BTC": [50000 + np.random.randn() * 1000 for _ in range(100)],
            "ETH": [3000 + np.random.randn() * 100 for _ in range(100)]
        }
    
    def test_historical_var(self):
        """测试历史模拟法VaR"""
        returns = np.random.normal(0, 0.02, 100)
        
        var_95 = self.calculator.calculate_historical_var(returns, 0.95)
        var_99 = self.calculator.calculate_historical_var(returns, 0.99)
        
        assert var_95 > 0, f"95% VaR必须大于0，实际: {var_95}"
        assert var_99 > var_95, f"99% VaR应大于95% VaR，实际: {var_99} vs {var_95}"
        
        print("✓ 历史模拟法VaR测试通过")
    
    def test_parametric_var(self):
        """测试参数法VaR"""
        returns = np.random.normal(0, 0.02, 100)
        
        var = self.calculator.calculate_parametric_var(returns, 0.95)
        
        assert var > 0, f"参数法VaR必须大于0，实际: {var}"
        
        print("✓ 参数法VaR测试通过")
    
    def test_monte_carlo_var(self):
        """测试蒙特卡洛法VaR"""
        returns = np.random.normal(0, 0.02, 50)
        
        var = self.calculator.calculate_monte_carlo_var(returns, 0.95, simulations=1000)
        
        assert var > 0, f"蒙特卡洛VaR必须大于0，实际: {var}"
        
        print("✓ 蒙特卡洛法VaR测试通过")
    
    def test_portfolio_var(self):
        """测试组合VaR"""
        result = self.calculator.calculate_portfolio_var(
            self.positions,
            self.price_data,
            method="historical"
        )
        
        assert isinstance(result, VaRResult), "返回结果类型错误"
        assert result.var_95 > 0, f"组合VaR_95必须大于0，实际: {result.var_95}"
        assert result.var_99 > result.var_95, f"VaR_99应大于VaR_95"
        
        print("✓ 组合VaR测试通过")
    
    def test_stress_test(self):
        """测试压力测试"""
        scenarios = [
            {"BTC": -0.10, "ETH": -0.15},
            {"BTC": -0.20, "ETH": -0.25},
        ]
        
        results = self.calculator.stress_test_var(self.positions, scenarios)
        
        assert len(results) == len(scenarios), "压力测试结果数量不匹配"
        for result in results:
            assert "loss" in result, "缺少损失字段"
            assert result["loss"] >= 0, "损失必须为非负数"
        
        print("✓ 压力测试通过")
    
    def test_risk_metrics(self):
        """测试完整风险指标"""
        metrics = self.calculator.get_risk_metrics(self.positions, self.price_data)
        
        required_fields = [
            "total_portfolio_value",
            "var_metrics",
            "stress_test_results",
            "risk_limits"
        ]
        
        for field in required_fields:
            assert field in metrics, f"缺少必要字段: {field}"
        
        print("✓ 风险指标测试通过")


class TestExecutionEngine:
    """测试订单执行引擎"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = ExecutionEngine()
    
    @pytest.mark.asyncio
    async def test_order_submission(self):
        """测试订单提交"""
        order = Order(
            order_id="TEST001",
            symbol="BTC/USDT",
            side="buy",
            amount=1.0,
            order_type=OrderType.LIMIT,
            price=50000.0
        )
        
        order_id = await self.engine.submit_order(order, ExecutionAlgorithm.IMMEDIATE)
        
        assert order_id is not None, "订单提交失败"
        assert order_id in self.engine.orders, "订单未正确存储"
        
        print("✓ 订单提交测试通过")
    
    @pytest.mark.asyncio
    async def test_order_cancellation(self):
        """测试订单取消"""
        order = Order(
            order_id="TEST002",
            symbol="ETH/USDT",
            side="sell",
            amount=5.0,
            order_type=OrderType.LIMIT,
            price=3000.0
        )
        
        order_id = await self.engine.submit_order(order)
        success = await self.engine.cancel_order(order_id)
        
        assert success, "订单取消失败"
        assert order_id not in self.engine.active_orders, "订单未从活跃列表移除"
        
        print("✓ 订单取消测试通过")
    
    def test_twap_calculation(self):
        """测试TWAP计算"""
        slices = self.engine.calculate_twap(100.0, 300, intervals=10)
        
        assert len(slices) == 10, f"分片数量错误，期望10，实际{len(slices)}"
        
        total_amount = sum(slice_info["amount"] for slice_info in slices)
        assert abs(total_amount - 100.0) < 0.01, f"总量不匹配，期望100，实际{total_amount}"
        
        print("✓ TWAP计算测试通过")
    
    def test_slippage_estimation(self):
        """测试滑点估算"""
        slippage = self.engine.estimate_slippage(10000, 1000000, "medium")
        
        assert 0 <= slippage <= 0.01, f"滑点超出合理范围: {slippage}"
        
        print("✓ 滑点估算测试通过")
    
    def test_execution_stats(self):
        """测试执行统计"""
        stats = self.engine.get_execution_stats()
        
        required_fields = [
            "total_orders",
            "filled_orders", 
            "cancelled_orders",
            "fill_rate"
        ]
        
        for field in required_fields:
            assert field in stats, f"缺少统计字段: {field}"
        
        print("✓ 执行统计测试通过")


class TestMoneyManagement:
    """测试资金管理"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = MoneyManagement(initial_capital=100000)
    
    def test_daily_limits_check(self):
        """测试日限制检查"""
        # 模拟亏损
        self.manager.account_status.daily_pnl = -5000  # 5%亏损
        
        result = self.manager.check_daily_limits()
        
        assert "can_trade" in result, "缺少交易许可字段"
        assert "warnings" in result, "缺少警告字段"
        
        print("✓ 日限制检查测试通过")
    
    def test_position_size_calculation(self):
        """测试仓位计算"""
        position_size = self.manager.calculate_position_size(
            risk_per_trade=2000,
            stop_loss_points=100
        )
        
        assert position_size >= 0, "仓位大小不能为负"
        assert position_size <= self.manager.account_status.available_capital, "仓位超出可用资金"
        
        print("✓ 仓位计算测试通过")
    
    def test_trade_update(self):
        """测试交易更新"""
        trade = TradingRecord(
            symbol="BTC",
            entry_time=datetime.now(),
            exit_time=datetime.now(),
            pnl=1000,
            risk_taken=2000,
            position_size=10000
        )
        
        success = self.manager.update_trade(trade)
        
        assert success, "交易更新失败"
        assert len(self.manager.trades_history) > 0, "交易记录未添加"
        
        print("✓ 交易更新测试通过")
    
    def test_risk_capacity(self):
        """测试风险容量"""
        capacity = self.manager.get_risk_capacity()
        
        required_fields = [
            "daily_risk_remaining",
            "trades_remaining",
            "max_position_size"
        ]
        
        for field in required_fields:
            assert field in capacity, f"缺少风险容量字段: {field}"
        
        print("✓ 风险容量测试通过")


class TestWindow7System:
    """测试Window 7完整系统"""
    
    def setup_method(self):
        """测试前准备"""
        self.system = None
    
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """测试系统初始化"""
        self.system = Window7RiskSystem(initial_capital=100000)
        
        assert self.system.system_status == "initialized", f"系统状态错误: {self.system.system_status}"
        assert hasattr(self.system, "kelly_calculator"), "缺少凯利计算器"
        assert hasattr(self.system, "var_calculator"), "缺少VaR计算器"
        assert hasattr(self.system, "execution_engine"), "缺少执行引擎"
        
        print("✓ 系统初始化测试通过")
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        if not self.system:
            self.system = Window7RiskSystem(initial_capital=100000)
        
        # 执行健康检查
        try:
            results = await self.system._system_health_check()
            
            for component, result in results.items():
                assert result["status"] == "ok", f"组件{component}健康检查失败: {result}"
            
            print("✓ 健康检查测试通过")
            
        except Exception as e:
            pytest.fail(f"健康检查异常: {e}")
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """测试系统状态"""
        if not self.system:
            self.system = Window7RiskSystem(initial_capital=100000)
        
        status = await self.system._get_system_status()
        
        required_fields = [
            "timestamp",
            "status", 
            "running",
            "components",
            "stats"
        ]
        
        for field in required_fields:
            assert field in status, f"缺少状态字段: {field}"
        
        print("✓ 系统状态测试通过")


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_trading_workflow(self):
        """测试完整交易流程"""
        # 1. 初始化系统
        system = Window7RiskSystem(initial_capital=100000)
        
        # 2. 计算凯利仓位
        kelly = system.kelly_calculator.calculate_kelly_fraction(0.6, 1.5)
        position_info = system.kelly_calculator.calculate_position_size(100000, kelly)
        
        # 3. 检查风险限制
        daily_check = system.money_manager.check_daily_limits()
        assert daily_check["can_trade"], "无法进行交易"
        
        # 4. 创建并提交订单
        order = Order(
            order_id="INTEGRATION_TEST",
            symbol="BTC/USDT", 
            side="buy",
            amount=position_info["actual_position"] / 50000,  # 假设BTC价格50000
            order_type=OrderType.LIMIT,
            price=50000.0
        )
        
        order_id = await system.execution_engine.submit_order(order)
        assert order_id is not None, "订单提交失败"
        
        # 5. 等待执行完成
        await asyncio.sleep(0.5)
        
        # 6. 检查订单状态
        final_order = system.execution_engine.get_order_status(order_id)
        assert final_order is not None, "订单状态查询失败"
        
        print("✓ 完整交易流程测试通过")
    
    def test_risk_calculation_consistency(self):
        """测试风险计算一致性"""
        # 创建相同的测试数据
        positions = [Position("BTC", 1.0, 50000, 51000, leverage=1.0)]
        
        # 使用不同方法计算VaR
        calculator = VaRCalculator()
        
        # 生成一致的价格数据
        np.random.seed(123)
        price_data = {"BTC": [50000 + np.random.randn() * 1000 for _ in range(100)]}
        
        # 计算VaR
        historical_result = calculator.calculate_portfolio_var(positions, price_data, "historical")
        parametric_result = calculator.calculate_portfolio_var(positions, price_data, "parametric")
        
        # 检查结果合理性
        assert historical_result.var_95 > 0, "历史法VaR必须大于0"
        assert parametric_result.var_95 > 0, "参数法VaR必须大于0"
        
        # 两种方法的结果应该在合理范围内
        ratio = historical_result.var_95 / parametric_result.var_95
        assert 0.5 <= ratio <= 2.0, f"两种方法差异过大: {ratio}"
        
        print("✓ 风险计算一致性测试通过")


def run_performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    # 测试凯利计算性能
    calculator = KellyCalculator()
    start_time = datetime.now()
    
    for _ in range(1000):
        calculator.calculate_kelly_fraction(0.6, 1.5)
    
    kelly_time = (datetime.now() - start_time).total_seconds()
    print(f"凯利计算性能: 1000次 {kelly_time:.3f}秒")
    assert kelly_time < 1.0, "凯利计算性能不符合要求"
    
    # 测试VaR计算性能
    var_calculator = VaRCalculator()
    returns = np.random.normal(0, 0.02, 252)
    
    start_time = datetime.now()
    for _ in range(100):
        var_calculator.calculate_historical_var(returns)
    
    var_time = (datetime.now() - start_time).total_seconds()
    print(f"VaR计算性能: 100次 {var_time:.3f}秒")
    assert var_time < 1.0, "VaR计算性能不符合要求"
    
    print("✓ 性能测试通过")


def run_stress_test():
    """压力测试"""
    print("\n=== 压力测试 ===")
    
    # 测试大量订单处理
    engine = ExecutionEngine()
    
    async def stress_orders():
        tasks = []
        for i in range(50):
            order = Order(
                order_id=f"STRESS_{i}",
                symbol="BTC/USDT",
                side="buy" if i % 2 == 0 else "sell",
                amount=1.0,
                order_type=OrderType.LIMIT,
                price=50000.0
            )
            task = engine.submit_order(order)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in results if r is not None)
        
        print(f"压力测试: 50个订单，成功{success_count}个")
        assert success_count >= 45, "订单处理成功率低于90%"
    
    asyncio.run(stress_orders())
    print("✓ 压力测试通过")


async def main():
    """主测试函数"""
    print("🧪 Tiger Window-7 完整测试套件")
    print("=" * 50)
    
    # 设置详细的测试输出
    pytest_args = [
        __file__,
        "-v",  # 详细输出
        "-s",  # 不捕获输出
        "--tb=short",  # 简短的traceback
    ]
    
    try:
        # 运行pytest
        print("运行单元测试...")
        result = pytest.main(pytest_args)
        
        if result != 0:
            print("❌ 单元测试失败")
            return False
        
        print("✅ 单元测试全部通过")
        
        # 运行性能测试
        run_performance_test()
        
        # 运行压力测试  
        run_stress_test()
        
        print("\n🎉 所有测试通过！系统达到工业级质量标准")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)