"""
信号质量评估系统 - 5大维度评分，6级质量等级
维度：技术、市场、情绪、风险、时机
等级：Premium/High/Good/Medium/Low/Poor
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import statistics

logger = logging.getLogger(__name__)


class QualityTier(Enum):
    """质量等级"""
    PREMIUM = "Premium"    # 0.9-1.0 特优
    HIGH = "High"         # 0.8-0.9 高质量
    GOOD = "Good"         # 0.7-0.8 良好
    MEDIUM = "Medium"     # 0.6-0.7 中等
    LOW = "Low"           # 0.4-0.6 较低
    POOR = "Poor"         # 0.0-0.4 较差


@dataclass
class SignalEvaluation:
    """信号评估结果"""
    overall_score: float
    tier: QualityTier
    category_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class QualityRanker:
    """
    信号质量评估系统
    
    评分维度：
    1. 技术强度 (Technical) - 技术指标的强度和一致性
    2. 市场环境 (Market) - 市场情绪和流动性
    3. 情绪因子 (Sentiment) - 社交媒体和新闻情绪
    4. 风险评估 (Risk) - 风险回报比和波动性
    5. 时机选择 (Timing) - 进场时机的合适性
    """
    
    def __init__(self):
        """初始化评估系统"""
        # 评分权重 (总和为1.0)
        self.weights = {
            "technical": 0.25,    # 技术分析权重
            "market": 0.20,       # 市场环境权重
            "sentiment": 0.20,    # 情绪因子权重
            "risk": 0.20,         # 风险评估权重
            "timing": 0.15        # 时机选择权重
        }
        
        # 质量等级阈值
        self.tier_thresholds = {
            QualityTier.PREMIUM: 0.90,
            QualityTier.HIGH: 0.80,
            QualityTier.GOOD: 0.70,
            QualityTier.MEDIUM: 0.60,
            QualityTier.LOW: 0.40,
            QualityTier.POOR: 0.00
        }
        
        # 历史评估记录
        self.evaluation_history = []
        
        logger.info("信号质量评估系统初始化完成")
    
    def evaluate_signal_quality(self, signal_data: Dict) -> Tuple[float, QualityTier, Dict]:
        """
        评估信号质量
        
        Args:
            signal_data: 信号数据
                {
                    "symbol": "BTCUSDT",
                    "action": "buy",
                    "confidence": 0.8,
                    "technical_strength": 0.9,
                    "volume_score": 0.8,
                    "sentiment_score": 0.7,
                    "risk_reward_ratio": 2.5,
                    "volatility": 0.03,
                    "entry_price": 50000,
                    "support_level": 49000,
                    "resistance_level": 52000,
                    "market_cap": 1000000000,
                    "social_mentions": 1000,
                    "news_sentiment": 0.6
                }
        
        Returns:
            (overall_score, tier, evaluation_details)
        """
        # 计算各维度评分
        category_scores = {
            "technical": self._evaluate_technical(signal_data),
            "market": self._evaluate_market(signal_data),
            "sentiment": self._evaluate_sentiment(signal_data),
            "risk": self._evaluate_risk(signal_data),
            "timing": self._evaluate_timing(signal_data)
        }
        
        # 计算加权总分
        overall_score = sum(
            score * self.weights[category]
            for category, score in category_scores.items()
        )
        
        # 确定质量等级
        tier = self._determine_tier(overall_score)
        
        # 生成详细评估
        evaluation_details = self._generate_evaluation_details(
            overall_score, tier, category_scores, signal_data
        )
        
        # 记录评估历史
        self._record_evaluation(signal_data, overall_score, tier, category_scores)
        
        return overall_score, tier, evaluation_details
    
    def _evaluate_technical(self, signal_data: Dict) -> float:
        """评估技术强度"""
        score = 0.0
        
        # 基础技术强度
        technical_strength = signal_data.get("technical_strength", 0.5)
        score += technical_strength * 0.4
        
        # 成交量支持
        volume_score = signal_data.get("volume_score", 0.5)
        score += volume_score * 0.3
        
        # 价格位置评估
        entry_price = signal_data.get("entry_price", 0)
        support_level = signal_data.get("support_level", 0)
        resistance_level = signal_data.get("resistance_level", 0)
        
        if entry_price > 0 and support_level > 0 and resistance_level > 0:
            # 计算价格在支撑阻力区间的位置
            price_range = resistance_level - support_level
            if price_range > 0:
                if signal_data.get("action") == "buy":
                    # 买入信号：价格越接近支撑越好
                    distance_from_support = (entry_price - support_level) / price_range
                    position_score = max(0, 1 - distance_from_support * 2)
                else:
                    # 卖出信号：价格越接近阻力越好
                    distance_from_resistance = (resistance_level - entry_price) / price_range
                    position_score = max(0, 1 - distance_from_resistance * 2)
                
                score += position_score * 0.2
        
        # 趋势一致性
        confidence = signal_data.get("confidence", 0.5)
        score += confidence * 0.1
        
        return min(1.0, score)
    
    def _evaluate_market(self, signal_data: Dict) -> float:
        """评估市场环境"""
        score = 0.0
        
        # 市场流动性
        market_cap = signal_data.get("market_cap", 0)
        if market_cap > 0:
            # 市值越大流动性越好
            if market_cap >= 10_000_000_000:  # 100亿+
                liquidity_score = 1.0
            elif market_cap >= 1_000_000_000:  # 10亿+
                liquidity_score = 0.8
            elif market_cap >= 100_000_000:    # 1亿+
                liquidity_score = 0.6
            else:
                liquidity_score = 0.3
            
            score += liquidity_score * 0.3
        
        # 成交量活跃度
        volume_score = signal_data.get("volume_score", 0.5)
        score += volume_score * 0.3
        
        # 波动性评估
        volatility = signal_data.get("volatility", 0.02)
        # 适中的波动性最好 (1-5%)
        if 0.01 <= volatility <= 0.05:
            volatility_score = 1.0
        elif volatility < 0.01:
            volatility_score = 0.6  # 波动性太低
        elif volatility > 0.1:
            volatility_score = 0.3  # 波动性太高
        else:
            volatility_score = 0.8
        
        score += volatility_score * 0.2
        
        # 市场情绪
        market_sentiment = signal_data.get("market_sentiment", 0.5)
        score += market_sentiment * 0.2
        
        return min(1.0, score)
    
    def _evaluate_sentiment(self, signal_data: Dict) -> float:
        """评估情绪因子"""
        score = 0.0
        
        # 新闻情绪
        news_sentiment = signal_data.get("news_sentiment", 0.5)
        score += news_sentiment * 0.4
        
        # 社交媒体提及量
        social_mentions = signal_data.get("social_mentions", 0)
        if social_mentions > 0:
            if social_mentions >= 10000:
                mention_score = 1.0
            elif social_mentions >= 1000:
                mention_score = 0.8
            elif social_mentions >= 100:
                mention_score = 0.6
            else:
                mention_score = 0.4
            
            score += mention_score * 0.3
        
        # 社交情绪评分
        sentiment_score = signal_data.get("sentiment_score", 0.5)
        score += sentiment_score * 0.3
        
        return min(1.0, score)
    
    def _evaluate_risk(self, signal_data: Dict) -> float:
        """评估风险因子"""
        score = 0.0
        
        # 风险回报比
        risk_reward_ratio = signal_data.get("risk_reward_ratio", 1.0)
        if risk_reward_ratio >= 3.0:
            rr_score = 1.0
        elif risk_reward_ratio >= 2.0:
            rr_score = 0.8
        elif risk_reward_ratio >= 1.5:
            rr_score = 0.6
        else:
            rr_score = 0.3
        
        score += rr_score * 0.4
        
        # 价格波动性风险
        volatility = signal_data.get("volatility", 0.02)
        if volatility <= 0.03:
            vol_score = 1.0
        elif volatility <= 0.05:
            vol_score = 0.8
        elif volatility <= 0.1:
            vol_score = 0.5
        else:
            vol_score = 0.2
        
        score += vol_score * 0.3
        
        # 止损设置
        stop_loss = signal_data.get("stop_loss")
        entry_price = signal_data.get("entry_price", 0)
        
        if stop_loss is not None and entry_price > 0:
            stop_loss_distance = abs(entry_price - stop_loss) / entry_price
            if 0.02 <= stop_loss_distance <= 0.05:  # 2-5%的止损
                stop_score = 1.0
            elif stop_loss_distance <= 0.1:
                stop_score = 0.8
            else:
                stop_score = 0.5
        else:
            stop_score = 0.3  # 没有止损扣分
        
        score += stop_score * 0.3
        
        return min(1.0, score)
    
    def _evaluate_timing(self, signal_data: Dict) -> float:
        """评估时机选择"""
        score = 0.0
        
        # 基础置信度
        confidence = signal_data.get("confidence", 0.5)
        score += confidence * 0.4
        
        # 技术指标同步性
        technical_alignment = signal_data.get("technical_alignment", 0.5)
        score += technical_alignment * 0.3
        
        # 市场时机
        market_timing = signal_data.get("market_timing", 0.5)
        score += market_timing * 0.3
        
        return min(1.0, score)
    
    def _determine_tier(self, overall_score: float) -> QualityTier:
        """确定质量等级"""
        for tier, threshold in self.tier_thresholds.items():
            if overall_score >= threshold:
                return tier
        return QualityTier.POOR
    
    def _generate_evaluation_details(self, overall_score: float, tier: QualityTier,
                                   category_scores: Dict[str, float], signal_data: Dict) -> Dict:
        """生成详细评估结果"""
        # 找出优势和劣势
        strengths = []
        weaknesses = []
        recommendations = []
        
        for category, score in category_scores.items():
            if score >= 0.8:
                strengths.append(f"{category}指标表现优秀 ({score:.2f})")
            elif score <= 0.4:
                weaknesses.append(f"{category}指标需要改善 ({score:.2f})")
        
        # 生成建议
        if tier in [QualityTier.PREMIUM, QualityTier.HIGH]:
            recommendations.append("信号质量优秀，建议优先执行")
        elif tier == QualityTier.GOOD:
            recommendations.append("信号质量良好，可以考虑执行")
        elif tier == QualityTier.MEDIUM:
            recommendations.append("信号质量中等，谨慎执行")
        else:
            recommendations.append("信号质量较差，不建议执行")
        
        # 具体建议
        if category_scores["risk"] < 0.6:
            recommendations.append("建议优化风险控制设置")
        
        if category_scores["technical"] < 0.6:
            recommendations.append("等待更强的技术信号确认")
        
        if category_scores["sentiment"] < 0.5:
            recommendations.append("关注市场情绪变化")
        
        return {
            "overall_score": overall_score,
            "tier": tier.value,
            "category_scores": category_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "evaluation_time": datetime.now().isoformat()
        }
    
    def _record_evaluation(self, signal_data: Dict, overall_score: float,
                          tier: QualityTier, category_scores: Dict):
        """记录评估历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": signal_data.get("symbol", "UNKNOWN"),
            "action": signal_data.get("action", "unknown"),
            "overall_score": overall_score,
            "tier": tier.value,
            "category_scores": category_scores.copy()
        }
        
        self.evaluation_history.append(record)
        
        # 限制历史记录数量
        if len(self.evaluation_history) > 10000:
            self.evaluation_history = self.evaluation_history[-10000:]
    
    def rank_signals(self, signals: List[Dict]) -> List[Tuple[Dict, float, QualityTier]]:
        """
        对多个信号进行排序
        
        Returns:
            List of (signal_data, score, tier) sorted by score desc
        """
        evaluated_signals = []
        
        for signal in signals:
            score, tier, _ = self.evaluate_signal_quality(signal)
            evaluated_signals.append((signal, score, tier))
        
        # 按评分降序排序
        evaluated_signals.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"信号排序完成: {len(signals)}个信号，"
                   f"最高分: {evaluated_signals[0][1]:.3f}，"
                   f"最低分: {evaluated_signals[-1][1]:.3f}")
        
        return evaluated_signals
    
    def get_quality_distribution(self, signals: List[Dict]) -> Dict:
        """获取信号质量分布统计"""
        if not signals:
            return {"message": "无信号数据"}
        
        scores = []
        tier_counts = {tier.value: 0 for tier in QualityTier}
        
        for signal in signals:
            score, tier, _ = self.evaluate_signal_quality(signal)
            scores.append(score)
            tier_counts[tier.value] += 1
        
        return {
            "total_signals": len(signals),
            "average_score": statistics.mean(scores),
            "median_score": statistics.median(scores),
            "score_std": statistics.stdev(scores) if len(scores) > 1 else 0,
            "tier_distribution": tier_counts,
            "score_range": {
                "min": min(scores),
                "max": max(scores)
            }
        }
    
    def adjust_weights(self, new_weights: Dict[str, float]):
        """调整评分权重"""
        # 验证权重键
        valid_keys = set(self.weights.keys())
        provided_keys = set(new_weights.keys())
        
        if not provided_keys.issubset(valid_keys):
            invalid_keys = provided_keys - valid_keys
            raise ValueError(f"无效的权重键: {invalid_keys}")
        
        # 更新权重
        self.weights.update(new_weights)
        
        # 标准化权重使总和为1
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for key in self.weights:
                self.weights[key] /= total_weight
        
        logger.info(f"评分权重已更新: {self.weights}")
    
    def get_category_performance(self) -> Dict:
        """获取各类别评分表现统计"""
        if not self.evaluation_history:
            return {"message": "无评估历史"}
        
        category_stats = {}
        
        for category in self.weights.keys():
            scores = [record["category_scores"][category] for record in self.evaluation_history]
            
            category_stats[category] = {
                "average": statistics.mean(scores),
                "median": statistics.median(scores),
                "std": statistics.stdev(scores) if len(scores) > 1 else 0,
                "min": min(scores),
                "max": max(scores),
                "weight": self.weights[category]
            }
        
        return category_stats
    
    def filter_by_quality(self, signals: List[Dict], min_tier: QualityTier) -> List[Dict]:
        """按质量等级过滤信号"""
        min_score = self.tier_thresholds[min_tier]
        filtered_signals = []
        
        for signal in signals:
            score, tier, _ = self.evaluate_signal_quality(signal)
            if score >= min_score:
                filtered_signals.append(signal)
        
        logger.info(f"质量过滤完成: {len(signals)}个信号 -> {len(filtered_signals)}个信号 "
                   f"(最低要求: {min_tier.value})")
        
        return filtered_signals
    
    def get_improvement_suggestions(self, signal_data: Dict) -> List[str]:
        """获取信号改善建议"""
        score, tier, details = self.evaluate_signal_quality(signal_data)
        suggestions = []
        
        category_scores = details["category_scores"]
        
        # 技术分析改善
        if category_scores["technical"] < 0.7:
            suggestions.append("增强技术分析：等待更多技术指标确认")
            suggestions.append("检查多时间框架一致性")
        
        # 市场环境改善
        if category_scores["market"] < 0.7:
            suggestions.append("评估市场流动性和成交量")
            suggestions.append("考虑市场整体趋势影响")
        
        # 情绪因子改善
        if category_scores["sentiment"] < 0.7:
            suggestions.append("监控社交媒体情绪变化")
            suggestions.append("关注相关新闻和事件")
        
        # 风险控制改善
        if category_scores["risk"] < 0.7:
            suggestions.append("优化风险回报比设置")
            suggestions.append("设置合理的止损和止盈位")
        
        # 时机选择改善
        if category_scores["timing"] < 0.7:
            suggestions.append("等待更佳入场时机")
            suggestions.append("确认趋势和动量指标同步")
        
        return suggestions
    
    def export_evaluation_history(self, days: int = 30) -> List[Dict]:
        """导出评估历史"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        recent_history = [
            record for record in self.evaluation_history
            if record["timestamp"] >= cutoff_str
        ]
        
        return recent_history