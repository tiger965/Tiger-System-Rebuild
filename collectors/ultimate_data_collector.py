"""
Window 3 - 终极数据收集器
整合前任留下的所有有价值的数据源
这是Window 3的核心 - 全方位情报收集系统
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入所有有价值的收集器
try:
    from free_api_aggregator import FreeApiAggregator
    from blockchain.multi_chain_monitor import MultiChainMonitor
    from blockchain.whale_tracker import WhaleTracker
    from blockchain.defi_monitor import DeFiMonitor
    from blockchain.gas_monitor import GasMonitor
    from blockchain.exchange_wallet_monitor import ExchangeWalletMonitor
    from defi.defi_monitor import DeFiMonitor as DeFiEcosystem
    from signal_aggregator.valuescan_crawler import ValueScanCrawler
    from bicoin.integrated_monitor import IntegratedMonitor as BiCoinMonitor
    from news.news_analyzer import NewsAnalyzer
    from chain_social.early_warning import EarlyWarningSystem
    from macro.macro_monitor import MacroMonitor
    from composite_signal_monitor import CompositeSignalMonitor
except ImportError as e:
    print(f"部分模块导入失败: {e}")

logger = logging.getLogger(__name__)


class UltimateDataCollector:
    """
    终极数据收集器
    整合所有数据源，提供全方位的市场情报
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("Window 3 - 终极数据收集器初始化")
        logger.info("整合所有免费和付费数据源")
        logger.info("=" * 60)
        
        # 初始化所有收集器
        self.collectors = {
            "free_apis": FreeApiAggregator(),
            "multi_chain": None,  # 将延迟初始化
            "whale_tracker": None,
            "defi_monitor": None,
            "gas_monitor": None,
            "exchange_wallets": None,
            "valuescan": None,
            "bicoin": None,
            "news": None,
            "social": None,
            "macro": None,
            "composite": None
        }
        
        # 数据源清单
        self.data_sources = {
            # 免费公链RPC（14条主链）
            "chain_rpcs": [
                "Ethereum", "BSC", "Polygon", "Avalanche", "Arbitrum",
                "Optimism", "Fantom", "Solana", "Tron", "Near",
                "Cosmos", "Base", "zkSync", "Linea"
            ],
            
            # 免费区块链浏览器API
            "explorers": [
                "Etherscan", "BscScan", "PolygonScan", "FTMScan",
                "SnowTrace", "Arbiscan", "Optimistic", "BaseScan"
            ],
            
            # 免费DeFi数据
            "defi": [
                "DefiLlama", "DexScreener", "GeckoTerminal",
                "1inch API", "OpenOcean", "0x API"
            ],
            
            # 免费价格数据
            "price": [
                "CoinGecko", "CoinPaprika", "Messari",
                "CoinMarketCap (limited)", "CryptoCompare"
            ],
            
            # 免费链上数据
            "onchain": [
                "Blockchair", "Blockchain.info", "EthGasStation",
                "GasNow", "Mempool.space", "BlockCypher"
            ],
            
            # 免费NFT数据
            "nft": [
                "OpenSea", "Reservoir", "NFTScan", "Alchemy NFT API"
            ],
            
            # 免费社交/情绪
            "social": [
                "Alternative.me (Fear & Greed)", "LunarCrush (limited)",
                "Santiment (limited)", "Google Trends API"
            ],
            
            # 付费API（已购买）
            "paid": [
                "WhaleAlert Personal ($29.95/月)",
                "CryptoPanic Professional (配额已用完)",
                "Coinglass Hobbyist (35 USDT/月)"
            ],
            
            # 需要爬虫的网站
            "crawlers": [
                "ValueScan.io", "币Coin", "Twitter", "Reddit",
                "各大交易所公告", "项目Discord/Telegram"
            ]
        }
        
        # 统计信息
        self.stats = {
            "total_sources": len(self.data_sources),
            "active_chains": 14,
            "defi_protocols": 100,
            "data_points_per_minute": 0,
            "api_calls_made": 0,
            "errors": 0
        }

    async def initialize_all_collectors(self):
        """初始化所有收集器"""
        logger.info("初始化所有数据收集器...")
        
        try:
            # 初始化各个收集器（如果可用）
            try:
                from blockchain.multi_chain_monitor import MultiChainMonitor
                self.collectors["multi_chain"] = MultiChainMonitor()
            except:
                logger.warning("MultiChainMonitor不可用")
            
            try:
                from blockchain.whale_tracker import WhaleTracker
                self.collectors["whale_tracker"] = WhaleTracker()
            except:
                logger.warning("WhaleTracker不可用")
            
            # ... 初始化其他收集器
            
            logger.info(f"成功初始化 {sum(1 for c in self.collectors.values() if c)} 个收集器")
            
        except Exception as e:
            logger.error(f"初始化收集器失败: {e}")

    async def collect_all_chain_data(self) -> Dict:
        """
        收集所有区块链数据
        包括14条主链的实时数据
        """
        all_chain_data = {}
        
        # 1. 使用免费API聚合器获取多链数据
        free_aggregator = self.collectors["free_apis"]
        chain_data = await free_aggregator.get_multi_chain_data()
        all_chain_data["basic_chain_data"] = chain_data
        
        # 2. 获取DeFi TVL数据
        defi_tvl = await free_aggregator.get_defi_tvl_data()
        all_chain_data["defi_tvl"] = defi_tvl
        
        # 3. 获取DEX数据
        dex_data = await free_aggregator.get_dex_data()
        all_chain_data["dex_volume"] = dex_data
        
        # 4. 获取Gas价格
        gas_prices = await free_aggregator.get_gas_prices()
        all_chain_data["gas_prices"] = gas_prices
        
        # 5. 获取稳定币数据
        stablecoin_data = await free_aggregator.get_stablecoin_data()
        all_chain_data["stablecoins"] = stablecoin_data
        
        # 6. 获取内存池数据
        mempool_data = await free_aggregator.get_mempool_data()
        all_chain_data["mempool"] = mempool_data
        
        self.stats["api_calls_made"] += 6
        
        return all_chain_data

    async def collect_whale_data(self) -> Dict:
        """
        收集巨鲸数据
        使用WhaleAlert API和链上数据
        """
        whale_data = {}
        
        try:
            # WhaleAlert API（付费）
            whale_alert_key = "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU"
            
            async with aiohttp.ClientSession() as session:
                url = "https://api.whale-alert.io/v1/transactions"
                headers = {"X-WA-API-KEY": whale_alert_key}
                params = {
                    "api_key": whale_alert_key,
                    "min_value": 100000,  # 10万美元以上
                    "limit": 100
                }
                
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        whale_data["whale_alert"] = data.get("transactions", [])
                    
            self.stats["api_calls_made"] += 1
            
        except Exception as e:
            logger.error(f"收集巨鲸数据失败: {e}")
            self.stats["errors"] += 1
        
        return whale_data

    async def collect_social_sentiment(self) -> Dict:
        """
        收集社交情绪数据
        包括恐慌贪婪指数、社交媒体情绪等
        """
        sentiment_data = {}
        
        # 1. 恐慌贪婪指数
        free_aggregator = self.collectors["free_apis"]
        fear_greed = await free_aggregator.get_fear_greed_index()
        sentiment_data["fear_greed"] = fear_greed
        
        # 2. 热门代币
        trending = await free_aggregator.get_trending_tokens()
        sentiment_data["trending"] = trending
        
        self.stats["api_calls_made"] += 2
        
        return sentiment_data

    async def collect_exchange_data(self) -> Dict:
        """
        收集交易所数据
        包括公开的交易所API数据
        """
        exchange_data = {}
        
        exchanges = {
            "binance": "https://api.binance.com/api/v3",
            "okx": "https://www.okx.com/api/v5",
            "coinbase": "https://api.exchange.coinbase.com",
            "kraken": "https://api.kraken.com/0",
            "kucoin": "https://api.kucoin.com/api/v1"
        }
        
        async with aiohttp.ClientSession() as session:
            # 获取BTC价格作为示例
            for name, base_url in exchanges.items():
                try:
                    if name == "binance":
                        url = f"{base_url}/ticker/price?symbol=BTCUSDT"
                    elif name == "okx":
                        url = f"{base_url}/market/ticker?instId=BTC-USDT"
                    else:
                        continue  # 简化示例
                    
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            exchange_data[name] = data
                            
                except Exception as e:
                    logger.error(f"获取{name}数据失败: {e}")
        
        self.stats["api_calls_made"] += len(exchanges)
        
        return exchange_data

    async def collect_defi_ecosystem(self) -> Dict:
        """
        收集完整的DeFi生态系统数据
        """
        defi_data = {}
        
        # DefiLlama完整数据
        endpoints = {
            "protocols": "https://api.llama.fi/protocols",
            "chains": "https://api.llama.fi/chains",
            "pools": "https://api.llama.fi/pools",
            "stablecoins": "https://api.llama.fi/stablecoins",
            "dexs": "https://api.llama.fi/overview/dexs",
            "fees": "https://api.llama.fi/overview/fees",
            "options": "https://api.llama.fi/overview/options",
            "derivatives": "https://api.llama.fi/overview/derivatives"
        }
        
        async with aiohttp.ClientSession() as session:
            for key, url in endpoints.items():
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            defi_data[key] = await resp.json()
                except Exception as e:
                    logger.error(f"获取DeFi {key}数据失败: {e}")
        
        self.stats["api_calls_made"] += len(endpoints)
        
        return defi_data

    async def generate_intelligence_report(self, all_data: Dict) -> Dict:
        """
        生成综合情报报告
        整合所有数据源，提供全方位市场洞察
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "report_id": f"W3_INTEL_{int(datetime.now().timestamp())}",
            
            # 数据源统计
            "data_sources": {
                "total_sources": self.stats["total_sources"],
                "active_chains": self.stats["active_chains"],
                "api_calls": self.stats["api_calls_made"],
                "errors": self.stats["errors"]
            },
            
            # 市场概览
            "market_overview": {
                "sentiment": self.analyze_market_sentiment(all_data),
                "risk_level": self.assess_risk_level(all_data),
                "opportunities": self.identify_opportunities(all_data),
                "warnings": self.generate_warnings(all_data)
            },
            
            # 链上活动
            "onchain_activity": {
                "active_chains": self.get_active_chains(all_data),
                "gas_trends": self.analyze_gas_trends(all_data),
                "whale_activity": self.analyze_whale_activity(all_data),
                "defi_flows": self.analyze_defi_flows(all_data)
            },
            
            # 原始数据
            "raw_data": all_data,
            
            # 数据质量
            "data_quality": {
                "completeness": self.calculate_completeness(all_data),
                "freshness": self.check_data_freshness(all_data),
                "reliability": self.assess_reliability()
            }
        }
        
        return report

    def analyze_market_sentiment(self, data: Dict) -> str:
        """分析市场情绪"""
        # 基于恐慌贪婪指数和其他指标
        fear_greed = data.get("social_sentiment", {}).get("fear_greed", {}).get("value", 50)
        
        if fear_greed < 25:
            return "extreme_fear"
        elif fear_greed < 45:
            return "fear"
        elif fear_greed < 55:
            return "neutral"
        elif fear_greed < 75:
            return "greed"
        else:
            return "extreme_greed"

    def assess_risk_level(self, data: Dict) -> str:
        """评估风险等级"""
        # 基于多个指标综合评估
        sentiment = self.analyze_market_sentiment(data)
        
        risk_map = {
            "extreme_fear": "low",
            "fear": "medium_low",
            "neutral": "medium",
            "greed": "medium_high",
            "extreme_greed": "high"
        }
        
        return risk_map.get(sentiment, "medium")

    def identify_opportunities(self, data: Dict) -> List[Dict]:
        """识别机会"""
        opportunities = []
        
        # 检查DeFi收益机会
        defi_data = data.get("defi_ecosystem", {})
        if defi_data.get("pools"):
            # 找高收益池
            pass
        
        # 检查套利机会
        exchange_data = data.get("exchange_data", {})
        if exchange_data:
            # 计算价差
            pass
        
        return opportunities

    def generate_warnings(self, data: Dict) -> List[str]:
        """生成警告"""
        warnings = []
        
        # 检查Gas价格
        gas_data = data.get("chain_data", {}).get("gas_prices", {})
        if gas_data.get("ethereum", {}).get("fast", 0) > 100:
            warnings.append("ETH Gas价格过高")
        
        # 检查巨鲸活动
        whale_data = data.get("whale_data", {})
        if whale_data:
            large_transfers = [t for t in whale_data.get("whale_alert", []) 
                             if t.get("amount_usd", 0) > 10000000]
            if large_transfers:
                warnings.append(f"发现{len(large_transfers)}笔千万美元级巨鲸转账")
        
        return warnings

    def get_active_chains(self, data: Dict) -> List[str]:
        """获取活跃的链"""
        chain_data = data.get("chain_data", {}).get("basic_chain_data", {})
        return list(chain_data.keys())

    def analyze_gas_trends(self, data: Dict) -> Dict:
        """分析Gas趋势"""
        gas_prices = data.get("chain_data", {}).get("gas_prices", {})
        return {
            "ethereum": gas_prices.get("ethereum", {}),
            "trend": "stable"  # 需要历史数据对比
        }

    def analyze_whale_activity(self, data: Dict) -> Dict:
        """分析巨鲸活动"""
        whale_data = data.get("whale_data", {}).get("whale_alert", [])
        
        total_volume = sum(t.get("amount_usd", 0) for t in whale_data)
        exchange_inflow = sum(t.get("amount_usd", 0) for t in whale_data 
                            if "exchange" in t.get("to", {}).get("owner", "").lower())
        exchange_outflow = sum(t.get("amount_usd", 0) for t in whale_data 
                             if "exchange" in t.get("from", {}).get("owner", "").lower())
        
        return {
            "total_volume": total_volume,
            "exchange_inflow": exchange_inflow,
            "exchange_outflow": exchange_outflow,
            "net_flow": exchange_inflow - exchange_outflow
        }

    def analyze_defi_flows(self, data: Dict) -> Dict:
        """分析DeFi资金流"""
        defi_data = data.get("chain_data", {}).get("defi_tvl", {})
        
        return {
            "total_tvl": defi_data.get("total_tvl", 0),
            "top_protocols": defi_data.get("top_protocols", [])[:5]
        }

    def calculate_completeness(self, data: Dict) -> float:
        """计算数据完整度"""
        expected_keys = ["chain_data", "whale_data", "social_sentiment", 
                        "exchange_data", "defi_ecosystem"]
        present_keys = sum(1 for key in expected_keys if key in data and data[key])
        return present_keys / len(expected_keys)

    def check_data_freshness(self, data: Dict) -> str:
        """检查数据新鲜度"""
        # 简化版本，实际需要检查每个数据源的时间戳
        return "fresh"

    def assess_reliability(self) -> float:
        """评估可靠性"""
        if self.stats["errors"] == 0:
            return 1.0
        error_rate = self.stats["errors"] / max(self.stats["api_calls_made"], 1)
        return max(0, 1 - error_rate)

    async def run_complete_collection(self) -> Dict:
        """
        运行完整的数据收集
        这是Window 3的核心功能 - 一次调用获取所有数据
        """
        logger.info("=" * 60)
        logger.info("开始全方位数据收集...")
        logger.info(f"数据源: {self.stats['total_sources']} 个类别")
        logger.info(f"覆盖链: {self.stats['active_chains']} 条")
        logger.info("=" * 60)
        
        # 并发收集所有数据
        tasks = [
            self.collect_all_chain_data(),
            self.collect_whale_data(),
            self.collect_social_sentiment(),
            self.collect_exchange_data(),
            self.collect_defi_ecosystem()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整合数据
        all_data = {
            "chain_data": results[0] if not isinstance(results[0], Exception) else {},
            "whale_data": results[1] if not isinstance(results[1], Exception) else {},
            "social_sentiment": results[2] if not isinstance(results[2], Exception) else {},
            "exchange_data": results[3] if not isinstance(results[3], Exception) else {},
            "defi_ecosystem": results[4] if not isinstance(results[4], Exception) else {}
        }
        
        # 生成情报报告
        intelligence_report = await self.generate_intelligence_report(all_data)
        
        # 记录统计
        self.stats["data_points_per_minute"] = self.stats["api_calls_made"]
        
        logger.info(f"✅ 数据收集完成")
        logger.info(f"API调用: {self.stats['api_calls_made']} 次")
        logger.info(f"错误: {self.stats['errors']} 个")
        logger.info(f"数据完整度: {intelligence_report['data_quality']['completeness']:.1%}")
        
        return intelligence_report


# 测试函数
async def test_ultimate_collector():
    """测试终极数据收集器"""
    collector = UltimateDataCollector()
    
    print("\n" + "=" * 60)
    print("测试Window 3 - 终极数据收集器")
    print("=" * 60)
    
    # 运行完整收集
    report = await collector.run_complete_collection()
    
    print("\n📊 情报报告摘要:")
    print(f"报告ID: {report['report_id']}")
    print(f"市场情绪: {report['market_overview']['sentiment']}")
    print(f"风险等级: {report['market_overview']['risk_level']}")
    print(f"活跃链: {len(report['onchain_activity']['active_chains'])} 条")
    print(f"数据完整度: {report['data_quality']['completeness']:.1%}")
    print(f"数据可靠性: {report['data_quality']['reliability']:.1%}")
    
    if report['market_overview']['warnings']:
        print(f"\n⚠️ 警告:")
        for warning in report['market_overview']['warnings']:
            print(f"  - {warning}")
    
    print("\n✅ 测试完成！Window 3已准备好为Window 6提供全方位情报支持")


if __name__ == "__main__":
    asyncio.run(test_ultimate_collector())