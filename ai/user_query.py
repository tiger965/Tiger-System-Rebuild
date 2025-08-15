"""
用户主动查询系统 - 让用户拥有决策主动权
不依赖触发机制，用户随时可以主动请求AI分析
支持多种查询类型和自定义分析需求
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from claude_client import ClaudeClient, RequestPriority
from prompts.prompt_templates import PromptTemplates, PromptType
from context_manager import ContextManager
from decision_formatter import DecisionFormatter

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """用户查询类型"""
    QUICK_ANALYSIS = "quick_analysis"        # 快速分析
    SHORT_TERM = "short_term"                # 短线机会
    TREND_DIRECTION = "trend_direction"      # 趋势方向
    ENTRY_POINT = "entry_point"              # 入场点位
    PENDING_ORDER = "pending_order"          # 挂单建议
    RISK_ASSESSMENT = "risk_assessment"      # 风险评估
    PORTFOLIO_ADVICE = "portfolio_advice"    # 组合建议
    CUSTOM = "custom"                        # 自定义查询


@dataclass
class UserQuery:
    """用户查询请求"""
    query_type: QueryType
    symbol: str
    timeframe: str = "4H"  # 默认4小时
    custom_question: Optional[str] = None
    risk_preference: str = "moderate"  # low/moderate/high
    position_size: Optional[float] = None
    additional_context: Dict[str, Any] = None


class UserQueryHandler:
    """用户主动查询处理器"""
    
    def __init__(self):
        self.client = ClaudeClient()
        self.templates = PromptTemplates()
        self.context_mgr = ContextManager()
        self.formatter = DecisionFormatter()
        
        # 查询模板
        self.query_templates = self._init_query_templates()
        
        # 查询统计
        self.query_stats = {
            'total_queries': 0,
            'query_types': {},
            'avg_response_time': 0
        }
    
    def _init_query_templates(self) -> Dict[QueryType, str]:
        """初始化查询模板"""
        return {
            QueryType.QUICK_ANALYSIS: """
你是专业的加密货币分析师。用户想要快速了解{symbol}的当前状况。

当前价格：${price}
24小时变化：{change_24h}%
成交量：${volume}

请提供简洁的分析（200字以内）：
1. 当前市场状态
2. 短期方向判断
3. 关键支撑/阻力
4. 操作建议（买入/卖出/观望）
5. 风险提示
""",
            
            QueryType.SHORT_TERM: """
用户想做{symbol}的短线交易（{timeframe}时间框架）。

市场数据：
{market_data}

技术指标：
{technical_indicators}

请提供短线交易建议：
1. 最佳入场时机和价位
2. 短线目标（1-3个）
3. 止损设置
4. 仓位建议（用户风险偏好：{risk_preference}）
5. 预期持仓时间
6. 注意事项

要求：建议必须具体可执行，避免模糊表述。
""",
            
            QueryType.TREND_DIRECTION: """
用户想了解{symbol}的趋势方向，为后续操作做准备。

历史数据：
- 7天变化：{change_7d}%
- 30天变化：{change_30d}%
- 当前价格：${price}

技术面：
{technical_analysis}

市场情绪：
{market_sentiment}

请分析：
1. 当前主趋势（上升/下降/震荡）
2. 趋势强度（强/中/弱）
3. 趋势可能持续时间
4. 关键转折价位
5. 建议的操作策略
6. 什么情况下趋势会改变
""",
            
            QueryType.ENTRY_POINT: """
用户想知道{symbol}的最佳入场点。

当前价格：${price}
用户意向：{intent}（做多/做空）
风险偏好：{risk_preference}

市场深度：
{order_book}

技术位：
{technical_levels}

请提供入场建议：
1. 立即入场 vs 等待回调
2. 最佳入场价位（1-3个）
3. 分批建仓策略
4. 每个价位的仓位分配
5. 总体仓位建议
6. 入场后的管理策略
""",
            
            QueryType.PENDING_ORDER: """
用户想设置{symbol}的挂单。

当前价格：${price}
账户余额：${balance}
风险承受：{risk_preference}

技术分析：
{technical_analysis}

支撑阻力：
{support_resistance}

请提供挂单建议：
1. 限价买单设置
   - 价位：$[具体价格]
   - 数量：[建议数量]
   - 理由：[为什么在此价位]
   
2. 限价卖单设置
   - 价位：$[具体价格]
   - 数量：[建议数量]
   - 理由：[为什么在此价位]
   
3. 止损单设置
   - 触发价：$[具体价格]
   - 理由：[风险控制逻辑]
   
4. 挂单有效期建议
5. 市场变化后的调整策略
""",
            
            QueryType.RISK_ASSESSMENT: """
用户想评估{symbol}的当前风险。

持仓信息：
{position_info}

市场状况：
{market_condition}

风险指标：
{risk_indicators}

请进行风险评估：
1. 当前风险等级（低/中/高/极高）
2. 主要风险来源（列举3-5个）
3. 风险发生概率
4. 潜在最大损失
5. 风险对冲建议
6. 是否需要调整仓位
7. 紧急情况应对预案
""",
            
            QueryType.PORTFOLIO_ADVICE: """
用户想优化投资组合配置。

当前持仓：
{current_portfolio}

市场环境：
{market_environment}

用户目标：
{user_goals}

请提供组合建议：
1. 当前组合评价
2. 建议调整方案
   - 增持：[币种及比例]
   - 减持：[币种及比例]
   - 新增：[币种及理由]
3. 目标配置比例
4. 风险分散度评估
5. 预期收益和风险
6. 调仓执行步骤
""",
            
            QueryType.CUSTOM: """
用户自定义查询：

问题：{custom_question}

相关数据：
{context_data}

请提供专业分析和建议。
"""
        }
    
    async def handle_query(self, query: UserQuery) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            query: 用户查询请求
            
        Returns:
            分析结果
        """
        start_time = datetime.now()
        
        try:
            # 获取市场数据（这里需要从其他模块获取）
            market_data = await self._fetch_market_data(query.symbol)
            
            # 构建查询上下文
            context = self._build_query_context(query, market_data)
            
            # 选择合适的提示词
            if query.query_type == QueryType.CUSTOM:
                prompt = self.query_templates[QueryType.CUSTOM].format(
                    custom_question=query.custom_question,
                    context_data=context
                )
                prompt_type = PromptType.BASIC_ANALYSIS
            else:
                template = self.query_templates.get(query.query_type)
                prompt = template.format(**context)
                prompt_type = self._map_query_to_prompt_type(query.query_type)
            
            # 调用AI（用户主动查询使用NORMAL优先级）
            response = await self.client.analyze(
                prompt_type=prompt_type,
                context={'custom_prompt': prompt, **context},
                priority=RequestPriority.NORMAL,
                use_cache=True  # 使用缓存避免重复查询
            )
            
            # 解析响应
            if response.success:
                # 尝试解析为结构化决策
                decision = self.formatter.parse_response(
                    response.content,
                    query.symbol,
                    market_data.get('price', 0)
                )
                
                # 记录到上下文
                self.context_mgr.add_conversation(
                    symbol=query.symbol,
                    prompt_type=query.query_type.value,
                    question=query.custom_question or query.query_type.value,
                    answer=response.content,
                    decision=decision.action.value if decision else None,
                    confidence=decision.confidence if decision else 0
                )
                
                # 更新统计
                self._update_stats(query.query_type, datetime.now() - start_time)
                
                return {
                    'success': True,
                    'query_type': query.query_type.value,
                    'symbol': query.symbol,
                    'response': response.content,
                    'decision': self.formatter.format_json(decision) if decision else None,
                    'cost': response.cost,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': response.error,
                    'query_type': query.query_type.value,
                    'symbol': query.symbol,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Query handling error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query_type': query.query_type.value,
                'symbol': query.symbol,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据（需要与其他模块集成）"""
        # TODO: 这里需要从2号窗口获取实时数据
        # 临时返回模拟数据
        return {
            'symbol': symbol,
            'price': 67500,
            'change_24h': 2.5,
            'change_7d': 5.2,
            'change_30d': 15.3,
            'volume': 25_000_000_000,
            'rsi': 58,
            'macd': 'bullish',
            'support': [66000, 65000, 63000],
            'resistance': [68000, 69000, 70000]
        }
    
    def _build_query_context(self, query: UserQuery, market_data: Dict) -> Dict:
        """构建查询上下文"""
        context = {
            'symbol': query.symbol,
            'timeframe': query.timeframe,
            'risk_preference': query.risk_preference,
            **market_data
        }
        
        # 添加额外上下文
        if query.additional_context:
            context.update(query.additional_context)
        
        # 从上下文管理器获取历史信息
        historical_context = self.context_mgr.build_context(
            query.symbol,
            include_history=True,
            include_market=True
        )
        context.update(historical_context)
        
        return context
    
    def _map_query_to_prompt_type(self, query_type: QueryType) -> PromptType:
        """映射查询类型到提示词类型"""
        mapping = {
            QueryType.QUICK_ANALYSIS: PromptType.BASIC_ANALYSIS,
            QueryType.SHORT_TERM: PromptType.TECHNICAL_DEEP,
            QueryType.TREND_DIRECTION: PromptType.TECHNICAL_DEEP,
            QueryType.ENTRY_POINT: PromptType.BASIC_ANALYSIS,
            QueryType.PENDING_ORDER: PromptType.TECHNICAL_DEEP,
            QueryType.RISK_ASSESSMENT: PromptType.RISK_ASSESSMENT,
            QueryType.PORTFOLIO_ADVICE: PromptType.PORTFOLIO_OPTIMIZATION,
        }
        return mapping.get(query_type, PromptType.BASIC_ANALYSIS)
    
    def _update_stats(self, query_type: QueryType, duration: Any):
        """更新查询统计"""
        self.query_stats['total_queries'] += 1
        
        # 按类型统计
        type_key = query_type.value
        if type_key not in self.query_stats['query_types']:
            self.query_stats['query_types'][type_key] = 0
        self.query_stats['query_types'][type_key] += 1
        
        # 更新平均响应时间
        total = self.query_stats['total_queries']
        avg_time = self.query_stats['avg_response_time']
        new_time = duration.total_seconds()
        self.query_stats['avg_response_time'] = (avg_time * (total - 1) + new_time) / total
    
    def get_available_queries(self) -> List[Dict]:
        """获取可用的查询类型列表"""
        return [
            {
                'type': QueryType.QUICK_ANALYSIS.value,
                'name': '快速分析',
                'description': '快速了解币种当前状况',
                'estimated_time': '20秒'
            },
            {
                'type': QueryType.SHORT_TERM.value,
                'name': '短线机会',
                'description': '寻找短线交易机会',
                'estimated_time': '25秒'
            },
            {
                'type': QueryType.TREND_DIRECTION.value,
                'name': '趋势方向',
                'description': '判断当前趋势和后续发展',
                'estimated_time': '25秒'
            },
            {
                'type': QueryType.ENTRY_POINT.value,
                'name': '入场点位',
                'description': '寻找最佳入场时机',
                'estimated_time': '20秒'
            },
            {
                'type': QueryType.PENDING_ORDER.value,
                'name': '挂单建议',
                'description': '设置限价单和止损单',
                'estimated_time': '25秒'
            },
            {
                'type': QueryType.RISK_ASSESSMENT.value,
                'name': '风险评估',
                'description': '评估当前持仓风险',
                'estimated_time': '25秒'
            },
            {
                'type': QueryType.PORTFOLIO_ADVICE.value,
                'name': '组合优化',
                'description': '优化投资组合配置',
                'estimated_time': '30秒'
            },
            {
                'type': QueryType.CUSTOM.value,
                'name': '自定义查询',
                'description': '提出任何交易相关问题',
                'estimated_time': '20-30秒'
            }
        ]
    
    def get_stats(self) -> Dict:
        """获取查询统计"""
        return {
            **self.query_stats,
            'most_used_query': max(
                self.query_stats['query_types'].items(),
                key=lambda x: x[1]
            )[0] if self.query_stats['query_types'] else None
        }


# 便捷接口函数
async def quick_analysis(symbol: str) -> Dict:
    """快速分析接口"""
    handler = UserQueryHandler()
    query = UserQuery(
        query_type=QueryType.QUICK_ANALYSIS,
        symbol=symbol
    )
    return await handler.handle_query(query)


async def get_short_term_opportunity(symbol: str, timeframe: str = "1H") -> Dict:
    """获取短线机会"""
    handler = UserQueryHandler()
    query = UserQuery(
        query_type=QueryType.SHORT_TERM,
        symbol=symbol,
        timeframe=timeframe
    )
    return await handler.handle_query(query)


async def check_trend(symbol: str) -> Dict:
    """检查趋势方向"""
    handler = UserQueryHandler()
    query = UserQuery(
        query_type=QueryType.TREND_DIRECTION,
        symbol=symbol
    )
    return await handler.handle_query(query)


async def get_entry_points(symbol: str, intent: str = "long") -> Dict:
    """获取入场点位"""
    handler = UserQueryHandler()
    query = UserQuery(
        query_type=QueryType.ENTRY_POINT,
        symbol=symbol,
        additional_context={'intent': intent}
    )
    return await handler.handle_query(query)


async def get_pending_orders(symbol: str, balance: float) -> Dict:
    """获取挂单建议"""
    handler = UserQueryHandler()
    query = UserQuery(
        query_type=QueryType.PENDING_ORDER,
        symbol=symbol,
        additional_context={'balance': balance}
    )
    return await handler.handle_query(query)


async def custom_query(symbol: str, question: str) -> Dict:
    """自定义查询"""
    handler = UserQueryHandler()
    query = UserQuery(
        query_type=QueryType.CUSTOM,
        symbol=symbol,
        custom_question=question
    )
    return await handler.handle_query(query)