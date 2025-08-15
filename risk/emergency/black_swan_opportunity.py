"""
Tiger系统 - 黑天鹅机会系统
窗口：7号
功能：将黑天鹅事件转化为盈利机会
作者：Window-7 Risk Control Officer
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlackSwanPhase(Enum):
    """黑天鹅阶段"""
    EARLY_WARNING = "early_warning"  # 预警期
    PROTECTION = "protection"  # 保护期
    OBSERVATION = "observation"  # 观察期
    OPPORTUNITY = "opportunity"  # 机会期
    RECOVERY = "recovery"  # 恢复期


class WarningLevel(Enum):
    """预警级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BlackSwanEvent:
    """黑天鹅事件"""
    id: str
    type: str
    severity: str
    phase: BlackSwanPhase
    start_time: datetime
    indicators: Dict
    actions_taken: List[str]
    opportunities_identified: List[Dict]
    profit_captured: float = 0


class BlackSwanOpportunitySystem:
    """黑天鹅机会系统 - 危机就是机会！"""
    
    def __init__(self):
        self.current_events = {}  # 当前事件
        self.event_history = []  # 历史事件
        self.warning_signals = {}  # 预警信号
        self.protection_mode = False  # 保护模式
        self.opportunity_mode = False  # 机会模式
        
        # 历史黑天鹅案例库
        self.historical_patterns = {
            "2020_312": {
                "event": "COVID暴跌",
                "pattern": {
                    "pre_signals": ["链上大额转移", "期货持仓激增", "主流媒体恐慌"],
                    "crash_magnitude": -0.50,
                    "bottom_signals": ["极度恐慌", "大规模爆仓", "成交量爆炸"],
                    "recovery_time": 30,  # 天
                    "recovery_magnitude": 10.0  # 倍
                },
                "lesson": "提前2天有链上异常，底部3850是绝佳机会"
            },
            "2022_luna": {
                "event": "LUNA崩盘",
                "pattern": {
                    "pre_signals": ["UST脱锚", "大额赎回", "社区恐慌"],
                    "crash_magnitude": -0.40,
                    "bottom_signals": ["连环清算", "交易所限制", "投降式抛售"],
                    "recovery_time": 7,
                    "recovery_magnitude": 0.40
                },
                "lesson": "算法稳定币风险暴露，BTC被错杀到26000"
            },
            "2023_ftx": {
                "event": "FTX破产",
                "pattern": {
                    "pre_signals": ["FTT异常抛售", "流动性危机", "挤兑传闻"],
                    "crash_magnitude": -0.25,
                    "bottom_signals": ["破产确认", "全面恐慌", "无差别抛售"],
                    "recovery_time": 14,
                    "recovery_magnitude": 1.0
                },
                "lesson": "中心化交易所风险，15500抄底机会"
            }
        }
        
        # 三阶段策略配置
        self.phase_strategies = {
            BlackSwanPhase.EARLY_WARNING: {
                "duration": 48,  # 小时
                "actions": ["reduce_leverage", "prepare_cash", "set_alerts", "notify_ai"],
                "position_adjustment": -0.3  # 减仓30%
            },
            BlackSwanPhase.PROTECTION: {
                "duration": 6,  # 小时
                "actions": ["protect_portfolio", "open_hedges", "monitor_closely"],
                "position_adjustment": -0.5  # 再减50%
            },
            BlackSwanPhase.OBSERVATION: {
                "duration": 6,  # 小时
                "actions": ["monitor_panic", "identify_bottom", "prepare_entry"],
                "position_adjustment": 0  # 观察不动
            },
            BlackSwanPhase.OPPORTUNITY: {
                "duration": 24,  # 小时
                "actions": ["gradual_accumulation", "aggressive_buying", "set_targets"],
                "position_adjustment": 0.5  # 激进建仓50%
            },
            BlackSwanPhase.RECOVERY: {
                "duration": 168,  # 小时（一周）
                "actions": ["take_profits", "rebalance", "review_lessons"],
                "position_adjustment": 0  # 正常管理
            }
        }
    
    def detect_early_warning_signals(self, market_data: Dict) -> Tuple[WarningLevel, Dict]:
        """
        检测早期预警信号
        
        Args:
            market_data: 市场数据
            
        Returns:
            (预警级别, 详细信号)
        """
        warning_scores = {
            "on_chain": self._analyze_on_chain_anomaly(market_data),
            "market_structure": self._analyze_market_structure(market_data),
            "social_sentiment": self._analyze_social_panic(market_data)
        }
        
        # 计算总分
        total_score = sum(warning_scores.values())
        
        # 确定预警级别
        if total_score >= 25:
            level = WarningLevel.CRITICAL
        elif total_score >= 20:
            level = WarningLevel.HIGH
        elif total_score >= 15:
            level = WarningLevel.MEDIUM
        else:
            level = WarningLevel.LOW
        
        detailed_signals = {
            "level": level.value,
            "total_score": total_score,
            "components": warning_scores,
            "timestamp": datetime.now().isoformat(),
            "recommended_action": self._get_recommended_action(level)
        }
        
        # 记录预警
        if level in [WarningLevel.HIGH, WarningLevel.CRITICAL]:
            self._create_black_swan_event(level, detailed_signals)
        
        return level, detailed_signals
    
    def _analyze_on_chain_anomaly(self, market_data: Dict) -> float:
        """分析链上异常"""
        score = 0
        
        # 大户流出
        whale_outflow = market_data.get("whale_net_flow", 0)
        if whale_outflow < -1000:  # 净流出超过1000 BTC
            score += 5
            if whale_outflow < -3000:
                score += 5
        
        # 交易所流入
        exchange_inflow = market_data.get("exchange_inflow", 0)
        if exchange_inflow > 10000:  # 流入超过10000 BTC
            score += 3
            if exchange_inflow > 20000:
                score += 3
        
        # 稳定币增发
        stablecoin_print = market_data.get("usdt_print", 0)
        if stablecoin_print > 1000000000:  # 10亿美元
            score -= 2  # 增发是利好，减少警告分
        
        # DeFi清算
        defi_liquidations = market_data.get("defi_liquidations", 0)
        if defi_liquidations > 50000000:  # 5000万美元
            score += 3
        
        return min(10, max(0, score))
    
    def _analyze_market_structure(self, market_data: Dict) -> float:
        """分析市场结构"""
        score = 0
        
        # 资金费率
        funding_rate = market_data.get("funding_rate", 0)
        if abs(funding_rate) > 0.003:  # 0.3%极端费率
            score += 4
        
        # 现货期货基差
        basis = market_data.get("futures_basis", 0)
        if abs(basis) > 0.05:  # 5%基差
            score += 3
        
        # 成交量
        volume_ratio = market_data.get("volume_ratio", 1)
        if volume_ratio < 0.3:  # 成交量萎缩70%
            score += 2
        
        # 波动率
        volatility = market_data.get("volatility", 0)
        if volatility > 1.0:  # 日波动超过100%年化
            score += 3
        
        return min(10, max(0, score))
    
    def _analyze_social_panic(self, market_data: Dict) -> float:
        """分析社交恐慌"""
        score = 0
        
        # 恐慌指数
        fear_index = market_data.get("fear_greed_index", 50)
        if fear_index < 20:
            score += 5
        elif fear_index < 30:
            score += 3
        
        # 社交情绪
        twitter_sentiment = market_data.get("twitter_sentiment", 0)
        if twitter_sentiment < -0.7:  # 极度负面
            score += 3
        
        # 搜索趋势
        google_trends = market_data.get("bitcoin_dead_searches", 0)
        if google_trends > 80:  # 搜索激增
            score += 2
        
        # 主流媒体
        media_fud = market_data.get("mainstream_media_negative", 0)
        if media_fud > 0.8:  # 80%负面报道
            score += 2
        
        return min(10, max(0, score))
    
    def execute_black_swan_strategy(self, warning_level: WarningLevel, market_data: Dict) -> Dict:
        """
        执行黑天鹅策略
        
        Args:
            warning_level: 预警级别
            market_data: 市场数据
            
        Returns:
            执行结果
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "warning_level": warning_level.value,
            "actions": [],
            "positions_adjusted": {},
            "opportunities": []
        }
        
        if warning_level == WarningLevel.LOW:
            result["actions"].append("继续监控")
            return result
        
        elif warning_level == WarningLevel.MEDIUM:
            # 早期预警阶段
            result["actions"].extend([
                "降低杠杆至1倍",
                "准备30%现金",
                "设置价格警报",
                "通知AI系统准备"
            ])
            result["positions_adjusted"]["leverage"] = 1
            result["positions_adjusted"]["cash_ratio"] = 0.3
            
        elif warning_level == WarningLevel.HIGH:
            # 保护阶段
            self.protection_mode = True
            result["actions"].extend([
                "立即减仓50%",
                "开设对冲仓位",
                "严格止损",
                "密切监控"
            ])
            result["positions_adjusted"]["reduction"] = 0.5
            result["positions_adjusted"]["hedges"] = True
            
            # 同时开始寻找机会
            self._monitor_panic_level(market_data, result)
            
        elif warning_level == WarningLevel.CRITICAL:
            # 黑天鹅确认，执行完整策略
            return self._execute_full_black_swan_strategy(market_data)
        
        return result
    
    def _execute_full_black_swan_strategy(self, market_data: Dict) -> Dict:
        """执行完整的黑天鹅策略"""
        current_phase = self._determine_current_phase(market_data)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "phase": current_phase.value,
            "actions": [],
            "opportunities": []
        }
        
        if current_phase == BlackSwanPhase.EARLY_WARNING:
            # 提前准备
            self._reduce_leverage()
            self._prepare_dry_powder()
            self._set_alerts()
            self._notify_ai_system("PREPARE_FOR_BLACK_SWAN")
            
            result["actions"] = [
                "杠杆已降至0",
                "准备50%现金弹药",
                "设置多级警报",
                "AI系统已通知"
            ]
            
        elif current_phase == BlackSwanPhase.PROTECTION:
            # 立即保护
            self._protect_portfolio()
            self._monitor_panic_level(market_data, result)
            self._identify_bottom_signals(market_data, result)
            
            result["actions"] = [
                "保护现有仓位",
                "监控恐慌程度",
                "寻找底部信号"
            ]
            
        elif current_phase == BlackSwanPhase.OBSERVATION:
            # 观察等待
            panic_level = self._calculate_panic_level(market_data)
            if panic_level > 0.8:  # 恐慌达到极点
                current_phase = BlackSwanPhase.OPPORTUNITY
            
            result["actions"] = [
                f"恐慌水平: {panic_level:.1%}",
                "继续观察",
                "准备出击"
            ]
            
        elif current_phase == BlackSwanPhase.OPPORTUNITY:
            # 转守为攻！
            self.opportunity_mode = True
            opportunities = self._identify_opportunities(market_data)
            
            for opp in opportunities:
                self._execute_opportunity_trade(opp)
                result["opportunities"].append(opp)
            
            result["actions"] = [
                "激进模式启动",
                f"发现{len(opportunities)}个机会",
                "分批建仓中",
                "设置止盈目标"
            ]
            
        elif current_phase == BlackSwanPhase.RECOVERY:
            # 恢复期管理
            result["actions"] = [
                "逐步止盈",
                "恢复正常配置",
                "总结经验教训"
            ]
        
        return result
    
    def _determine_current_phase(self, market_data: Dict) -> BlackSwanPhase:
        """确定当前阶段"""
        # 简化判断逻辑
        price_drop = market_data.get("price_drop_from_high", 0)
        time_since_drop = market_data.get("hours_since_drop", 0)
        panic_level = self._calculate_panic_level(market_data)
        
        if price_drop < -0.1 and time_since_drop < 2:
            return BlackSwanPhase.PROTECTION
        elif price_drop < -0.2 and time_since_drop < 6:
            return BlackSwanPhase.OBSERVATION
        elif price_drop < -0.3 and panic_level > 0.8:
            return BlackSwanPhase.OPPORTUNITY
        elif time_since_drop > 24:
            return BlackSwanPhase.RECOVERY
        else:
            return BlackSwanPhase.EARLY_WARNING
    
    def _calculate_panic_level(self, market_data: Dict) -> float:
        """计算恐慌水平"""
        factors = {
            "fear_index": (100 - market_data.get("fear_greed_index", 50)) / 100,
            "liquidations": min(market_data.get("liquidations", 0) / 1000000000, 1),
            "volume_spike": min(market_data.get("volume_ratio", 1) / 5, 1),
            "price_drop": min(abs(market_data.get("price_drop_24h", 0)) / 0.3, 1)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _identify_opportunities(self, market_data: Dict) -> List[Dict]:
        """识别机会"""
        opportunities = []
        current_price = market_data.get("price", 0)
        
        # 极度恐慌买入机会
        if market_data.get("fear_greed_index", 50) < 10:
            opportunities.append({
                "type": "EXTREME_FEAR_BUY",
                "symbol": market_data.get("symbol", "BTC"),
                "entry_price": current_price,
                "size": 0.10,  # 10%仓位
                "stop_loss": current_price * 0.95,
                "targets": [
                    current_price * 1.15,
                    current_price * 1.30,
                    current_price * 1.50
                ],
                "confidence": 8.5
            })
        
        # 爆仓底部机会
        if market_data.get("liquidations", 0) > 1000000000:
            opportunities.append({
                "type": "LIQUIDATION_BOTTOM",
                "symbol": market_data.get("symbol", "BTC"),
                "entry_price": current_price,
                "size": 0.08,
                "stop_loss": current_price * 0.97,
                "targets": [
                    current_price * 1.10,
                    current_price * 1.20
                ],
                "confidence": 7.5
            })
        
        # 巨鲸抄底跟随
        if market_data.get("whale_accumulation", False):
            opportunities.append({
                "type": "WHALE_FOLLOWING",
                "symbol": market_data.get("symbol", "BTC"),
                "entry_price": current_price,
                "size": 0.05,
                "stop_loss": current_price * 0.95,
                "targets": [
                    current_price * 1.25
                ],
                "confidence": 7.0
            })
        
        return opportunities
    
    def _monitor_panic_level(self, market_data: Dict, result: Dict):
        """监控恐慌水平"""
        panic_level = self._calculate_panic_level(market_data)
        
        if panic_level > 0.9:
            result["opportunities"].append({
                "signal": "EXTREME_PANIC",
                "action": "准备激进买入",
                "confidence": 9.0
            })
        elif panic_level > 0.7:
            result["opportunities"].append({
                "signal": "HIGH_PANIC",
                "action": "开始小仓位试探",
                "confidence": 7.0
            })
    
    def _identify_bottom_signals(self, market_data: Dict, result: Dict):
        """识别底部信号"""
        bottom_signals = []
        
        # 成交量爆炸
        if market_data.get("volume_ratio", 1) > 5:
            bottom_signals.append("VOLUME_CLIMAX")
        
        # RSI极度超卖
        if market_data.get("rsi", 50) < 20:
            bottom_signals.append("EXTREME_OVERSOLD")
        
        # 大规模投降
        if market_data.get("capitulation_indicator", 0) > 0.8:
            bottom_signals.append("CAPITULATION")
        
        if len(bottom_signals) >= 2:
            result["opportunities"].append({
                "signal": "BOTTOM_FORMING",
                "indicators": bottom_signals,
                "action": "准备建仓",
                "confidence": 8.0
            })
    
    def _create_black_swan_event(self, level: WarningLevel, signals: Dict):
        """创建黑天鹅事件记录"""
        event_id = f"BS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        event = BlackSwanEvent(
            id=event_id,
            type="MARKET_CRASH",
            severity=level.value,
            phase=BlackSwanPhase.EARLY_WARNING,
            start_time=datetime.now(),
            indicators=signals,
            actions_taken=[],
            opportunities_identified=[]
        )
        
        self.current_events[event_id] = event
        logger.warning(f"黑天鹅事件创建: {event_id} - 级别: {level.value}")
    
    def _get_recommended_action(self, level: WarningLevel) -> str:
        """获取建议行动"""
        actions = {
            WarningLevel.LOW: "继续观察",
            WarningLevel.MEDIUM: "提高警惕，准备现金",
            WarningLevel.HIGH: "立即减仓，准备对冲",
            WarningLevel.CRITICAL: "紧急避险，等待机会"
        }
        return actions.get(level, "观察")
    
    # 模拟的执行函数
    def _reduce_leverage(self):
        logger.info("降低杠杆至0")
    
    def _prepare_dry_powder(self):
        logger.info("准备现金弹药")
    
    def _set_alerts(self):
        logger.info("设置价格警报")
    
    def _notify_ai_system(self, message: str):
        logger.info(f"通知AI系统: {message}")
    
    def _protect_portfolio(self):
        logger.info("保护投资组合")
    
    def _execute_opportunity_trade(self, opportunity: Dict):
        logger.info(f"执行机会交易: {opportunity['type']}")
    
    def get_historical_lessons(self) -> Dict:
        """获取历史经验教训"""
        return {
            "patterns": self.historical_patterns,
            "key_lessons": [
                "链上数据往往提前1-2天预警",
                "恐慌极值往往是最佳买点",
                "不要试图抄底飞刀，等待止跌信号",
                "黑天鹅后的反弹通常很猛烈",
                "分批建仓，不要all in"
            ],
            "success_factors": [
                "提前准备现金",
                "严格风控",
                "耐心等待",
                "果断执行",
                "及时止盈"
            ]
        }
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "protection_mode": self.protection_mode,
            "opportunity_mode": self.opportunity_mode,
            "active_events": len(self.current_events),
            "current_events": [
                {
                    "id": event.id,
                    "phase": event.phase.value,
                    "severity": event.severity,
                    "duration": str(datetime.now() - event.start_time),
                    "opportunities": len(event.opportunities_identified)
                }
                for event in self.current_events.values()
            ],
            "total_profit_captured": sum(e.profit_captured for e in self.event_history)
        }


if __name__ == "__main__":
    # 测试代码
    bs_system = BlackSwanOpportunitySystem()
    
    # 模拟市场数据 - 黑天鹅场景
    test_market = {
        "symbol": "BTC",
        "price": 60000,
        "price_drop_from_high": -0.25,
        "price_drop_24h": -0.15,
        "hours_since_drop": 4,
        "whale_net_flow": -5000,
        "exchange_inflow": 25000,
        "usdt_print": 0,
        "defi_liquidations": 80000000,
        "funding_rate": -0.004,
        "futures_basis": -0.06,
        "volume_ratio": 0.2,
        "volatility": 1.5,
        "fear_greed_index": 8,
        "twitter_sentiment": -0.9,
        "bitcoin_dead_searches": 95,
        "mainstream_media_negative": 0.9,
        "liquidations": 1500000000,
        "rsi": 15,
        "whale_accumulation": True
    }
    
    # 检测预警
    warning_level, signals = bs_system.detect_early_warning_signals(test_market)
    print(f"预警级别: {warning_level.value}")
    print(f"预警信号: {json.dumps(signals, indent=2)}")
    
    # 执行策略
    result = bs_system.execute_black_swan_strategy(warning_level, test_market)
    print(f"\n执行结果: {json.dumps(result, indent=2)}")
    
    # 获取历史经验
    lessons = bs_system.get_historical_lessons()
    print(f"\n历史经验:")
    for lesson in lessons["key_lessons"]:
        print(f"  - {lesson}")
    
    # 状态报告
    status = bs_system.get_status_report()
    print(f"\n系统状态: {json.dumps(status, indent=2)}")