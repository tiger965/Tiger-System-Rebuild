"""
Window 3 API接口
提供给Window 6和其他窗口调用的标准接口
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# 导入各个监控模块
from .monitoring_activation_system import MonitoringActivationSystem
from .social.twitter_monitor import TwitterMonitor
from .social.reddit_monitor import RedditMonitor
from .social.sentiment_analyzer import SentimentAnalyzer
from .blockchain.whale_tracker import WhaleTracker
from .blockchain.chain_monitor import ChainMonitor
from .news.news_collector import NewsCollector
from .signal_aggregator.valuescan_enhanced import ValueScanCrawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """API响应数据类"""
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class Window3API:
    """Window 3必须实现的所有函数"""
    
    def __init__(self):
        # 初始化各个监控组件
        self.monitoring_system = MonitoringActivationSystem()
        self.twitter_monitor = TwitterMonitor()
        self.reddit_monitor = RedditMonitor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.whale_tracker = WhaleTracker()
        self.chain_monitor = ChainMonitor()
        self.news_collector = NewsCollector()
        self.valuescan_crawler = ValueScanCrawler()
        
        # API调用统计
        self.api_stats = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "last_call_time": None
        }
        
        # 初始化标志
        self.initialized = False
    
    async def initialize(self):
        """初始化所有组件"""
        if self.initialized:
            logger.warning("Window3 API已经初始化")
            return
        
        logger.info("正在初始化Window3 API...")
        
        try:
            # 初始化监控系统
            await self.monitoring_system.initialize()
            
            # 初始化其他组件
            await self.twitter_monitor.initialize()
            await self.reddit_monitor.initialize()
            await self.whale_tracker.initialize()
            await self.chain_monitor.initialize()
            await self.news_collector.initialize()
            await self.valuescan_crawler.initialize()
            
            self.initialized = True
            logger.info("Window3 API初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    async def crawl_twitter(self, keyword: str, time_range_minutes: int = 60,
                           get_sentiment: bool = True, min_followers: int = 10000) -> APIResponse:
        """
        爬取Twitter数据
        
        参数:
            keyword: 搜索关键词
            time_range_minutes: 时间范围（分钟）
            get_sentiment: 是否分析情绪
            min_followers: 最小粉丝数要求
        
        返回:
            APIResponse: 包含Twitter数据的响应
        """
        self._record_api_call()
        
        try:
            # 爬取Twitter数据
            tweets = await self.twitter_monitor.search_tweets(
                keyword=keyword,
                time_range=timedelta(minutes=time_range_minutes),
                min_followers=min_followers
            )
            
            # 如果需要情绪分析
            if get_sentiment and tweets:
                for tweet in tweets:
                    sentiment = await self.sentiment_analyzer.analyze_text(
                        tweet.get("text", "")
                    )
                    tweet["sentiment"] = sentiment
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "tweets": tweets,
                    "count": len(tweets),
                    "keyword": keyword,
                    "time_range_minutes": time_range_minutes
                }
            )
            
        except Exception as e:
            logger.error(f"爬取Twitter失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def crawl_reddit(self, subreddit: str = "cryptocurrency", 
                          time_range_minutes: int = 60,
                          get_sentiment: bool = True) -> APIResponse:
        """
        爬取Reddit数据
        
        参数:
            subreddit: 子版块名称
            time_range_minutes: 时间范围（分钟）
            get_sentiment: 是否分析情绪
        
        返回:
            APIResponse: 包含Reddit数据的响应
        """
        self._record_api_call()
        
        try:
            # 爬取Reddit数据
            posts = await self.reddit_monitor.get_hot_posts(
                subreddit=subreddit,
                time_range=timedelta(minutes=time_range_minutes)
            )
            
            # 如果需要情绪分析
            if get_sentiment and posts:
                for post in posts:
                    sentiment = await self.sentiment_analyzer.analyze_text(
                        post.get("title", "") + " " + post.get("text", "")
                    )
                    post["sentiment"] = sentiment
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "posts": posts,
                    "count": len(posts),
                    "subreddit": subreddit,
                    "time_range_minutes": time_range_minutes
                }
            )
            
        except Exception as e:
            logger.error(f"爬取Reddit失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def track_whale_transfers(self, min_amount_usd: float = 1000000,
                                   chains: List[str] = None,
                                   direction: str = "all") -> APIResponse:
        """
        追踪巨鲸转账
        
        参数:
            min_amount_usd: 最小金额（美元）
            chains: 区块链列表 ["ETH", "BTC", "BSC"]
            direction: 方向 "exchange_inflow", "exchange_outflow", "all"
        
        返回:
            APIResponse: 包含巨鲸转账数据的响应
        """
        self._record_api_call()
        
        if chains is None:
            chains = ["ETH", "BTC", "BSC"]
        
        try:
            # 获取巨鲸转账
            transfers = await self.whale_tracker.get_large_transfers(
                min_amount_usd=min_amount_usd,
                chains=chains,
                direction=direction
            )
            
            # 分析转账影响
            analysis = await self._analyze_whale_impact(transfers)
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "transfers": transfers,
                    "count": len(transfers),
                    "total_volume_usd": sum(t.get("amount_usd", 0) for t in transfers),
                    "analysis": analysis,
                    "chains": chains,
                    "direction": direction
                }
            )
            
        except Exception as e:
            logger.error(f"追踪巨鲸转账失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def crawl_valuescan(self, signal_type: str = "OPPORTUNITY",
                             min_confidence: float = 0.7) -> APIResponse:
        """
        爬取ValueScan信号
        
        参数:
            signal_type: 信号类型 "OPPORTUNITY", "RISK", "SIGNAL", "TRACKING"
            min_confidence: 最小置信度 (0-1)
        
        返回:
            APIResponse: 包含ValueScan信号的响应
        """
        self._record_api_call()
        
        try:
            # 爬取ValueScan信号
            signals = await self.valuescan_crawler.get_signals(
                signal_type=signal_type,
                min_confidence=min_confidence
            )
            
            # 过滤和排序信号
            filtered_signals = [
                s for s in signals 
                if s.get("confidence", 0) >= min_confidence
            ]
            
            # 按置信度排序
            filtered_signals.sort(
                key=lambda x: x.get("confidence", 0), 
                reverse=True
            )
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "signals": filtered_signals,
                    "count": len(filtered_signals),
                    "signal_type": signal_type,
                    "min_confidence": min_confidence
                }
            )
            
        except Exception as e:
            logger.error(f"爬取ValueScan失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def monitor_kol_accounts(self, accounts: List[str] = None,
                                  include_deleted: bool = True) -> APIResponse:
        """
        监控KOL账号
        
        参数:
            accounts: KOL账号列表
            include_deleted: 是否包含已删除的内容
        
        返回:
            APIResponse: 包含KOL活动的响应
        """
        self._record_api_call()
        
        if accounts is None:
            accounts = [
                "@elonmusk", "@cz_binance", "@VitalikButerin",
                "@SBF_FTX", "@CathieDWood", "@michael_saylor"
            ]
        
        try:
            kol_activities = []
            
            for account in accounts:
                # 获取账号活动
                activities = await self.twitter_monitor.get_user_timeline(
                    username=account.replace("@", ""),
                    include_deleted=include_deleted
                )
                
                # 分析每个活动的影响力
                for activity in activities:
                    # 情绪分析
                    sentiment = await self.sentiment_analyzer.analyze_text(
                        activity.get("text", "")
                    )
                    
                    activity["sentiment"] = sentiment
                    activity["account"] = account
                    
                    # 检测关键词
                    activity["crypto_mentions"] = self._detect_crypto_mentions(
                        activity.get("text", "")
                    )
                    
                    kol_activities.append(activity)
            
            # 按时间排序
            kol_activities.sort(
                key=lambda x: x.get("created_at", ""), 
                reverse=True
            )
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "activities": kol_activities,
                    "count": len(kol_activities),
                    "accounts": accounts,
                    "include_deleted": include_deleted
                }
            )
            
        except Exception as e:
            logger.error(f"监控KOL账号失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def get_news_alerts(self, importance_threshold: int = 5,
                             symbols: List[str] = None) -> APIResponse:
        """
        获取新闻警报
        
        参数:
            importance_threshold: 重要性阈值 (1-10)
            symbols: 相关币种列表
        
        返回:
            APIResponse: 包含新闻警报的响应
        """
        self._record_api_call()
        
        try:
            # 获取新闻
            news = await self.news_collector.get_latest_news(
                importance_threshold=importance_threshold,
                symbols=symbols
            )
            
            # 分析新闻影响
            for item in news:
                # 情绪分析
                sentiment = await self.sentiment_analyzer.analyze_text(
                    item.get("title", "") + " " + item.get("summary", "")
                )
                item["sentiment"] = sentiment
                
                # 影响力评分
                item["impact_score"] = self._calculate_news_impact(item)
            
            # 按影响力排序
            news.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "news": news,
                    "count": len(news),
                    "importance_threshold": importance_threshold,
                    "symbols": symbols
                }
            )
            
        except Exception as e:
            logger.error(f"获取新闻警报失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def get_social_sentiment(self, symbols: List[str] = None,
                                  time_range_hours: int = 24) -> APIResponse:
        """
        获取社交媒体情绪
        
        参数:
            symbols: 币种列表
            time_range_hours: 时间范围（小时）
        
        返回:
            APIResponse: 包含情绪分析的响应
        """
        self._record_api_call()
        
        if symbols is None:
            symbols = ["BTC", "ETH", "BNB", "SOL", "ADA"]
        
        try:
            sentiment_data = {}
            
            for symbol in symbols:
                # 获取Twitter情绪
                twitter_sentiment = await self._get_twitter_sentiment(
                    symbol, time_range_hours
                )
                
                # 获取Reddit情绪
                reddit_sentiment = await self._get_reddit_sentiment(
                    symbol, time_range_hours
                )
                
                # 综合情绪
                overall_sentiment = {
                    "twitter": twitter_sentiment,
                    "reddit": reddit_sentiment,
                    "overall": (twitter_sentiment["score"] + reddit_sentiment["score"]) / 2,
                    "trend": self._calculate_sentiment_trend(
                        twitter_sentiment, reddit_sentiment
                    )
                }
                
                sentiment_data[symbol] = overall_sentiment
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "sentiments": sentiment_data,
                    "symbols": symbols,
                    "time_range_hours": time_range_hours,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"获取社交情绪失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def get_chain_activity(self, chains: List[str] = None) -> APIResponse:
        """
        获取链上活动
        
        参数:
            chains: 区块链列表
        
        返回:
            APIResponse: 包含链上活动的响应
        """
        self._record_api_call()
        
        if chains is None:
            chains = ["ETH", "BSC", "Polygon"]
        
        try:
            chain_data = {}
            
            for chain in chains:
                # 获取链上数据
                activity = await self.chain_monitor.get_chain_metrics(chain)
                
                # 添加额外分析
                activity["health_score"] = self._calculate_chain_health(activity)
                activity["congestion_level"] = self._get_congestion_level(activity)
                
                chain_data[chain] = activity
            
            self._record_success()
            
            return APIResponse(
                success=True,
                data={
                    "chains": chain_data,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"获取链上活动失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def execute_command(self, command: Dict[str, Any]) -> APIResponse:
        """
        执行Window 6发来的命令
        
        参数:
            command: 命令字典
                {
                    "window": 3,
                    "function": "function_name",
                    "params": {...}
                }
        
        返回:
            APIResponse: 执行结果
        """
        self._record_api_call()
        
        try:
            # 验证命令格式
            if command.get("window") != 3:
                raise ValueError(f"错误的窗口号: {command.get('window')}")
            
            function_name = command.get("function")
            params = command.get("params", {})
            
            # 映射函数名到实际方法
            function_map = {
                "crawl_twitter": self.crawl_twitter,
                "crawl_reddit": self.crawl_reddit,
                "track_whale_transfers": self.track_whale_transfers,
                "crawl_valuescan": self.crawl_valuescan,
                "monitor_kol_accounts": self.monitor_kol_accounts,
                "get_news_alerts": self.get_news_alerts,
                "get_social_sentiment": self.get_social_sentiment,
                "get_chain_activity": self.get_chain_activity
            }
            
            if function_name not in function_map:
                raise ValueError(f"未知的函数: {function_name}")
            
            # 执行函数
            result = await function_map[function_name](**params)
            
            self._record_success()
            return result
            
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            self._record_failure()
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
    
    # 辅助方法
    
    async def _analyze_whale_impact(self, transfers: List[Dict]) -> Dict[str, Any]:
        """分析巨鲸转账影响"""
        total_inflow = sum(
            t.get("amount_usd", 0) for t in transfers 
            if "inflow" in t.get("direction", "").lower()
        )
        
        total_outflow = sum(
            t.get("amount_usd", 0) for t in transfers 
            if "outflow" in t.get("direction", "").lower()
        )
        
        net_flow = total_inflow - total_outflow
        
        # 判断市场影响
        if net_flow > 10000000:  # 净流入超过1000万
            impact = "极度看涨"
        elif net_flow > 1000000:  # 净流入超过100万
            impact = "看涨"
        elif net_flow < -10000000:  # 净流出超过1000万
            impact = "极度看跌"
        elif net_flow < -1000000:  # 净流出超过100万
            impact = "看跌"
        else:
            impact = "中性"
        
        return {
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_flow": net_flow,
            "impact": impact
        }
    
    def _detect_crypto_mentions(self, text: str) -> List[str]:
        """检测文本中的加密货币提及"""
        crypto_keywords = [
            "BTC", "Bitcoin", "ETH", "Ethereum", "BNB", "Binance",
            "SOL", "Solana", "ADA", "Cardano", "XRP", "Ripple",
            "DOT", "Polkadot", "AVAX", "Avalanche", "MATIC", "Polygon"
        ]
        
        mentions = []
        text_upper = text.upper()
        
        for keyword in crypto_keywords:
            if keyword.upper() in text_upper:
                mentions.append(keyword)
        
        return mentions
    
    def _calculate_news_impact(self, news_item: Dict) -> float:
        """计算新闻影响力评分"""
        base_score = news_item.get("importance", 5) / 10.0
        
        # 根据情绪调整
        sentiment = news_item.get("sentiment", {})
        if sentiment.get("label") == "positive":
            base_score *= 1.2
        elif sentiment.get("label") == "negative":
            base_score *= 1.3  # 负面新闻影响更大
        
        # 根据来源调整
        trusted_sources = ["Reuters", "Bloomberg", "CoinDesk", "CoinTelegraph"]
        if news_item.get("source") in trusted_sources:
            base_score *= 1.5
        
        return min(base_score, 1.0)  # 最高1.0
    
    async def _get_twitter_sentiment(self, symbol: str, hours: int) -> Dict[str, Any]:
        """获取Twitter情绪"""
        tweets = await self.twitter_monitor.search_tweets(
            keyword=symbol,
            time_range=timedelta(hours=hours)
        )
        
        if not tweets:
            return {"score": 0.5, "label": "neutral", "count": 0}
        
        sentiments = []
        for tweet in tweets:
            sentiment = await self.sentiment_analyzer.analyze_text(
                tweet.get("text", "")
            )
            sentiments.append(sentiment.get("score", 0.5))
        
        avg_score = sum(sentiments) / len(sentiments)
        
        if avg_score > 0.6:
            label = "positive"
        elif avg_score < 0.4:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "score": avg_score,
            "label": label,
            "count": len(tweets)
        }
    
    async def _get_reddit_sentiment(self, symbol: str, hours: int) -> Dict[str, Any]:
        """获取Reddit情绪"""
        posts = await self.reddit_monitor.search_posts(
            keyword=symbol,
            time_range=timedelta(hours=hours)
        )
        
        if not posts:
            return {"score": 0.5, "label": "neutral", "count": 0}
        
        sentiments = []
        for post in posts:
            text = post.get("title", "") + " " + post.get("text", "")
            sentiment = await self.sentiment_analyzer.analyze_text(text)
            sentiments.append(sentiment.get("score", 0.5))
        
        avg_score = sum(sentiments) / len(sentiments)
        
        if avg_score > 0.6:
            label = "positive"
        elif avg_score < 0.4:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "score": avg_score,
            "label": label,
            "count": len(posts)
        }
    
    def _calculate_sentiment_trend(self, twitter: Dict, reddit: Dict) -> str:
        """计算情绪趋势"""
        combined_score = (twitter["score"] + reddit["score"]) / 2
        
        if combined_score > 0.7:
            return "强烈看涨"
        elif combined_score > 0.6:
            return "看涨"
        elif combined_score < 0.3:
            return "强烈看跌"
        elif combined_score < 0.4:
            return "看跌"
        else:
            return "中性"
    
    def _calculate_chain_health(self, activity: Dict) -> float:
        """计算链健康度"""
        # 基于多个指标计算健康度
        tps = activity.get("tps", 0)
        gas_price = activity.get("gas_price", 0)
        pending_txs = activity.get("pending_transactions", 0)
        
        # 简单的健康度计算
        health = 1.0
        
        if tps < 10:
            health -= 0.3
        elif tps < 50:
            health -= 0.1
        
        if gas_price > 100:
            health -= 0.3
        elif gas_price > 50:
            health -= 0.1
        
        if pending_txs > 10000:
            health -= 0.2
        elif pending_txs > 5000:
            health -= 0.1
        
        return max(health, 0.0)
    
    def _get_congestion_level(self, activity: Dict) -> str:
        """获取拥堵级别"""
        pending = activity.get("pending_transactions", 0)
        
        if pending > 10000:
            return "严重拥堵"
        elif pending > 5000:
            return "中度拥堵"
        elif pending > 1000:
            return "轻度拥堵"
        else:
            return "畅通"
    
    def _record_api_call(self):
        """记录API调用"""
        self.api_stats["total_calls"] += 1
        self.api_stats["last_call_time"] = datetime.now().isoformat()
    
    def _record_success(self):
        """记录成功调用"""
        self.api_stats["success_calls"] += 1
    
    def _record_failure(self):
        """记录失败调用"""
        self.api_stats["failed_calls"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取API统计信息"""
        return {
            **self.api_stats,
            "monitoring_stats": self.monitoring_system.get_statistics(),
            "initialized": self.initialized
        }
    
    async def shutdown(self):
        """关闭API接口"""
        logger.info("正在关闭Window3 API...")
        
        # 关闭各个组件
        await self.monitoring_system.shutdown()
        await self.twitter_monitor.shutdown()
        await self.reddit_monitor.shutdown()
        await self.whale_tracker.shutdown()
        await self.chain_monitor.shutdown()
        await self.news_collector.shutdown()
        await self.valuescan_crawler.shutdown()
        
        logger.info("Window3 API已关闭")


# 全局API实例
window3_api = Window3API()


async def handle_window6_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理Window 6发来的命令
    
    参数:
        command: 命令字典
    
    返回:
        执行结果
    """
    if not window3_api.initialized:
        await window3_api.initialize()
    
    response = await window3_api.execute_command(command)
    return asdict(response)


async def main():
    """主函数 - 用于测试"""
    api = Window3API()
    
    try:
        # 初始化
        await api.initialize()
        
        # 测试各个接口
        logger.info("测试Twitter爬取...")
        result = await api.crawl_twitter("BTC", time_range_minutes=60)
        logger.info(f"Twitter结果: {result.success}")
        
        logger.info("测试巨鲸追踪...")
        result = await api.track_whale_transfers(min_amount_usd=100000)
        logger.info(f"巨鲸追踪结果: {result.success}")
        
        logger.info("测试KOL监控...")
        result = await api.monitor_kol_accounts()
        logger.info(f"KOL监控结果: {result.success}")
        
        # 输出统计
        logger.info(f"API统计: {api.get_statistics()}")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
    finally:
        await api.shutdown()


if __name__ == "__main__":
    asyncio.run(main())