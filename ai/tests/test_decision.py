"""
决策格式化系统测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision_formatter import DecisionFormatter, DecisionAction, UrgencyLevel, RiskLevel
from datetime import datetime


def test_decision_parsing():
    """测试决策解析"""
    formatter = DecisionFormatter()
    
    # 测试做多决策解析
    long_response = """
    基于当前市场分析，BTC正处于上升趋势的初期阶段。
    
    决策：【做多】
    
    入场价位：$67500
    目标价位：
    - 目标1：$68500 (预期收益：+1.5%)
    - 目标2：$69500 (预期收益：+3.0%)
    - 目标3：$71000 (预期收益：+5.2%)
    
    止损价位：$66000 (风险：-2.2%)
    建议仓位：15%
    杠杆：2x
    
    置信度：8.5/10
    风险等级：【中等】
    紧急程度：【立即执行】
    预期持仓时间：4-8小时
    
    关键因素：
    - 技术指标多头共振
    - 成交量持续放大
    - 突破关键阻力位
    
    风险提示：
    - 注意美股开盘影响
    - 关注68000整数关口压力
    - 警惕获利盘抛压
    """
    
    decision = formatter.parse_response(long_response, "BTC/USDT", 67500)
    
    assert decision is not None
    assert decision.action == DecisionAction.LONG
    assert decision.entry_price == 67500
    assert len(decision.targets) == 3
    assert decision.targets[0] == 68500
    assert decision.stop_loss == 66000
    assert decision.position_size == 15
    assert decision.leverage == 2
    assert decision.confidence == 8.5
    assert decision.urgency == UrgencyLevel.IMMEDIATE
    assert decision.risk_level == RiskLevel.MEDIUM
    
    print("✓ Long decision parsed correctly")
    return decision


def test_decision_validation():
    """测试决策验证"""
    formatter = DecisionFormatter()
    
    # 创建一个完整的决策
    good_response = """
    决策：【做空】
    入场价位：$67500
    目标1：$66500
    目标2：$65500
    止损：$68500
    仓位：20%
    置信度：7/10
    """
    
    decision = formatter.parse_response(good_response, "BTC/USDT", 67500)
    is_valid, issues = formatter.validate_decision(decision)
    
    assert is_valid == True
    assert len(issues) == 0
    print("✓ Valid decision passed validation")
    
    # 创建一个有问题的决策
    bad_response = """
    决策：【做多】
    入场价位：$67500
    止损：$68500  # 止损在入场价上方，错误
    仓位：150%  # 超过100%，错误
    置信度：2/10  # 置信度太低
    """
    
    bad_decision = formatter.parse_response(bad_response, "BTC/USDT", 67500)
    is_valid, issues = formatter.validate_decision(bad_decision)
    
    assert is_valid == False
    assert len(issues) > 0
    print(f"✓ Invalid decision detected {len(issues)} issues: {issues}")


def test_decision_formatting():
    """测试决策格式化输出"""
    formatter = DecisionFormatter()
    
    response = """
    决策：【做多】
    入场价：$67500
    目标1：$68500
    目标2：$69500
    止损：$66000
    仓位：15%
    置信度：8/10
    紧急度：【立即】
    风险：【中】
    """
    
    decision = formatter.parse_response(response, "BTC/USDT", 67500)
    
    # 测试JSON格式化
    json_output = formatter.format_json(decision)
    assert "BTC/USDT" in json_output
    assert "LONG" in json_output
    print("✓ JSON formatting working")
    
    # 测试消息格式化
    message = formatter.format_message(decision)
    assert "BTC/USDT" in message
    assert "📈" in message
    assert "67,500" in message
    print("✓ Message formatting working")
    print(f"\nFormatted message:\n{message}")
    
    # 测试执行指令格式化
    execution = formatter.format_execution(decision)
    assert execution['execute'] == True
    assert execution['symbol'] == "BTC/USDT"
    assert execution['side'] == "BUY"
    assert execution['entry_price'] == 67500
    print("✓ Execution formatting working")


def test_decision_enhancement():
    """测试决策增强"""
    formatter = DecisionFormatter()
    
    # 创建一个不完整的决策
    incomplete_response = """
    决策：【做多】
    置信度：7/10
    """
    
    decision = formatter.parse_response(incomplete_response, "BTC/USDT", 67500)
    
    # 增强决策
    enhanced = formatter.enhance_decision(decision)
    
    assert enhanced.entry_price == 67500  # 使用当前价
    assert enhanced.stop_loss is not None  # 自动设置止损
    assert len(enhanced.targets) > 0  # 自动设置目标
    assert enhanced.position_size > 0  # 自动设置仓位
    
    print("✓ Decision enhancement working")
    print(f"  - Auto stop loss: ${enhanced.stop_loss:,.0f}")
    print(f"  - Auto targets: {[f'${t:,.0f}' for t in enhanced.targets]}")
    print(f"  - Auto position: {enhanced.position_size}%")


def test_complex_parsing():
    """测试复杂响应解析"""
    formatter = DecisionFormatter()
    
    complex_response = """
    市场分析显示当前处于关键位置。考虑到多个技术指标的共振，
    以及市场情绪的改善，我认为这是一个不错的做多机会。
    
    决策：【做多】
    
    操作建议：
    入场价位：$67,500（当前价格附近）
    
    目标设置（分批止盈）：
    T1: $68,500 (+1.48%)
    T2: $69,500 (+2.96%)  
    T3: $71,000 (+5.19%)
    
    风险控制：
    止损价位：$66,000 (-2.22%)
    建议仓位：15% （基于当前市场波动）
    杠杆建议：2x
    
    执行紧急度：【30分钟内】
    风险等级：【中等】
    置信度评分：7.5/10
    
    预期持仓时间：4小时到1天
    
    主要依据：
    * RSI从超卖区域反弹
    * MACD即将金叉
    * 成交量明显放大
    * 突破下降趋势线
    
    风险提示：
    * 美联储会议临近，注意消息面影响
    * 68,000是强阻力位，可能有抛压
    * 整体市场情绪仍偏谨慎
    """
    
    decision = formatter.parse_response(complex_response, "BTC/USDT", 67500)
    
    assert decision is not None
    assert decision.action == DecisionAction.LONG
    assert decision.confidence == 7.5
    assert decision.urgency == UrgencyLevel.SOON
    assert len(decision.key_factors) > 0
    assert len(decision.risks) > 0
    
    print("✓ Complex response parsed successfully")
    print(f"  - Extracted {len(decision.key_factors)} key factors")
    print(f"  - Extracted {len(decision.risks)} risks")
    print(f"  - Time frame: {decision.time_frame}")


if __name__ == "__main__":
    print("\n=== Testing Decision Formatter ===\n")
    
    # 运行所有测试
    test_decision_parsing()
    test_decision_validation()
    test_decision_formatting()
    test_decision_enhancement()
    test_complex_parsing()
    
    print("\n=== All Decision Tests Passed! ===\n")