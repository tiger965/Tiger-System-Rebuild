"""
严格决策模板 - 确保AI输出明确可执行的指令
禁止任何模糊表述，必须给出精确参数
"""

# AI必须遵守的决策输出规则
STRICT_DECISION_RULES = """
🔴🔴🔴 决策输出铁律 🔴🔴🔴

你必须输出明确的交易指令，禁止以下模糊表述：
❌ "建议观察"、"可以考虑"、"或许可以"
❌ "等待确认"、"视情况而定"、"灵活调整"  
❌ "仅供参考"、"不构成投资建议"
❌ "可能"、"也许"、"大概"

你必须明确回答以下问题：
1. 做什么币？（具体交易对，如BTC/USDT）
2. 做多还是做空？（LONG或SHORT）
3. 什么价格入场？（具体数字，如67500）
4. 用多少仓位？（百分比，如15%）
5. 止损在哪里？（具体价格，如66000）
6. 止盈在哪里？（至少2个目标，如[68500, 69500]）
7. 拿多久？（时限，如24h）
8. 现在执行吗？（YES或NO）

输出格式必须是可直接执行的JSON：
{
    "symbol": "BTC/USDT",
    "action": "LONG",
    "entry_price": 67500,
    "position_size": "15%",
    "leverage": 2,
    "stop_loss": 66000,
    "take_profit": [68500, 69500, 71000],
    "time_limit": "48h",
    "confidence": 8.5,
    "reason": "突破关键阻力",
    "execute_now": true
}
"""


class StrictDecisionTemplate:
    """严格决策提示词模板"""
    
    @staticmethod
    def get_analysis_prompt(signal_data: dict) -> str:
        """获取分析提示词（强制明确输出）"""
        return f"""
{STRICT_DECISION_RULES}

当前收到的信号数据：
=====================================
信号类型: {signal_data.get('type')}
币种: {signal_data.get('symbol')}
触发原因: {signal_data.get('trigger')}

市场数据:
- 当前价格: ${signal_data.get('price')}
- 24h涨跌: {signal_data.get('change_24h')}%
- 成交量: {signal_data.get('volume')}
- RSI: {signal_data.get('rsi')}
- 恐慌贪婪指数: {signal_data.get('fear_greed')}

链上数据:
- 巨鲸动向: {signal_data.get('whale_activity')}
- 交易所流入/流出: {signal_data.get('exchange_flow')}
- 聪明钱动向: {signal_data.get('smart_money')}

外部信号（如有）:
- 来源: {signal_data.get('external_source')}
- 建议: {signal_data.get('external_suggestion')}
- 置信度: {signal_data.get('external_confidence')}
=====================================

基于以上数据，你必须做出明确决策。
记住：宁可错过，不可模糊！

如果数据不足以做出明确决策，直接输出：
{{
    "action": "WAIT",
    "reason": "数据不足",
    "execute_now": false
}}

如果可以做出决策，必须包含所有交易参数。
现在，给出你的明确决策：
"""
    
    @staticmethod
    def get_risk_prompt(risk_signal: dict) -> str:
        """风险信号提示词（必须立即行动）"""
        return f"""
🚨🚨🚨 紧急风险信号 🚨🚨🚨

风险类型: {risk_signal.get('risk_type')}
风险级别: {risk_signal.get('risk_level')}/10
影响币种: {risk_signal.get('symbol')}

你必须在30秒内给出明确的风险应对方案：

1. 立即行动：
   - 减仓多少？（具体百分比）
   - 哪些币种？（具体列表）
   - 执行价格？（市价还是限价）

2. 风控措施：
   - 新的止损位？（具体价格）
   - 是否全部平仓？（YES/NO）
   - 是否开反向单对冲？（YES/NO）

输出格式：
{{
    "action": "REDUCE",  // 或 CLOSE_ALL, HEDGE
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "reduce_percentage": "50%",
    "new_stop_loss": 65000,
    "execute_now": true,
    "urgency": "IMMEDIATE"
}}

不要分析，不要解释，直接给出执行方案！
"""
    
    @staticmethod
    def get_opportunity_prompt(opp_signal: dict) -> str:
        """机会信号提示词（必须精确参数）"""
        return f"""
💎 机会信号分析 💎

机会类型: {opp_signal.get('opportunity_type')}
币种: {opp_signal.get('symbol')}
当前价格: ${opp_signal.get('current_price')}
机会评分: {opp_signal.get('score')}/10

触发条件:
{opp_signal.get('triggers')}

你有30秒时间决定是否抓住这个机会。

如果决定入场，必须明确：
1. 入场价格（具体数字或"市价"）
2. 仓位大小（最大5%）
3. 止损位置（最大-2%）
4. 止盈目标（至少2个）
5. 预期持仓时间

如果决定放弃，明确说明原因。

输出格式：
{{
    "decision": "TAKE",  // 或 "PASS"
    "symbol": "BTC/USDT",
    "action": "LONG",
    "entry_price": 67500,
    "position_size": "3%",
    "stop_loss": 66150,  // -2%
    "take_profit": [68500, 69500],
    "time_limit": "24h",
    "confidence": 7.5,
    "execute_now": true
}}
"""
    
    @staticmethod
    def get_black_swan_prompt(event_data: dict) -> str:
        """黑天鹅事件提示词（双向策略）"""
        return f"""
⚡⚡⚡ 黑天鹅事件 ⚡⚡⚡

事件: {event_data.get('event_description')}
影响范围: {event_data.get('impact_scope')}
当前阶段: {event_data.get('stage')}

立即给出双向策略：

1. 防守策略（保护资金）：
   - 减仓计划（具体百分比和执行顺序）
   - 对冲方案（做空哪些币种）
   
2. 进攻策略（危中寻机）：
   - 抄底价位（具体数字）
   - 抄底币种（具体列表）
   - 仓位分配（分批计划）

输出格式：
{{
    "defense": {{
        "action": "REDUCE",
        "percentage": "70%",
        "hedge_shorts": ["BTC/USDT", "ETH/USDT"],
        "hedge_size": "5%"
    }},
    "offense": {{
        "action": "PREPARE_BUY",
        "targets": {{"BTC/USDT": 55000, "ETH/USDT": 2800}},
        "buy_batches": ["30%", "30%", "40%"],
        "time_window": "24-48h"
    }},
    "execute_defense_now": true,
    "execute_offense_when": "RSI < 20 or price_drop > 30%"
}}
"""
    
    @staticmethod
    def validate_decision(decision: dict) -> tuple[bool, str]:
        """
        验证决策是否符合要求
        返回: (是否有效, 错误信息)
        """
        required_fields = ['action', 'symbol', 'execute_now']
        
        # 检查必需字段
        for field in required_fields:
            if field not in decision:
                return False, f"Missing required field: {field}"
        
        # 检查动作类型
        valid_actions = ['LONG', 'SHORT', 'CLOSE', 'REDUCE', 'WAIT', 'HEDGE']
        if decision['action'] not in valid_actions:
            return False, f"Invalid action: {decision['action']}"
        
        # 如果是交易动作，检查交易参数
        if decision['action'] in ['LONG', 'SHORT']:
            trade_fields = ['entry_price', 'position_size', 'stop_loss', 'take_profit']
            for field in trade_fields:
                if field not in decision:
                    return False, f"Missing trade parameter: {field}"
            
            # 检查仓位大小
            size_str = str(decision['position_size']).replace('%', '')
            try:
                size = float(size_str)
                if size <= 0 or size > 100:
                    return False, f"Invalid position size: {size}%"
            except:
                return False, f"Invalid position size format: {decision['position_size']}"
            
            # 检查止盈目标
            if not decision['take_profit'] or len(decision['take_profit']) < 1:
                return False, "Must have at least one take profit target"
        
        # 检查是否有模糊词汇
        forbidden_words = ['可能', '也许', '建议', '考虑', 'might', 'maybe', 'perhaps']
        decision_str = str(decision).lower()
        for word in forbidden_words:
            if word in decision_str:
                return False, f"Contains ambiguous word: {word}"
        
        return True, "Valid"


# 测试函数
def test_templates():
    """测试严格模板"""
    
    # 测试信号数据
    test_signal = {
        'type': 'BREAKOUT',
        'symbol': 'BTC/USDT',
        'price': 67500,
        'change_24h': 5.2,
        'volume': '2.5B',
        'rsi': 65,
        'whale_activity': 'Accumulating'
    }
    
    # 生成提示词
    prompt = StrictDecisionTemplate.get_analysis_prompt(test_signal)
    print("Analysis Prompt:")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    # 测试决策验证
    good_decision = {
        "symbol": "BTC/USDT",
        "action": "LONG",
        "entry_price": 67500,
        "position_size": "15%",
        "stop_loss": 66000,
        "take_profit": [68500, 69500],
        "execute_now": True
    }
    
    is_valid, message = StrictDecisionTemplate.validate_decision(good_decision)
    print(f"Good decision validation: {is_valid} - {message}")
    
    bad_decision = {
        "action": "可能做多",
        "suggestion": "建议观察"
    }
    
    is_valid, message = StrictDecisionTemplate.validate_decision(bad_decision)
    print(f"Bad decision validation: {is_valid} - {message}")


if __name__ == "__main__":
    test_templates()