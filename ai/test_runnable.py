#!/usr/bin/env python3
"""
测试系统是否真的能跑通
不调用实际API，只测试逻辑流程
"""

import asyncio
import sys
from datetime import datetime

# 测试触发系统
async def test_trigger():
    print("\n1. 测试触发系统...")
    from trigger.trigger_system import TriggerSystem, TriggerLevel
    
    trigger = TriggerSystem()
    
    # 模拟市场数据
    market_data = {
        'symbol': 'BTC/USDT',
        'price_change_24h': 5.0,  # 5%涨幅，应该触发Level 2
        'volume_ratio': 3.5,
        'rsi': 75,
        'whale_transfer': 20_000_000,
        'liquidations': 5_000_000,
        'top_traders_action': ['trader1', 'trader2'],
        'technical_signals_count': 4
    }
    
    signal = await trigger.evaluate_trigger(market_data)
    
    if signal and signal.level == TriggerLevel.LEVEL_2:
        print(f"   ✓ 触发成功: {signal.level.name}")
        print(f"   原因: {signal.trigger_reason}")
        return True
    else:
        print(f"   ✗ 触发失败")
        return False

# 测试决策解析
def test_decision_parser():
    print("\n2. 测试决策解析...")
    from decision_formatter import DecisionFormatter
    
    formatter = DecisionFormatter()
    
    # 模拟AI响应
    ai_response = """
    决策：【做多】
    入场价：$67500
    目标1：$68500
    止损：$66000
    仓位：15%
    置信度：8/10
    """
    
    decision = formatter.parse_response(ai_response, "BTC/USDT", 67500)
    
    if decision and decision.action.value == "LONG":
        print(f"   ✓ 解析成功: {decision.action.value}")
        print(f"   入场: ${decision.entry_price}")
        return True
    else:
        print(f"   ✗ 解析失败")
        return False

# 测试上下文管理
def test_context():
    print("\n3. 测试上下文管理...")
    from context_manager import ContextManager, MarketCycle
    
    ctx = ContextManager()
    
    # 添加对话记录
    ctx.add_conversation(
        symbol="BTC/USDT",
        prompt_type="test",
        question="测试问题",
        answer="测试回答",
        decision="LONG",
        confidence=7.5
    )
    
    # 获取记录
    conversations = ctx.get_recent_conversations("BTC/USDT")
    
    if len(conversations) > 0:
        print(f"   ✓ 记录成功: {len(conversations)}条对话")
        return True
    else:
        print(f"   ✗ 记录失败")
        return False

# 测试策略权重
def test_weights():
    print("\n4. 测试策略权重...")
    from strategy_weights import StrategyWeights, StrategyType
    
    weights = StrategyWeights()
    
    # 更新市场状态
    indicators = {
        'trend_strength': 0.7,
        'volatility': 'normal',
        'fear_greed': 70,
        'volume_trend': 'increasing'
    }
    
    market = weights.update_market_condition(indicators)
    weight = weights.get_strategy_weight(StrategyType.TREND_FOLLOWING)
    
    if weight > 0:
        print(f"   ✓ 权重计算成功: {weight:.2f}")
        print(f"   市场: {market.value}")
        return True
    else:
        print(f"   ✗ 权重计算失败")
        return False

# 测试用户查询结构
def test_user_query():
    print("\n5. 测试用户查询...")
    from user_query import UserQuery, QueryType
    
    # 创建查询
    query = UserQuery(
        query_type=QueryType.QUICK_ANALYSIS,
        symbol="BTC/USDT",
        risk_preference="moderate"
    )
    
    if query.query_type == QueryType.QUICK_ANALYSIS:
        print(f"   ✓ 查询创建成功: {query.query_type.value}")
        return True
    else:
        print(f"   ✗ 查询创建失败")
        return False

# 主测试函数
async def main():
    print("="*60)
    print("  测试AI决策系统是否能真正跑通")
    print("="*60)
    
    results = []
    
    # 运行各项测试
    results.append(await test_trigger())
    results.append(test_decision_parser())
    results.append(test_context())
    results.append(test_weights())
    results.append(test_user_query())
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"  测试结果: {passed}/{total} 通过")
    print("="*60)
    
    if passed == total:
        print("\n🎉 系统完全可以跑通！")
        print("   所有核心功能正常工作")
        print("   可以接入实际数据和API使用")
        return True
    else:
        print("\n⚠️ 部分功能有问题")
        print("   需要进一步调试")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)