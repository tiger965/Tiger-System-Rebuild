"""
黑天鹅双向机会策略模板
危机=危险+机会，双向都要抓！
历史验证的双赢策略
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class BlackSwanStage(Enum):
    """黑天鹅事件阶段"""
    WARNING = "warning"        # 预警期 -48h到-24h → 做空机会
    OUTBREAK = "outbreak"      # 爆发期 -24h到0h → 减仓+对冲
    PANIC = "panic"           # 恐慌期 0h到+12h → 观察底部
    RECOVERY = "recovery"     # 恢复期 +12h到+48h → 抄底机会
    AFTERMATH = "aftermath"   # 余波期 +48h后 → 恢复常态


class BlackSwanBidirectionalStrategy:
    """黑天鹅双向机会策略"""
    
    def __init__(self):
        # 历史案例库
        self.historical_cases = [
            {
                'date': '2020-03-12',
                'event': 'COVID Crash',
                'short_profit': 30,  # 做空收益
                'bottom_price': 3850,
                'long_profit': 300,  # 抄底收益
                'lesson': '提前做空赚30% → 3850抄底赚300%'
            },
            {
                'date': '2022-05-09',
                'event': 'LUNA Collapse',
                'short_profit': 50,
                'bottom_price': 26000,
                'long_profit': 40,
                'lesson': '提前做空赚50% → 26000抄底赚40%'
            },
            {
                'date': '2022-11-08',
                'event': 'FTX Bankruptcy',
                'short_profit': 20,
                'bottom_price': 15500,
                'long_profit': 100,
                'lesson': '提前做空赚20% → 15500抄底赚100%'
            }
        ]
        
        # 策略参数
        self.strategy_params = {
            'short': {
                'position_size': (0.03, 0.05),  # 3-5%
                'leverage': (2, 3),  # 2-3倍
                'stop_loss': 0.05,  # 向上5%
                'targets': [-0.15, -0.30],  # -15%到-30%
                'time_limit': 48  # 48小时
            },
            'long': {
                'position_sizes': [0.03, 0.03, 0.04],  # 分批建仓
                'stop_loss': 0.05,  # -5%（宽松）
                'targets': [0.20, 0.50],  # +20%到+50%
                'holding_days': 7  # 1-7天
            }
        }
    
    def get_bidirectional_prompt(self) -> str:
        """获取黑天鹅双向机会分析模板"""
        return """
💎⚡ 黑天鹅双向机会分析

当前阶段：{stage}
├── 预警期（-48h到-24h）→ 做空机会
├── 爆发期（-24h到0h）→ 减仓+对冲
├── 恐慌期（0h到+12h）→ 观察底部
└── 恢复期（+12h到+48h）→ 抄底机会

=== 做空机会评估 ===
触发条件：
- 链上巨鲸出逃：{whale_exodus}
- 交易所异常：{exchange_anomaly}
- 社交恐慌蔓延：{social_panic}
- 技术形态破位：{technical_breakdown}

做空策略：
1. 仓位：3-5%（不要贪心）
2. 杠杆：2-3倍（控制风险）
3. 止损：向上5%（严格执行）
4. 目标：-15%到-30%
5. 时限：24-48小时

=== 抄底机会评估 ===
触发条件：
- RSI极度超卖：{rsi}（<20）
- 爆仓达到极值：{max_liquidation}
- 恐慌指数>90：{fear_greed}
- 链上聪明钱买入：{smart_money}

抄底策略：
1. 仓位：分批建仓（3%+3%+4%）
2. 时机：恐慌最高点
3. 止损：-5%（宽松一点）
4. 目标：+20%到+50%反弹
5. 持有：短期1-7天

=== 历史案例对比 ===
2020.3.12：提前做空赚30% → 3850抄底赚300%
2022.5 LUNA：提前做空赚50% → 26000抄底赚40%
2022.11 FTX：提前做空赚20% → 15500抄底赚100%

请综合分析：
1. 当前最适合的策略（做空/等待/抄底）
2. 具体执行参数
3. 风险控制要点
4. 预期收益目标
5. 备用方案

记住：危机=危险+机会，两边都要抓！
"""
    
    def identify_stage(self, event_data: Dict) -> BlackSwanStage:
        """识别当前所处阶段"""
        event_time = event_data.get('first_signal_time')
        if not event_time:
            return BlackSwanStage.WARNING
        
        # 计算时间差
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time)
        
        time_diff = (datetime.now() - event_time).total_seconds() / 3600  # 小时
        
        if time_diff < -24:
            return BlackSwanStage.WARNING
        elif -24 <= time_diff < 0:
            return BlackSwanStage.OUTBREAK
        elif 0 <= time_diff < 12:
            return BlackSwanStage.PANIC
        elif 12 <= time_diff < 48:
            return BlackSwanStage.RECOVERY
        else:
            return BlackSwanStage.AFTERMATH
    
    def analyze_short_opportunity(self, market_data: Dict) -> Dict:
        """分析做空机会"""
        score = 0
        triggers = []
        
        # 链上巨鲸出逃
        whale_exodus = market_data.get('whale_outflow', 0)
        if whale_exodus > 100_000_000:  # 1亿美元
            score += 30
            triggers.append(f"Whale exodus: ${whale_exodus/1e6:.0f}M")
        
        # 交易所异常
        if market_data.get('exchange_issues', False):
            score += 25
            triggers.append("Exchange anomaly detected")
        
        # 社交恐慌
        social_sentiment = market_data.get('social_sentiment', 50)
        if social_sentiment < 20:
            score += 20
            triggers.append(f"Social panic: {social_sentiment}/100")
        
        # 技术破位
        if market_data.get('technical_breakdown', False):
            score += 25
            triggers.append("Technical breakdown confirmed")
        
        # 生成建议
        if score >= 60:
            return {
                'opportunity': 'HIGH',
                'score': score,
                'action': 'SHORT',
                'position_size': '5%',
                'leverage': 3,
                'stop_loss': '+5%',
                'targets': ['-15%', '-25%'],
                'triggers': triggers,
                'confidence': score / 100
            }
        elif score >= 40:
            return {
                'opportunity': 'MEDIUM',
                'score': score,
                'action': 'SHORT',
                'position_size': '3%',
                'leverage': 2,
                'stop_loss': '+5%',
                'targets': ['-10%', '-20%'],
                'triggers': triggers,
                'confidence': score / 100
            }
        else:
            return {
                'opportunity': 'LOW',
                'score': score,
                'action': 'WAIT',
                'triggers': triggers,
                'confidence': score / 100
            }
    
    def analyze_long_opportunity(self, market_data: Dict) -> Dict:
        """分析抄底机会"""
        score = 0
        triggers = []
        
        # RSI超卖
        rsi = market_data.get('rsi', 50)
        if rsi < 20:
            score += 35
            triggers.append(f"RSI extremely oversold: {rsi}")
        elif rsi < 30:
            score += 20
            triggers.append(f"RSI oversold: {rsi}")
        
        # 爆仓极值
        liquidations = market_data.get('liquidations_24h', 0)
        if liquidations > 1_000_000_000:  # 10亿美元
            score += 30
            triggers.append(f"Massive liquidations: ${liquidations/1e9:.1f}B")
        
        # 恐慌指数
        fear_greed = market_data.get('fear_greed_index', 50)
        if fear_greed < 10:
            score += 35
            triggers.append(f"Extreme fear: {fear_greed}/100")
        elif fear_greed < 20:
            score += 20
            triggers.append(f"High fear: {fear_greed}/100")
        
        # 聪明钱流入
        smart_money = market_data.get('smart_money_flow', 0)
        if smart_money > 50_000_000:  # 5000万美元
            score += 25
            triggers.append(f"Smart money buying: ${smart_money/1e6:.0f}M")
        
        # 生成建议
        if score >= 70:
            return {
                'opportunity': 'HIGH',
                'score': score,
                'action': 'LONG',
                'position_sizes': ['3%', '3%', '4%'],  # 分批
                'entry_strategy': 'DCA over 6 hours',
                'stop_loss': '-5%',
                'targets': ['+20%', '+40%', '+60%'],
                'holding_period': '3-7 days',
                'triggers': triggers,
                'confidence': score / 100
            }
        elif score >= 50:
            return {
                'opportunity': 'MEDIUM',
                'score': score,
                'action': 'LONG',
                'position_sizes': ['2%', '3%'],
                'entry_strategy': 'DCA over 12 hours',
                'stop_loss': '-5%',
                'targets': ['+15%', '+30%'],
                'holding_period': '2-5 days',
                'triggers': triggers,
                'confidence': score / 100
            }
        else:
            return {
                'opportunity': 'LOW',
                'score': score,
                'action': 'WAIT',
                'triggers': triggers,
                'confidence': score / 100
            }
    
    def get_comprehensive_strategy(self, market_data: Dict) -> Dict:
        """获取综合双向策略"""
        # 识别阶段
        stage = self.identify_stage(market_data)
        
        # 分析机会
        short_opp = self.analyze_short_opportunity(market_data)
        long_opp = self.analyze_long_opportunity(market_data)
        
        # 根据阶段推荐策略
        if stage == BlackSwanStage.WARNING:
            primary_strategy = 'SHORT'
            primary_analysis = short_opp
            secondary_strategy = 'PREPARE_HEDGE'
        elif stage == BlackSwanStage.OUTBREAK:
            primary_strategy = 'HEDGE'
            primary_analysis = {'action': 'REDUCE', 'message': 'Reduce positions and hedge'}
            secondary_strategy = 'MONITOR'
        elif stage == BlackSwanStage.PANIC:
            primary_strategy = 'OBSERVE'
            primary_analysis = {'action': 'WAIT', 'message': 'Observe for bottom signals'}
            secondary_strategy = 'PREPARE_LONG'
        elif stage == BlackSwanStage.RECOVERY:
            primary_strategy = 'LONG'
            primary_analysis = long_opp
            secondary_strategy = 'DCA'
        else:
            primary_strategy = 'NORMAL'
            primary_analysis = {'action': 'NORMAL_TRADING'}
            secondary_strategy = 'MONITOR'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_stage': stage.value,
            'primary_strategy': primary_strategy,
            'primary_analysis': primary_analysis,
            'secondary_strategy': secondary_strategy,
            'short_opportunity': short_opp,
            'long_opportunity': long_opp,
            'historical_reference': self._get_similar_case(market_data),
            'risk_warning': self._get_risk_warning(stage),
            'execution_checklist': self._get_execution_checklist(stage)
        }
    
    def _get_similar_case(self, market_data: Dict) -> Optional[Dict]:
        """找到最相似的历史案例"""
        # 简单匹配逻辑
        severity = market_data.get('severity', 'medium')
        
        if severity == 'extreme':
            return self.historical_cases[0]  # COVID
        elif 'exchange' in market_data.get('event_type', '').lower():
            return self.historical_cases[2]  # FTX
        else:
            return self.historical_cases[1]  # LUNA
    
    def _get_risk_warning(self, stage: BlackSwanStage) -> str:
        """获取风险警告"""
        warnings = {
            BlackSwanStage.WARNING: "Early stage - be cautious with position size",
            BlackSwanStage.OUTBREAK: "High volatility - use tight stops",
            BlackSwanStage.PANIC: "Extreme emotions - don't catch falling knife",
            BlackSwanStage.RECOVERY: "False rallies possible - take profits gradually",
            BlackSwanStage.AFTERMATH: "Return to normal - reduce speculation"
        }
        return warnings.get(stage, "Monitor closely")
    
    def _get_execution_checklist(self, stage: BlackSwanStage) -> List[str]:
        """获取执行清单"""
        checklists = {
            BlackSwanStage.WARNING: [
                "✓ Check news sources",
                "✓ Set price alerts",
                "✓ Prepare short orders",
                "✓ Reduce long exposure"
            ],
            BlackSwanStage.OUTBREAK: [
                "✓ Execute hedges",
                "✓ Cancel pending longs",
                "✓ Move to stablecoins",
                "✓ Set tight stops"
            ],
            BlackSwanStage.PANIC: [
                "✓ Monitor RSI (<20)",
                "✓ Watch liquidation data",
                "✓ Identify support levels",
                "✓ Prepare buy orders"
            ],
            BlackSwanStage.RECOVERY: [
                "✓ Start DCA buying",
                "✓ Set profit targets",
                "✓ Monitor resistance",
                "✓ Trail stops up"
            ],
            BlackSwanStage.AFTERMATH: [
                "✓ Review performance",
                "✓ Adjust position sizes",
                "✓ Update strategies",
                "✓ Document lessons"
            ]
        }
        return checklists.get(stage, [])