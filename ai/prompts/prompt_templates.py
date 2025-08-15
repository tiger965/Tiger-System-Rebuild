"""
提示词工程系统 - AI决策的灵魂
精心设计的提示词是获得高质量AI建议的关键
每个提示词都经过深思熟虑，融入20年交易经验
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class PromptType(Enum):
    """提示词类型"""
    BASIC_ANALYSIS = "basic_analysis"
    TRADER_ANALYSIS = "trader_analysis"
    BLACK_SWAN = "black_swan"
    TECHNICAL_DEEP = "technical_deep"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    MARKET_CORRELATION = "market_correlation"


class PromptTemplates:
    """提示词模板管理系统"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.optimization_history = []
        
    def _initialize_templates(self) -> Dict[PromptType, str]:
        """初始化所有提示词模板"""
        return {
            PromptType.BASIC_ANALYSIS: self._get_basic_analysis_template(),
            PromptType.TRADER_ANALYSIS: self._get_trader_analysis_template(),
            PromptType.BLACK_SWAN: self._get_black_swan_template(),
            PromptType.TECHNICAL_DEEP: self._get_technical_deep_template(),
            PromptType.SENTIMENT_ANALYSIS: self._get_sentiment_analysis_template(),
            PromptType.RISK_ASSESSMENT: self._get_risk_assessment_template(),
            PromptType.PORTFOLIO_OPTIMIZATION: self._get_portfolio_optimization_template(),
            PromptType.MARKET_CORRELATION: self._get_market_correlation_template(),
        }
    
    def _get_basic_analysis_template(self) -> str:
        """基础市场分析模板 - 最常用的通用分析"""
        return """你是一位拥有20年加密货币交易经验的顶级交易员和量化分析师。你曾在顶级对冲基金工作，精通技术分析、基本面分析和市场心理学。你的分析必须精准、可执行、风险可控。

当前UTC时间：{current_time}

=== 市场数据 ===
币种：{symbol}
当前价格：${price:,.2f}
24小时变化：{change_24h:+.2f}%
24小时成交量：${volume_24h:,.0f}
市值排名：#{market_cap_rank}
流通供应量：{circulating_supply:,.0f}
总供应量：{total_supply:,.0f}

=== 价格历史 ===
1小时变化：{change_1h:+.2f}%
7天变化：{change_7d:+.2f}%
30天变化：{change_30d:+.2f}%
90天变化：{change_90d:+.2f}%
年初至今：{change_ytd:+.2f}%
历史最高价：${ath:,.2f} ({ath_date})
距离ATH：{ath_change:+.2f}%

=== 技术指标 ===
RSI(14)：{rsi_14:.2f}
RSI(4H)：{rsi_4h:.2f}
RSI(日线)：{rsi_daily:.2f}
MACD：
  - MACD线：{macd:.4f}
  - 信号线：{macd_signal:.4f}
  - 柱状图：{macd_histogram:.4f}
  - 状态：{macd_status}
布林带：
  - 上轨：${bb_upper:,.2f}
  - 中轨：${bb_middle:,.2f}
  - 下轨：${bb_lower:,.2f}
  - 位置：{bb_position}
移动平均：
  - MA7：${ma7:,.2f}
  - MA25：${ma25:,.2f}
  - MA99：${ma99:,.2f}
  - MA200：${ma200:,.2f}
成交量指标：
  - OBV：{obv:,.0f}
  - 成交量MA：{volume_ma:,.0f}
  - 量比：{volume_ratio:.2f}x
支撑位：{support_levels}
阻力位：{resistance_levels}

=== 市场深度 ===
买盘深度：${bid_depth:,.0f}
卖盘深度：${ask_depth:,.0f}
买卖比：{bid_ask_ratio:.2f}
大单净流入：${large_order_net_flow:,.0f}

=== 链上数据 ===
活跃地址数：{active_addresses:,}
交易所流入：${exchange_inflow:,.0f}
交易所流出：${exchange_outflow:,.0f}
交易所净流量：${exchange_netflow:+,.0f}
长期持有者行为：{hodler_behavior}

=== 衍生品数据 ===
永续合约资金费率：{funding_rate:.4f}%
持仓量：${open_interest:,.0f}
持仓量变化24h：{oi_change_24h:+.2f}%
多空比：{long_short_ratio:.2f}
预估清算（多）：${estimated_liq_long:,.0f}
预估清算（空）：${estimated_liq_short:,.0f}

=== 市场情绪 ===
恐惧贪婪指数：{fear_greed_index}/100 ({fear_greed_label})
社交媒体情绪：{social_sentiment}
新闻情绪：{news_sentiment}
Google趋势：{google_trends}

=== 宏观背景 ===
BTC主导率：{btc_dominance:.1f}%
总市值：${total_market_cap:,.0f}B
DXY指数：{dxy_index:.2f}
纳斯达克相关性：{nasdaq_correlation:.2f}
近期重要事件：{recent_events}

=== 触发原因 ===
{trigger_reason}

=== 额外信息 ===
{additional_info}

请基于以上数据进行全面分析，并提供明确的交易建议：

1. **市场状态评估**（50字以内）
   - 当前趋势判断（上升/下降/震荡）
   - 市场强度评估（强势/中性/弱势）
   - 关键价位识别

2. **技术面分析**（100字以内）
   - 技术形态识别
   - 指标共振情况
   - 支撑阻力有效性

3. **市场情绪与资金流向**（50字以内）
   - 情绪是否过热或过冷
   - 资金流向解读
   - 市场参与度评估

4. **风险与机会评估**（100字以内）
   - 主要风险点（至少3个）
   - 潜在机会（明确指出）
   - 风险收益比评估

5. **明确的操作建议**
   决策：【做多/做空/观望】
   
   如果建议交易：
   - 入场价位：$[具体价格]
   - 目标价位：
     * 目标1：$[价格] (预期收益：+X%)
     * 目标2：$[价格] (预期收益：+X%)
     * 目标3：$[价格] (预期收益：+X%)
   - 止损价位：$[价格] (风险：-X%)
   - 建议仓位：[5-30]%（基于账户总资金）
   - 杠杆建议：[1-3]x（如果使用杠杆）
   - 预期持仓时间：[具体时间范围]
   
   如果建议观望：
   - 观望原因：[明确说明]
   - 关注价位：$[价格]
   - 重新评估条件：[具体条件]

6. **置信度评分**：[1-10]/10
   - 评分依据：[简要说明]

7. **特别提醒**（如有）
   - 需要特别注意的风险
   - 可能改变判断的因素

请确保你的分析逻辑清晰、建议具体可执行、风险提示充分。避免模糊的表述，每个建议都要有明确的数据支撑。"""
    
    def _get_trader_analysis_template(self) -> str:
        """顶级交易员跟踪分析模板"""
        return """你是专门研究顶级交易员行为模式的量化分析师。你需要解读他们的操作逻辑，评估跟单价值，并给出独立的专业判断。

=== 核心交易员动态 ===
交易员：{trader_name}
平台：{platform}
操作类型：{action_type} （开多/开空/加仓/减仓/平仓）
币种：{symbol}
开仓价格：${entry_price:,.2f}
仓位规模：${position_size:,.0f} ({position_percentage:.1f}% of portfolio)
杠杆倍数：{leverage}x
开仓时间：{entry_time}

=== 该交易员历史表现 ===
总体胜率：{overall_winrate:.1f}%
该币种胜率：{symbol_winrate:.1f}%
平均盈利：+{avg_profit:.1f}%
平均亏损：-{avg_loss:.1f}%
盈亏比：{profit_loss_ratio:.2f}
最大回撤：-{max_drawdown:.1f}%
夏普比率：{sharpe_ratio:.2f}
最近10笔交易：{recent_trades}

=== 其他顶级交易员动态 ===
{other_traders_status}

=== 交易员共识度分析 ===
做多交易员数：{long_traders_count}
做空交易员数：{short_traders_count}
观望交易员数：{neutral_traders_count}
平均仓位：{avg_position_size:.1f}%
一致性指数：{consensus_index:.1f}/10

=== 当前市场数据 ===
{market_data}

=== 该交易员的典型策略 ===
偏好时间周期：{preferred_timeframe}
常用策略：{typical_strategies}
风格特征：{trading_style}
止损习惯：{stop_loss_pattern}
持仓时长：{avg_holding_period}

请进行深度分析：

1. **操作逻辑解读**（100字以内）
   - 为什么该交易员在此时此价开仓？
   - 他可能看到了什么信号？
   - 这符合他的一贯风格吗？

2. **跟单价值评估**
   - 跟单建议：【强烈推荐/推荐/中性/不推荐/强烈反对】
   - 评估得分：[1-10]/10
   - 主要依据：
     * 历史表现权重(30%)：[得分]
     * 当前市场契合度(25%)：[得分]
     * 风险收益比(25%)：[得分]
     * 其他交易员共识(20%)：[得分]

3. **风险分析**（100字以内）
   - 该交易员可能的止损位：$[价格]
   - 潜在风险点：[至少3个]
   - 最坏情况预估：-[X]%

4. **独立判断与建议**
   我的独立判断：【看多/看空/中性】
   
   操作建议：
   - 如果跟单：
     * 建议仓位：[原仓位的X%]
     * 入场价格：$[价格]
     * 止损设置：$[价格]
     * 目标价位：$[价格]
   
   - 如果不跟单：
     * 原因说明：[具体原因]
     * 替代策略：[如有]

5. **后续跟踪计划**
   - 关键观察点：[价格或时间]
   - 调整信号：[具体条件]
   - 退出信号：[明确标准]

6. **特别提醒**
   - 该交易员的弱点或盲区
   - 当前市场的特殊风险
   - 其他需要注意的因素

请保持客观、独立的分析立场，不要盲目跟从任何交易员。你的价值在于提供专业的第二意见。"""
    
    def _get_black_swan_template(self) -> str:
        """黑天鹅事件紧急分析模板"""
        return """🚨 紧急情况！你需要在极短时间内做出准确判断。你是危机管理专家，擅长在极端市场事件中保护资产并识别机会。

=== 事件信息 ===
事件类型：{event_type}
事件描述：{event_description}
发生时间：{event_time}
信息来源：{source}
可信度：{credibility}/10
影响范围：{impact_scope}

=== 市场即时反应 ===
价格变化：
- BTC：{btc_change:+.1f}%
- ETH：{eth_change:+.1f}%
- {symbol}：{symbol_change:+.1f}%

爆仓数据：
- 1小时爆仓：${liquidations_1h:,.0f}
- 多单爆仓：${long_liquidations:,.0f}
- 空单爆仓：${short_liquidations:,.0f}

交易所状况：
- 主要交易所状态：{exchange_status}
- 提币状态：{withdrawal_status}
- 交易深度变化：{depth_change:+.1f}%

资金流向：
- USDT流入交易所：${usdt_inflow:,.0f}
- BTC流出交易所：{btc_outflow:,.0f} BTC
- 稳定币铸造/销毁：${stablecoin_mint_burn:+,.0f}

=== 历史相似事件对比 ===
{historical_similar_events}

=== 当前持仓状况 ===
{current_positions}

请立即提供分析和行动方案：

1. **事件性质判断**（30秒内完成）
   - 真实性评估：[确认/可能/存疑]
   - 影响程度：[毁灭性/重大/中等/有限]
   - 持续时间预估：[瞬时/短期/中期/长期]

2. **市场影响评估**（50字以内）
   - 直接影响：[具体说明]
   - 连锁反应：[可能的后续]
   - 最坏情况：[极端场景]

3. **紧急操作建议**（必须明确）
   
   立即执行（1分钟内）：
   □ 平仓清单：[具体仓位]
   □ 止损调整：[新止损位]
   □ 对冲操作：[具体操作]
   
   短期应对（1小时内）：
   □ 仓位调整：[增/减/维持]
   □ 资产配置：[调整建议]
   □ 风险对冲：[对冲策略]

4. **机会识别**（如有）
   - 超跌机会：[标的及价位]
   - 套利机会：[具体操作]
   - 其他机会：[说明]

5. **风控措施**
   - 最大可承受损失：[X]%
   - 强制止损线：$[价格]
   - 资金保护策略：[具体措施]

6. **后续监控**
   - 关键指标：[需要持续关注的]
   - 预警信号：[恶化或好转的标志]
   - 下次评估时间：[具体时间]

决策总结：
【行动等级：紧急/高/中/低】
【主要操作：具体说明】
【风险等级：极高/高/中/低】
【置信度：X/10】

⚠️ 记住：在危机中，保护资本比抓住机会更重要。宁可错过，不可做错。"""
    
    def _get_technical_deep_template(self) -> str:
        """深度技术分析模板"""
        return """你是技术分析大师，精通各种技术指标和形态识别。请进行多维度、多周期的深度技术分析。

=== 多周期价格数据 ===
1分钟：{m1_data}
5分钟：{m5_data}
15分钟：{m15_data}
1小时：{h1_data}
4小时：{h4_data}
日线：{daily_data}
周线：{weekly_data}

=== 技术形态识别 ===
当前识别形态：
{identified_patterns}

=== 高级技术指标 ===
艾略特波浪：{elliott_wave}
斐波那契回撤：{fibonacci_levels}
一目均衡表：{ichimoku}
威廉指标：{williams_r}
KDJ指标：{kdj}
DMI指标：{dmi}
SAR指标：{sar}

=== 量价关系分析 ===
{volume_price_analysis}

=== 市场微观结构 ===
{market_microstructure}

请提供专业的技术分析报告：

1. **当前技术格局**
   - 主要趋势：[上升/下降/震荡]
   - 趋势强度：[强/中/弱]
   - 所处阶段：[初期/中期/末期]

2. **关键技术位**
   - 即时支撑：$[price] (强度：[强/中/弱])
   - 即时阻力：$[price] (强度：[强/中/弱])
   - 关键突破位：$[price]
   - 关键止损位：$[price]

3. **技术指标共振分析**
   - 多头信号：[列举]
   - 空头信号：[列举]
   - 中性信号：[列举]
   - 综合评分：[X]/10

4. **形态与结构**
   - 当前形态：[具体形态名称]
   - 完成度：[X]%
   - 目标位：$[price]
   - 失败位：$[price]

5. **时间周期分析**
   - 短期（1-4H）：[看多/看空/震荡]
   - 中期（日线）：[看多/看空/震荡]
   - 长期（周线）：[看多/看空/震荡]
   - 共振情况：[是否同向]

6. **交易策略建议**
   - 最优入场点：$[price]
   - 备选入场点：$[price]
   - 目标位阶梯：
     * T1: $[price] ([X]% profit)
     * T2: $[price] ([X]% profit)
     * T3: $[price] ([X]% profit)
   - 止损设置：$[price] ([X]% loss)
   - 仓位建议：[X]%

7. **风险提示**
   - 技术面风险：[具体说明]
   - 假突破风险：[评估]
   - 其他注意事项：[列举]

技术面综合评分：[X]/10
置信度：[X]/10"""
    
    def _get_sentiment_analysis_template(self) -> str:
        """市场情绪分析模板"""
        return """你是市场心理学专家，擅长解读市场情绪并预测群体行为。

=== 情绪指标 ===
恐惧贪婪指数：{fear_greed_index}
市场情绪评分：{market_sentiment_score}
散户情绪：{retail_sentiment}
机构情绪：{institutional_sentiment}
鲸鱼活动：{whale_sentiment}

=== 社交媒体数据 ===
Twitter提及量：{twitter_mentions}
Twitter情绪：{twitter_sentiment}
Reddit讨论热度：{reddit_activity}
Telegram活跃度：{telegram_activity}
YouTube视频数：{youtube_videos}
Google搜索趋势：{google_trends}

=== 新闻媒体分析 ===
正面新闻数：{positive_news_count}
负面新闻数：{negative_news_count}
中性新闻数：{neutral_news_count}
主流媒体态度：{mainstream_media_sentiment}
加密媒体态度：{crypto_media_sentiment}

=== 资金流向情绪 ===
稳定币流入：{stablecoin_inflow}
交易所净流量：{exchange_netflow}
DeFi锁仓变化：{defi_tvl_change}
衍生品情绪：{derivatives_sentiment}

=== 链上情绪指标 ===
持币地址变化：{holder_change}
大户持仓变化：{whale_position_change}
长期持有者行为：{ltl_behavior}
实现盈亏比：{realized_pl_ratio}

请进行情绪分析：

1. **整体情绪诊断**
   - 当前情绪：[极度恐慌/恐慌/担忧/中性/乐观/贪婪/极度贪婪]
   - 情绪强度：[1-10]/10
   - 情绪趋势：[改善/稳定/恶化]

2. **情绪驱动因素**
   - 主要驱动：[具体因素]
   - 次要因素：[列举]
   - 潜在变化因素：[可能改变情绪的]

3. **市场心理阶段**
   - 当前阶段：[不信/怀疑/希望/乐观/兴奋/欣快/否认/恐慌/投降]
   - 阶段特征：[描述]
   - 预期演化：[下一阶段预测]

4. **情绪交易机会**
   - 逆向机会：[如有]
   - 顺势机会：[如有]
   - 情绪拐点：[识别标准]

5. **风险评估**
   - 情绪过热风险：[评估]
   - 恐慌踩踏风险：[评估]
   - FOMO风险：[评估]

6. **操作建议**
   基于情绪的策略：
   - 仓位调整：[建议]
   - 进场时机：[判断]
   - 风控措施：[具体]

情绪面评分：[X]/10
预测准确度：[X]/10"""
    
    def _get_risk_assessment_template(self) -> str:
        """风险评估模板"""
        return """你是风险管理专家，负责识别、量化和管理交易风险。

=== 当前持仓 ===
{current_positions}

=== 市场风险指标 ===
波动率（ATR）：{atr}
波动率（历史）：{historical_volatility}
波动率（隐含）：{implied_volatility}
VaR（95%）：{var_95}
CVaR（95%）：{cvar_95}
最大回撤：{max_drawdown}

=== 流动性风险 ===
买卖价差：{bid_ask_spread}
市场深度：{market_depth}
滑点预估：{slippage_estimate}
大单影响：{large_order_impact}

=== 关联风险 ===
与BTC相关性：{btc_correlation}
与美股相关性：{stock_correlation}
与DXY相关性：{dxy_correlation}
板块联动性：{sector_correlation}

=== 事件风险 ===
近期事件：{upcoming_events}
监管风险：{regulatory_risks}
技术风险：{technical_risks}
黑天鹅概率：{black_swan_probability}

=== 对手方风险 ===
交易所风险：{exchange_risk}
DeFi协议风险：{defi_risk}
跨链桥风险：{bridge_risk}

请进行全面风险评估：

1. **风险识别与分级**
   高风险因素：
   - [因素1]：影响程度[高/中/低]，发生概率[%]
   - [因素2]：影响程度[高/中/低]，发生概率[%]
   
   中等风险：
   - [列举]
   
   低风险：
   - [列举]

2. **风险量化**
   - 总体风险评分：[1-10]/10
   - 预期最大损失：[X]%
   - 风险调整收益：[X]%
   - 夏普比率：[X]

3. **风险对冲建议**
   - 对冲工具：[期权/期货/现货]
   - 对冲比例：[X]%
   - 对冲成本：[X]%
   - 执行建议：[具体操作]

4. **仓位管理建议**
   - 最大仓位：[X]%
   - 分批建仓：[方案]
   - 动态调整：[规则]
   - 强制止损：[条件]

5. **风控规则设定**
   - 单笔止损：[X]%
   - 日止损：[X]%
   - 总止损：[X]%
   - 追踪止损：[设置]

6. **应急预案**
   - 极端下跌：[应对措施]
   - 流动性枯竭：[应对措施]
   - 系统性风险：[应对措施]

风险综合评级：[低/中/高/极高]
风控建议强度：[宽松/正常/严格/极严]"""
    
    def _get_portfolio_optimization_template(self) -> str:
        """投资组合优化模板"""
        return """你是投资组合管理专家，精通现代投资组合理论和加密资产配置。

=== 当前组合 ===
{current_portfolio}

=== 候选资产 ===
{candidate_assets}

=== 约束条件 ===
最大仓位：{max_position}
最小仓位：{min_position}
风险偏好：{risk_preference}
投资期限：{investment_horizon}
流动性要求：{liquidity_requirement}

=== 市场环境 ===
{market_environment}

请提供组合优化建议：

1. **当前组合诊断**
   - 组合表现：[评估]
   - 风险状况：[评估]
   - 优化空间：[评估]

2. **优化建议**
   调整方案：
   - 增持：[资产及比例]
   - 减持：[资产及比例]
   - 新增：[资产及比例]
   - 清仓：[资产及原因]

3. **目标组合**
   - 预期收益：[X]%
   - 预期风险：[X]%
   - 夏普比率：[X]
   - 最大回撤：[X]%

4. **执行计划**
   - 调整顺序：[步骤]
   - 时间安排：[计划]
   - 成本预估：[X]%

5. **再平衡策略**
   - 触发条件：[具体]
   - 再平衡周期：[时间]
   - 容忍度：[X]%

组合优化评分：[X]/10"""
    
    def _get_market_correlation_template(self) -> str:
        """市场关联分析模板"""
        return """你是市场关联性分析专家，擅长发现资产间的相互关系和传导机制。

=== 相关性矩阵 ===
{correlation_matrix}

=== 领先滞后关系 ===
{lead_lag_relationships}

=== 板块轮动 ===
{sector_rotation}

=== 宏观联动 ===
{macro_linkage}

请进行关联性分析：

1. **关键关联发现**
   - 强相关资产：[列举]
   - 负相关资产：[列举]
   - 独立资产：[列举]

2. **传导路径分析**
   - 价格传导：[路径]
   - 情绪传导：[路径]
   - 资金传导：[路径]

3. **套利机会**
   - 配对交易：[机会]
   - 统计套利：[机会]
   - 期现套利：[机会]

4. **风险传染评估**
   - 传染源：[识别]
   - 传染路径：[分析]
   - 防护建议：[措施]

5. **投资启示**
   - 分散化建议：[具体]
   - 对冲组合：[建议]
   - 轮动策略：[方案]

关联性评分：[X]/10"""
    
    def build_prompt(self, 
                     prompt_type: PromptType,
                     context: Dict[str, Any],
                     custom_params: Optional[Dict] = None) -> str:
        """
        构建完整的提示词
        
        Args:
            prompt_type: 提示词类型
            context: 上下文数据
            custom_params: 自定义参数
            
        Returns:
            格式化后的完整提示词
        """
        # 获取基础模板
        template = self.templates.get(prompt_type)
        if not template:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        # 合并上下文
        full_context = {
            'current_time': datetime.now().isoformat(),
            **context
        }
        
        # 添加自定义参数
        if custom_params:
            full_context.update(custom_params)
        
        # 处理缺失值
        for key in full_context:
            if full_context[key] is None:
                full_context[key] = "N/A"
            elif isinstance(full_context[key], (list, dict)) and not full_context[key]:
                full_context[key] = "无数据"
        
        # 格式化模板
        try:
            formatted_prompt = template.format(**full_context)
        except KeyError as e:
            # 如果缺少某些键，使用默认值
            missing_key = str(e).strip("'")
            full_context[missing_key] = "数据暂缺"
            formatted_prompt = template.format(**full_context)
        
        # 记录优化历史
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'prompt_type': prompt_type.value,
            'context_keys': list(full_context.keys()),
            'prompt_length': len(formatted_prompt)
        })
        
        return formatted_prompt
    
    def optimize_prompt(self, 
                        prompt_type: PromptType,
                        feedback: str,
                        performance_score: float):
        """
        根据反馈优化提示词
        
        Args:
            prompt_type: 提示词类型
            feedback: 使用反馈
            performance_score: 性能评分(0-1)
        """
        # 这里可以实现提示词的自动优化逻辑
        # 比如根据表现调整措辞、增删内容等
        optimization_record = {
            'timestamp': datetime.now(),
            'prompt_type': prompt_type.value,
            'feedback': feedback,
            'score': performance_score,
            'action': 'recorded for future optimization'
        }
        
        self.optimization_history.append(optimization_record)
        
        # 如果性能太差，可以触发警报或自动调整
        if performance_score < 0.5:
            self._trigger_prompt_review(prompt_type, feedback)
    
    def _trigger_prompt_review(self, prompt_type: PromptType, feedback: str):
        """触发提示词审查流程"""
        # 这里可以实现通知机制，提醒人工审查
        pass
    
    def get_prompt_stats(self) -> Dict:
        """获取提示词使用统计"""
        if not self.optimization_history:
            return {}
        
        stats = {
            'total_uses': len(self.optimization_history),
            'prompt_types': {},
            'avg_length': 0,
            'recent_optimizations': []
        }
        
        # 统计各类型使用次数
        for record in self.optimization_history:
            ptype = record.get('prompt_type')
            if ptype:
                stats['prompt_types'][ptype] = stats['prompt_types'].get(ptype, 0) + 1
        
        # 计算平均长度
        lengths = [r.get('prompt_length', 0) for r in self.optimization_history if 'prompt_length' in r]
        if lengths:
            stats['avg_length'] = sum(lengths) / len(lengths)
        
        # 最近的优化记录
        stats['recent_optimizations'] = self.optimization_history[-5:]
        
        return stats