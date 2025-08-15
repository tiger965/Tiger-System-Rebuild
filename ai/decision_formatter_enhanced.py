"""
增强版决策格式化器 - 只输出明确可执行的指令
绝对禁止模糊表述，必须给出精确的交易参数
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DecisionAction(Enum):
    """决策动作 - 必须明确"""
    LONG = "LONG"          # 做多
    SHORT = "SHORT"        # 做空
    CLOSE = "CLOSE"        # 平仓
    HOLD = "HOLD"          # 持有
    WAIT = "WAIT"          # 等待


class EnhancedDecisionFormatter:
    """
    增强版决策格式化器
    确保AI输出的每个决策都是明确可执行的
    """
    
    def __init__(self):
        # 决策模板 - 必须包含所有关键参数
        self.decision_template = {
            "timestamp": None,
            "symbol": None,           # 具体币种 BTC/USDT
            "action": None,            # LONG/SHORT/CLOSE
            "entry_price": None,       # 精确入场价 67500
            "position_size": None,     # 仓位大小 10%
            "leverage": None,          # 杠杆倍数 2x
            "stop_loss": None,         # 止损价 66000
            "take_profit": [],         # 止盈目标 [68500, 69500, 71000]
            "time_limit": None,        # 持仓时限 24h
            "confidence": None,        # 置信度 8.5/10
            "reason": None,            # 简要原因
            "execute_now": None        # 立即执行 True/False
        }
        
        # 禁止的模糊词汇
        self.forbidden_words = [
            "可能", "也许", "或许", "建议考虑", "可以尝试",
            "might", "maybe", "perhaps", "consider", "could",
            "建议观察", "等待确认", "视情况", "灵活调整",
            "具体情况具体分析", "仅供参考", "不构成投资建议"
        ]
    
    def format_decision(self, raw_decision: Dict, signal_data: Dict) -> Dict:
        """
        格式化决策，确保明确性
        如果有任何模糊，直接拒绝
        """
        # 检查是否有模糊表述
        if self._contains_ambiguity(raw_decision):
            logger.error("Decision contains ambiguous language - REJECTED")
            return self._create_rejection_decision("Decision too vague")
        
        # 提取明确参数
        formatted = {
            "timestamp": datetime.now().isoformat(),
            "signal_source": signal_data.get('source', 'unknown'),
            "decision_type": "EXECUTABLE_ORDER",
            
            # 核心交易参数 - 必须明确
            "symbol": self._extract_symbol(raw_decision, signal_data),
            "action": self._extract_action(raw_decision),
            "entry_price": self._extract_price(raw_decision, 'entry'),
            "position_size": self._extract_position_size(raw_decision),
            "leverage": self._extract_leverage(raw_decision),
            "stop_loss": self._extract_price(raw_decision, 'stop'),
            "take_profit": self._extract_targets(raw_decision),
            "time_limit": self._extract_time_limit(raw_decision),
            
            # 执行参数
            "execute_now": self._should_execute_now(raw_decision),
            "order_type": self._determine_order_type(raw_decision),
            "confidence": self._extract_confidence(raw_decision),
            
            # 验证标记
            "validation": self._validate_parameters(raw_decision)
        }
        
        # 最终验证
        if not self._is_executable(formatted):
            return self._create_rejection_decision("Missing critical parameters")
        
        return formatted
    
    def _contains_ambiguity(self, decision: Dict) -> bool:
        """检查是否包含模糊表述"""
        text = str(decision).lower()
        for word in self.forbidden_words:
            if word in text:
                logger.warning(f"Found ambiguous word: {word}")
                return True
        return False
    
    def _extract_symbol(self, decision: Dict, signal: Dict) -> str:
        """提取具体币种"""
        # 必须是明确的交易对
        symbol = decision.get('symbol') or signal.get('symbol')
        if not symbol or '/' not in symbol:
            raise ValueError("Symbol must be specific (e.g., BTC/USDT)")
        return symbol.upper()
    
    def _extract_action(self, decision: Dict) -> str:
        """提取明确动作"""
        action = decision.get('action', '').upper()
        if action not in ['LONG', 'SHORT', 'CLOSE', 'HOLD', 'WAIT']:
            raise ValueError(f"Action must be explicit: {action}")
        return action
    
    def _extract_price(self, decision: Dict, price_type: str) -> float:
        """提取精确价格"""
        if price_type == 'entry':
            price = decision.get('entry_price') or decision.get('entry')
        else:
            price = decision.get('stop_loss') or decision.get('stop')
        
        if isinstance(price, str):
            # 处理 "current", "market" 等
            if price.lower() in ['current', 'market']:
                return 0  # 表示市价
            # 提取数字
            import re
            match = re.search(r'[\d.]+', price)
            if match:
                return float(match.group())
        
        if isinstance(price, (int, float)):
            return float(price)
        
        raise ValueError(f"Price must be specific number: {price}")
    
    def _extract_position_size(self, decision: Dict) -> str:
        """提取仓位大小"""
        size = decision.get('position_size') or decision.get('size')
        
        if isinstance(size, str):
            # 确保是百分比格式
            if '%' not in size:
                size = f"{size}%"
            # 验证范围
            import re
            match = re.search(r'([\d.]+)%', size)
            if match:
                value = float(match.group(1))
                if 0 < value <= 100:
                    return f"{value}%"
        
        raise ValueError(f"Position size must be specific percentage: {size}")
    
    def _extract_leverage(self, decision: Dict) -> int:
        """提取杠杆倍数"""
        leverage = decision.get('leverage', 1)
        if isinstance(leverage, str):
            import re
            match = re.search(r'(\d+)', leverage)
            if match:
                leverage = int(match.group(1))
        
        if not isinstance(leverage, int) or leverage < 1 or leverage > 125:
            leverage = 1  # 默认不加杠杆
        
        return leverage
    
    def _extract_targets(self, decision: Dict) -> List[float]:
        """提取止盈目标"""
        targets = decision.get('take_profit') or decision.get('targets', [])
        
        if not targets:
            # 必须有止盈目标
            raise ValueError("Must have take profit targets")
        
        if not isinstance(targets, list):
            targets = [targets]
        
        # 转换为数字
        result = []
        for target in targets:
            if isinstance(target, (int, float)):
                result.append(float(target))
            elif isinstance(target, str):
                import re
                match = re.search(r'[\d.]+', target)
                if match:
                    result.append(float(match.group()))
        
        if not result:
            raise ValueError("No valid targets extracted")
        
        return sorted(result)  # 从低到高排序
    
    def _extract_time_limit(self, decision: Dict) -> str:
        """提取持仓时限"""
        time_limit = decision.get('time_limit') or decision.get('time_horizon', '24h')
        
        # 标准化时间格式
        if isinstance(time_limit, str):
            if 'h' not in time_limit and 'd' not in time_limit:
                time_limit = f"{time_limit}h"
        
        return time_limit
    
    def _extract_confidence(self, decision: Dict) -> float:
        """提取置信度"""
        confidence = decision.get('confidence', 5)
        
        if isinstance(confidence, str):
            import re
            match = re.search(r'([\d.]+)', confidence)
            if match:
                confidence = float(match.group(1))
        
        # 归一化到0-10
        if confidence > 1 and confidence <= 100:
            confidence = confidence / 10
        
        if confidence < 0 or confidence > 10:
            confidence = 5  # 默认中等置信度
        
        return round(confidence, 1)
    
    def _should_execute_now(self, decision: Dict) -> bool:
        """判断是否立即执行"""
        # 关键词判断
        text = str(decision).lower()
        immediate_words = ['now', 'immediate', '立即', '马上', 'urgent', '紧急']
        wait_words = ['wait', 'hold', '等待', '观察', 'monitor']
        
        for word in immediate_words:
            if word in text:
                return True
        
        for word in wait_words:
            if word in text:
                return False
        
        # 默认立即执行
        return True
    
    def _determine_order_type(self, decision: Dict) -> str:
        """确定订单类型"""
        entry = decision.get('entry_price')
        
        if not entry or entry == 0 or str(entry).lower() in ['market', 'current']:
            return "MARKET"
        else:
            return "LIMIT"
    
    def _validate_parameters(self, decision: Dict) -> Dict:
        """验证参数完整性"""
        required = ['symbol', 'action', 'position_size', 'stop_loss']
        validation = {
            'is_valid': True,
            'missing': [],
            'warnings': []
        }
        
        for param in required:
            if not decision.get(param):
                validation['is_valid'] = False
                validation['missing'].append(param)
        
        # 风险检查
        if decision.get('position_size'):
            size = float(decision['position_size'].replace('%', ''))
            if size > 30:
                validation['warnings'].append("Position size > 30%")
        
        return validation
    
    def _is_executable(self, formatted: Dict) -> bool:
        """判断决策是否可执行"""
        validation = formatted.get('validation', {})
        return validation.get('is_valid', False)
    
    def _create_rejection_decision(self, reason: str) -> Dict:
        """创建拒绝决策"""
        return {
            "timestamp": datetime.now().isoformat(),
            "decision_type": "REJECTED",
            "action": "WAIT",
            "reason": reason,
            "execute_now": False
        }
    
    def create_standard_decision(
        self,
        symbol: str,
        action: str,
        entry: float,
        stop: float,
        targets: List[float],
        size: str = "10%",
        leverage: int = 1,
        reason: str = ""
    ) -> Dict:
        """
        创建标准决策（供AI使用的模板）
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "decision_type": "STANDARD_ORDER",
            "symbol": symbol,
            "action": action,
            "entry_price": entry,
            "position_size": size,
            "leverage": leverage,
            "stop_loss": stop,
            "take_profit": targets,
            "time_limit": "24h",
            "confidence": 7.5,
            "reason": reason,
            "execute_now": True,
            "order_type": "LIMIT" if entry > 0 else "MARKET"
        }


# 决策示例（AI必须输出这种格式）
DECISION_EXAMPLES = {
    "做多示例": {
        "symbol": "BTC/USDT",
        "action": "LONG",
        "entry_price": 67500,
        "position_size": "15%",
        "leverage": 2,
        "stop_loss": 66000,
        "take_profit": [68500, 69500, 71000],
        "time_limit": "48h",
        "confidence": 8.5,
        "reason": "突破关键阻力，量价配合",
        "execute_now": True
    },
    
    "做空示例": {
        "symbol": "ETH/USDT",
        "action": "SHORT",
        "entry_price": 3850,
        "position_size": "10%",
        "leverage": 3,
        "stop_loss": 3950,
        "take_profit": [3750, 3650, 3500],
        "time_limit": "24h",
        "confidence": 7.0,
        "reason": "顶部背离，巨鲸出货",
        "execute_now": True
    },
    
    "平仓示例": {
        "symbol": "SOL/USDT",
        "action": "CLOSE",
        "entry_price": 0,  # 市价
        "position_size": "100%",  # 全部平仓
        "leverage": 1,
        "stop_loss": 0,
        "take_profit": [],
        "time_limit": "0h",
        "confidence": 9.0,
        "reason": "黑天鹅事件，立即止损",
        "execute_now": True
    }
}


def test_formatter():
    """测试格式化器"""
    formatter = EnhancedDecisionFormatter()
    
    # 测试明确的决策
    good_decision = {
        "symbol": "BTC/USDT",
        "action": "LONG",
        "entry_price": 67500,
        "position_size": "10%",
        "stop_loss": 66000,
        "take_profit": [68500, 69500],
        "confidence": 8
    }
    
    result = formatter.format_decision(good_decision, {"source": "test"})
    print("Good decision:", json.dumps(result, indent=2))
    
    # 测试模糊的决策（应该被拒绝）
    bad_decision = {
        "action": "可能做多",
        "suggestion": "建议观察",
        "analysis": "可以考虑入场"
    }
    
    result = formatter.format_decision(bad_decision, {"source": "test"})
    print("Bad decision:", json.dumps(result, indent=2))


if __name__ == "__main__":
    test_formatter()