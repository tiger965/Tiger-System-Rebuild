"""
Reddit监控器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class RedditMonitor:
    """Reddit社区监控器"""
    
    # 重点监控的子版块
    SUBREDDITS = [
        {'name': 'cryptocurrency', 'importance': 'high', 'members': 6000000},
        {'name': 'bitcoin', 'importance': 'high', 'members': 5000000},
        {'name': 'ethereum', 'importance': 'high', 'members': 2000000},
        {'name': 'defi', 'importance': 'medium', 'members': 500000},
        {'name': 'CryptoMarkets', 'importance': 'medium', 'members': 3000000},
        {'name': 'altcoin', 'importance': 'low', 'members': 1000000},
        {'name': 'NFT', 'importance': 'medium', 'members': 800000},
        {'name': 'CryptoTechnology', 'importance': 'low', 'members': 300000}
    ]
    
    # 情绪关键词
    SENTIMENT_KEYWORDS = {
        'extremely_bullish': ['to the moon', 'going parabolic', 'massive pump', 'guaranteed 10x'],
        'bullish': ['bullish', 'buy signal', 'accumulate', 'undervalued', 'breakout'],
        'neutral': ['discussion', 'analysis', 'update', 'news', 'question'],
        'bearish': ['bearish', 'sell signal', 'overvalued', 'crash incoming', 'bubble'],
        'extremely_bearish': ['rug pull', 'scam', 'ponzi', 'dead project', 'exit scam']
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Reddit监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.client_id = config.get('reddit_client_id', '')
        self.client_secret = config.get('reddit_client_secret', '')
        self.user_agent = config.get('reddit_user_agent', 'TigerSystem/1.0')
        
        # 使用Reddit API还是爬虫
        self.use_api = bool(self.client_id and self.client_secret)
        
        # 缓存数据
        self.posts_cache = []
        self.subreddit_stats = {}
        self.trending_posts = []
    
    async def get_hot_posts(self) -> List[Dict[str, Any]]:
        """
        获取热门帖子
        
        Returns:
            热门帖子列表
        """
        if self.use_api:
            return await self._api_get_hot_posts()
        else:
            return await self._scrape_hot_posts()
    
    async def _api_get_hot_posts(self) -> List[Dict[str, Any]]:
        """通过Reddit API获取热门帖子"""
        posts = []
        
        # 获取访问令牌
        token = await self._get_access_token()
        if not token:
            logger.warning("无法获取Reddit访问令牌")
            return posts
        
        headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': self.user_agent
        }
        
        async with aiohttp.ClientSession() as session:
            for subreddit in self.SUBREDDITS[:5]:  # 限制查询数量
                try:
                    url = f"https://oauth.reddit.com/r/{subreddit['name']}/hot"
                    params = {'limit': 10}
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for post in data['data']['children']:
                                post_data = post['data']
                                
                                post_info = {
                                    'id': post_data['id'],
                                    'subreddit': subreddit['name'],
                                    'title': post_data['title'],
                                    'author': post_data['author'],
                                    'score': post_data['score'],
                                    'num_comments': post_data['num_comments'],
                                    'created_utc': post_data['created_utc'],
                                    'url': f"https://reddit.com{post_data['permalink']}",
                                    'selftext': post_data.get('selftext', '')[:500],  # 限制长度
                                    'sentiment': self._analyze_post_sentiment(
                                        post_data['title'] + ' ' + post_data.get('selftext', '')
                                    ),
                                    'importance': self._calculate_importance(post_data)
                                }
                                posts.append(post_info)
                    
                    await asyncio.sleep(1)  # 限流
                    
                except Exception as e:
                    logger.error(f"获取 r/{subreddit['name']} 帖子失败: {e}")
        
        return posts
    
    async def _scrape_hot_posts(self) -> List[Dict[str, Any]]:
        """通过爬虫获取热门帖子（备用方案）"""
        posts = []
        
        async with aiohttp.ClientSession() as session:
            for subreddit in self.SUBREDDITS[:3]:  # 限制数量
                try:
                    # 使用old.reddit.com更容易解析
                    url = f"https://old.reddit.com/r/{subreddit['name']}/hot.json"
                    headers = {'User-Agent': self.user_agent}
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for post in data['data']['children'][:5]:
                                post_data = post['data']
                                
                                post_info = {
                                    'id': post_data['id'],
                                    'subreddit': subreddit['name'],
                                    'title': post_data['title'],
                                    'author': post_data['author'],
                                    'score': post_data['score'],
                                    'num_comments': post_data['num_comments'],
                                    'created_utc': post_data['created_utc'],
                                    'url': f"https://reddit.com{post_data['permalink']}",
                                    'sentiment': self._analyze_post_sentiment(post_data['title']),
                                    'importance': self._calculate_importance(post_data)
                                }
                                posts.append(post_info)
                    
                    await asyncio.sleep(2)  # 限流
                    
                except Exception as e:
                    logger.error(f"爬取 r/{subreddit['name']} 失败: {e}")
        
        return posts
    
    async def _get_access_token(self) -> Optional[str]:
        """获取Reddit API访问令牌"""
        if not self.client_id or not self.client_secret:
            return None
        
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            data = {'grant_type': 'client_credentials'}
            headers = {'User-Agent': self.user_agent}
            
            try:
                async with session.post(
                    'https://www.reddit.com/api/v1/access_token',
                    auth=auth,
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return token_data.get('access_token')
            except Exception as e:
                logger.error(f"获取Reddit访问令牌失败: {e}")
        
        return None
    
    def _analyze_post_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析帖子情绪
        
        Args:
            text: 帖子文本
            
        Returns:
            情绪分析结果
        """
        text_lower = text.lower()
        
        # 计算各类情绪得分
        sentiment_scores = {}
        for sentiment, keywords in self.SENTIMENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            sentiment_scores[sentiment] = score
        
        # 确定主要情绪
        max_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        max_score = sentiment_scores[max_sentiment]
        
        # 如果没有明显情绪，标记为中性
        if max_score == 0:
            primary_sentiment = 'neutral'
        else:
            primary_sentiment = max_sentiment
        
        # 计算情绪强度（-100到100）
        bullish_score = sentiment_scores['extremely_bullish'] * 2 + sentiment_scores['bullish']
        bearish_score = sentiment_scores['extremely_bearish'] * 2 + sentiment_scores['bearish']
        sentiment_strength = min(100, bullish_score * 20) - min(100, bearish_score * 20)
        
        return {
            'primary': primary_sentiment,
            'strength': sentiment_strength,
            'scores': sentiment_scores,
            'confidence': 'high' if max_score > 2 else 'medium' if max_score > 0 else 'low'
        }
    
    def _calculate_importance(self, post_data: Dict[str, Any]) -> str:
        """
        计算帖子重要性
        
        Args:
            post_data: 帖子数据
            
        Returns:
            重要性级别
        """
        score = post_data.get('score', 0)
        comments = post_data.get('num_comments', 0)
        
        # 基于互动度判断重要性
        if score > 10000 or comments > 1000:
            return 'critical'
        elif score > 5000 or comments > 500:
            return 'high'
        elif score > 1000 or comments > 100:
            return 'medium'
        else:
            return 'low'
    
    async def get_subreddit_metrics(self) -> Dict[str, Any]:
        """
        获取子版块指标
        
        Returns:
            子版块活跃度指标
        """
        metrics = {}
        
        for subreddit in self.SUBREDDITS:
            metrics[subreddit['name']] = {
                'members': subreddit['members'],
                'importance': subreddit['importance'],
                'activity_level': 'high',  # 应该动态计算
                'sentiment': 'neutral',     # 应该基于帖子分析
                'trending_topics': []        # 应该提取热门话题
            }
        
        return metrics
    
    async def monitor_mentions(self, symbols: List[str]) -> Dict[str, int]:
        """
        监控代币提及次数
        
        Args:
            symbols: 代币符号列表
            
        Returns:
            提及次数统计
        """
        mentions = {symbol: 0 for symbol in symbols}
        
        # 获取最近的帖子
        posts = await self.get_hot_posts()
        
        for post in posts:
            text = (post.get('title', '') + ' ' + post.get('selftext', '')).upper()
            for symbol in symbols:
                if symbol.upper() in text:
                    mentions[symbol] += 1
        
        return mentions
    
    async def get_community_sentiment(self) -> Dict[str, Any]:
        """
        获取社区整体情绪
        
        Returns:
            社区情绪分析
        """
        posts = await self.get_hot_posts()
        
        # 统计情绪分布
        sentiment_distribution = {
            'extremely_bullish': 0,
            'bullish': 0,
            'neutral': 0,
            'bearish': 0,
            'extremely_bearish': 0
        }
        
        total_score = 0
        total_engagement = 0
        
        for post in posts:
            sentiment = post.get('sentiment', {})
            primary = sentiment.get('primary', 'neutral')
            sentiment_distribution[primary] += 1
            
            # 加权计算（考虑帖子互动度）
            weight = (post.get('score', 0) + post.get('num_comments', 0) * 2)
            total_score += sentiment.get('strength', 0) * weight
            total_engagement += weight
        
        # 计算加权平均情绪
        avg_sentiment_score = total_score / total_engagement if total_engagement > 0 else 0
        
        # 确定整体情绪
        if avg_sentiment_score > 30:
            overall_sentiment = 'bullish'
        elif avg_sentiment_score < -30:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': overall_sentiment,
            'sentiment_score': avg_sentiment_score,
            'sentiment_distribution': sentiment_distribution,
            'total_posts_analyzed': len(posts),
            'total_engagement': total_engagement,
            'top_posts': self._get_top_posts(posts)
        }
    
    def _get_top_posts(self, posts: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最热门的帖子
        
        Args:
            posts: 帖子列表
            limit: 返回数量限制
            
        Returns:
            热门帖子列表
        """
        # 按互动度排序
        sorted_posts = sorted(
            posts,
            key=lambda x: x.get('score', 0) + x.get('num_comments', 0) * 2,
            reverse=True
        )
        
        return [
            {
                'title': post['title'],
                'subreddit': post['subreddit'],
                'score': post['score'],
                'comments': post['num_comments'],
                'url': post['url'],
                'sentiment': post['sentiment']['primary']
            }
            for post in sorted_posts[:limit]
        ]
    
    def get_cached_posts(self) -> List[Dict[str, Any]]:
        """获取缓存的帖子"""
        return self.posts_cache.copy()
    
    def get_subreddit_list(self) -> List[Dict[str, Any]]:
        """获取监控的子版块列表"""
        return self.SUBREDDITS.copy()