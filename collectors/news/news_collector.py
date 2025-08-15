"""
新闻采集器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
import json
import hashlib

logger = logging.getLogger(__name__)

class NewsCollector:
    """新闻数据采集器"""
    
    # 新闻源配置
    NEWS_SOURCES = {
        'CoinDesk': {
            'rss': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'type': 'rss',
            'importance': 'high',
            'categories': ['news', 'markets', 'tech']
        },
        'CoinTelegraph': {
            'rss': 'https://cointelegraph.com/rss',
            'type': 'rss',
            'importance': 'high',
            'categories': ['news', 'analysis']
        },
        'TheBlock': {
            'url': 'https://www.theblock.co',
            'type': 'scraper',
            'importance': 'high',
            'categories': ['news', 'research']
        },
        'Decrypt': {
            'rss': 'https://decrypt.co/feed',
            'type': 'rss',
            'importance': 'medium',
            'categories': ['news', 'defi', 'nft']
        },
        'Bitcoin Magazine': {
            'rss': 'https://bitcoinmagazine.com/.rss/full/',
            'type': 'rss',
            'importance': 'medium',
            'categories': ['bitcoin', 'tech']
        },
        'SEC': {
            'url': 'https://www.sec.gov/news/pressreleases',
            'type': 'scraper',
            'importance': 'critical',
            'categories': ['regulation', 'enforcement']
        }
    }
    
    # 事件分类关键词
    EVENT_CATEGORIES = {
        'regulation': ['sec', 'regulation', 'compliance', 'legal', 'lawsuit', 'court', 'government'],
        'hack': ['hack', 'exploit', 'vulnerability', 'breach', 'stolen', 'attack', 'security'],
        'partnership': ['partnership', 'collaboration', 'integration', 'alliance', 'joins', 'teams up'],
        'launch': ['launch', 'release', 'unveil', 'introduce', 'debut', 'rollout', 'mainnet'],
        'upgrade': ['upgrade', 'update', 'improvement', 'enhancement', 'v2', 'version'],
        'market': ['price', 'market cap', 'volume', 'trading', 'exchange', 'listing'],
        'defi': ['defi', 'yield', 'lending', 'liquidity', 'amm', 'dex', 'protocol'],
        'nft': ['nft', 'non-fungible', 'collectible', 'opensea', 'marketplace'],
        'adoption': ['adoption', 'accept', 'payment', 'institutional', 'corporate', 'mainstream']
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化新闻采集器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.news_cache = []  # 新闻缓存
        self.seen_urls = set()  # 已见过的URL（去重）
        self.important_news = []  # 重要新闻
    
    async def collect_news(self) -> List[Dict[str, Any]]:
        """
        采集新闻
        
        Returns:
            新闻列表
        """
        all_news = []
        
        # 并发采集各个新闻源
        tasks = []
        for source_name, source_config in self.NEWS_SOURCES.items():
            if source_config['type'] == 'rss':
                tasks.append(self._collect_rss_news(source_name, source_config))
            elif source_config['type'] == 'scraper':
                tasks.append(self._scrape_news(source_name, source_config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"新闻采集失败: {result}")
            else:
                all_news.extend(result)
        
        # 去重
        unique_news = self._deduplicate_news(all_news)
        
        # 分类和评级
        categorized_news = self._categorize_news(unique_news)
        
        # 更新缓存
        self.news_cache = categorized_news[:100]  # 保留最新100条
        
        # 识别重要新闻
        self._identify_important_news(categorized_news)
        
        return categorized_news
    
    async def _collect_rss_news(self, source_name: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        通过RSS采集新闻
        
        Args:
            source_name: 新闻源名称
            config: 新闻源配置
            
        Returns:
            新闻列表
        """
        news_items = []
        
        try:
            # 解析RSS源
            feed = feedparser.parse(config['rss'])
            
            for entry in feed.entries[:20]:  # 限制数量
                # 生成唯一ID
                news_id = hashlib.md5(entry.link.encode()).hexdigest()
                
                # 检查是否已存在
                if news_id not in self.seen_urls:
                    self.seen_urls.add(news_id)
                    
                    news_item = {
                        'id': news_id,
                        'source': source_name,
                        'title': entry.title,
                        'url': entry.link,
                        'summary': entry.get('summary', '')[:500],  # 限制长度
                        'published': entry.get('published', datetime.now().isoformat()),
                        'importance': config['importance'],
                        'categories': [],
                        'entities': [],  # 相关实体（币种、项目等）
                        'sentiment': 'neutral',
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    news_items.append(news_item)
        
        except Exception as e:
            logger.error(f"采集 {source_name} RSS失败: {e}")
        
        return news_items
    
    async def _scrape_news(self, source_name: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        通过爬虫采集新闻
        
        Args:
            source_name: 新闻源名称
            config: 新闻源配置
            
        Returns:
            新闻列表
        """
        news_items = []
        
        if source_name == 'SEC':
            news_items = await self._scrape_sec_news(config)
        elif source_name == 'TheBlock':
            news_items = await self._scrape_theblock_news(config)
        
        return news_items
    
    async def _scrape_sec_news(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """爬取SEC新闻"""
        news_items = []
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                async with session.get(config['url'], headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 查找新闻条目（SEC网站结构）
                        press_releases = soup.find_all('tr', class_='pr-list-page-row')[:10]
                        
                        for pr in press_releases:
                            title_elem = pr.find('a')
                            date_elem = pr.find('td', class_='pr-list-page-date')
                            
                            if title_elem:
                                news_id = hashlib.md5(title_elem['href'].encode()).hexdigest()
                                
                                if news_id not in self.seen_urls:
                                    self.seen_urls.add(news_id)
                                    
                                    news_items.append({
                                        'id': news_id,
                                        'source': 'SEC',
                                        'title': title_elem.get_text(strip=True),
                                        'url': f"https://www.sec.gov{title_elem['href']}",
                                        'published': date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat(),
                                        'importance': 'critical',  # SEC新闻都很重要
                                        'categories': ['regulation'],
                                        'collected_at': datetime.now().isoformat()
                                    })
            
            except Exception as e:
                logger.error(f"爬取SEC新闻失败: {e}")
        
        return news_items
    
    async def _scrape_theblock_news(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """爬取TheBlock新闻"""
        news_items = []
        
        # TheBlock需要更复杂的爬虫策略，这里简化处理
        # 实际应该使用Selenium或其API
        
        return news_items
    
    def _deduplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重新闻
        
        Args:
            news_list: 原始新闻列表
            
        Returns:
            去重后的新闻列表
        """
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            # 基于标题相似度去重
            title_key = news['title'].lower()[:50]  # 取前50字符
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        return unique_news
    
    def _categorize_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分类新闻
        
        Args:
            news_list: 新闻列表
            
        Returns:
            分类后的新闻列表
        """
        for news in news_list:
            # 基于标题和摘要分类
            text = (news.get('title', '') + ' ' + news.get('summary', '')).lower()
            
            categories = []
            for category, keywords in self.EVENT_CATEGORIES.items():
                if any(keyword in text for keyword in keywords):
                    categories.append(category)
            
            news['categories'] = categories if categories else ['general']
            
            # 提取相关实体
            entities = self._extract_entities(text)
            news['entities'] = entities
            
            # 评估重要性
            news['importance_score'] = self._calculate_importance(news)
        
        # 按重要性排序
        news_list.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return news_list
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        提取相关实体（币种、项目等）
        
        Args:
            text: 文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 常见加密货币
        cryptos = ['bitcoin', 'btc', 'ethereum', 'eth', 'binance', 'bnb', 
                  'cardano', 'ada', 'solana', 'sol', 'polygon', 'matic',
                  'chainlink', 'link', 'uniswap', 'uni', 'aave', 'compound']
        
        # 常见交易所
        exchanges = ['binance', 'coinbase', 'okx', 'kraken', 'ftx', 
                    'huobi', 'kucoin', 'bitfinex', 'gemini']
        
        # 检查文本中的实体
        for crypto in cryptos:
            if crypto in text:
                entities.append(crypto.upper())
        
        for exchange in exchanges:
            if exchange in text:
                entities.append(exchange.capitalize())
        
        return list(set(entities))  # 去重
    
    def _calculate_importance(self, news: Dict[str, Any]) -> int:
        """
        计算新闻重要性得分
        
        Args:
            news: 新闻项
            
        Returns:
            重要性得分（0-100）
        """
        score = 0
        
        # 基础分数（根据来源）
        source_scores = {
            'critical': 50,
            'high': 30,
            'medium': 20,
            'low': 10
        }
        score += source_scores.get(news.get('importance', 'low'), 10)
        
        # 类别加分
        critical_categories = ['regulation', 'hack', 'launch']
        for category in news.get('categories', []):
            if category in critical_categories:
                score += 20
            else:
                score += 5
        
        # 实体加分（提到的项目越多可能越重要）
        entity_count = len(news.get('entities', []))
        score += min(entity_count * 5, 20)
        
        # 时效性加分（越新越重要）
        try:
            published_time = datetime.fromisoformat(news.get('published', ''))
            age_hours = (datetime.now() - published_time).total_seconds() / 3600
            if age_hours < 1:
                score += 20
            elif age_hours < 6:
                score += 10
            elif age_hours < 24:
                score += 5
        except:
            pass
        
        return min(score, 100)  # 最高100分
    
    def _identify_important_news(self, news_list: List[Dict[str, Any]]):
        """
        识别重要新闻
        
        Args:
            news_list: 新闻列表
        """
        self.important_news = []
        
        for news in news_list:
            # 重要性阈值
            if news.get('importance_score', 0) >= 70:
                self.important_news.append(news)
            
            # 特定类别直接标记为重要
            if any(cat in ['regulation', 'hack'] for cat in news.get('categories', [])):
                if news not in self.important_news:
                    self.important_news.append(news)
        
        # 限制数量
        self.important_news = self.important_news[:10]
    
    async def monitor_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        监控特定关键词的新闻
        
        Args:
            keywords: 关键词列表
            
        Returns:
            相关新闻列表
        """
        relevant_news = []
        
        # 获取最新新闻
        all_news = await self.collect_news()
        
        for news in all_news:
            text = (news.get('title', '') + ' ' + news.get('summary', '')).lower()
            
            for keyword in keywords:
                if keyword.lower() in text:
                    news['matched_keyword'] = keyword
                    relevant_news.append(news)
                    break
        
        return relevant_news
    
    def get_news_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取特定类别的新闻
        
        Args:
            category: 类别名称
            
        Returns:
            该类别的新闻列表
        """
        return [
            news for news in self.news_cache
            if category in news.get('categories', [])
        ]
    
    def get_important_news(self) -> List[Dict[str, Any]]:
        """获取重要新闻"""
        return self.important_news.copy()
    
    def get_recent_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取最近的新闻
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            最近的新闻列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for news in self.news_cache:
            try:
                collected_time = datetime.fromisoformat(news['collected_at'])
                if collected_time > cutoff_time:
                    recent.append(news)
            except:
                pass
        
        return recent