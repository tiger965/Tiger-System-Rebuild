"""
Twitter监控器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class TwitterMonitor:
    """Twitter监控器"""
    
    # 重点KOL列表
    KOL_LIST = [
        {"username": "cz_binance", "name": "CZ Binance", "importance": "critical"},
        {"username": "VitalikButerin", "name": "Vitalik Buterin", "importance": "critical"},
        {"username": "elonmusk", "name": "Elon Musk", "importance": "high"},
        {"username": "APompliano", "name": "Anthony Pompliano", "importance": "high"},
        {"username": "100trillionUSD", "name": "Plan B", "importance": "high"},
        {"username": "cobie", "name": "Cobie", "importance": "medium"},
        {"username": "hsaka", "name": "Hsaka", "importance": "medium"},
        {"username": "lowstrife", "name": "Lowstrife", "importance": "medium"},
        {"username": "WClementeIII", "name": "Will Clemente", "importance": "medium"},
        {"username": "woonomic", "name": "Willy Woo", "importance": "medium"}
    ]
    
    # 关键词列表
    KEYWORDS = {
        'bullish': ['bullish', 'moon', 'pump', 'breakthrough', 'ATH', 'all time high'],
        'bearish': ['bearish', 'dump', 'crash', 'sell', 'short', 'bear market'],
        'neutral': ['update', 'announcement', 'news', 'report'],
        'urgent': ['hack', 'exploit', 'scam', 'rug', 'emergency', 'urgent', 'breaking']
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Twitter监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.api_key = config.get('twitter_api_key', '')
        self.api_secret = config.get('twitter_api_secret', '')
        self.bearer_token = config.get('twitter_bearer_token', '')
        
        # 如果没有API密钥，使用爬虫模式
        self.use_scraper = not self.bearer_token
        
        # 缓存数据
        self.tweets_cache = []
        self.kol_activities = {}
        self.trending_topics = []
    
    async def get_kol_tweets(self) -> List[Dict[str, Any]]:
        """
        获取KOL推文
        
        Returns:
            KOL推文列表
        """
        if self.use_scraper:
            return await self._scrape_kol_tweets()
        else:
            return await self._api_get_kol_tweets()
    
    async def _api_get_kol_tweets(self) -> List[Dict[str, Any]]:
        """通过API获取KOL推文"""
        tweets = []
        
        if not self.bearer_token:
            logger.warning("未配置Twitter Bearer Token")
            return tweets
        
        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        async with aiohttp.ClientSession() as session:
            for kol in self.KOL_LIST[:5]:  # 限制查询数量
                try:
                    # 获取用户ID
                    user_url = f"https://api.twitter.com/2/users/by/username/{kol['username']}"
                    
                    async with session.get(user_url, headers=headers) as response:
                        if response.status == 200:
                            user_data = await response.json()
                            user_id = user_data['data']['id']
                            
                            # 获取用户推文
                            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
                            params = {
                                'max_results': 10,
                                'tweet.fields': 'created_at,public_metrics,referenced_tweets'
                            }
                            
                            async with session.get(tweets_url, headers=headers, params=params) as tweets_response:
                                if tweets_response.status == 200:
                                    tweets_data = await tweets_response.json()
                                    
                                    for tweet in tweets_data.get('data', []):
                                        tweet_info = {
                                            'id': tweet['id'],
                                            'username': kol['username'],
                                            'name': kol['name'],
                                            'importance': kol['importance'],
                                            'text': tweet['text'],
                                            'created_at': tweet.get('created_at', ''),
                                            'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                                            'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                                            'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                                            'sentiment': self._analyze_tweet_sentiment(tweet['text'])
                                        }
                                        tweets.append(tweet_info)
                    
                    await asyncio.sleep(1)  # 限流
                    
                except Exception as e:
                    logger.error(f"获取 {kol['username']} 推文失败: {e}")
        
        return tweets
    
    async def _scrape_kol_tweets(self) -> List[Dict[str, Any]]:
        """通过爬虫获取KOL推文（备用方案）"""
        tweets = []
        
        # 使用nitter等第三方服务
        nitter_instances = [
            'nitter.net',
            'nitter.it',
            'nitter.privacydev.net'
        ]
        
        async with aiohttp.ClientSession() as session:
            for kol in self.KOL_LIST[:3]:  # 限制数量
                for instance in nitter_instances:
                    try:
                        url = f"https://{instance}/{kol['username']}"
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        async with session.get(url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # 解析推文
                                tweet_items = soup.find_all('div', class_='timeline-item')[:5]
                                
                                for item in tweet_items:
                                    tweet_text = item.find('div', class_='tweet-content')
                                    if tweet_text:
                                        tweet_info = {
                                            'username': kol['username'],
                                            'name': kol['name'],
                                            'importance': kol['importance'],
                                            'text': tweet_text.get_text(strip=True),
                                            'created_at': datetime.now().isoformat(),
                                            'sentiment': self._analyze_tweet_sentiment(tweet_text.get_text())
                                        }
                                        tweets.append(tweet_info)
                                
                                break  # 成功获取后跳出
                    
                    except Exception as e:
                        logger.debug(f"从 {instance} 获取 {kol['username']} 失败: {e}")
                        continue
                
                await asyncio.sleep(2)  # 限流
        
        return tweets
    
    def _analyze_tweet_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析推文情绪
        
        Args:
            text: 推文文本
            
        Returns:
            情绪分析结果
        """
        text_lower = text.lower()
        
        # 计算各类关键词出现次数
        bullish_count = sum(1 for word in self.KEYWORDS['bullish'] if word in text_lower)
        bearish_count = sum(1 for word in self.KEYWORDS['bearish'] if word in text_lower)
        urgent_count = sum(1 for word in self.KEYWORDS['urgent'] if word in text_lower)
        
        # 判断整体情绪
        sentiment = 'neutral'
        score = 0
        
        if bullish_count > bearish_count:
            sentiment = 'bullish'
            score = min(bullish_count * 20, 100)
        elif bearish_count > bullish_count:
            sentiment = 'bearish'
            score = -min(bearish_count * 20, 100)
        
        # 检查紧急程度
        urgency = 'normal'
        if urgent_count > 0:
            urgency = 'high'
        elif any(kol['importance'] == 'critical' for kol in self.KOL_LIST if kol['username'] in text):
            urgency = 'medium'
        
        return {
            'sentiment': sentiment,
            'score': score,
            'urgency': urgency,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'urgent_signals': urgent_count
        }
    
    async def get_trending_topics(self) -> List[Dict[str, Any]]:
        """
        获取趋势话题
        
        Returns:
            趋势话题列表
        """
        topics = []
        
        # 模拟趋势话题（实际应该从API或爬虫获取）
        crypto_topics = [
            {'topic': '#Bitcoin', 'tweets': 50000, 'sentiment': 'bullish'},
            {'topic': '#Ethereum', 'tweets': 30000, 'sentiment': 'neutral'},
            {'topic': '#DeFi', 'tweets': 15000, 'sentiment': 'bullish'},
            {'topic': '#NFT', 'tweets': 10000, 'sentiment': 'bearish'},
            {'topic': '#Web3', 'tweets': 8000, 'sentiment': 'neutral'}
        ]
        
        for topic in crypto_topics:
            topic['timestamp'] = datetime.now().isoformat()
            topic['category'] = 'crypto'
            topics.append(topic)
        
        self.trending_topics = topics
        return topics
    
    async def monitor_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        监控特定关键词
        
        Args:
            keywords: 关键词列表
            
        Returns:
            相关推文列表
        """
        results = []
        
        # 这里应该实现关键词监控逻辑
        # 简化处理，返回模拟数据
        for keyword in keywords:
            results.append({
                'keyword': keyword,
                'mentions': 100,
                'sentiment': 'neutral',
                'sample_tweets': [],
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """
        获取市场整体情绪
        
        Returns:
            市场情绪分析
        """
        # 获取最近的推文
        recent_tweets = await self.get_kol_tweets()
        
        # 统计情绪
        sentiment_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        total_score = 0
        urgent_count = 0
        
        for tweet in recent_tweets:
            sentiment_data = tweet.get('sentiment', {})
            sentiment = sentiment_data.get('sentiment', 'neutral')
            sentiment_counts[sentiment] += 1
            total_score += sentiment_data.get('score', 0)
            
            if sentiment_data.get('urgency') == 'high':
                urgent_count += 1
        
        total_tweets = len(recent_tweets)
        
        # 计算整体情绪
        overall_sentiment = 'neutral'
        if total_tweets > 0:
            avg_score = total_score / total_tweets
            if avg_score > 20:
                overall_sentiment = 'bullish'
            elif avg_score < -20:
                overall_sentiment = 'bearish'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': overall_sentiment,
            'sentiment_score': total_score / total_tweets if total_tweets > 0 else 0,
            'sentiment_distribution': sentiment_counts,
            'urgent_signals': urgent_count,
            'sample_size': total_tweets,
            'top_influencers': self._get_top_influencers(recent_tweets)
        }
    
    def _get_top_influencers(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        获取最活跃的影响者
        
        Args:
            tweets: 推文列表
            
        Returns:
            影响者列表
        """
        influencer_activity = {}
        
        for tweet in tweets:
            username = tweet.get('username', '')
            if username:
                if username not in influencer_activity:
                    influencer_activity[username] = {
                        'name': tweet.get('name', ''),
                        'count': 0,
                        'importance': tweet.get('importance', 'low')
                    }
                influencer_activity[username]['count'] += 1
        
        # 排序并返回前5
        sorted_influencers = sorted(
            influencer_activity.items(),
            key=lambda x: (x[1]['importance'] == 'critical', x[1]['count']),
            reverse=True
        )
        
        return [
            {
                'username': username,
                'name': data['name'],
                'tweet_count': data['count'],
                'importance': data['importance']
            }
            for username, data in sorted_influencers[:5]
        ]
    
    def get_cached_tweets(self) -> List[Dict[str, Any]]:
        """获取缓存的推文"""
        return self.tweets_cache.copy()
    
    def get_kol_list(self) -> List[Dict[str, str]]:
        """获取KOL列表"""
        return self.KOL_LIST.copy()