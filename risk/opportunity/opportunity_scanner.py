"""
Tiger系统 - 机会发现系统
窗口：7号
功能：在风控的同时主动发现市场机会
作者：Window-7 Risk Control Officer
"""

import logging
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    """机会类型"""
    EXTREME_OVERSOLD = "extreme_oversold"
    SUPPORT_BOUNCE = "support_bounce"
    WHALE_ACCUMULATION = "whale_accumulation"
    PANIC_SELLING = "panic_selling"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"


@dataclass
class OpportunitySignal:
    """机会信号"""
    id: str
    type: OpportunityType
    symbol: str
    price: float
    confidence: float  # 0-10
    risk_score: float  # 0-10
    potential_return: float  # 预期收益率
    suggested_size: float  # 建议仓位
    stop_loss: float  # 止损价
    targets: List[float]  # 目标价位
    expire_time: datetime  # 过期时间
    trigger_conditions: Dict  # 触发条件
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class OpportunityScanner:
    """机会扫描器 - 危中寻机，守中带攻"""
    
    def __init__(self):
        self.active_opportunities = {}  # 活跃的机会
        self.opportunity_history = []  # 历史机会
        self.ai_communication_channel = None  # AI通信通道
        
        # 机会触发条件配置
        self.triggers = {
            OpportunityType.EXTREME_OVERSOLD: {
                "rsi": {"threshold": 20, "operator": "<"},
                "price_drop": {"threshold": 0.15, "period": "24h", "operator": ">"},
                "volume": {"multiplier": 3, "operator": ">"},
                "confidence_required": 7
            },
            OpportunityType.SUPPORT_BOUNCE: {
                "support_distance": {"threshold": 0.02, "operator": "<"},
                "test_count": {"threshold": 3, "operator": ">="},
                "volume_trend": {"pattern": "decreasing"},
                "confidence_required": 6
            },
            OpportunityType.WHALE_ACCUMULATION: {
                "on_chain_buys": {"threshold": 1000000, "operator": ">"},
                "exchange_outflow": {"trend": "increasing"},
                "price_action": {"pattern": "consolidating"},
                "confidence_required": 7
            },
            OpportunityType.PANIC_SELLING: {
                "liquidations": {"threshold": 100000000, "operator": ">"},
                "funding_rate": {"threshold": -0.001, "operator": "<"},
                "fear_index": {"threshold": 20, "operator": "<"},
                "confidence_required": 8
            }
        }
        
        # 机会仓位管理规则
        self.position_rules = {
            "max_size": 0.05,  # 最大5%
            "min_size": 0.01,  # 最小1%
            "stop_loss": 0.02,  # 2%止损
            "time_limit_hours": 48,  # 48小时时限
            "max_concurrent": 3,  # 最多3个并发机会
            "total_risk": 0.10  # 总风险10%
        }
        
        # 机会评分权重
        self.scoring_weights = {
            "technical": 0.3,
            "volume": 0.2,
            "sentiment": 0.2,
            "on_chain": 0.2,
            "timing": 0.1
        }
        
    def scan_market(self, market_data: Dict) -> List[OpportunitySignal]:
        """
        扫描市场寻找机会
        
        Args:
            market_data: 市场数据
            
        Returns:
            机会信号列表
        """
        opportunities = []
        
        # 检查各类机会
        for opp_type in OpportunityType:
            signal = self._check_opportunity_type(opp_type, market_data)
            if signal and signal.confidence >= self.triggers[opp_type]["confidence_required"]:
                opportunities.append(signal)
                logger.info(f"发现机会: {opp_type.value} - {signal.symbol} (置信度: {signal.confidence})")
        
        # 过滤和排序
        opportunities = self._filter_opportunities(opportunities)
        opportunities.sort(key=lambda x: x.confidence * x.potential_return, reverse=True)
        
        # 限制并发数量
        if len(opportunities) > self.position_rules["max_concurrent"]:
            opportunities = opportunities[:self.position_rules["max_concurrent"]]
        
        return opportunities
    
    def _check_opportunity_type(self, opp_type: OpportunityType, market_data: Dict) -> Optional[OpportunitySignal]:
        """检查特定类型的机会"""
        if opp_type == OpportunityType.EXTREME_OVERSOLD:
            return self._check_extreme_oversold(market_data)
        elif opp_type == OpportunityType.SUPPORT_BOUNCE:
            return self._check_support_bounce(market_data)
        elif opp_type == OpportunityType.WHALE_ACCUMULATION:
            return self._check_whale_accumulation(market_data)
        elif opp_type == OpportunityType.PANIC_SELLING:
            return self._check_panic_selling(market_data)
        return None
    
    def _check_extreme_oversold(self, market_data: Dict) -> Optional[OpportunitySignal]:
        """检查极度超卖机会"""
        symbol = market_data.get("symbol", "BTC")
        rsi = market_data.get("rsi", 50)
        price_drop = market_data.get("price_drop_24h", 0)
        volume_ratio = market_data.get("volume_ratio", 1)
        
        triggers = self.triggers[OpportunityType.EXTREME_OVERSOLD]
        
        # 检查触发条件
        if (rsi < triggers["rsi"]["threshold"] and
            price_drop > triggers["price_drop"]["threshold"] and
            volume_ratio > triggers["volume"]["multiplier"]):
            
            # 计算机会参数
            confidence = self._calculate_confidence({
                "rsi": 10 - (rsi / 2),  # RSI越低信心越高
                "price_drop": min(price_drop * 20, 10),  # 跌幅越大信心越高
                "volume": min(volume_ratio, 10)  # 成交量越大信心越高
            })
            
            current_price = market_data.get("price", 0)
            
            return OpportunitySignal(
                id=f"OS_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                type=OpportunityType.EXTREME_OVERSOLD,
                symbol=symbol,
                price=current_price,
                confidence=confidence,
                risk_score=self._calculate_risk_score(market_data),
                potential_return=0.15,  # 预期15%反弹
                suggested_size=self._calculate_position_size(confidence),
                stop_loss=current_price * 0.98,  # 2%止损
                targets=[
                    current_price * 1.05,  # 目标1: 5%
                    current_price * 1.10,  # 目标2: 10%
                    current_price * 1.15   # 目标3: 15%
                ],
                expire_time=datetime.now() + timedelta(hours=48),
                trigger_conditions={
                    "rsi": rsi,
                    "price_drop": price_drop,
                    "volume_ratio": volume_ratio
                }
            )
        
        return None
    
    def _check_support_bounce(self, market_data: Dict) -> Optional[OpportunitySignal]:
        """检查支撑位反弹机会"""
        symbol = market_data.get("symbol", "BTC")
        current_price = market_data.get("price", 0)
        support_level = market_data.get("support_level", 0)
        test_count = market_data.get("support_test_count", 0)
        volume_trend = market_data.get("volume_trend", "stable")
        
        if support_level == 0:
            return None
        
        distance_to_support = abs(current_price - support_level) / support_level
        
        triggers = self.triggers[OpportunityType.SUPPORT_BOUNCE]
        
        if (distance_to_support < triggers["support_distance"]["threshold"] and
            test_count >= triggers["test_count"]["threshold"] and
            volume_trend == "decreasing"):
            
            confidence = self._calculate_confidence({
                "support_strength": min(test_count * 2, 10),
                "distance": 10 - (distance_to_support * 100),
                "volume": 7 if volume_trend == "decreasing" else 3
            })
            
            return OpportunitySignal(
                id=f"SB_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                type=OpportunityType.SUPPORT_BOUNCE,
                symbol=symbol,
                price=current_price,
                confidence=confidence,
                risk_score=self._calculate_risk_score(market_data),
                potential_return=0.10,  # 预期10%反弹
                suggested_size=self._calculate_position_size(confidence),
                stop_loss=support_level * 0.98,  # 支撑位下方2%
                targets=[
                    current_price * 1.03,  # 目标1: 3%
                    current_price * 1.06,  # 目标2: 6%
                    current_price * 1.10   # 目标3: 10%
                ],
                expire_time=datetime.now() + timedelta(hours=24),
                trigger_conditions={
                    "support_level": support_level,
                    "test_count": test_count,
                    "distance": distance_to_support
                }
            )
        
        return None
    
    def _check_whale_accumulation(self, market_data: Dict) -> Optional[OpportunitySignal]:
        """检查巨鲸吸筹机会"""
        symbol = market_data.get("symbol", "BTC")
        on_chain_buys = market_data.get("whale_buys", 0)
        exchange_outflow = market_data.get("exchange_outflow", 0)
        price_volatility = market_data.get("volatility", 1)
        
        triggers = self.triggers[OpportunityType.WHALE_ACCUMULATION]
        
        if (on_chain_buys > triggers["on_chain_buys"]["threshold"] and
            exchange_outflow > 0 and
            price_volatility < 0.5):  # 低波动率表示横盘
            
            confidence = self._calculate_confidence({
                "whale_activity": min(on_chain_buys / 1000000, 10),
                "outflow": min(exchange_outflow / 100000, 10),
                "consolidation": 10 - (price_volatility * 10)
            })
            
            current_price = market_data.get("price", 0)
            
            return OpportunitySignal(
                id=f"WA_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                type=OpportunityType.WHALE_ACCUMULATION,
                symbol=symbol,
                price=current_price,
                confidence=confidence,
                risk_score=self._calculate_risk_score(market_data),
                potential_return=0.20,  # 预期20%上涨
                suggested_size=self._calculate_position_size(confidence),
                stop_loss=current_price * 0.95,  # 5%止损（给更多空间）
                targets=[
                    current_price * 1.07,  # 目标1: 7%
                    current_price * 1.15,  # 目标2: 15%
                    current_price * 1.25   # 目标3: 25%
                ],
                expire_time=datetime.now() + timedelta(hours=72),  # 72小时
                trigger_conditions={
                    "whale_buys": on_chain_buys,
                    "exchange_outflow": exchange_outflow,
                    "volatility": price_volatility
                }
            )
        
        return None
    
    def _check_panic_selling(self, market_data: Dict) -> Optional[OpportunitySignal]:
        """检查恐慌抛售机会"""
        symbol = market_data.get("symbol", "BTC")
        liquidations = market_data.get("liquidations", 0)
        funding_rate = market_data.get("funding_rate", 0)
        fear_index = market_data.get("fear_greed_index", 50)
        
        triggers = self.triggers[OpportunityType.PANIC_SELLING]
        
        if (liquidations > triggers["liquidations"]["threshold"] and
            funding_rate < triggers["funding_rate"]["threshold"] and
            fear_index < triggers["fear_index"]["threshold"]):
            
            confidence = self._calculate_confidence({
                "liquidation_scale": min(liquidations / 100000000, 10),
                "funding_extreme": min(abs(funding_rate) * 1000, 10),
                "fear_level": 10 - (fear_index / 10)
            })
            
            current_price = market_data.get("price", 0)
            
            return OpportunitySignal(
                id=f"PS_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                type=OpportunityType.PANIC_SELLING,
                symbol=symbol,
                price=current_price,
                confidence=confidence,
                risk_score=self._calculate_risk_score(market_data),
                potential_return=0.30,  # 预期30%反弹（恐慌后反弹通常很猛）
                suggested_size=self._calculate_position_size(confidence) * 1.5,  # 可以稍微激进
                stop_loss=current_price * 0.97,  # 3%止损
                targets=[
                    current_price * 1.10,  # 目标1: 10%
                    current_price * 1.20,  # 目标2: 20%
                    current_price * 1.35   # 目标3: 35%
                ],
                expire_time=datetime.now() + timedelta(hours=24),  # 24小时快进快出
                trigger_conditions={
                    "liquidations": liquidations,
                    "funding_rate": funding_rate,
                    "fear_index": fear_index
                }
            )
        
        return None
    
    def notify_ai_system(self, opportunity: OpportunitySignal) -> Dict:
        """
        通知AI系统进行深度分析
        
        Args:
            opportunity: 机会信号
            
        Returns:
            通信结果
        """
        message = {
            "type": "OPPORTUNITY_SIGNAL",
            "from": "window_7_risk",
            "priority": "HIGH",
            "timestamp": datetime.now().isoformat(),
            "opportunity": {
                "id": opportunity.id,
                "type": opportunity.type.value,
                "symbol": opportunity.symbol,
                "price": opportunity.price,
                "confidence": opportunity.confidence,
                "potential_return": opportunity.potential_return,
                "trigger_conditions": opportunity.trigger_conditions
            },
            "current_risk": self._calculate_current_portfolio_risk(),
            "suggested_size": opportunity.suggested_size,
            "require_response": True,
            "timeout": 30  # 30秒超时
        }
        
        # 模拟发送到Redis通道
        logger.info(f"通知AI系统: {opportunity.type.value} - {opportunity.symbol}")
        
        # TODO: 实际实现时连接Redis
        # redis_client.publish("ai_analysis_channel", json.dumps(message))
        
        return {"status": "sent", "message_id": message["opportunity"]["id"]}
    
    def execute_opportunity(self, ai_response: Dict) -> Optional[Dict]:
        """
        根据AI响应执行机会
        
        Args:
            ai_response: AI系统的响应
            
        Returns:
            执行结果
        """
        # 检查置信度
        if ai_response.get("confidence", 0) < 7:
            logger.info(f"AI置信度不足: {ai_response.get('confidence')}, 放弃执行")
            return None
        
        opportunity_id = ai_response.get("opportunity_id")
        if opportunity_id not in self.active_opportunities:
            logger.warning(f"机会已过期或不存在: {opportunity_id}")
            return None
        
        opportunity = self.active_opportunities[opportunity_id]
        
        # 构建执行仓位
        position = {
            "type": "OPPORTUNITY",
            "symbol": opportunity.symbol,
            "size": min(ai_response.get("suggested_size", opportunity.suggested_size), 
                       self.position_rules["max_size"]),
            "stop_loss": max(ai_response.get("stop_loss", opportunity.stop_loss),
                           opportunity.price * (1 - self.position_rules["stop_loss"])),
            "targets": ai_response.get("targets", opportunity.targets),
            "expire_time": opportunity.expire_time,
            "management": "STRICT",  # 严格管理
            "ai_analysis": ai_response.get("analysis", "")
        }
        
        # 检查风险容量
        if not self._check_risk_capacity(position["size"]):
            logger.warning("风险容量不足，无法执行机会")
            return None
        
        logger.info(f"执行机会仓位: {opportunity.symbol} - {position['size']*100:.1f}%")
        
        # 记录执行
        execution_record = {
            "opportunity_id": opportunity_id,
            "position": position,
            "timestamp": datetime.now().isoformat(),
            "status": "EXECUTED"
        }
        
        # 移到历史记录
        self.opportunity_history.append(opportunity)
        del self.active_opportunities[opportunity_id]
        
        return execution_record
    
    def manage_opportunities(self) -> Dict:
        """
        管理活跃的机会仓位
        
        Returns:
            管理报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "active_opportunities": len(self.active_opportunities),
            "actions": []
        }
        
        expired_opportunities = []
        
        for opp_id, opportunity in self.active_opportunities.items():
            # 检查过期
            if datetime.now() > opportunity.expire_time:
                expired_opportunities.append(opp_id)
                report["actions"].append({
                    "id": opp_id,
                    "action": "EXPIRED",
                    "symbol": opportunity.symbol
                })
                continue
            
            # 检查止损
            current_price = self._get_current_price(opportunity.symbol)
            if current_price and current_price <= opportunity.stop_loss:
                report["actions"].append({
                    "id": opp_id,
                    "action": "STOP_LOSS",
                    "symbol": opportunity.symbol,
                    "stop_price": opportunity.stop_loss
                })
            
            # 检查目标
            for i, target in enumerate(opportunity.targets):
                if current_price and current_price >= target:
                    report["actions"].append({
                        "id": opp_id,
                        "action": f"TARGET_{i+1}_REACHED",
                        "symbol": opportunity.symbol,
                        "target_price": target
                    })
        
        # 清理过期机会
        for opp_id in expired_opportunities:
            self.opportunity_history.append(self.active_opportunities[opp_id])
            del self.active_opportunities[opp_id]
        
        return report
    
    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """计算综合置信度"""
        if not factors:
            return 0
        
        total_score = sum(factors.values())
        max_score = len(factors) * 10
        
        confidence = (total_score / max_score) * 10
        return min(10, max(0, confidence))
    
    def _calculate_risk_score(self, market_data: Dict) -> float:
        """计算风险分数"""
        risk_factors = {
            "volatility": min(market_data.get("volatility", 0) * 10, 10),
            "volume": 10 - min(market_data.get("volume_ratio", 1) * 2, 10),
            "trend": 5 if market_data.get("trend") == "down" else 3
        }
        
        return sum(risk_factors.values()) / len(risk_factors)
    
    def _calculate_position_size(self, confidence: float) -> float:
        """根据置信度计算仓位大小"""
        base_size = self.position_rules["min_size"]
        max_size = self.position_rules["max_size"]
        
        # 置信度越高，仓位越大
        size = base_size + (confidence / 10) * (max_size - base_size)
        
        return min(max_size, max(base_size, size))
    
    def _filter_opportunities(self, opportunities: List[OpportunitySignal]) -> List[OpportunitySignal]:
        """过滤机会列表"""
        filtered = []
        
        for opp in opportunities:
            # 过滤低置信度
            if opp.confidence < 6:
                continue
            
            # 过滤高风险
            if opp.risk_score > 8:
                continue
            
            # 过滤低收益
            if opp.potential_return < 0.05:
                continue
            
            filtered.append(opp)
        
        return filtered
    
    def _calculate_current_portfolio_risk(self) -> float:
        """计算当前组合风险"""
        # TODO: 连接实际的仓位管理系统
        return 5.0  # 模拟返回中等风险
    
    def _check_risk_capacity(self, new_position_size: float) -> bool:
        """检查风险容量"""
        current_risk = sum(opp.suggested_size for opp in self.active_opportunities.values())
        
        if current_risk + new_position_size > self.position_rules["total_risk"]:
            return False
        
        if len(self.active_opportunities) >= self.position_rules["max_concurrent"]:
            return False
        
        return True
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        # TODO: 连接实际的价格源
        return None
    
    def get_opportunity_report(self) -> Dict:
        """获取机会报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_opportunities": [
                {
                    "id": opp.id,
                    "type": opp.type.value,
                    "symbol": opp.symbol,
                    "confidence": opp.confidence,
                    "potential_return": f"{opp.potential_return:.1%}",
                    "time_remaining": str(opp.expire_time - datetime.now())
                }
                for opp in self.active_opportunities.values()
            ],
            "statistics": {
                "total_scanned": len(self.opportunity_history) + len(self.active_opportunities),
                "active": len(self.active_opportunities),
                "executed": len([h for h in self.opportunity_history if hasattr(h, "executed")]),
                "expired": len([h for h in self.opportunity_history if not hasattr(h, "executed")])
            }
        }


if __name__ == "__main__":
    # 测试代码
    scanner = OpportunityScanner()
    
    # 模拟市场数据
    test_market_data = {
        "symbol": "BTC",
        "price": 65000,
        "rsi": 18,  # 极度超卖
        "price_drop_24h": 0.18,  # 24小时跌18%
        "volume_ratio": 4.5,  # 成交量4.5倍
        "support_level": 64000,
        "support_test_count": 3,
        "volume_trend": "decreasing",
        "whale_buys": 2000000,
        "exchange_outflow": 500000,
        "volatility": 0.3,
        "liquidations": 150000000,
        "funding_rate": -0.0015,
        "fear_greed_index": 15,
        "trend": "down"
    }
    
    # 扫描机会
    opportunities = scanner.scan_market(test_market_data)
    
    for opp in opportunities:
        print(f"\n发现机会: {opp.type.value}")
        print(f"  币种: {opp.symbol}")
        print(f"  置信度: {opp.confidence:.1f}/10")
        print(f"  预期收益: {opp.potential_return:.1%}")
        print(f"  建议仓位: {opp.suggested_size:.1%}")
        print(f"  止损: {opp.stop_loss:.0f}")
        print(f"  目标: {opp.targets}")
        
        # 通知AI系统
        scanner.notify_ai_system(opp)
    
    # 获取报告
    report = scanner.get_opportunity_report()
    print(f"\n机会报告: {json.dumps(report, indent=2)}")