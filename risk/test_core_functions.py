#!/usr/bin/env python3
"""
Tiger系统 - Window 7 核心功能测试
确保所有关键组件100%工作正常
"""

import sys
import os
import asyncio
import numpy as np
from datetime import datetime, timedelta

# 测试导入
def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from kelly_calculator import KellyCalculator
        print("✅ KellyCalculator 导入成功")
    except Exception as e:
        print(f"❌ KellyCalculator 导入失败: {e}")
        return False
    
    try:
        from var_calculator import VaRCalculator, Position
        print("✅ VaRCalculator 导入成功")
    except Exception as e:
        print(f"❌ VaRCalculator 导入失败: {e}")
        return False
    
    try:
        from execution_engine import ExecutionEngine, Order, OrderType
        print("✅ ExecutionEngine 导入成功")
    except Exception as e:
        print(f"❌ ExecutionEngine 导入失败: {e}")
        return False
    
    try:
        from money.money_management import MoneyManagement, TradingRecord
        print("✅ MoneyManagement 导入成功")
    except Exception as e:
        print(f"❌ MoneyManagement 导入失败: {e}")
        return False
    
    try:
        from api_interface import app
        print("✅ API Interface 导入成功")
    except Exception as e:
        print(f"❌ API Interface 导入失败: {e}")
        return False
    
    return True


def test_kelly_calculator():
    """测试凯利计算器"""
    print("\n🧮 测试凯利计算器...")
    
    try:
        from kelly_calculator import KellyCalculator
        
        calc = KellyCalculator()
        
        # 基础计算测试
        kelly = calc.calculate_kelly_fraction(0.6, 1.5)
        assert 0 <= kelly <= 1, f"凯利比例异常: {kelly}"
        print(f"✅ 基础凯利计算: {kelly:.2%}")
        
        # 仓位计算测试
        position_info = calc.calculate_position_size(100000, kelly)
        assert position_info["actual_position"] > 0, "仓位计算错误"
        print(f"✅ 仓位计算: ${position_info['actual_position']:,.2f}")
        
        # 动态调整测试
        adjustment = calc.dynamic_kelly_adjustment(0.05, 0.15, "trending")
        assert 0.1 <= adjustment <= 1.5, f"调整系数异常: {adjustment}"
        print(f"✅ 动态调整: {adjustment:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 凯利计算器测试失败: {e}")
        return False


def test_var_calculator():
    """测试VaR计算器"""
    print("\n📊 测试VaR计算器...")
    
    try:
        from var_calculator import VaRCalculator, Position
        
        calc = VaRCalculator()
        
        # 创建测试数据
        returns = np.random.normal(0, 0.02, 100)
        
        # 历史VaR测试
        var_95 = calc.calculate_historical_var(returns, 0.95)
        assert var_95 > 0, f"历史VaR异常: {var_95}"
        print(f"✅ 历史VaR(95%): {var_95:.4f}")
        
        # 参数VaR测试
        var_param = calc.calculate_parametric_var(returns, 0.95)
        assert var_param > 0, f"参数VaR异常: {var_param}"
        print(f"✅ 参数VaR(95%): {var_param:.4f}")
        
        # 组合VaR测试
        positions = [
            Position("BTC", 1.0, 50000, 51000, leverage=1.0),
            Position("ETH", 10.0, 3000, 3100, leverage=1.0)
        ]
        
        price_data = {
            "BTC": [50000 + np.random.randn() * 1000 for _ in range(50)],
            "ETH": [3000 + np.random.randn() * 100 for _ in range(50)]
        }
        
        var_result = calc.calculate_portfolio_var(positions, price_data)
        assert var_result.var_95 > 0, "组合VaR计算失败"
        print(f"✅ 组合VaR(95%): ${var_result.var_95:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ VaR计算器测试失败: {e}")
        return False


async def test_execution_engine():
    """测试执行引擎"""
    print("\n⚡ 测试执行引擎...")
    
    try:
        from execution_engine import ExecutionEngine, Order, OrderType, ExecutionAlgorithm
        
        engine = ExecutionEngine()
        
        # 创建测试订单
        order = Order(
            order_id="TEST_ORDER_001",
            symbol="BTC/USDT",
            side="buy",
            amount=1.0,
            order_type=OrderType.LIMIT,
            price=50000.0
        )
        
        # 提交订单测试
        order_id = await engine.submit_order(order, ExecutionAlgorithm.IMMEDIATE)
        assert order_id is not None, "订单提交失败"
        print(f"✅ 订单提交成功: {order_id}")
        
        # 等待执行
        await asyncio.sleep(0.2)
        
        # 查询订单状态
        final_order = engine.get_order_status(order_id)
        assert final_order is not None, "订单状态查询失败"
        print(f"✅ 订单状态: {final_order.status.value}")
        
        # TWAP计算测试
        slices = engine.calculate_twap(100.0, 300)
        total_amount = sum(s["amount"] for s in slices)
        assert abs(total_amount - 100.0) < 0.01, "TWAP计算错误"
        print(f"✅ TWAP计算: {len(slices)}片, 总量{total_amount:.2f}")
        
        # 执行统计测试
        stats = engine.get_execution_stats()
        assert "total_orders" in stats, "执行统计缺失字段"
        print(f"✅ 执行统计: {stats['total_orders']}笔订单")
        
        return True
        
    except Exception as e:
        print(f"❌ 执行引擎测试失败: {e}")
        return False


def test_money_management():
    """测试资金管理"""
    print("\n💰 测试资金管理...")
    
    try:
        from money.money_management import MoneyManagement, TradingRecord
        
        manager = MoneyManagement(initial_capital=100000)
        
        # 日限制检查
        daily_check = manager.check_daily_limits()
        assert "can_trade" in daily_check, "日限制检查缺失字段"
        print(f"✅ 日限制检查: 可交易={daily_check['can_trade']}")
        
        # 仓位计算
        position_size = manager.calculate_position_size(2000, 100)
        assert position_size >= 0, "仓位计算错误"
        print(f"✅ 仓位计算: {position_size:.2f}")
        
        # 交易记录更新
        trade = TradingRecord(
            symbol="TEST",
            entry_time=datetime.now(),
            exit_time=datetime.now(),
            pnl=500,
            risk_taken=2000,
            position_size=10000
        )
        
        success = manager.update_trade(trade)
        assert success, "交易记录更新失败"
        print("✅ 交易记录更新成功")
        
        # 风险容量检查
        capacity = manager.get_risk_capacity()
        assert "daily_risk_remaining" in capacity, "风险容量缺失字段"
        print(f"✅ 风险容量: 剩余${capacity['daily_risk_remaining']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 资金管理测试失败: {e}")
        return False


def test_api_routes():
    """测试API路由"""
    print("\n🌐 测试API路由...")
    
    try:
        from api_interface import app
        
        # 检查路由数量
        routes = [route for route in app.routes if hasattr(route, 'path')]
        assert len(routes) >= 15, f"API路由数量不足: {len(routes)}"
        print(f"✅ API路由数量: {len(routes)}")
        
        # 检查关键路由
        key_paths = ['/health', '/kelly/calculate', '/var/calculate', '/order/submit']
        existing_paths = [route.path for route in routes]
        
        for path in key_paths:
            assert path in existing_paths, f"缺少关键路由: {path}"
        
        print("✅ 关键API路由检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False


async def test_integration():
    """集成测试"""
    print("\n🔗 集成测试...")
    
    try:
        from kelly_calculator import KellyCalculator
        from var_calculator import VaRCalculator, Position
        from execution_engine import ExecutionEngine, Order, OrderType
        from money.money_management import MoneyManagement
        
        # 初始化组件
        kelly_calc = KellyCalculator()
        var_calc = VaRCalculator()
        execution_engine = ExecutionEngine()
        money_manager = MoneyManagement(100000)
        
        print("✅ 所有组件初始化成功")
        
        # 模拟完整交易流程
        # 1. 计算凯利仓位
        kelly = kelly_calc.calculate_kelly_fraction(0.6, 1.5)
        position_info = kelly_calc.calculate_position_size(100000, kelly)
        
        # 2. 检查资金管理限制
        daily_check = money_manager.check_daily_limits()
        assert daily_check["can_trade"], "无法交易"
        
        # 3. 计算VaR
        positions = [Position("BTC", 1.0, 50000, 51000)]
        price_data = {"BTC": [50000 + np.random.randn() * 1000 for _ in range(30)]}
        var_result = var_calc.calculate_portfolio_var(positions, price_data)
        
        # 4. 创建订单
        order = Order(
            order_id="INTEGRATION_001",
            symbol="BTC/USDT",
            side="buy",
            amount=0.1,  # 小量测试
            order_type=OrderType.LIMIT,
            price=50000.0
        )
        
        # 5. 提交订单
        order_id = await execution_engine.submit_order(order)
        assert order_id is not None, "订单提交失败"
        
        await asyncio.sleep(0.1)
        
        print("✅ 集成测试：完整交易流程正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


def test_performance():
    """性能测试"""
    print("\n⚡ 性能测试...")
    
    try:
        from kelly_calculator import KellyCalculator
        from var_calculator import VaRCalculator
        import time
        
        # 凯利计算性能
        calc = KellyCalculator()
        start_time = time.time()
        
        for _ in range(1000):
            calc.calculate_kelly_fraction(0.6, 1.5)
        
        kelly_time = time.time() - start_time
        print(f"✅ 凯利计算性能: 1000次耗时{kelly_time:.3f}秒")
        assert kelly_time < 1.0, "凯利计算性能不达标"
        
        # VaR计算性能
        var_calc = VaRCalculator()
        returns = np.random.normal(0, 0.02, 252)
        
        start_time = time.time()
        for _ in range(100):
            var_calc.calculate_historical_var(returns)
        
        var_time = time.time() - start_time
        print(f"✅ VaR计算性能: 100次耗时{var_time:.3f}秒")
        assert var_time < 1.0, "VaR计算性能不达标"
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🛡️ Tiger Window-7 风控执行系统 - 核心功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("模块导入", test_imports),
        ("凯利计算器", test_kelly_calculator),
        ("VaR计算器", test_var_calculator),
        ("执行引擎", test_execution_engine),
        ("资金管理", test_money_management),
        ("API路由", test_api_routes),
        ("集成测试", test_integration),
        ("性能测试", test_performance)
    ]
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            test_results.append((test_name, result))
            
            if result:
                print(f"🟢 {test_name}: 通过")
            else:
                print(f"🔴 {test_name}: 失败")
                
        except Exception as e:
            print(f"🔴 {test_name}: 异常 - {e}")
            test_results.append((test_name, False))
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📋 测试报告")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:.<30} {status}")
    
    print("-" * 60)
    print(f"总测试: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统达到工业级质量标准")
        return True
    else:
        print(f"\n⚠️  有{total - passed}个测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)