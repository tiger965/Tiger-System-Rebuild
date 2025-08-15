"""
Tiger系统 - 风控系统测试
窗口：7号
功能：测试所有风控模块
作者：Window-7 Risk Control Officer
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

# 导入所有模块
from position.position_manager import PositionManager
from stoploss.stoploss_system import StopLossSystem, Position
from money.money_management import MoneyManagement, TradingRecord
from assessment.risk_assessment import RiskAssessment, MarketData
from execution.execution_monitor import ExecutionMonitor
from opportunity.opportunity_scanner import OpportunityScanner
from emergency.black_swan_opportunity import BlackSwanOpportunitySystem
from alert_executor import AlertExecutor, AIAlert, AlertLevel


def test_position_manager():
    """测试仓位管理"""
    print("\n" + "="*50)
    print("测试仓位管理系统")
    print("="*50)
    
    pm = PositionManager()
    pm.total_capital = 100000
    
    # 测试凯利公式
    optimal_size = pm.kelly_criterion(0.6, 2.0, 1.0)
    print(f"✅ 凯利公式建议仓位: {optimal_size:.2%}")
    
    # 测试仓位计算
    position, reason = pm.calculate_position_size(
        signal_strength=8,
        market_conditions={"trend": "strong_uptrend", "volatility": "medium"},
        risk_score=10
    )
    print(f"✅ 计算仓位: {position:.2%}")
    print(f"   原因: {reason}")
    
    # 测试仓位更新
    pm.update_position("BTC", 0.15, "open")
    pm.update_position("ETH", 0.10, "open")
    
    # 测试动态调整
    adjustment = pm.adjust_position_dynamic("BTC", {"winning_streak": 3})
    print(f"✅ 动态调整建议: {adjustment['action']} - {adjustment['reason']}")
    
    # 获取状态
    status = pm.get_position_status()
    print(f"✅ 仓位状态: 总使用 {status['total_used']:.2%}, 风险等级 {status['risk_level']}")
    
    return True


def test_stoploss_system():
    """测试止损系统"""
    print("\n" + "="*50)
    print("测试止损系统")
    print("="*50)
    
    sl = StopLossSystem()
    
    # 创建测试仓位
    test_position = Position(
        symbol="BTC",
        entry_price=70000,
        current_price=68500,
        quantity=0.1,
        entry_time=datetime.now() - timedelta(days=1),
        unrealized_pnl=-150,
        atr=1500,
        support_level=68000,
        resistance_level=72000
    )
    
    # 测试综合止损
    stop_decision = sl.get_combined_stop(test_position, highest_price=71000)
    print(f"✅ 止损决策:")
    print(f"   止损价: {stop_decision['stop_price']:.2f}")
    print(f"   类型: {stop_decision['stop_type']}")
    print(f"   原因: {stop_decision['reason']}")
    print(f"   触发: {stop_decision['triggered']}")
    
    # 更新止损
    sl.update_stop("BTC", stop_decision)
    
    # 检查触发
    triggers = sl.check_stop_triggers({"BTC": {"price": 67900}})
    if triggers:
        print(f"⚠️ 止损触发: {triggers[0]['symbol']} @ {triggers[0]['trigger_price']}")
    
    return True


def test_money_management():
    """测试资金管理"""
    print("\n" + "="*50)
    print("测试资金管理系统")
    print("="*50)
    
    mm = MoneyManagement(initial_capital=100000)
    
    # 模拟交易
    trades = [
        TradingRecord("BTC", datetime.now(), datetime.now(), 1500, 1000, 10000),
        TradingRecord("ETH", datetime.now(), datetime.now(), -800, 1000, 5000),
        TradingRecord("SOL", datetime.now(), datetime.now(), 2000, 1500, 8000),
    ]
    
    for trade in trades:
        mm.update_trade(trade)
    
    # 检查限制
    daily_check = mm.check_daily_limits()
    print(f"✅ 日限制检查: 可交易={daily_check['can_trade']}")
    if daily_check['warnings']:
        print(f"   警告: {daily_check['warnings']}")
    
    # 获取风险容量
    risk_capacity = mm.get_risk_capacity()
    print(f"✅ 风险容量:")
    print(f"   日风险剩余: ${risk_capacity['daily_risk_remaining']:.2f}")
    print(f"   剩余交易次数: {risk_capacity['trades_remaining']}")
    print(f"   建议单笔风险: ${risk_capacity['suggested_risk_per_trade']:.2f}")
    
    # 盈利管理
    mm.account_status.monthly_pnl = 25000  # 模拟月盈利
    profit_mgmt = mm.profit_management()
    if profit_mgmt['actions']:
        print(f"✅ 盈利管理建议:")
        for action in profit_mgmt['actions']:
            print(f"   {action['type']}: ${action['amount']:.2f} - {action['reason']}")
    
    return True


def test_risk_assessment():
    """测试风险评估"""
    print("\n" + "="*50)
    print("测试风险评估引擎")
    print("="*50)
    
    ra = RiskAssessment()
    
    # 创建测试数据
    test_market = MarketData(
        symbol="BTC",
        price=69000,
        volume=2000000,
        volatility=0.7,
        liquidity=0.6,
        correlation_matrix={"ETH": 0.85, "SOL": 0.7},
        funding_rate=0.0012,
        open_interest=900000000
    )
    
    test_position = {
        "positions": {"BTC": 60000, "ETH": 40000},
        "leverage": 2,
        "unrealized_pnl": 1000
    }
    
    test_timing = {
        "trend": "neutral",
        "momentum": 0.3,
        "events": [{"name": "CPI Release", "impact": "high"}]
    }
    
    # 计算综合风险
    risk_report = ra.get_comprehensive_risk_score(
        test_market,
        test_position,
        test_timing,
        "BTC",
        "Binance"
    )
    
    print(f"✅ 风险评估结果:")
    print(f"   总分: {risk_report['total_score']}/30")
    print(f"   等级: {risk_report['risk_level']}")
    if risk_report['alerts']:
        print(f"   警报: {risk_report['alerts'][0]}")
    if risk_report['recommendations']:
        print(f"   建议: {risk_report['recommendations'][0]}")
    
    # 计算VaR
    returns = [-0.02, 0.01, -0.03, 0.02, -0.01, 0.03, -0.02, 0.01]
    var_95 = ra.calculate_var(100000, returns, 0.95)
    print(f"✅ VaR (95%置信度): ${var_95:.2f}")
    
    return True


def test_execution_monitor():
    """测试执行监控"""
    print("\n" + "="*50)
    print("测试执行监控系统")
    print("="*50)
    
    em = ExecutionMonitor()
    
    # 跟踪建议
    suggestions = [
        {"symbol": "BTC", "price": 70000, "quantity": 0.1},
        {"symbol": "ETH", "price": 3500, "quantity": 1.0},
    ]
    
    suggestion_ids = []
    for sugg in suggestions:
        sid = em.track_suggestion(sugg)
        suggestion_ids.append(sid)
        print(f"✅ 跟踪建议: {sid}")
    
    # 更新执行
    em.update_execution(suggestion_ids[0], {
        "price": 70050,
        "quantity": 0.1,
        "status": "filled"
    })
    
    em.update_execution(suggestion_ids[1], {
        "price": 3495,
        "quantity": 1.0,
        "status": "filled"
    })
    
    # 计算绩效
    test_trades = [
        {"pnl": 1200, "capital": 10000},
        {"pnl": -500, "capital": 10000},
        {"pnl": 800, "capital": 10000},
        {"pnl": 1500, "capital": 10000},
        {"pnl": -300, "capital": 10000}
    ]
    
    performance = em.calculate_performance(test_trades)
    print(f"✅ 绩效指标:")
    print(f"   胜率: {performance['metrics']['win_rate']}")
    print(f"   盈亏比: {performance['metrics']['profit_factor']}")
    print(f"   夏普比率: {performance['metrics']['sharpe_ratio']}")
    print(f"   评级: {performance['rating']}")
    
    # 执行质量
    quality = em.get_execution_quality_report()
    print(f"✅ 执行质量分数: {quality.get('quality_score', 'N/A')}/100")
    
    return True


def test_opportunity_scanner():
    """测试机会发现系统"""
    print("\n" + "="*50)
    print("测试机会发现系统")
    print("="*50)
    
    scanner = OpportunityScanner()
    
    # 模拟极度超卖场景
    oversold_market = {
        "symbol": "BTC",
        "price": 65000,
        "rsi": 15,  # 极度超卖
        "price_drop_24h": 0.20,  # 24小时跌20%
        "volume_ratio": 5.0,  # 成交量5倍
        "support_level": 64500,
        "support_test_count": 4,
        "volume_trend": "decreasing",
        "whale_buys": 3000000,
        "exchange_outflow": 800000,
        "volatility": 0.2,
        "liquidations": 200000000,
        "funding_rate": -0.002,
        "fear_greed_index": 10
    }
    
    # 扫描机会
    opportunities = scanner.scan_market(oversold_market)
    
    print(f"✅ 发现 {len(opportunities)} 个机会:")
    for opp in opportunities:
        print(f"\n   类型: {opp.type.value}")
        print(f"   币种: {opp.symbol}")
        print(f"   置信度: {opp.confidence:.1f}/10")
        print(f"   预期收益: {opp.potential_return:.1%}")
        print(f"   建议仓位: {opp.suggested_size:.1%}")
        
        # 模拟通知AI
        result = scanner.notify_ai_system(opp)
        print(f"   AI通知: {result['status']}")
    
    return True


def test_black_swan_system():
    """测试黑天鹅机会系统"""
    print("\n" + "="*50)
    print("测试黑天鹅机会系统")
    print("="*50)
    
    bs_system = BlackSwanOpportunitySystem()
    
    # 模拟黑天鹅早期信号
    early_warning_market = {
        "symbol": "BTC",
        "price": 68000,
        "whale_net_flow": -2000,  # 大户流出
        "exchange_inflow": 15000,  # 交易所流入增加
        "defi_liquidations": 60000000,
        "funding_rate": 0.004,  # 极端费率
        "futures_basis": 0.06,
        "volume_ratio": 0.25,  # 成交量萎缩
        "volatility": 1.2,
        "fear_greed_index": 25,
        "twitter_sentiment": -0.6,
        "bitcoin_dead_searches": 70,
        "mainstream_media_negative": 0.7
    }
    
    # 检测预警
    warning_level, signals = bs_system.detect_early_warning_signals(early_warning_market)
    print(f"✅ 预警级别: {warning_level.value}")
    print(f"   总分: {signals['total_score']}")
    print(f"   建议: {signals['recommended_action']}")
    
    # 模拟黑天鹅爆发
    black_swan_market = {
        "symbol": "BTC",
        "price": 58000,
        "price_drop_from_high": -0.30,
        "price_drop_24h": -0.18,
        "hours_since_drop": 5,
        "whale_net_flow": -8000,
        "exchange_inflow": 30000,
        "liquidations": 2000000000,
        "funding_rate": -0.005,
        "fear_greed_index": 5,
        "rsi": 12,
        "whale_accumulation": True
    }
    
    # 执行策略
    from emergency.black_swan_opportunity import WarningLevel
    result = bs_system.execute_black_swan_strategy(WarningLevel.CRITICAL, black_swan_market)
    print(f"\n✅ 黑天鹅策略执行:")
    print(f"   阶段: {result['phase']}")
    print(f"   行动: {result['actions'][:2]}")  # 显示前2个行动
    if result['opportunities']:
        print(f"   发现机会: {len(result['opportunities'])}个")
    
    # 历史经验
    lessons = bs_system.get_historical_lessons()
    print(f"\n✅ 历史黑天鹅案例:")
    for case_name, case_data in list(lessons['patterns'].items())[:2]:
        print(f"   {case_name}: {case_data['lesson']}")
    
    return True


def test_alert_executor():
    """测试预警响应执行系统"""
    print("\n" + "="*50)
    print("测试预警响应执行系统")
    print("="*50)
    
    executor = AlertExecutor()
    
    # 测试一级预警
    alert_1 = AIAlert(
        id="TEST_L1",
        level=AlertLevel.LEVEL_1,
        source="window_6_ai",
        timestamp=datetime.now(),
        strategy={"monitoring": "increase"},
        urgency="medium",
        confidence=0.75,
        expires_in=3600
    )
    
    result_1 = executor.receive_alert_from_ai(alert_1)
    print(f"✅ 一级预警执行: 成功={result_1.success}, 耗时={result_1.execution_time:.1f}秒")
    
    # 测试二级预警
    alert_2 = AIAlert(
        id="TEST_L2",
        level=AlertLevel.LEVEL_2,
        source="window_6_ai",
        timestamp=datetime.now(),
        strategy={
            "reduction_rate": 0.3,
            "open_hedge": True,
            "stop_loss": 0.03
        },
        urgency="high",
        confidence=0.85,
        expires_in=1800
    )
    
    result_2 = executor.receive_alert_from_ai(alert_2)
    print(f"✅ 二级预警执行: 成功={result_2.success}")
    print(f"   执行动作: {len(result_2.actions_taken)}个")
    
    # 测试执行速度
    if result_2.execution_time < 30:
        print(f"✅ 执行速度达标: {result_2.execution_time:.1f}秒 < 30秒")
    
    # 测试机会执行
    alert_opp = AIAlert(
        id="TEST_OPP",
        level=AlertLevel.OPPORTUNITY,
        source="window_6_ai",
        timestamp=datetime.now(),
        strategy={
            "type": "bottom_fishing",
            "batches": [0.02, 0.03, 0.05],
            "stop_loss": 0.05
        },
        urgency="low",
        confidence=0.8,
        expires_in=7200
    )
    
    result_opp = executor.receive_alert_from_ai(alert_opp)
    print(f"✅ 机会执行: {result_opp.details.get('long_position', {}).get('type', 'N/A')}")
    
    # 获取统计
    stats = executor.get_execution_stats()
    print(f"✅ 执行统计: 成功率={stats.get('success_rate', 'N/A')}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀"*25)
    print("Tiger系统 - 7号窗口风控系统测试")
    print("🚀"*25)
    
    tests = [
        ("仓位管理", test_position_manager),
        ("止损系统", test_stoploss_system),
        ("资金管理", test_money_management),
        ("风险评估", test_risk_assessment),
        ("执行监控", test_execution_monitor),
        ("机会发现", test_opportunity_scanner),
        ("黑天鹅系统", test_black_swan_system),
        ("预警执行", test_alert_executor)  # 新增测试
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "✅ 通过" if success else "❌ 失败"))
        except Exception as e:
            print(f"\n❌ {name}测试失败: {e}")
            results.append((name, f"❌ 异常: {str(e)[:50]}"))
    
    # 测试报告
    print("\n" + "="*50)
    print("测试报告汇总")
    print("="*50)
    
    for name, status in results:
        print(f"{name}: {status}")
    
    passed = sum(1 for _, s in results if "✅" in s)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！风控系统运行正常！")
    else:
        print(f"\n⚠️ 有 {total-passed} 个测试失败，请检查")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)