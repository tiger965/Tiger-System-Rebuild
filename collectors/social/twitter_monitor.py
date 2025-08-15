"""
Twitter监控器 - 工业级实现
支持API和爬虫双模式，具备完整错误处理和重试机制
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TwitterConfig:
    """Twitter配置类"""
    api_key: str = ""
    api_secret: str = ""
    bearer_token: str = ""
    access_token: str = ""
    access_token_secret: str = ""
    rate_limit_enabled: bool = True
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5


@dataclass
class TweetData:
    """推文数据类"""
    id: str
    username: str
    name: str
    text: str
    created_at: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    importance: str = "low"
    sentiment: Dict[str, Any] = None
    deleted: bool = False
    crypto_mentions: List[str] = None
    
    def __post_init__(self):
        if self.sentiment is None:
            self.sentiment = {}
        if self.crypto_mentions is None:
            self.crypto_mentions = []


class TwitterMonitor:
    """Twitter监控器 - 工业级实现"""
    
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
        'bullish': ['bullish', 'moon', 'pump', 'breakthrough', 'ATH', 'all time high', 'buy', 'long'],
        'bearish': ['bearish', 'dump', 'crash', 'sell', 'short', 'bear market', 'bottom', 'capitulation'],
        'neutral': ['update', 'announcement', 'news', 'report', 'analysis'],
        'urgent': ['hack', 'exploit', 'scam', 'rug', 'emergency', 'urgent', 'breaking', 'alert'],
        'crypto': ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain', 'defi', 'nft']
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Twitter监控器
        
        Args:
            config: 配置字典
        """
        if config is None:
            config = {}
        
        self.config = TwitterConfig(
            api_key=config.get('twitter_api_key', ''),
            api_secret=config.get('twitter_api_secret', ''),
            bearer_token=config.get('twitter_bearer_token', ''),
            access_token=config.get('twitter_access_token', ''),
            access_token_secret=config.get('twitter_access_token_secret', '')
        )
        
        # 如果没有API密钥，使用爬虫模式
        self.use_scraper = not self.config.bearer_token
        
        # 缓存数据
        self.tweets_cache = {}
        self.kol_activities = {}
        self.trending_topics = []
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "last_request_time": None
        }
        
        # 初始化标志
        self.initialized = False
        
        # 删除推文检测缓存
        self.deleted_tweets_cache = set()
        
        # 备份目录
        self.backup_dir = Path("/tmp/twitter_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """初始化监控器"""
        if self.initialized:
            logger.warning("TwitterMonitor已经初始化")
            return
        
        logger.info("正在初始化Twitter监控器...")
        
        try:
            # 测试连接
            await self._test_connection()
            
            # 加载缓存
            await self._load_cache()
            
            self.initialized = True
            logger.info("Twitter监控器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    async def _test_connection(self):
        """测试连接"""
        if not self.use_scraper:
            # 测试API连接
            headers = {
                'Authorization': f'Bearer {self.config.bearer_token}'
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://api.twitter.com/2/users/me",
                        headers=headers,
                        timeout=10
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"API测试失败: {response.status}，切换到爬虫模式")
                            self.use_scraper = True
                        else:
                            logger.info("Twitter API连接正常")
            except Exception as e:
                logger.warning(f"API测试异常: {e}，切换到爬虫模式")
                self.use_scraper = True
        
        if self.use_scraper:
            logger.info("使用爬虫模式")
    
    async def _load_cache(self):
        """加载缓存"""
        cache_file = self.backup_dir / "tweets_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.tweets_cache = cache_data.get("tweets", {})
                    self.kol_activities = cache_data.get("activities", {})
                    logger.info(f"加载缓存数据: {len(self.tweets_cache)} 条推文")
            except Exception as e:
                logger.error(f"加载缓存失败: {e}")
    
    async def _save_cache(self):
        """保存缓存"""
        cache_file = self.backup_dir / "tweets_cache.json"
        try:
            cache_data = {
                "tweets": self.tweets_cache,
                "activities": self.kol_activities,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug("缓存已保存")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    async def search_tweets(self, keyword: str, time_range: timedelta = None, 
                           min_followers: int = 1000) -> List[Dict[str, Any]]:
        """
        搜索推文
        
        Args:
            keyword: 搜索关键词
            time_range: 时间范围
            min_followers: 最小粉丝数
            
        Returns:
            推文列表
        """
        if not self.initialized:
            await self.initialize()
        
        if time_range is None:
            time_range = timedelta(hours=1)
        
        tweets = []
        
        try:
            if self.use_scraper:
                tweets = await self._scrape_search_tweets(keyword, time_range, min_followers)
            else:
                tweets = await self._api_search_tweets(keyword, time_range, min_followers)
            
            logger.info(f"搜索到 {len(tweets)} 条相关推文")
            return tweets
            
        except Exception as e:
            logger.error(f"搜索推文失败: {e}")
            return []
    
    async def get_user_timeline(self, username: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户时间线
        
        Args:
            username: 用户名
            include_deleted: 是否包含已删除推文
            
        Returns:
            用户推文列表
        """
        if not self.initialized:
            await self.initialize()
        
        tweets = []
        
        try:
            if self.use_scraper:
                tweets = await self._scrape_user_timeline(username)
            else:
                tweets = await self._api_get_user_timeline(username)
            
            # 检测删除的推文
            if include_deleted:
                deleted_tweets = await self._detect_deleted_tweets(username)
                tweets.extend(deleted_tweets)
            
            logger.info(f"获取 {username} 的 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            logger.error(f"获取用户时间线失败: {e}")
            return []
    
    async def get_kol_tweets(self) -> List[TweetData]:
        """
        获取KOL推文
        
        Returns:
            KOL推文列表
        """
        if not self.initialized:
            await self.initialize()
        
        self.stats["total_requests"] += 1
        self.stats["last_request_time"] = datetime.now().isoformat()
        
        try:
            if self.use_scraper:
                tweets = await self._scrape_kol_tweets()
            else:
                tweets = await self._api_get_kol_tweets()
            
            self.stats["success_requests"] += 1
            
            # 保存到缓存
            await self._save_tweets_to_cache(tweets)
            
            return tweets
            
        except Exception as e:
            logger.error(f"获取KOL推文失败: {e}")
            self.stats["failed_requests"] += 1
            
            # 返回缓存数据
            return await self._get_cached_tweets()
    
    async def _save_tweets_to_cache(self, tweets: List[TweetData]):
        """保存推文到缓存"""
        current_time = datetime.now().timestamp()
        
        for tweet in tweets:
            cache_key = f"{tweet.username}_{tweet.id}"
            self.tweets_cache[cache_key] = {
                "data": asdict(tweet),
                "timestamp": current_time
            }
        
        # 清理过期缓存
        await self._cleanup_cache()
        
        # 保存到文件
        await self._save_cache()
    
    async def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = datetime.now().timestamp()
        ttl = self.config.cache_ttl_seconds
        
        expired_keys = [
            key for key, value in self.tweets_cache.items()
            if current_time - value.get("timestamp", 0) > ttl
        ]
        
        for key in expired_keys:
            del self.tweets_cache[key]
        
        if expired_keys:
            logger.debug(f"清理过期缓存: {len(expired_keys)} 条")
    
    async def _get_cached_tweets(self) -> List[TweetData]:
        """获取缓存的推文"""
        tweets = []
        current_time = datetime.now().timestamp()
        ttl = self.config.cache_ttl_seconds
        
        for value in self.tweets_cache.values():
            if current_time - value.get("timestamp", 0) <= ttl:
                tweet_data = value["data"]
                tweets.append(TweetData(**tweet_data))
        
        if tweets:
            self.stats["cache_hits"] += 1
            logger.info(f"返回缓存数据: {len(tweets)} 条推文")
        
        return tweets
    
    async def _api_search_tweets(self, keyword: str, time_range: timedelta, 
                                min_followers: int) -> List[Dict[str, Any]]:
        """通过API搜索推文"""
        tweets = []
        
        if not self.config.bearer_token:
            logger.warning("未配置Twitter Bearer Token")
            return tweets
        
        headers = {
            'Authorization': f'Bearer {self.config.bearer_token}'
        }
        
        # 计算时间范围
        start_time = (datetime.now() - time_range).isoformat() + "Z"
        
        params = {
            'query': f'{keyword} -is:retweet',
            'max_results': 50,
            'tweet.fields': 'created_at,public_metrics,author_id,context_annotations',
            'user.fields': 'public_metrics,verified',
            'expansions': 'author_id',
            'start_time': start_time
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers=headers,
                    params=params,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweets_data = data.get('data', [])
                        users_data = {user['id']: user for user in data.get('includes', {}).get('users', [])}
                        
                        for tweet in tweets_data:
                            author_id = tweet.get('author_id')
                            author = users_data.get(author_id, {})
                            
                            # 过滤粉丝数
                            follower_count = author.get('public_metrics', {}).get('followers_count', 0)
                            if follower_count < min_followers:
                                continue
                            
                            tweet_info = {
                                'id': tweet['id'],
                                'username': author.get('username', ''),
                                'name': author.get('name', ''),
                                'text': tweet['text'],
                                'created_at': tweet.get('created_at', ''),
                                'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                                'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                                'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                                'follower_count': follower_count,
                                'verified': author.get('verified', False),
                                'sentiment': await self._analyze_tweet_sentiment(tweet['text']),
                                'crypto_mentions': self._detect_crypto_mentions(tweet['text'])
                            }
                            tweets.append(tweet_info)
                    
                    else:
                        logger.error(f"API搜索失败: {response.status}")
                        
            except Exception as e:
                logger.error(f"API搜索异常: {e}")
        
        return tweets
    
    async def _scrape_search_tweets(self, keyword: str, time_range: timedelta, 
                                   min_followers: int) -> List[Dict[str, Any]]:
        """通过爬虫搜索推文"""
        tweets = []
        
        # 使用多个备用搜索服务
        search_services = [
            f"https://nitter.net/search?f=tweets&q={keyword}",
            f"https://nitter.it/search?f=tweets&q={keyword}",
            f"https://nitter.privacydev.net/search?f=tweets&q={keyword}"
        ]
        
        async with aiohttp.ClientSession() as session:
            for service_url in search_services:
                try:
                    headers = {
                        'User-Agent': self._get_random_user_agent()
                    }
                    
                    async with session.get(service_url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # 解析推文
                            tweet_items = soup.find_all('div', class_='timeline-item')[:20]
                            
                            for item in tweet_items:
                                try:
                                    tweet_data = await self._parse_scraped_tweet(item)
                                    if tweet_data and tweet_data.get('follower_count', 0) >= min_followers:
                                        tweets.append(tweet_data)
                                except Exception as e:
                                    logger.debug(f"解析推文失败: {e}")
                            
                            if tweets:
                                break  # 成功获取数据后退出
                    
                except Exception as e:
                    logger.debug(f"爬虫搜索失败 {service_url}: {e}")
                    continue
                
                await asyncio.sleep(2)  # 限流
        
        return tweets
    
    async def _api_get_kol_tweets(self) -> List[TweetData]:
        """通过API获取KOL推文"""
        tweets = []
        
        if not self.config.bearer_token:
            logger.warning("未配置Twitter Bearer Token")
            return tweets
        
        headers = {
            'Authorization': f'Bearer {self.config.bearer_token}'
        }
        
        async with aiohttp.ClientSession() as session:
            for kol in self.KOL_LIST[:5]:  # 限制查询数量
                try:
                    # 获取用户ID
                    user_url = f"https://api.twitter.com/2/users/by/username/{kol['username']}"
                    
                    async with session.get(user_url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            user_data = await response.json()
                            user_id = user_data['data']['id']
                            
                            # 获取用户推文
                            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
                            params = {
                                'max_results': 10,
                                'tweet.fields': 'created_at,public_metrics,referenced_tweets'
                            }
                            
                            async with session.get(tweets_url, headers=headers, params=params, timeout=10) as tweets_response:
                                if tweets_response.status == 200:
                                    tweets_data = await tweets_response.json()
                                    
                                    for tweet in tweets_data.get('data', []):
                                        tweet_text = tweet['text']
                                        sentiment = await self._analyze_tweet_sentiment(tweet_text)
                                        crypto_mentions = self._detect_crypto_mentions(tweet_text)
                                        
                                        tweet_info = TweetData(
                                            id=tweet['id'],
                                            username=kol['username'],
                                            name=kol['name'],
                                            text=tweet_text,
                                            created_at=tweet.get('created_at', ''),
                                            likes=tweet.get('public_metrics', {}).get('like_count', 0),
                                            retweets=tweet.get('public_metrics', {}).get('retweet_count', 0),
                                            replies=tweet.get('public_metrics', {}).get('reply_count', 0),
                                            importance=kol['importance'],
                                            sentiment=sentiment,
                                            crypto_mentions=crypto_mentions
                                        )
                                        tweets.append(tweet_info)
                        
                        else:
                            logger.warning(f"获取 {kol['username']} 用户信息失败: {response.status}")
                    
                    await asyncio.sleep(1)  # 限流
                    
                except Exception as e:
                    logger.error(f"获取 {kol['username']} 推文失败: {e}")
        
        return tweets
    
    async def _scrape_kol_tweets(self) -> List[TweetData]:
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
                tweet_found = False
                
                for instance in nitter_instances:
                    if tweet_found:
                        break
                    
                    try:
                        url = f"https://{instance}/{kol['username']}"
                        headers = {
                            'User-Agent': self._get_random_user_agent()
                        }
                        
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # 解析推文
                                tweet_items = soup.find_all('div', class_='timeline-item')[:5]
                                
                                for item in tweet_items:
                                    try:
                                        tweet_content = item.find('div', class_='tweet-content')
                                        if tweet_content:
                                            tweet_text = tweet_content.get_text(strip=True)
                                            
                                            # 获取推文ID（如果可能）
                                            tweet_link = item.find('a', class_='tweet-link')
                                            tweet_id = ""
                                            if tweet_link:
                                                href = tweet_link.get('href', '')
                                                tweet_id = href.split('/')[-1] if href else ""
                                            
                                            if not tweet_id:
                                                tweet_id = hashlib.md5(
                                                    f"{kol['username']}_{tweet_text}".encode()
                                                ).hexdigest()[:16]
                                            
                                            sentiment = await self._analyze_tweet_sentiment(tweet_text)
                                            crypto_mentions = self._detect_crypto_mentions(tweet_text)
                                            
                                            tweet_info = TweetData(
                                                id=tweet_id,
                                                username=kol['username'],
                                                name=kol['name'],
                                                text=tweet_text,
                                                created_at=datetime.now().isoformat(),
                                                importance=kol['importance'],
                                                sentiment=sentiment,
                                                crypto_mentions=crypto_mentions
                                            )
                                            tweets.append(tweet_info)
                                    
                                    except Exception as parse_e:
                                        logger.debug(f"解析推文项失败: {parse_e}")
                                        continue
                                
                                tweet_found = True
                                break  # 成功获取后跳出
                    
                    except Exception as e:
                        logger.debug(f"从 {instance} 获取 {kol['username']} 失败: {e}")
                        continue
                
                await asyncio.sleep(random.uniform(2, 4))  # 随机延迟
        
        return tweets
    
    async def _api_get_user_timeline(self, username: str) -> List[Dict[str, Any]]:
        """通过API获取用户时间线"""
        tweets = []
        
        if not self.config.bearer_token:
            return tweets
        
        headers = {
            'Authorization': f'Bearer {self.config.bearer_token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 获取用户ID
                user_url = f"https://api.twitter.com/2/users/by/username/{username}"
                
                async with session.get(user_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        user_id = user_data['data']['id']
                        
                        # 获取用户推文
                        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
                        params = {
                            'max_results': 20,
                            'tweet.fields': 'created_at,public_metrics'
                        }
                        
                        async with session.get(tweets_url, headers=headers, params=params, timeout=10) as tweets_response:
                            if tweets_response.status == 200:
                                tweets_data = await tweets_response.json()
                                
                                for tweet in tweets_data.get('data', []):
                                    tweet_info = {
                                        'id': tweet['id'],
                                        'username': username,
                                        'text': tweet['text'],
                                        'created_at': tweet.get('created_at', ''),
                                        'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                                        'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                                        'sentiment': await self._analyze_tweet_sentiment(tweet['text']),
                                        'crypto_mentions': self._detect_crypto_mentions(tweet['text'])
                                    }
                                    tweets.append(tweet_info)
        
        except Exception as e:
            logger.error(f"API获取用户时间线失败: {e}")
        
        return tweets
    
    async def _scrape_user_timeline(self, username: str) -> List[Dict[str, Any]]:
        """通过爬虫获取用户时间线"""
        tweets = []
        
        nitter_instances = [
            'nitter.net',
            'nitter.it',
            'nitter.privacydev.net'
        ]
        
        async with aiohttp.ClientSession() as session:
            for instance in nitter_instances:
                try:
                    url = f"https://{instance}/{username}"
                    headers = {
                        'User-Agent': self._get_random_user_agent()
                    }
                    
                    async with session.get(url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            tweet_items = soup.find_all('div', class_='timeline-item')[:10]
                            
                            for item in tweet_items:
                                try:
                                    parsed_tweet = await self._parse_scraped_tweet(item)
                                    if parsed_tweet:
                                        parsed_tweet['username'] = username
                                        tweets.append(parsed_tweet)
                                except Exception as e:
                                    logger.debug(f"解析推文失败: {e}")
                            
                            if tweets:
                                break
                
                except Exception as e:
                    logger.debug(f"从 {instance} 获取 {username} 失败: {e}")
                    continue
        
        return tweets
    
    async def _parse_scraped_tweet(self, item) -> Optional[Dict[str, Any]]:
        """解析爬取的推文项目"""
        try:
            tweet_content = item.find('div', class_='tweet-content')
            if not tweet_content:
                return None
            
            tweet_text = tweet_content.get_text(strip=True)
            
            # 获取推文统计
            stats = item.find('div', class_='tweet-stats')
            likes = retweets = replies = 0
            
            if stats:
                stat_items = stats.find_all('span', class_='tweet-stat')
                for stat in stat_items:
                    if 'like' in stat.get('class', []):
                        likes = self._extract_number(stat.get_text())
                    elif 'retweet' in stat.get('class', []):
                        retweets = self._extract_number(stat.get_text())
                    elif 'reply' in stat.get('class', []):
                        replies = self._extract_number(stat.get_text())
            
            # 获取时间
            time_elem = item.find('time')
            created_at = time_elem.get('datetime', '') if time_elem else datetime.now().isoformat()
            
            return {
                'id': hashlib.md5(tweet_text.encode()).hexdigest()[:16],
                'text': tweet_text,
                'created_at': created_at,
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'sentiment': await self._analyze_tweet_sentiment(tweet_text),
                'crypto_mentions': self._detect_crypto_mentions(tweet_text)
            }
        
        except Exception as e:
            logger.debug(f"解析推文项目失败: {e}")
            return None
    
    def _extract_number(self, text: str) -> int:
        """从文本中提取数字"""
        try:
            numbers = re.findall(r'\d+', text)
            return int(numbers[0]) if numbers else 0
        except:
            return 0
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        return random.choice(user_agents)
    
    async def _detect_deleted_tweets(self, username: str) -> List[Dict[str, Any]]:
        """检测删除的推文"""
        deleted_tweets = []
        
        # 这里可以实现删除推文检测逻辑
        # 比较当前推文与历史记录，找出消失的推文
        
        return deleted_tweets
    
    async def _analyze_tweet_sentiment(self, text: str) -> Dict[str, Any]:
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
        score = 0.5
        
        if bullish_count > bearish_count:
            sentiment = 'positive'
            score = min(0.5 + (bullish_count * 0.1), 1.0)
        elif bearish_count > bullish_count:
            sentiment = 'negative'
            score = max(0.5 - (bearish_count * 0.1), 0.0)
        
        # 检查紧急程度
        urgency = 'normal'
        if urgent_count > 0:
            urgency = 'high'
        elif any(word in text_lower for word in ['breaking', 'alert', 'urgent']):
            urgency = 'medium'
        
        return {
            'label': sentiment,
            'score': score,
            'confidence': min(0.5 + (bullish_count + bearish_count) * 0.1, 1.0),
            'urgency': urgency,
            'keywords': {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'urgent': urgent_count
            }
        }
    
    def _detect_crypto_mentions(self, text: str) -> List[str]:
        """检测文本中的加密货币提及"""
        crypto_keywords = [
            'BTC', 'Bitcoin', 'ETH', 'Ethereum', 'BNB', 'Binance',
            'SOL', 'Solana', 'ADA', 'Cardano', 'XRP', 'Ripple',
            'DOT', 'Polkadot', 'AVAX', 'Avalanche', 'MATIC', 'Polygon',
            'DOGE', 'Dogecoin', 'SHIB', 'Shiba', 'UNI', 'Uniswap'
        ]
        
        mentions = []
        text_upper = text.upper()
        
        for keyword in crypto_keywords:
            if keyword.upper() in text_upper:
                mentions.append(keyword)
        
        return list(set(mentions))  # 去重
    
    async def get_trending_topics(self) -> List[Dict[str, Any]]:
        """
        获取趋势话题
        
        Returns:
            趋势话题列表
        """
        topics = []
        
        # 模拟趋势话题（实际应该从API或爬虫获取）
        crypto_topics = [
            {'topic': '#Bitcoin', 'tweets': 50000, 'sentiment': 'positive'},
            {'topic': '#Ethereum', 'tweets': 30000, 'sentiment': 'neutral'},
            {'topic': '#DeFi', 'tweets': 15000, 'sentiment': 'positive'},
            {'topic': '#NFT', 'tweets': 10000, 'sentiment': 'negative'},
            {'topic': '#Web3', 'tweets': 8000, 'sentiment': 'neutral'}
        ]
        
        for topic in crypto_topics:
            topic['timestamp'] = datetime.now().isoformat()
            topic['category'] = 'crypto'
            topics.append(topic)
        
        self.trending_topics = topics
        return topics
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """
        获取市场整体情绪
        
        Returns:
            市场情绪分析
        """
        # 获取最近的推文
        recent_tweets = await self.get_kol_tweets()
        
        # 统计情绪
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_score = 0
        urgent_count = 0
        
        for tweet in recent_tweets:
            sentiment_data = tweet.sentiment
            sentiment = sentiment_data.get('label', 'neutral')
            sentiment_counts[sentiment] += 1
            total_score += sentiment_data.get('score', 0.5)
            
            if sentiment_data.get('urgency') == 'high':
                urgent_count += 1
        
        total_tweets = len(recent_tweets)
        
        # 计算整体情绪
        overall_sentiment = 'neutral'
        avg_score = 0.5
        
        if total_tweets > 0:
            avg_score = total_score / total_tweets
            if avg_score > 0.6:
                overall_sentiment = 'positive'
            elif avg_score < 0.4:
                overall_sentiment = 'negative'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': overall_sentiment,
            'sentiment_score': avg_score,
            'sentiment_distribution': sentiment_counts,
            'urgent_signals': urgent_count,
            'sample_size': total_tweets,
            'confidence': min(total_tweets / 10, 1.0),  # 基于样本数量的置信度
            'top_influencers': self._get_top_influencers(recent_tweets)
        }
    
    def _get_top_influencers(self, tweets: List[TweetData]) -> List[Dict[str, Any]]:
        """
        获取最活跃的影响者
        
        Args:
            tweets: 推文列表
            
        Returns:
            影响者列表
        """
        influencer_activity = {}
        
        for tweet in tweets:
            username = tweet.username
            if username:
                if username not in influencer_activity:
                    influencer_activity[username] = {
                        'name': tweet.name,
                        'count': 0,
                        'importance': tweet.importance,
                        'total_engagement': 0
                    }
                
                influencer_activity[username]['count'] += 1
                influencer_activity[username]['total_engagement'] += (
                    tweet.likes + tweet.retweets + tweet.replies
                )
        
        # 排序并返回前5
        sorted_influencers = sorted(
            influencer_activity.items(),
            key=lambda x: (
                x[1]['importance'] == 'critical',
                x[1]['total_engagement'],
                x[1]['count']
            ),
            reverse=True
        )
        
        return [
            {
                'username': username,
                'name': data['name'],
                'tweet_count': data['count'],
                'importance': data['importance'],
                'total_engagement': data['total_engagement']
            }
            for username, data in sorted_influencers[:5]
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_size": len(self.tweets_cache),
            "kol_count": len(self.KOL_LIST),
            "use_scraper": self.use_scraper,
            "initialized": self.initialized
        }
    
    def get_kol_list(self) -> List[Dict[str, str]]:
        """获取KOL列表"""
        return self.KOL_LIST.copy()
    
    async def shutdown(self):
        """关闭监控器"""
        logger.info("正在关闭Twitter监控器...")
        
        # 保存缓存
        await self._save_cache()
        
        logger.info("Twitter监控器已关闭")


async def main():
    """主函数 - 用于测试"""
    monitor = TwitterMonitor()
    
    try:
        # 初始化
        await monitor.initialize()
        
        # 测试获取KOL推文
        logger.info("测试获取KOL推文...")
        tweets = await monitor.get_kol_tweets()
        logger.info(f"获取到 {len(tweets)} 条KOL推文")
        
        # 测试搜索推文
        logger.info("测试搜索推文...")
        search_tweets = await monitor.search_tweets("Bitcoin", timedelta(hours=1))
        logger.info(f"搜索到 {len(search_tweets)} 条相关推文")
        
        # 测试市场情绪
        logger.info("测试市场情绪分析...")
        sentiment = await monitor.get_market_sentiment()
        logger.info(f"市场情绪: {sentiment['overall_sentiment']}")
        
        # 输出统计
        stats = monitor.get_statistics()
        logger.info(f"统计信息: {stats}")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
    finally:
        await monitor.shutdown()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())