"""
Window 3 API接口
为Window 6提供标准化的数据收集接口
纯工具属性，不含任何分析逻辑
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import requests

# 导入核心组件
try:
    from monitoring_activation_system import MonitoringActivationSystem
    from data_chain_integrator import (
        DataChainIntegrator, 
        SignalCorrelator, 
        IntelligencePackager
    )
except ImportError:
    from .monitoring_activation_system import MonitoringActivationSystem
    from .data_chain_integrator import (
        DataChainIntegrator, 
        SignalCorrelator, 
        IntelligencePackager
    )

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Window3-API] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Window3API:
    """
    Window 3的统一API接口
    所有函数名严格按照文档要求，不能更改
    """
    
    def __init__(self):
        # 初始化核心组件
        self.monitoring_system = MonitoringActivationSystem()
        self.data_integrator = DataChainIntegrator()
        self.signal_correlator = SignalCorrelator()
        self.intelligence_packager = IntelligencePackager()
        
        # API配置
        self.api_keys = {
            "whale_alert": "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU",
            "cryptopanic": "e79d3bb95497a40871d90a82056e3face2050c53",
            "coinglass": "35_usd_monthly_hobbyist"  # 标记级别
        }
        
        # API端点
        self.endpoints = {
            "whale_alert": "https://api.whale-alert.io/v1",
            "cryptopanic": "https://cryptopanic.com/api/v1/posts",
            "coingecko": "https://api.coingecko.com/api/v3",
            "alternative": "https://api.alternative.me",
            "blockchain_info": "https://blockchain.info",
            "etherscan": "https://api.etherscan.io/api",
            "defilama": "https://api.llama.fi"
        }
        
        # 数据缓存（减少API调用）
        self.cache = {}
        self.cache_ttl = 30  # 缓存30秒

    async def get_intelligence_package(self, 
                                      symbol: str = "BTC",
                                      include_window2_data: bool = True,
                                      analysis_depth: str = "deep") -> Dict:
        """
        获取整合情报包（Window 6的核心调用）
        整合所有数据源，提供全方位的市场情报
        """
        logger.info(f"生成{symbol}情报包，深度: {analysis_depth}")
        
        # 收集所有数据
        all_data = {}
        
        # 1. 获取Window 2数据（如果需要）
        if include_window2_data:
            window2_data = await self.fetch_window2_data()
            if window2_data:
                self.data_integrator.receive_window2_data(window2_data)
                all_data["window2"] = window2_data
        
        # 2. 获取链上数据
        chain_data = await self.fetch_all_chain_data(symbol)
        if chain_data:
            self.data_integrator.receive_chain_data(chain_data)
            all_data["chain"] = chain_data
        
        # 3. 获取社交数据
        social_data = await self.fetch_all_social_data(symbol)
        if social_data:
            self.data_integrator.receive_social_data(social_data)
            all_data["social"] = social_data
        
        # 4. 获取新闻数据
        news_data = await self.fetch_news_data(symbol)
        if news_data:
            self.data_integrator.receive_news_data(news_data)
            all_data["news"] = news_data
        
        # 5. 生成综合情报包
        intelligence = self.data_integrator.generate_intelligence_package(symbol)
        
        # 6. 添加关联分析（深度分析模式）
        if analysis_depth == "deep":
            # 收集所有数据点用于关联分析
            data_points = self.extract_data_points(all_data)
            correlations = self.signal_correlator.find_correlations(data_points)
            
            # 创建增强版情报包
            enhanced_package = self.intelligence_packager.create_package(
                raw_data=all_data,
                analysis=intelligence.get("analysis", {}),
                correlations=correlations,
                priority="high" if intelligence.get("alerts") else "normal"
            )
            
            return enhanced_package
        
        return intelligence

    async def crawl_twitter(self, 
                          keyword: str,
                          time_range_minutes: int = 60,
                          get_sentiment: bool = True,
                          min_followers: int = 10000) -> Dict:
        """
        爬取Twitter数据
        注意：需要Twitter API密钥，暂时返回模拟数据
        """
        logger.info(f"爬取Twitter: {keyword}, 时间范围: {time_range_minutes}分钟")
        
        # 实际生产环境需要Twitter API
        # 这里返回结构化的模拟数据供开发测试
        return {
            "keyword": keyword,
            "time_range": time_range_minutes,
            "tweets_count": 0,
            "sentiment_score": 0.5,
            "influential_tweets": [],
            "trending_topics": [],
            "kol_mentions": [],
            "timestamp": datetime.now().isoformat(),
            "note": "需要配置Twitter API才能获取真实数据"
        }

    async def track_whale_transfers(self,
                                   min_amount_usd: int = 1000000,
                                   chains: List[str] = ["BTC", "ETH"],
                                   direction: str = "all") -> Dict:
        """
        追踪巨鲸转账
        使用WhaleAlert API获取大额转账数据
        """
        logger.info(f"追踪巨鲸转账: 最小金额${min_amount_usd:,}, 链: {chains}")
        
        transfers = []
        
        try:
            # 使用WhaleAlert API
            url = f"{self.endpoints['whale_alert']}/transactions"
            headers = {"X-WA-API-KEY": self.api_keys["whale_alert"]}
            
            # 设置时间范围（最近1小时）
            end_time = int(time.time())
            start_time = end_time - 3600
            
            params = {
                "api_key": self.api_keys["whale_alert"],
                "min_value": min_amount_usd,
                "start": start_time,
                "end": end_time,
                "limit": 100
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 过滤指定链和方向的转账
                        for tx in data.get("transactions", []):
                            # 检查链
                            if tx.get("blockchain") not in [c.lower() for c in chains]:
                                continue
                            
                            # 检查方向
                            if direction == "exchange_inflow":
                                if not self.is_exchange(tx.get("to", {}).get("owner", "")):
                                    continue
                            elif direction == "exchange_outflow":
                                if not self.is_exchange(tx.get("from", {}).get("owner", "")):
                                    continue
                            
                            transfers.append({
                                "hash": tx.get("hash"),
                                "blockchain": tx.get("blockchain"),
                                "symbol": tx.get("symbol", "").upper(),
                                "amount": tx.get("amount"),
                                "amount_usd": tx.get("amount_usd"),
                                "from": tx.get("from", {}).get("owner", "unknown"),
                                "to": tx.get("to", {}).get("owner", "unknown"),
                                "timestamp": tx.get("timestamp"),
                                "transaction_type": self.classify_transaction(tx)
                            })
                    else:
                        logger.error(f"WhaleAlert API错误: {response.status}")
                        
        except Exception as e:
            logger.error(f"追踪巨鲸转账失败: {e}")
        
        return {
            "transfers": transfers,
            "total_count": len(transfers),
            "total_volume_usd": sum(t["amount_usd"] for t in transfers),
            "chains": chains,
            "direction": direction,
            "timestamp": datetime.now().isoformat()
        }

    async def crawl_valuescan(self,
                            signal_type: str = "OPPORTUNITY",
                            min_confidence: float = 0.7) -> Dict:
        """
        爬取ValueScan信号
        注意：需要登录凭证，暂时返回结构化数据
        """
        logger.info(f"爬取ValueScan: 类型={signal_type}, 最小置信度={min_confidence}")
        
        # ValueScan需要登录，这里返回模拟数据结构
        return {
            "signal_type": signal_type,
            "signals": [],
            "filtered_count": 0,
            "min_confidence": min_confidence,
            "timestamp": datetime.now().isoformat(),
            "note": "需要ValueScan登录凭证才能获取真实数据"
        }

    async def monitor_kol_accounts(self,
                                  accounts: List[str] = None,
                                  include_deleted: bool = True) -> Dict:
        """
        监控KOL账号动态
        包括马斯克、CZ、V神等重要人物
        """
        if accounts is None:
            accounts = [
                "@elonmusk",
                "@cz_binance",
                "@VitalikButerin",
                "@justinsuntron",
                "@brian_armstrong"
            ]
        
        logger.info(f"监控KOL账号: {accounts}")
        
        # 需要社交媒体API，返回结构化数据
        return {
            "accounts": accounts,
            "activities": [],
            "deleted_posts": [] if include_deleted else None,
            "sentiment_impact": "neutral",
            "timestamp": datetime.now().isoformat(),
            "note": "需要社交媒体API才能获取真实数据"
        }

    async def fetch_window2_data(self) -> Dict:
        """
        获取Window 2的数据
        包括实时价格、资金费率、交易所储备等
        """
        # 这里应该调用Window 2的API
        # 暂时返回模拟数据结构
        return {
            "real_time_prices": {
                "binance_btc": 117500.00,
                "okx_btc": 117480.00,
                "price_gap": 20.00
            },
            "funding_rates": {
                "binance_btc_perp": 0.0100,
                "okx_btc_perp": 0.0095,
                "market_sentiment": "neutral"
            },
            "exchange_reserves": {
                "total_btc_reserves": 316000,
                "reserve_changes": "+500 BTC (24h)",
                "alert_level": "normal"
            },
            "arbitrage_opportunities": [
                {"exchanges": "Binance vs OKX", "gap": 20.00, "percentage": 0.017}
            ],
            "timestamp": datetime.now().isoformat()
        }

    async def fetch_all_chain_data(self, symbol: str = "BTC") -> Dict:
        """
        获取全面的链上数据
        包括巨鲸活动、Gas费用、DeFi指标等
        """
        chain_data = {}
        
        # 1. 获取链上基础数据
        if symbol == "BTC":
            chain_data.update(await self.fetch_bitcoin_chain_data())
        elif symbol == "ETH":
            chain_data.update(await self.fetch_ethereum_chain_data())
        
        # 2. 获取DeFi数据
        defi_data = await self.fetch_defi_data()
        if defi_data:
            chain_data["defi"] = defi_data
        
        # 3. 获取跨链桥数据
        bridge_data = await self.fetch_bridge_data()
        if bridge_data:
            chain_data["bridges"] = bridge_data
        
        return chain_data

    async def fetch_bitcoin_chain_data(self) -> Dict:
        """获取比特币链上数据"""
        try:
            # 使用blockchain.info API
            async with aiohttp.ClientSession() as session:
                # 获取未确认交易池
                async with session.get(f"{self.endpoints['blockchain_info']}/unconfirmed-transactions?format=json") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        mempool_size = len(data.get("txs", []))
                    else:
                        mempool_size = 0
                
                # 获取最新区块
                async with session.get(f"{self.endpoints['blockchain_info']}/latestblock") as resp:
                    if resp.status == 200:
                        block_data = await resp.json()
                        block_height = block_data.get("height", 0)
                    else:
                        block_height = 0
            
            return {
                "blockchain": "bitcoin",
                "mempool_size": mempool_size,
                "block_height": block_height,
                "whale_activity": "normal",  # 需要进一步分析
                "exchange_netflow": 0,  # 需要额外数据源
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取比特币链上数据失败: {e}")
            return {}

    async def fetch_ethereum_chain_data(self) -> Dict:
        """获取以太坊链上数据"""
        try:
            # 获取Gas价格
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.endpoints['etherscan']}/module=gastracker&action=gasoracle") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "1":
                            gas_price = data.get("result", {}).get("SafeGasPrice", "0")
                        else:
                            gas_price = "0"
                    else:
                        gas_price = "0"
            
            return {
                "blockchain": "ethereum",
                "gas_price_gwei": gas_price,
                "defi_tvl": 0,  # 需要DeFiLlama数据
                "whale_activity": "normal",
                "exchange_netflow": 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取以太坊链上数据失败: {e}")
            return {}

    async def fetch_defi_data(self) -> Dict:
        """获取DeFi数据"""
        try:
            async with aiohttp.ClientSession() as session:
                # 获取总TVL
                async with session.get(f"{self.endpoints['defilama']}/tvl") as resp:
                    if resp.status == 200:
                        tvl = await resp.json()
                    else:
                        tvl = 0
                
                # 获取协议排名
                async with session.get(f"{self.endpoints['defilama']}/protocols") as resp:
                    if resp.status == 200:
                        protocols = await resp.json()
                        top_protocols = protocols[:10] if isinstance(protocols, list) else []
                    else:
                        top_protocols = []
            
            return {
                "total_tvl": tvl,
                "top_protocols": top_protocols,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取DeFi数据失败: {e}")
            return {}

    async def fetch_bridge_data(self) -> Dict:
        """获取跨链桥数据"""
        # 需要专门的跨链桥API
        return {
            "total_volume_24h": 0,
            "active_bridges": [],
            "timestamp": datetime.now().isoformat()
        }

    async def fetch_all_social_data(self, keyword: str = "BTC") -> Dict:
        """
        获取全面的社交媒体数据
        整合Twitter、Reddit、Telegram等
        """
        social_data = {}
        
        # 1. 获取恐慌贪婪指数
        fear_greed = await self.fetch_fear_greed_index()
        if fear_greed:
            social_data["fear_greed"] = fear_greed
        
        # 2. 获取社交媒体情绪（需要API）
        social_data["twitter_sentiment"] = await self.analyze_twitter_sentiment(keyword)
        social_data["reddit_sentiment"] = await self.analyze_reddit_sentiment(keyword)
        
        # 3. 获取搜索趋势
        social_data["search_trends"] = await self.fetch_search_trends(keyword)
        
        return social_data

    async def fetch_fear_greed_index(self) -> Dict:
        """获取恐慌贪婪指数"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.endpoints['alternative']}/fng/") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "data" in data and data["data"]:
                            current = data["data"][0]
                            return {
                                "value": int(current["value"]),
                                "classification": current["value_classification"],
                                "timestamp": current["timestamp"]
                            }
        except Exception as e:
            logger.error(f"获取恐慌贪婪指数失败: {e}")
        
        return {"value": 50, "classification": "Neutral"}

    async def analyze_twitter_sentiment(self, keyword: str) -> Dict:
        """分析Twitter情绪"""
        # 需要Twitter API
        return {
            "keyword": keyword,
            "sentiment_score": 0.5,
            "positive_ratio": 0.5,
            "volume_24h": 0,
            "influential_posts": []
        }

    async def analyze_reddit_sentiment(self, keyword: str) -> Dict:
        """分析Reddit情绪"""
        # 需要Reddit API
        return {
            "keyword": keyword,
            "sentiment_score": 0.5,
            "active_discussions": 0,
            "top_posts": []
        }

    async def fetch_search_trends(self, keyword: str) -> Dict:
        """获取搜索趋势"""
        # 需要Google Trends API或类似服务
        return {
            "keyword": keyword,
            "trend_score": 50,
            "change_7d": 0,
            "related_queries": []
        }

    async def fetch_news_data(self, symbol: str = "BTC") -> Dict:
        """
        获取新闻数据
        注意：CryptoPanic配额已用完，使用其他源或缓存
        """
        news_data = {
            "symbol": symbol,
            "articles": [],
            "important_news": [],
            "sentiment": "neutral",
            "timestamp": datetime.now().isoformat()
        }
        
        # CryptoPanic配额问题，暂时跳过
        # 可以使用其他新闻源或等待配额恢复
        
        return news_data

    def is_exchange(self, address: str) -> bool:
        """判断地址是否为交易所"""
        exchanges = [
            "binance", "okx", "coinbase", "kraken", "bitfinex",
            "huobi", "kucoin", "bybit", "gate.io", "mexc"
        ]
        address_lower = address.lower()
        return any(ex in address_lower for ex in exchanges)

    def classify_transaction(self, tx: Dict) -> str:
        """分类交易类型"""
        from_owner = tx.get("from", {}).get("owner", "").lower()
        to_owner = tx.get("to", {}).get("owner", "").lower()
        
        from_exchange = self.is_exchange(from_owner)
        to_exchange = self.is_exchange(to_owner)
        
        if from_exchange and to_exchange:
            return "exchange_to_exchange"
        elif from_exchange and not to_exchange:
            return "exchange_withdrawal"
        elif not from_exchange and to_exchange:
            return "exchange_deposit"
        else:
            return "wallet_to_wallet"

    def extract_data_points(self, all_data: Dict) -> List[Dict]:
        """从原始数据中提取数据点用于关联分析"""
        data_points = []
        current_time = time.time()
        
        # 提取Window 2数据点
        if "window2" in all_data:
            w2 = all_data["window2"]
            if "funding_rates" in w2:
                data_points.append({
                    "type": "funding_rate",
                    "value": w2["funding_rates"].get("binance_btc_perp", 0),
                    "timestamp": current_time
                })
            if "exchange_reserves" in w2:
                data_points.append({
                    "type": "reserve_change",
                    "value": w2["exchange_reserves"].get("reserve_changes", ""),
                    "timestamp": current_time
                })
        
        # 提取链上数据点
        if "chain" in all_data:
            chain = all_data["chain"]
            if "whale_activity" in chain:
                data_points.append({
                    "type": "chain_activity",
                    "value": chain["whale_activity"],
                    "timestamp": current_time - 300  # 5分钟前
                })
        
        # 提取社交数据点
        if "social" in all_data:
            social = all_data["social"]
            if "fear_greed" in social:
                data_points.append({
                    "type": "social_sentiment",
                    "value": social["fear_greed"]["value"],
                    "timestamp": current_time - 600  # 10分钟前
                })
        
        return data_points

    async def get_market_overview(self) -> Dict:
        """
        获取市场总览
        快速获取所有重要指标的快照
        """
        overview = {
            "timestamp": datetime.now().isoformat(),
            "btc_price": 0,
            "eth_price": 0,
            "total_market_cap": 0,
            "fear_greed_index": 50,
            "dominant_sentiment": "neutral",
            "major_events": [],
            "risk_level": "medium"
        }
        
        # 获取价格数据
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.endpoints['coingecko']}/simple/price"
                params = {
                    "ids": "bitcoin,ethereum",
                    "vs_currencies": "usd",
                    "include_market_cap": "true"
                }
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        overview["btc_price"] = data.get("bitcoin", {}).get("usd", 0)
                        overview["eth_price"] = data.get("ethereum", {}).get("usd", 0)
        except Exception as e:
            logger.error(f"获取市场总览失败: {e}")
        
        # 获取恐慌贪婪指数
        fear_greed = await self.fetch_fear_greed_index()
        if fear_greed:
            overview["fear_greed_index"] = fear_greed["value"]
            
            # 根据指数判断情绪
            if fear_greed["value"] < 25:
                overview["dominant_sentiment"] = "extreme_fear"
                overview["risk_level"] = "low"
            elif fear_greed["value"] < 45:
                overview["dominant_sentiment"] = "fear"
                overview["risk_level"] = "medium_low"
            elif fear_greed["value"] < 55:
                overview["dominant_sentiment"] = "neutral"
                overview["risk_level"] = "medium"
            elif fear_greed["value"] < 75:
                overview["dominant_sentiment"] = "greed"
                overview["risk_level"] = "medium_high"
            else:
                overview["dominant_sentiment"] = "extreme_greed"
                overview["risk_level"] = "high"
        
        return overview


# 触发信号发送器
class TriggerSender:
    """
    触发信号发送器
    负责将触发信号发送给Window 6
    """
    
    def __init__(self):
        self.window6_endpoint = "http://localhost:8006/api/trigger"  # Window 6的接收端点
        self.retry_count = 3
        self.retry_delay = 1

    async def send_to_window6(self, trigger_data: Dict) -> bool:
        """
        发送触发信号到Window 6
        """
        for attempt in range(self.retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.window6_endpoint,
                        json=trigger_data,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"成功发送{trigger_data['level']}级触发到Window 6")
                            return True
                        else:
                            logger.warning(f"发送触发失败，状态码: {response.status}")
                            
            except aiohttp.ClientConnectorError:
                logger.warning(f"无法连接到Window 6，尝试 {attempt + 1}/{self.retry_count}")
            except Exception as e:
                logger.error(f"发送触发信号错误: {e}")
            
            if attempt < self.retry_count - 1:
                await asyncio.sleep(self.retry_delay)
        
        # 如果发送失败，保存到文件
        self.save_trigger_to_file(trigger_data)
        return False

    def save_trigger_to_file(self, trigger_data: Dict):
        """
        保存触发信号到文件（备用方案）
        """
        import os
        
        trigger_dir = "/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/triggers"
        os.makedirs(trigger_dir, exist_ok=True)
        
        filename = f"trigger_{trigger_data['level']}_{int(time.time())}.json"
        filepath = os.path.join(trigger_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trigger_data, f, ensure_ascii=False, indent=2)
            logger.info(f"触发信号已保存到文件: {filename}")
        except Exception as e:
            logger.error(f"保存触发信号失败: {e}")


# 创建全局API实例
window3_api = Window3API()
trigger_sender = TriggerSender()


# 供外部调用的函数
async def handle_window6_request(command: Dict) -> Dict:
    """
    处理来自Window 6的请求
    """
    function = command.get("function")
    params = command.get("params", {})
    
    try:
        if function == "get_intelligence_package":
            return await window3_api.get_intelligence_package(**params)
        
        elif function == "crawl_twitter":
            return await window3_api.crawl_twitter(**params)
        
        elif function == "track_whale_transfers":
            return await window3_api.track_whale_transfers(**params)
        
        elif function == "crawl_valuescan":
            return await window3_api.crawl_valuescan(**params)
        
        elif function == "monitor_kol_accounts":
            return await window3_api.monitor_kol_accounts(**params)
        
        elif function == "get_market_overview":
            return await window3_api.get_market_overview()
        
        else:
            return {
                "error": f"未知函数: {function}",
                "available_functions": [
                    "get_intelligence_package",
                    "crawl_twitter",
                    "track_whale_transfers",
                    "crawl_valuescan",
                    "monitor_kol_accounts",
                    "get_market_overview"
                ]
            }
            
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # 测试API
    async def test():
        # 测试情报包生成
        package = await window3_api.get_intelligence_package(
            symbol="BTC",
            include_window2_data=True,
            analysis_depth="deep"
        )
        print(json.dumps(package, indent=2, ensure_ascii=False))
        
        # 测试巨鲸追踪
        whales = await window3_api.track_whale_transfers(
            min_amount_usd=100000,
            chains=["BTC", "ETH"]
        )
        print(f"\n发现 {whales['total_count']} 笔巨鲸转账")
    
    asyncio.run(test())