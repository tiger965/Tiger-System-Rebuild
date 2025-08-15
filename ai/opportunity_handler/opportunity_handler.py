"""
机会信号快速响应系统
处理7号窗口(风控系统)发现的交易机会
30秒内快速响应，独立仓位管理
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import redis

logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    """机会类型"""
    OVERSOLD_BOUNCE = "oversold_bounce"      # 超卖反弹
    BREAKOUT = "breakout"                     # 突破机会
    REVERSAL = "reversal"                     # 反转机会
    MOMENTUM = "momentum"                      # 动量机会
    ARBITRAGE = "arbitrage"                   # 套利机会
    BLACK_SWAN = "black_swan"                 # 黑天鹅机会


@dataclass
class OpportunitySignal:
    """7号窗口发来的机会信号"""
    timestamp: datetime
    symbol: str
    opportunity_type: OpportunityType
    triggers: List[str]
    current_risk: str  # low/medium/high
    suggested_size: float
    market_data: Dict[str, Any]
    urgency: str  # immediate/soon/watch
    source: str = "window_7_risk_control"


class OpportunityHandler:
    """机会信号快速响应处理器"""
    
    def __init__(self, claude_client=None, redis_client=None):
        self.claude_client = claude_client
        self.redis_client = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            decode_responses=True
        )
        
        # 机会仓位限制
        self.MAX_OPPORTUNITY_SIZE = 0.05  # 最大5%
        self.MAX_STOP_LOSS = 0.02  # 最大止损2%
        self.TIME_LIMIT_HOURS = 48  # 最长持仓48小时
        
        # 响应时间要求
        self.RESPONSE_TIMEOUT = 25  # 25秒超时(留5秒余量)
        
        # 统计
        self.stats = {
            'total_signals': 0,
            'executed': 0,
            'passed': 0,
            'avg_response_time': 0,
            'total_profit': 0
        }
        
        # 启动监听
        self.start_listening()
    
    def start_listening(self):
        """启动Redis订阅监听7号窗口信号"""
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe('opportunity_signals')
            
            # 异步处理消息
            asyncio.create_task(self._listen_for_signals(pubsub))
            logger.info("Started listening for opportunity signals from Window 7")
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
    
    async def _listen_for_signals(self, pubsub):
        """监听并处理信号"""
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    signal_data = json.loads(message['data'])
                    signal = self._parse_signal(signal_data)
                    
                    # 快速响应
                    await self.handle_opportunity_signal(signal)
                    
                except Exception as e:
                    logger.error(f"Error processing signal: {e}")
    
    def _parse_signal(self, data: Dict) -> OpportunitySignal:
        """解析7号窗口的信号"""
        return OpportunitySignal(
            timestamp=datetime.fromisoformat(data['timestamp']),
            symbol=data['symbol'],
            opportunity_type=OpportunityType(data['opportunity']['type']),
            triggers=data['opportunity']['triggers'],
            current_risk=data['current_risk'],
            suggested_size=data['suggested_size'],
            market_data=data['market_data'],
            urgency=data.get('urgency', 'soon')
        )
    
    async def handle_opportunity_signal(self, signal: OpportunitySignal) -> Dict:
        """
        快速响应7号窗口的机会信号
        必须在30秒内完成分析和决策
        """
        start_time = time.time()
        self.stats['total_signals'] += 1
        
        logger.info(f"⚡ Processing opportunity signal for {signal.symbol}")
        logger.info(f"   Type: {signal.opportunity_type.value}")
        logger.info(f"   Risk: {signal.current_risk}")
        logger.info(f"   Urgency: {signal.urgency}")
        
        # 构建专用提示词
        prompt = self._build_opportunity_prompt(signal)
        
        try:
            # 快速API调用（优先级最高）
            if self.claude_client:
                response = await self._quick_analyze(prompt)
            else:
                # 模拟响应（测试用）
                response = self._simulate_response(signal)
            
            # 解析和标准化响应
            decision = self._standardize_decision(response, signal)
            
            # 验证决策
            decision = self._validate_decision(decision)
            
            # 计算响应时间
            response_time = time.time() - start_time
            self._update_stats(response_time, decision)
            
            logger.info(f"✓ Decision made in {response_time:.2f}s")
            logger.info(f"  Action: {decision['action']}")
            logger.info(f"  Confidence: {decision['confidence']}")
            
            # 发送回7号窗口
            await self._send_to_risk_control(decision)
            
            return decision
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout analyzing opportunity for {signal.symbol}")
            return self._create_pass_decision("Timeout")
            
        except Exception as e:
            logger.error(f"Error analyzing opportunity: {e}")
            return self._create_pass_decision(str(e))
    
    def _build_opportunity_prompt(self, signal: OpportunitySignal) -> str:
        """构建机会分析专用提示词"""
        return f"""
⚡ 紧急机会分析（风控系统发现）

机会类型：{signal.opportunity_type.value}
触发条件：{', '.join(signal.triggers)}
当前风险水平：{signal.current_risk}
建议仓位：{signal.suggested_size:.1%}
紧急度：{signal.urgency}

市场快照：
- RSI: {signal.market_data.get('rsi', 'N/A')}
- 价格变化: {signal.market_data.get('price_change', 'N/A')}%
- 成交量比: {signal.market_data.get('volume_ratio', 'N/A')}x
- 买卖比: {signal.market_data.get('bid_ask_ratio', 'N/A')}
- 链上活跃度: {signal.market_data.get('on_chain_activity', 'N/A')}

请在30秒内快速分析并给出明确建议：

1. 机会真实性评分（1-10）：基于数据可靠性
2. 风险收益比：预期收益/潜在损失
3. 建议仓位：最大5%，需比常规更谨慎
4. 严格止损位：最大-2%，必须执行
5. 目标价位：至少2个，要现实
6. 持仓时限：24-48小时内
7. 执行建议：立即执行/等待确认/放弃

决策要求：
- 这是独立的机会仓位，与主仓位分开管理
- 风控要求更严格，宁可错过不可做错
- 快进快出，不恋战
- 如果不确定，选择放弃

请给出JSON格式的决策：
{{
    "confidence": 0-10,
    "action": "LONG/SHORT/PASS",
    "entry_price": 具体价格,
    "position_size": "X%",
    "stop_loss": 具体价格,
    "targets": [目标1, 目标2],
    "time_limit": "24h/48h",
    "reasoning": "简要说明"
}}
"""
    
    async def _quick_analyze(self, prompt: str) -> Dict:
        """快速调用Claude API"""
        from claude_client import RequestPriority
        
        response = await self.claude_client.analyze(
            prompt_type="OPPORTUNITY",
            context={'custom_prompt': prompt},
            priority=RequestPriority.URGENT,
            timeout=self.RESPONSE_TIMEOUT,
            max_tokens=1000  # 减少token加快响应
        )
        
        # 解析JSON响应
        try:
            return json.loads(response.content)
        except:
            # 如果不是JSON，尝试提取关键信息
            return self._extract_decision_from_text(response.content)
    
    def _simulate_response(self, signal: OpportunitySignal) -> Dict:
        """模拟AI响应（测试用）"""
        # 基于信号类型和风险给出保守决策
        if signal.current_risk == "high":
            return {
                "confidence": 3,
                "action": "PASS",
                "reasoning": "Risk too high for opportunity trade"
            }
        
        if signal.opportunity_type == OpportunityType.OVERSOLD_BOUNCE:
            return {
                "confidence": 7,
                "action": "LONG",
                "entry_price": 67000,
                "position_size": "3%",
                "stop_loss": 65700,
                "targets": [68000, 69000],
                "time_limit": "24h",
                "reasoning": "RSI oversold bounce opportunity"
            }
        
        return {
            "confidence": 5,
            "action": "PASS",
            "reasoning": "Insufficient confidence"
        }
    
    def _standardize_decision(self, response: Dict, signal: OpportunitySignal) -> Dict:
        """标准化决策格式"""
        decision = {
            "type": "OPPORTUNITY_RESPONSE",
            "timestamp": datetime.now().isoformat(),
            "symbol": signal.symbol,
            "opportunity_type": signal.opportunity_type.value,
            "confidence": response.get('confidence', 0),
            "action": response.get('action', 'PASS'),
            "suggested_size": response.get('position_size', '0%'),
            "entry_price": response.get('entry_price'),
            "stop_loss": response.get('stop_loss'),
            "targets": response.get('targets', []),
            "time_limit": response.get('time_limit', '24h'),
            "reasoning": response.get('reasoning', ''),
            "source": "window_6_ai"
        }
        
        return decision
    
    def _validate_decision(self, decision: Dict) -> Dict:
        """验证和调整决策以符合风控要求"""
        # 限制仓位大小
        size_str = decision['suggested_size'].replace('%', '')
        try:
            size = float(size_str) / 100
            if size > self.MAX_OPPORTUNITY_SIZE:
                decision['suggested_size'] = f"{self.MAX_OPPORTUNITY_SIZE*100:.1f}%"
                decision['reasoning'] += " (Position size capped at 5%)"
        except:
            decision['suggested_size'] = "0%"
        
        # 确保止损不超过2%
        if decision['entry_price'] and decision['stop_loss']:
            loss_pct = abs(decision['entry_price'] - decision['stop_loss']) / decision['entry_price']
            if loss_pct > self.MAX_STOP_LOSS:
                if decision['action'] == 'LONG':
                    decision['stop_loss'] = decision['entry_price'] * 0.98
                else:
                    decision['stop_loss'] = decision['entry_price'] * 1.02
                decision['reasoning'] += " (Stop loss adjusted to 2%)"
        
        # 如果置信度太低，改为PASS
        if decision['confidence'] < 5:
            decision['action'] = 'PASS'
            decision['reasoning'] = "Confidence too low (<5)"
        
        return decision
    
    async def _send_to_risk_control(self, decision: Dict):
        """发送决策回7号窗口"""
        try:
            self.redis_client.publish(
                'risk_control_channel',
                json.dumps(decision)
            )
            logger.info(f"Decision sent to Window 7: {decision['action']}")
        except Exception as e:
            logger.error(f"Failed to send decision to Window 7: {e}")
    
    def _create_pass_decision(self, reason: str) -> Dict:
        """创建放弃决策"""
        return {
            "type": "OPPORTUNITY_RESPONSE",
            "timestamp": datetime.now().isoformat(),
            "action": "PASS",
            "confidence": 0,
            "reasoning": reason,
            "source": "window_6_ai"
        }
    
    def _update_stats(self, response_time: float, decision: Dict):
        """更新统计"""
        # 更新平均响应时间
        total = self.stats['total_signals']
        avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = (avg * (total - 1) + response_time) / total
        
        # 更新执行统计
        if decision['action'] != 'PASS':
            self.stats['executed'] += 1
        else:
            self.stats['passed'] += 1
    
    def _extract_decision_from_text(self, text: str) -> Dict:
        """从文本响应中提取决策信息"""
        # 简单的文本解析逻辑
        decision = {
            "confidence": 5,
            "action": "PASS",
            "reasoning": text[:200]
        }
        
        # 查找关键词
        if "做多" in text or "LONG" in text.upper():
            decision["action"] = "LONG"
        elif "做空" in text or "SHORT" in text.upper():
            decision["action"] = "SHORT"
        
        # 尝试提取数字
        import re
        conf_match = re.search(r'置信度[:：]?\s*(\d+)', text)
        if conf_match:
            decision["confidence"] = int(conf_match.group(1))
        
        return decision
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'execution_rate': self.stats['executed'] / self.stats['total_signals'] 
                if self.stats['total_signals'] > 0 else 0,
            'avg_response_time_ms': self.stats['avg_response_time'] * 1000
        }