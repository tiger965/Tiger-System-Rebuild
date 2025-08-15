"""
情绪分析器
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from textblob import TextBlob
import statistics

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """社交媒体情绪分析器"""
    
    # 加密货币相关的情绪词典
    CRYPTO_LEXICON = {
        'positive': {
            'moon': 3,
            'bullish': 2,
            'pump': 2,
            'breakout': 2,
            'ath': 3,
            'all time high': 3,
            'buy': 1,
            'long': 1,
            'accumulate': 2,
            'undervalued': 2,
            'gem': 2,
            'rocket': 3,
            '🚀': 3,
            '💎': 2,
            '🐂': 2,
            'hodl': 1,
            'dip buying': 2,
            'support': 1,
            'resistance broken': 2,
            'golden cross': 3
        },
        'negative': {
            'dump': -2,
            'bearish': -2,
            'crash': -3,
            'sell': -1,
            'short': -1,
            'overvalued': -2,
            'bubble': -2,
            'scam': -3,
            'rug': -3,
            'rekt': -3,
            'blood': -2,
            '🐻': -2,
            '📉': -2,
            'fud': -1,
            'fear': -2,
            'panic': -3,
            'capitulation': -3,
            'death cross': -3,
            'support broken': -2
        },
        'urgent': {
            'breaking': 2,
            'urgent': 2,
            'alert': 2,
            'hack': 3,
            'exploit': 3,
            'emergency': 3,
            'warning': 2,
            'critical': 2,
            'immediate': 2
        }
    }
    
    # 影响力权重（不同来源的权重）
    SOURCE_WEIGHTS = {
        'twitter_kol_critical': 3.0,
        'twitter_kol_high': 2.0,
        'twitter_kol_medium': 1.5,
        'twitter_regular': 1.0,
        'reddit_hot': 1.5,
        'reddit_new': 1.0,
        'news_major': 2.5,
        'news_minor': 1.0
    }
    
    def __init__(self):
        """初始化情绪分析器"""
        self.sentiment_history = []
        self.aggregated_sentiment = None
    
    def analyze_text(self, text: str, source_type: str = 'general') -> Dict[str, Any]:
        """
        分析单条文本的情绪
        
        Args:
            text: 要分析的文本
            source_type: 来源类型
            
        Returns:
            情绪分析结果
        """
        # 基础情绪分析（使用TextBlob）
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1到1
        subjectivity = blob.sentiment.subjectivity  # 0到1
        
        # 加密货币专门词汇分析
        crypto_score = self._calculate_crypto_score(text)
        
        # 紧急程度分析
        urgency = self._calculate_urgency(text)
        
        # 综合得分（结合通用NLP和加密词典）
        combined_score = (polarity * 50 + crypto_score) / 2
        
        # 确定情绪类别
        if combined_score > 30:
            sentiment_category = 'strongly_bullish'
        elif combined_score > 10:
            sentiment_category = 'bullish'
        elif combined_score < -30:
            sentiment_category = 'strongly_bearish'
        elif combined_score < -10:
            sentiment_category = 'bearish'
        else:
            sentiment_category = 'neutral'
        
        # 应用来源权重
        weight = self.SOURCE_WEIGHTS.get(source_type, 1.0)
        weighted_score = combined_score * weight
        
        result = {
            'text': text[:200],  # 保存前200字符
            'timestamp': datetime.now().isoformat(),
            'sentiment_category': sentiment_category,
            'raw_score': combined_score,
            'weighted_score': weighted_score,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'crypto_score': crypto_score,
            'urgency': urgency,
            'source_type': source_type,
            'confidence': self._calculate_confidence(text, subjectivity)
        }
        
        # 添加到历史记录
        self.sentiment_history.append(result)
        
        return result
    
    def _calculate_crypto_score(self, text: str) -> float:
        """
        计算加密货币专门词汇得分
        
        Args:
            text: 文本
            
        Returns:
            加密货币情绪得分
        """
        text_lower = text.lower()
        score = 0
        word_count = 0
        
        # 计算正面词汇得分
        for word, weight in self.CRYPTO_LEXICON['positive'].items():
            count = text_lower.count(word)
            if count > 0:
                score += weight * count
                word_count += count
        
        # 计算负面词汇得分
        for word, weight in self.CRYPTO_LEXICON['negative'].items():
            count = text_lower.count(word)
            if count > 0:
                score += weight * count
                word_count += count
        
        # 归一化得分到-100到100
        if word_count > 0:
            normalized_score = (score / word_count) * 33.33
            return max(-100, min(100, normalized_score))
        
        return 0
    
    def _calculate_urgency(self, text: str) -> str:
        """
        计算紧急程度
        
        Args:
            text: 文本
            
        Returns:
            紧急程度: 'low', 'medium', 'high', 'critical'
        """
        text_lower = text.lower()
        urgency_score = 0
        
        for word, weight in self.CRYPTO_LEXICON['urgent'].items():
            if word in text_lower:
                urgency_score += weight
        
        # 检查大写字母比例（全大写可能表示紧急）
        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if uppercase_ratio > 0.5:
            urgency_score += 2
        
        # 检查感叹号数量
        exclamation_count = text.count('!')
        if exclamation_count > 2:
            urgency_score += 2
        
        # 确定紧急级别
        if urgency_score >= 6:
            return 'critical'
        elif urgency_score >= 4:
            return 'high'
        elif urgency_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, text: str, subjectivity: float) -> str:
        """
        计算分析置信度
        
        Args:
            text: 文本
            subjectivity: 主观性得分
            
        Returns:
            置信度级别
        """
        # 文本长度
        text_length = len(text.split())
        
        # 基于文本长度和主观性计算置信度
        if text_length < 5:
            return 'low'
        elif text_length < 20:
            if subjectivity < 0.5:
                return 'medium'
            else:
                return 'low'
        else:
            if subjectivity < 0.3:
                return 'high'
            elif subjectivity < 0.6:
                return 'medium'
            else:
                return 'low'
    
    def aggregate_sentiments(self, sentiments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合多个情绪分析结果
        
        Args:
            sentiments: 情绪分析结果列表
            
        Returns:
            聚合后的情绪分析
        """
        if not sentiments:
            return {
                'overall_sentiment': 'neutral',
                'aggregated_score': 0,
                'confidence': 'low'
            }
        
        # 计算加权平均分
        total_weighted_score = 0
        total_weight = 0
        
        sentiment_counts = {
            'strongly_bullish': 0,
            'bullish': 0,
            'neutral': 0,
            'bearish': 0,
            'strongly_bearish': 0
        }
        
        urgency_levels = []
        
        for sentiment in sentiments:
            weight = self.SOURCE_WEIGHTS.get(sentiment.get('source_type', 'general'), 1.0)
            total_weighted_score += sentiment.get('weighted_score', 0)
            total_weight += weight
            
            category = sentiment.get('sentiment_category', 'neutral')
            sentiment_counts[category] += 1
            
            urgency_levels.append(sentiment.get('urgency', 'low'))
        
        # 计算平均得分
        avg_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # 确定整体情绪
        if avg_score > 30:
            overall_sentiment = 'strongly_bullish'
        elif avg_score > 10:
            overall_sentiment = 'bullish'
        elif avg_score < -30:
            overall_sentiment = 'strongly_bearish'
        elif avg_score < -10:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        # 计算最高紧急程度
        urgency_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        max_urgency = max(urgency_levels, key=lambda x: urgency_priority.get(x, 0))
        
        # 计算置信度
        confidence_scores = {'high': 3, 'medium': 2, 'low': 1}
        avg_confidence = statistics.mean([
            confidence_scores.get(s.get('confidence', 'low'), 1)
            for s in sentiments
        ])
        
        if avg_confidence > 2.5:
            overall_confidence = 'high'
        elif avg_confidence > 1.5:
            overall_confidence = 'medium'
        else:
            overall_confidence = 'low'
        
        aggregated = {
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': overall_sentiment,
            'aggregated_score': avg_score,
            'sentiment_distribution': sentiment_counts,
            'max_urgency': max_urgency,
            'confidence': overall_confidence,
            'sample_size': len(sentiments),
            'score_range': {
                'min': min(s.get('raw_score', 0) for s in sentiments),
                'max': max(s.get('raw_score', 0) for s in sentiments),
                'std_dev': statistics.stdev([s.get('raw_score', 0) for s in sentiments]) if len(sentiments) > 1 else 0
            }
        }
        
        self.aggregated_sentiment = aggregated
        return aggregated
    
    def get_sentiment_trend(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取情绪趋势
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            情绪趋势分析
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_sentiments = [
            s for s in self.sentiment_history
            if datetime.fromisoformat(s['timestamp']).timestamp() > cutoff_time
        ]
        
        if not recent_sentiments:
            return {
                'trend': 'stable',
                'change': 0,
                'data_points': 0
            }
        
        # 按时间排序
        recent_sentiments.sort(key=lambda x: x['timestamp'])
        
        # 分成两半比较
        mid_point = len(recent_sentiments) // 2
        first_half = recent_sentiments[:mid_point]
        second_half = recent_sentiments[mid_point:]
        
        if first_half and second_half:
            first_avg = statistics.mean([s['raw_score'] for s in first_half])
            second_avg = statistics.mean([s['raw_score'] for s in second_half])
            
            change = second_avg - first_avg
            
            if change > 10:
                trend = 'improving'
            elif change < -10:
                trend = 'deteriorating'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
            change = 0
        
        return {
            'trend': trend,
            'change': change,
            'data_points': len(recent_sentiments),
            'period_hours': hours,
            'latest_score': recent_sentiments[-1]['raw_score'] if recent_sentiments else 0
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        获取需要警报的情绪事件
        
        Returns:
            警报列表
        """
        alerts = []
        
        # 检查最近的情绪
        recent = self.sentiment_history[-10:] if len(self.sentiment_history) >= 10 else self.sentiment_history
        
        for sentiment in recent:
            # 极端情绪警报
            if abs(sentiment['raw_score']) > 70:
                alerts.append({
                    'type': 'extreme_sentiment',
                    'severity': 'high',
                    'sentiment': sentiment['sentiment_category'],
                    'score': sentiment['raw_score'],
                    'text': sentiment['text'],
                    'timestamp': sentiment['timestamp']
                })
            
            # 高紧急度警报
            if sentiment['urgency'] in ['high', 'critical']:
                alerts.append({
                    'type': 'urgent_event',
                    'severity': sentiment['urgency'],
                    'text': sentiment['text'],
                    'timestamp': sentiment['timestamp']
                })
        
        # 情绪突变警报
        trend = self.get_sentiment_trend(1)  # 最近1小时
        if abs(trend['change']) > 30:
            alerts.append({
                'type': 'sentiment_shift',
                'severity': 'medium',
                'change': trend['change'],
                'trend': trend['trend'],
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts