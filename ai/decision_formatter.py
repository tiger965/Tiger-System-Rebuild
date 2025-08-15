"""
决策输出标准化系统 - 确保AI输出的可执行性
将AI的自然语言响应转换为结构化的交易决策
包含格式验证、信息提取、紧急程度分级等功能
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class DecisionAction(Enum):
    """决策动作"""
    LONG = "LONG"       # 做多
    SHORT = "SHORT"     # 做空
    HOLD = "HOLD"       # 观望
    CLOSE = "CLOSE"     # 平仓
    REDUCE = "REDUCE"   # 减仓
    ADD = "ADD"         # 加仓


class UrgencyLevel(Enum):
    """紧急程度"""
    IMMEDIATE = "immediate"     # 立即执行
    SOON = "soon"              # 30分钟内
    TODAY = "today"            # 今日内
    WATCH = "watch"            # 持续观察
    CONDITIONAL = "conditional" # 条件触发


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class TradingDecision:
    """标准化交易决策"""
    # 基础信息
    timestamp: datetime
    symbol: str
    action: DecisionAction
    urgency: UrgencyLevel
    confidence: float  # 0-10
    
    # 价格信息
    current_price: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    targets: List[float] = field(default_factory=list)
    
    # 仓位信息
    position_size: float = 0.0  # 百分比
    leverage: float = 1.0
    
    # 风险信息
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_reward_ratio: float = 0.0
    max_loss_percentage: float = 0.0
    
    # 分析信息
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # 执行信息
    time_frame: str = ""  # 预期持仓时间
    conditions: List[str] = field(default_factory=list)  # 执行条件
    
    # 元数据
    source: str = ""  # 决策来源
    raw_response: str = ""  # 原始AI响应


class DecisionParser:
    """决策解析器 - 从AI响应中提取结构化信息"""
    
    def __init__(self):
        # 正则表达式模式
        self.patterns = {
            'action': r'决策[:：]\s*【([^\】]+)】',
            'confidence': r'置信度[:：]\s*(\d+(?:\.\d+)?)\s*/\s*10',
            'entry_price': r'入场价[位格]?[:：]\s*\$?([\d,]+(?:\.\d+)?)',
            'stop_loss': r'止损[价位]?[:：]\s*\$?([\d,]+(?:\.\d+)?)',
            'targets': r'目标[价位]?\d*[:：]\s*\$?([\d,]+(?:\.\d+)?)',
            'position_size': r'[建仓位]+[:：]\s*(\d+(?:\.\d+)?)\s*%',
            'leverage': r'杠杆[:：]\s*(\d+(?:\.\d+)?)[xX倍]?',
            'urgency': r'[紧急执行]+[级别等]?[:：]\s*【([^\】]+)】',
            'risk_level': r'风险[等级]?[:：]\s*【([^\】]+)】',
            'time_frame': r'[预期持仓]+时间[:：]\s*([^\n,，]+)',
        }
        
        # 动作映射
        self.action_mapping = {
            '做多': DecisionAction.LONG,
            '多': DecisionAction.LONG,
            'LONG': DecisionAction.LONG,
            '做空': DecisionAction.SHORT,
            '空': DecisionAction.SHORT,
            'SHORT': DecisionAction.SHORT,
            '观望': DecisionAction.HOLD,
            '持有': DecisionAction.HOLD,
            'HOLD': DecisionAction.HOLD,
            '平仓': DecisionAction.CLOSE,
            'CLOSE': DecisionAction.CLOSE,
            '减仓': DecisionAction.REDUCE,
            'REDUCE': DecisionAction.REDUCE,
            '加仓': DecisionAction.ADD,
            'ADD': DecisionAction.ADD,
        }
        
        # 紧急度映射
        self.urgency_mapping = {
            '立即': UrgencyLevel.IMMEDIATE,
            '立即执行': UrgencyLevel.IMMEDIATE,
            'immediate': UrgencyLevel.IMMEDIATE,
            '紧急': UrgencyLevel.IMMEDIATE,
            '30分钟内': UrgencyLevel.SOON,
            'soon': UrgencyLevel.SOON,
            '今日': UrgencyLevel.TODAY,
            '今日内': UrgencyLevel.TODAY,
            'today': UrgencyLevel.TODAY,
            '观察': UrgencyLevel.WATCH,
            '持续观察': UrgencyLevel.WATCH,
            'watch': UrgencyLevel.WATCH,
            '条件触发': UrgencyLevel.CONDITIONAL,
            'conditional': UrgencyLevel.CONDITIONAL,
        }
        
        # 风险等级映射
        self.risk_mapping = {
            '低': RiskLevel.LOW,
            'low': RiskLevel.LOW,
            '中': RiskLevel.MEDIUM,
            '中等': RiskLevel.MEDIUM,
            'medium': RiskLevel.MEDIUM,
            '高': RiskLevel.HIGH,
            'high': RiskLevel.HIGH,
            '极高': RiskLevel.EXTREME,
            'extreme': RiskLevel.EXTREME,
        }
    
    def parse(self, raw_response: str, symbol: str, current_price: float) -> Optional[TradingDecision]:
        """
        解析AI响应为标准化决策
        
        Args:
            raw_response: AI原始响应
            symbol: 交易对
            current_price: 当前价格
            
        Returns:
            标准化决策对象
        """
        try:
            # 提取动作
            action = self._extract_action(raw_response)
            if not action:
                logger.warning("Failed to extract action from response")
                return None
            
            # 创建决策对象
            decision = TradingDecision(
                timestamp=datetime.now(),
                symbol=symbol,
                action=action,
                urgency=self._extract_urgency(raw_response),
                confidence=self._extract_confidence(raw_response),
                current_price=current_price,
                raw_response=raw_response
            )
            
            # 提取价格信息
            if action in [DecisionAction.LONG, DecisionAction.SHORT]:
                decision.entry_price = self._extract_price(raw_response, 'entry_price', current_price) or current_price
                decision.stop_loss = self._extract_price(raw_response, 'stop_loss', current_price)
                decision.targets = self._extract_targets(raw_response)
                
                # 计算风险收益比
                if decision.stop_loss and decision.targets and decision.entry_price:
                    risk = abs(decision.entry_price - decision.stop_loss)
                    reward = abs(decision.targets[0] - decision.entry_price) if decision.targets else 0
                    decision.risk_reward_ratio = reward / risk if risk > 0 else 0
                    decision.max_loss_percentage = (risk / decision.entry_price) * 100
            
            # 提取仓位信息
            decision.position_size = self._extract_number(raw_response, 'position_size', 10)
            decision.leverage = self._extract_number(raw_response, 'leverage', 1)
            
            # 提取风险等级
            decision.risk_level = self._extract_risk_level(raw_response)
            
            # 提取时间框架
            decision.time_frame = self._extract_text(raw_response, 'time_frame', "未指定")
            
            # 提取分析信息
            decision.reasoning = self._extract_reasoning(raw_response)
            decision.key_factors = self._extract_list(raw_response, "关键因素|主要.*因素")
            decision.risks = self._extract_list(raw_response, "风险|注意")
            decision.conditions = self._extract_list(raw_response, "条件|如果")
            
            return decision
            
        except Exception as e:
            logger.error(f"Failed to parse decision: {str(e)}")
            return None
    
    def _extract_action(self, text: str) -> Optional[DecisionAction]:
        """提取交易动作"""
        # 首先尝试用正则提取
        match = re.search(self.patterns['action'], text, re.IGNORECASE)
        if match:
            action_text = match.group(1).upper()
            for key, action in self.action_mapping.items():
                if key in action_text or action_text in key:
                    return action
        
        # 备用：在整个文本中搜索关键词
        text_upper = text.upper()
        for key, action in self.action_mapping.items():
            if key.upper() in text_upper:
                return action
        
        return None
    
    def _extract_confidence(self, text: str) -> float:
        """提取置信度"""
        match = re.search(self.patterns['confidence'], text)
        if match:
            return float(match.group(1))
        
        # 备用：搜索数字/10格式
        match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', text)
        if match:
            return float(match.group(1))
        
        return 5.0  # 默认中等置信度
    
    def _extract_price(self, text: str, price_type: str, current_price: float) -> float:
        """提取价格"""
        pattern = self.patterns.get(price_type)
        if not pattern:
            return current_price
        
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            return float(price_str)
        
        return current_price
    
    def _extract_targets(self, text: str) -> List[float]:
        """提取目标价位"""
        targets = []
        
        # 搜索所有目标价位
        matches = re.findall(r'目标\d*[:：]\s*\$?([\d,]+(?:\.\d+)?)', text)
        for match in matches:
            price = float(match.replace(',', ''))
            targets.append(price)
        
        # 备用：搜索T1, T2, T3格式
        if not targets:
            matches = re.findall(r'T\d[:：]\s*\$?([\d,]+(?:\.\d+)?)', text)
            for match in matches:
                price = float(match.replace(',', ''))
                targets.append(price)
        
        return sorted(targets)  # 按价格排序
    
    def _extract_number(self, text: str, field: str, default: float) -> float:
        """提取数字"""
        pattern = self.patterns.get(field)
        if not pattern:
            return default
        
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        
        return default
    
    def _extract_urgency(self, text: str) -> UrgencyLevel:
        """提取紧急程度"""
        # 正则提取
        match = re.search(self.patterns['urgency'], text)
        if match:
            urgency_text = match.group(1).lower()
            for key, urgency in self.urgency_mapping.items():
                if key in urgency_text:
                    return urgency
        
        # 在文本中搜索关键词
        text_lower = text.lower()
        for key, urgency in self.urgency_mapping.items():
            if key in text_lower:
                return urgency
        
        return UrgencyLevel.WATCH  # 默认观察
    
    def _extract_risk_level(self, text: str) -> RiskLevel:
        """提取风险等级"""
        match = re.search(self.patterns['risk_level'], text)
        if match:
            risk_text = match.group(1).lower()
            for key, risk in self.risk_mapping.items():
                if key in risk_text:
                    return risk
        
        # 根据其他因素推断
        if "黑天鹅" in text or "崩盘" in text:
            return RiskLevel.EXTREME
        elif "高风险" in text:
            return RiskLevel.HIGH
        elif "低风险" in text:
            return RiskLevel.LOW
        
        return RiskLevel.MEDIUM
    
    def _extract_text(self, text: str, field: str, default: str) -> str:
        """提取文本字段"""
        if not text or not isinstance(text, str):
            return default
            
        pattern = self.patterns.get(field)
        if not pattern:
            return default
        
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        
        return default
    
    def _extract_reasoning(self, text: str) -> str:
        """提取推理过程"""
        # 查找分析部分
        patterns = [
            r'分析[:：](.*?)(?=\n\d+\.|$)',
            r'判断[:：](.*?)(?=\n\d+\.|$)',
            r'理由[:：](.*?)(?=\n\d+\.|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()[:500]  # 限制长度
        
        # 提取第一段作为推理
        lines = text.split('\n')
        for line in lines:
            if len(line) > 50:  # 足够长的段落
                return line.strip()[:500]
        
        return ""
    
    def _extract_list(self, text: str, keywords: str) -> List[str]:
        """提取列表项"""
        items = []
        
        # 查找包含关键词的段落
        pattern = rf'{keywords}.*?[:：]\s*(.*?)(?=\n\n|\n\d+\.|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            content = match.group(1)
            # 提取列表项
            list_patterns = [
                r'[*-]\s*(.+?)(?=\n|$)',  # * 或 - 开头
                r'\d+\.\s*(.+?)(?=\n|$)',  # 数字开头
                r'[•]\s*(.+?)(?=\n|$)',    # 圆点开头
            ]
            
            for pattern in list_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    items.extend([m.strip() for m in matches if m.strip()])
                    break
            
            # 如果没有找到列表，尝试按逗号分割
            if not items and '，' in content:
                items = [item.strip() for item in content.split('，') if item.strip()]
        
        return items[:5]  # 限制数量


class DecisionFormatter:
    """决策格式化器 - 将决策转换为各种输出格式"""
    
    def __init__(self):
        self.parser = DecisionParser()
    
    def parse_response(self, 
                      raw_response: str, 
                      symbol: str, 
                      current_price: float) -> Optional[TradingDecision]:
        """解析AI响应"""
        return self.parser.parse(raw_response, symbol, current_price)
    
    def format_json(self, decision: TradingDecision) -> str:
        """格式化为JSON"""
        data = asdict(decision)
        
        # 转换枚举为字符串
        data['action'] = decision.action.value
        data['urgency'] = decision.urgency.value
        data['risk_level'] = decision.risk_level.value
        data['timestamp'] = decision.timestamp.isoformat()
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def format_message(self, decision: TradingDecision) -> str:
        """格式化为消息通知"""
        if decision.action == DecisionAction.HOLD:
            message = f"🔍 {decision.symbol} - 建议观望\n"
            message += f"原因：{decision.reasoning[:100]}\n"
            message += f"置信度：{decision.confidence}/10"
        
        elif decision.action in [DecisionAction.LONG, DecisionAction.SHORT]:
            emoji = "📈" if decision.action == DecisionAction.LONG else "📉"
            message = f"{emoji} {decision.symbol} - {decision.action.value}\n"
            message += f"入场：${decision.entry_price:,.2f}\n"
            
            if decision.targets:
                message += f"目标：${', $'.join([f'{t:,.2f}' for t in decision.targets])}\n"
            
            if decision.stop_loss:
                message += f"止损：${decision.stop_loss:,.2f}\n"
            
            message += f"仓位：{decision.position_size}%\n"
            message += f"风险：{decision.risk_level.value}\n"
            message += f"置信度：{decision.confidence}/10\n"
            message += f"紧急度：{decision.urgency.value}"
        
        else:
            message = f"💹 {decision.symbol} - {decision.action.value}\n"
            message += f"置信度：{decision.confidence}/10"
        
        return message
    
    def format_execution(self, decision: TradingDecision) -> Dict[str, Any]:
        """格式化为执行指令"""
        if decision.action not in [DecisionAction.LONG, DecisionAction.SHORT]:
            return {
                'execute': False,
                'reason': f"Action {decision.action.value} is not executable"
            }
        
        return {
            'execute': True,
            'symbol': decision.symbol,
            'side': 'BUY' if decision.action == DecisionAction.LONG else 'SELL',
            'entry_price': decision.entry_price,
            'stop_loss': decision.stop_loss,
            'take_profits': decision.targets,
            'position_size_pct': decision.position_size,
            'leverage': decision.leverage,
            'urgency': decision.urgency.value,
            'confidence': decision.confidence,
            'metadata': {
                'reasoning': decision.reasoning,
                'risks': decision.risks,
                'timestamp': decision.timestamp.isoformat()
            }
        }
    
    def validate_decision(self, decision: TradingDecision) -> Tuple[bool, List[str]]:
        """
        验证决策的完整性和合理性
        
        Returns:
            (是否有效, 问题列表)
        """
        issues = []
        
        # 基础验证
        if not decision.symbol:
            issues.append("Missing symbol")
        
        if decision.confidence < 3:
            issues.append("Confidence too low (<3)")
        
        # 交易决策验证
        if decision.action in [DecisionAction.LONG, DecisionAction.SHORT]:
            if not decision.entry_price:
                issues.append("Missing entry price")
            
            if not decision.stop_loss:
                issues.append("Missing stop loss")
            
            if not decision.targets:
                issues.append("Missing target prices")
            
            # 验证价格合理性
            if decision.entry_price and decision.stop_loss:
                if decision.action == DecisionAction.LONG:
                    if decision.stop_loss >= decision.entry_price:
                        issues.append("Stop loss above entry for LONG")
                else:  # SHORT
                    if decision.stop_loss <= decision.entry_price:
                        issues.append("Stop loss below entry for SHORT")
            
            # 验证仓位
            if decision.position_size <= 0 or decision.position_size > 100:
                issues.append(f"Invalid position size: {decision.position_size}%")
            
            # 验证杠杆
            if decision.leverage < 1 or decision.leverage > 10:
                issues.append(f"Invalid leverage: {decision.leverage}x")
            
            # 验证风险收益比
            if decision.risk_reward_ratio < 1.5:
                issues.append(f"Poor risk/reward ratio: {decision.risk_reward_ratio:.2f}")
        
        return len(issues) == 0, issues
    
    def enhance_decision(self, decision: TradingDecision) -> TradingDecision:
        """增强决策（填充缺失信息）"""
        # 如果缺少入场价，使用当前价
        if not decision.entry_price:
            decision.entry_price = decision.current_price
        
        # 如果缺少止损，设置默认止损
        if not decision.stop_loss and decision.action in [DecisionAction.LONG, DecisionAction.SHORT]:
            if decision.action == DecisionAction.LONG:
                decision.stop_loss = decision.entry_price * 0.97  # 3%止损
            else:
                decision.stop_loss = decision.entry_price * 1.03
        
        # 如果缺少目标，设置默认目标
        if not decision.targets and decision.action in [DecisionAction.LONG, DecisionAction.SHORT]:
            if decision.action == DecisionAction.LONG:
                decision.targets = [
                    decision.entry_price * 1.03,  # 3%
                    decision.entry_price * 1.05,  # 5%
                    decision.entry_price * 1.10   # 10%
                ]
            else:
                decision.targets = [
                    decision.entry_price * 0.97,
                    decision.entry_price * 0.95,
                    decision.entry_price * 0.90
                ]
        
        # 如果缺少仓位，根据置信度设置
        if decision.position_size == 0:
            if decision.confidence >= 8:
                decision.position_size = 20
            elif decision.confidence >= 6:
                decision.position_size = 15
            else:
                decision.position_size = 10
        
        # 计算风险收益比
        if decision.stop_loss and decision.targets:
            risk = abs(decision.entry_price - decision.stop_loss)
            reward = abs(decision.targets[0] - decision.entry_price)
            decision.risk_reward_ratio = reward / risk if risk > 0 else 0
            decision.max_loss_percentage = (risk / decision.entry_price) * 100
        
        return decision