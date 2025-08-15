"""
新闻分析器
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """新闻分析器"""
    
    # 市场影响评级
    IMPACT_LEVELS = {
        'critical': {
            'keywords': ['sec', 'ban', 'hack', 'exploit', 'lawsuit', 'arrest', 'fraud'],
            'score': 100,
            'description': '可能造成市场剧烈波动'
        },
        'high': {
            'keywords': ['regulation', 'partnership', 'launch', 'acquisition', 'integration'],
            'score': 75,
            'description': '可能显著影响价格'
        },
        'medium': {
            'keywords': ['update', 'upgrade', 'development', 'announcement', 'report'],
            'score': 50,
            'description': '可能产生中等影响'
        },
        'low': {
            'keywords': ['analysis', 'opinion', 'prediction', 'forecast'],
            'score': 25,
            'description': '影响较小'
        }
    }
    
    # 情绪影响映射
    SENTIMENT_IMPACT = {
        'regulation': {
            'positive': ['approval', 'clarity', 'framework', 'support'],
            'negative': ['ban', 'restriction', 'investigation', 'enforcement']
        },
        'partnership': {
            'positive': ['collaboration', 'integration', 'adoption', 'expansion'],
            'negative': ['termination', 'dispute', 'breakdown']
        },
        'hack': {
            'positive': ['recovered', 'secured', 'patched'],
            'negative': ['breach', 'stolen', 'compromised', 'vulnerable']
        },
        'market': {
            'positive': ['surge', 'rally', 'breakout', 'ath', 'bullish'],
            'negative': ['crash', 'plunge', 'dump', 'bearish', 'correction']
        }
    }
    
    def __init__(self):
        """初始化新闻分析器"""
        self.analysis_cache = []
        self.impact_events = []
        self.trend_analysis = {}
    
    def analyze_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析新闻列表
        
        Args:
            news_list: 新闻列表
            
        Returns:
            分析结果
        """
        if not news_list:
            return {
                'total_news': 0,
                'impact_summary': {},
                'sentiment': 'neutral',
                'key_events': []
            }
        
        # 分析每条新闻
        analyzed_news = []
        for news in news_list:
            analysis = self._analyze_single_news(news)
            analyzed_news.append(analysis)
        
        # 汇总分析
        summary = self._summarize_analysis(analyzed_news)
        
        # 识别关键事件
        key_events = self._identify_key_events(analyzed_news)
        
        # 分析趋势
        trends = self._analyze_trends(analyzed_news)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_news': len(news_list),
            'impact_summary': summary['impact_distribution'],
            'overall_sentiment': summary['overall_sentiment'],
            'sentiment_score': summary['sentiment_score'],
            'key_events': key_events,
            'trends': trends,
            'category_distribution': summary['category_distribution'],
            'entity_mentions': summary['entity_mentions']
        }
        
        # 缓存分析结果
        self.analysis_cache.append(result)
        
        return result
    
    def _analyze_single_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单条新闻
        
        Args:
            news: 新闻项
            
        Returns:
            分析结果
        """
        # 评估市场影响
        impact_level = self._assess_impact(news)
        
        # 分析情绪
        sentiment = self._analyze_sentiment(news)
        
        # 预测价格影响
        price_impact = self._predict_price_impact(news, impact_level, sentiment)
        
        # 识别相关资产
        affected_assets = self._identify_affected_assets(news)
        
        analysis = {
            'news_id': news.get('id'),
            'title': news.get('title'),
            'source': news.get('source'),
            'categories': news.get('categories', []),
            'impact_level': impact_level,
            'sentiment': sentiment,
            'price_impact': price_impact,
            'affected_assets': affected_assets,
            'urgency': self._calculate_urgency(news),
            'timestamp': news.get('published', datetime.now().isoformat())
        }
        
        return analysis
    
    def _assess_impact(self, news: Dict[str, Any]) -> str:
        """
        评估新闻的市场影响级别
        
        Args:
            news: 新闻项
            
        Returns:
            影响级别
        """
        text = (news.get('title', '') + ' ' + news.get('summary', '')).lower()
        
        # 检查各级别关键词
        for level, config in self.IMPACT_LEVELS.items():
            if any(keyword in text for keyword in config['keywords']):
                return level
        
        # 基于来源判断
        if news.get('source') == 'SEC':
            return 'high'
        elif news.get('importance') == 'critical':
            return 'high'
        elif news.get('importance') == 'high':
            return 'medium'
        
        return 'low'
    
    def _analyze_sentiment(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析新闻情绪
        
        Args:
            news: 新闻项
            
        Returns:
            情绪分析结果
        """
        text = (news.get('title', '') + ' ' + news.get('summary', '')).lower()
        categories = news.get('categories', [])
        
        positive_count = 0
        negative_count = 0
        
        # 基于类别和关键词分析
        for category in categories:
            if category in self.SENTIMENT_IMPACT:
                impact_words = self.SENTIMENT_IMPACT[category]
                
                for word in impact_words.get('positive', []):
                    if word in text:
                        positive_count += 1
                
                for word in impact_words.get('negative', []):
                    if word in text:
                        negative_count += 1
        
        # 确定情绪
        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(positive_count * 20, 100)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = -min(negative_count * 20, 100)
        else:
            sentiment = 'neutral'
            score = 0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': 'high' if (positive_count + negative_count) > 3 else 'medium'
        }
    
    def _predict_price_impact(self, news: Dict[str, Any], impact_level: str, sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        预测价格影响
        
        Args:
            news: 新闻项
            impact_level: 影响级别
            sentiment: 情绪分析结果
            
        Returns:
            价格影响预测
        """
        # 基础影响分数
        impact_scores = {
            'critical': 50,
            'high': 30,
            'medium': 15,
            'low': 5
        }
        
        base_impact = impact_scores.get(impact_level, 5)
        
        # 结合情绪调整
        sentiment_multiplier = 1
        if sentiment['sentiment'] == 'positive':
            sentiment_multiplier = 1 + (sentiment['score'] / 100)
        elif sentiment['sentiment'] == 'negative':
            sentiment_multiplier = -(1 + abs(sentiment['score']) / 100)
        
        # 计算预期价格影响
        expected_impact = base_impact * sentiment_multiplier
        
        # 时间范围预测
        if abs(expected_impact) > 30:
            timeframe = 'immediate'  # 立即影响
        elif abs(expected_impact) > 15:
            timeframe = 'short_term'  # 短期（1-24小时）
        else:
            timeframe = 'medium_term'  # 中期（1-7天）
        
        return {
            'expected_change_percent': expected_impact,
            'direction': 'up' if expected_impact > 0 else 'down' if expected_impact < 0 else 'neutral',
            'timeframe': timeframe,
            'confidence': sentiment['confidence']
        }
    
    def _identify_affected_assets(self, news: Dict[str, Any]) -> List[str]:
        """
        识别受影响的资产
        
        Args:
            news: 新闻项
            
        Returns:
            受影响资产列表
        """
        affected = news.get('entities', [])
        
        # 基于类别添加相关资产
        categories = news.get('categories', [])
        
        if 'defi' in categories:
            affected.extend(['UNI', 'AAVE', 'COMP', 'MKR'])
        if 'nft' in categories:
            affected.extend(['MANA', 'SAND', 'AXS'])
        if 'regulation' in categories and 'SEC' in news.get('source', ''):
            affected.extend(['BTC', 'ETH'])  # 监管通常影响主流币
        
        return list(set(affected))  # 去重
    
    def _calculate_urgency(self, news: Dict[str, Any]) -> str:
        """
        计算新闻紧急程度
        
        Args:
            news: 新闻项
            
        Returns:
            紧急程度
        """
        # 基于时间判断
        try:
            published_time = datetime.fromisoformat(news.get('published', ''))
            age_hours = (datetime.now() - published_time).total_seconds() / 3600
        except:
            age_hours = 24  # 默认值
        
        # 基于影响和时间判断紧急程度
        if news.get('importance') == 'critical' and age_hours < 1:
            return 'immediate'
        elif news.get('importance') in ['critical', 'high'] and age_hours < 6:
            return 'high'
        elif age_hours < 24:
            return 'medium'
        else:
            return 'low'
    
    def _summarize_analysis(self, analyzed_news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        汇总分析结果
        
        Args:
            analyzed_news: 分析后的新闻列表
            
        Returns:
            汇总结果
        """
        # 影响级别分布
        impact_distribution = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        # 情绪统计
        sentiment_scores = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # 类别分布
        category_counts = {}
        
        # 实体提及次数
        entity_mentions = {}
        
        for news in analyzed_news:
            # 统计影响级别
            impact = news.get('impact_level', 'low')
            impact_distribution[impact] += 1
            
            # 统计情绪
            sentiment = news.get('sentiment', {})
            sentiment_type = sentiment.get('sentiment', 'neutral')
            sentiment_counts[sentiment_type] += 1
            sentiment_scores.append(sentiment.get('score', 0))
            
            # 统计类别
            for category in news.get('categories', []):
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # 统计实体
            for entity in news.get('affected_assets', []):
                entity_mentions[entity] = entity_mentions.get(entity, 0) + 1
        
        # 计算整体情绪
        avg_sentiment_score = statistics.mean(sentiment_scores) if sentiment_scores else 0
        
        if avg_sentiment_score > 20:
            overall_sentiment = 'positive'
        elif avg_sentiment_score < -20:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'impact_distribution': impact_distribution,
            'overall_sentiment': overall_sentiment,
            'sentiment_score': avg_sentiment_score,
            'sentiment_counts': sentiment_counts,
            'category_distribution': category_counts,
            'entity_mentions': dict(sorted(entity_mentions.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _identify_key_events(self, analyzed_news: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        识别关键事件
        
        Args:
            analyzed_news: 分析后的新闻列表
            
        Returns:
            关键事件列表
        """
        key_events = []
        
        for news in analyzed_news:
            # 高影响或紧急事件
            if news.get('impact_level') in ['critical', 'high'] or news.get('urgency') == 'immediate':
                key_events.append({
                    'title': news.get('title'),
                    'impact': news.get('impact_level'),
                    'sentiment': news.get('sentiment', {}).get('sentiment'),
                    'price_impact': news.get('price_impact', {}).get('expected_change_percent', 0),
                    'affected_assets': news.get('affected_assets', []),
                    'urgency': news.get('urgency'),
                    'timestamp': news.get('timestamp')
                })
        
        # 按影响程度排序
        key_events.sort(key=lambda x: abs(x.get('price_impact', 0)), reverse=True)
        
        return key_events[:10]  # 返回前10个
    
    def _analyze_trends(self, analyzed_news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析新闻趋势
        
        Args:
            analyzed_news: 分析后的新闻列表
            
        Returns:
            趋势分析结果
        """
        # 按时间排序
        sorted_news = sorted(analyzed_news, key=lambda x: x.get('timestamp', ''))
        
        if len(sorted_news) < 2:
            return {
                'sentiment_trend': 'stable',
                'volume_trend': 'stable',
                'dominant_narrative': 'none'
            }
        
        # 分析情绪趋势
        recent_sentiments = [n.get('sentiment', {}).get('score', 0) for n in sorted_news[-10:]]
        older_sentiments = [n.get('sentiment', {}).get('score', 0) for n in sorted_news[:-10]]
        
        if recent_sentiments and older_sentiments:
            recent_avg = statistics.mean(recent_sentiments)
            older_avg = statistics.mean(older_sentiments)
            
            if recent_avg > older_avg + 10:
                sentiment_trend = 'improving'
            elif recent_avg < older_avg - 10:
                sentiment_trend = 'deteriorating'
            else:
                sentiment_trend = 'stable'
        else:
            sentiment_trend = 'stable'
        
        # 分析主导叙事
        all_categories = []
        for news in sorted_news[-20:]:  # 最近20条
            all_categories.extend(news.get('categories', []))
        
        if all_categories:
            from collections import Counter
            category_counts = Counter(all_categories)
            dominant_narrative = category_counts.most_common(1)[0][0]
        else:
            dominant_narrative = 'none'
        
        return {
            'sentiment_trend': sentiment_trend,
            'volume_trend': 'increasing' if len(sorted_news) > 20 else 'normal',
            'dominant_narrative': dominant_narrative
        }
    
    def get_market_impact_summary(self) -> Dict[str, Any]:
        """
        获取市场影响摘要
        
        Returns:
            市场影响摘要
        """
        if not self.analysis_cache:
            return {
                'status': 'no_data',
                'message': '暂无分析数据'
            }
        
        latest = self.analysis_cache[-1]
        
        # 计算综合市场影响
        impact_score = 0
        if latest['impact_summary'].get('critical', 0) > 0:
            impact_score += 50
        impact_score += latest['impact_summary'].get('high', 0) * 20
        impact_score += latest['impact_summary'].get('medium', 0) * 5
        
        market_status = 'stable'
        if impact_score > 100:
            market_status = 'highly_volatile'
        elif impact_score > 50:
            market_status = 'volatile'
        elif impact_score > 20:
            market_status = 'active'
        
        return {
            'timestamp': latest['timestamp'],
            'market_status': market_status,
            'impact_score': impact_score,
            'overall_sentiment': latest['overall_sentiment'],
            'key_events_count': len(latest['key_events']),
            'dominant_narrative': latest['trends'].get('dominant_narrative'),
            'recommendation': self._get_trading_recommendation(market_status, latest['overall_sentiment'])
        }
    
    def _get_trading_recommendation(self, market_status: str, sentiment: str) -> str:
        """
        获取交易建议
        
        Args:
            market_status: 市场状态
            sentiment: 市场情绪
            
        Returns:
            交易建议
        """
        if market_status == 'highly_volatile':
            return '高波动性，建议降低仓位或观望'
        elif market_status == 'volatile':
            if sentiment == 'positive':
                return '波动性增加但情绪积极，可考虑逢低买入'
            else:
                return '波动性增加且情绪消极，建议谨慎或做空'
        elif sentiment == 'positive':
            return '市场情绪积极，可考虑增加仓位'
        elif sentiment == 'negative':
            return '市场情绪消极，建议减仓或做空'
        else:
            return '市场平稳，维持现有策略'