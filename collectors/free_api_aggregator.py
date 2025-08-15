"""
Window 3 - 免费API聚合器
整合所有免费的公链API、DeFi数据、链上数据等
这是Window 3的核心价值之一 - 免费获取全方位数据
"""

import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class FreeApiAggregator:
    """
    免费API聚合器
    整合所有可用的免费数据源
    """
    
    def __init__(self):
        # 所有免费的公链RPC节点
        self.chain_rpcs = {
            "ethereum": [
                "https://eth.drpc.org",
                "https://rpc.ankr.com/eth",
                "https://ethereum.publicnode.com",
                "https://eth.llamarpc.com",
                "https://cloudflare-eth.com"
            ],
            "bsc": [
                "https://bsc-dataseed.binance.org",
                "https://bsc-dataseed1.defibit.io",
                "https://bsc-dataseed1.ninicoin.io",
                "https://rpc.ankr.com/bsc"
            ],
            "polygon": [
                "https://polygon-rpc.com",
                "https://rpc.ankr.com/polygon",
                "https://matic-mainnet.chainstacklabs.com",
                "https://polygon.llamarpc.com"
            ],
            "avalanche": [
                "https://api.avax.network/ext/bc/C/rpc",
                "https://rpc.ankr.com/avalanche",
                "https://ava-mainnet.public.blastapi.io/ext/bc/C/rpc"
            ],
            "arbitrum": [
                "https://arb1.arbitrum.io/rpc",
                "https://rpc.ankr.com/arbitrum",
                "https://arbitrum.llamarpc.com"
            ],
            "optimism": [
                "https://mainnet.optimism.io",
                "https://rpc.ankr.com/optimism",
                "https://optimism.llamarpc.com"
            ],
            "fantom": [
                "https://rpc.ftm.tools",
                "https://rpc.ankr.com/fantom",
                "https://fantom.publicnode.com"
            ],
            "solana": [
                "https://api.mainnet-beta.solana.com",
                "https://solana-api.projectserum.com",
                "https://rpc.ankr.com/solana"
            ],
            "tron": [
                "https://api.trongrid.io",
                "https://api.tronstack.io"
            ],
            "near": [
                "https://rpc.mainnet.near.org",
                "https://rpc.ankr.com/near"
            ],
            "cosmos": [
                "https://cosmos-rpc.quickapi.com:443",
                "https://rpc-cosmoshub.blockapsis.com"
            ],
            "base": [
                "https://mainnet.base.org",
                "https://base.llamarpc.com"
            ],
            "zksync": [
                "https://mainnet.era.zksync.io",
                "https://zksync.drpc.org"
            ]
        }
        
        # 免费的区块链浏览器API
        self.explorer_apis = {
            "etherscan": "https://api.etherscan.io/api",
            "bscscan": "https://api.bscscan.com/api",
            "polygonscan": "https://api.polygonscan.com/api",
            "ftmscan": "https://api.ftmscan.com/api",
            "snowtrace": "https://api.snowtrace.io/api",
            "arbiscan": "https://api.arbiscan.io/api",
            "optimistic": "https://api-optimistic.etherscan.io/api",
            "basescan": "https://api.basescan.org/api"
        }
        
        # 免费的DeFi数据API
        self.defi_apis = {
            "defillama": {
                "base": "https://api.llama.fi",
                "tvl": "/tvl",
                "protocols": "/protocols",
                "chains": "/chains",
                "yields": "/pools",
                "stablecoins": "/stablecoins",
                "volumes": "/overview/dexs",
                "fees": "/overview/fees",
                "bridged": "/bridgedVolume"
            },
            "dexscreener": {
                "base": "https://api.dexscreener.com/latest",
                "pairs": "/dex/pairs",
                "tokens": "/dex/tokens",
                "search": "/dex/search"
            },
            "geckoterminal": {
                "base": "https://api.geckoterminal.com/api/v2",
                "trending": "/networks/trending_pools",
                "new_pools": "/networks/new_pools"
            }
        }
        
        # 免费的价格API
        self.price_apis = {
            "coingecko": {
                "base": "https://api.coingecko.com/api/v3",
                "price": "/simple/price",
                "market": "/coins/markets",
                "trending": "/search/trending",
                "global": "/global",
                "defi": "/global/decentralized_finance_defi"
            },
            "coinpaprika": {
                "base": "https://api.coinpaprika.com/v1",
                "tickers": "/tickers",
                "global": "/global"
            },
            "messari": {
                "base": "https://data.messari.io/api/v1",
                "assets": "/assets"
            }
        }
        
        # 免费的链上数据API
        self.onchain_apis = {
            "blockchair": {
                "base": "https://api.blockchair.com",
                "bitcoin": "/bitcoin/stats",
                "ethereum": "/ethereum/stats"
            },
            "blockchain_info": {
                "base": "https://blockchain.info",
                "stats": "/stats",
                "mempool": "/unconfirmed-transactions",
                "blocks": "/latestblock"
            },
            "ethgasstation": {
                "base": "https://api.ethgasstation.info",
                "gas": "/api/ethgasAPI.json"
            },
            "gasnow": {
                "base": "https://www.gasnow.org/api/v3",
                "gas": "/gas/price"
            }
        }
        
        # 免费的NFT数据API
        self.nft_apis = {
            "opensea": {
                "base": "https://api.opensea.io/api/v1",
                "stats": "/collection/{collection}/stats"
            },
            "reservoir": {
                "base": "https://api.reservoir.tools",
                "collections": "/collections/v5",
                "sales": "/sales/v4"
            }
        }
        
        # 免费的社交/情绪数据
        self.social_apis = {
            "alternative": {
                "base": "https://api.alternative.me",
                "fear_greed": "/fng/",
                "crypto_index": "/crypto/"
            },
            "lunarcrush": {
                "base": "https://lunarcrush.com/api3",
                "market": "/coins"  # 需要免费注册获取API key
            },
            "santiment": {
                "base": "https://api.santiment.net/graphql",
                "social_volume": "socialVolume"
            }
        }

    async def get_multi_chain_data(self) -> Dict:
        """
        获取所有主链的基础数据
        """
        chain_data = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 并发获取所有链的数据
            for chain, rpcs in self.chain_rpcs.items():
                if chain not in ["solana", "tron", "near", "cosmos"]:  # EVM链
                    tasks.append(self.get_evm_chain_data(session, chain, rpcs))
                else:
                    tasks.append(self.get_non_evm_chain_data(session, chain, rpcs))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    chain_data.update(result)
        
        return chain_data

    async def get_evm_chain_data(self, session: aiohttp.ClientSession, 
                                 chain: str, rpcs: List[str]) -> Dict:
        """获取EVM链数据"""
        for rpc in rpcs:
            try:
                # 获取最新区块
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                
                async with session.post(rpc, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        block_number = int(data.get("result", "0x0"), 16)
                        
                        # 获取Gas价格
                        gas_payload = {
                            "jsonrpc": "2.0",
                            "method": "eth_gasPrice",
                            "params": [],
                            "id": 2
                        }
                        
                        async with session.post(rpc, json=gas_payload, timeout=5) as gas_resp:
                            gas_data = await gas_resp.json()
                            gas_price = int(gas_data.get("result", "0x0"), 16) / 1e9  # 转换为Gwei
                        
                        return {
                            chain: {
                                "block_height": block_number,
                                "gas_price_gwei": gas_price,
                                "rpc_used": rpc,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
            except Exception as e:
                continue
        
        return {chain: {"error": "所有RPC节点失败"}}

    async def get_non_evm_chain_data(self, session: aiohttp.ClientSession,
                                     chain: str, rpcs: List[str]) -> Dict:
        """获取非EVM链数据"""
        if chain == "solana":
            return await self.get_solana_data(session, rpcs)
        elif chain == "tron":
            return await self.get_tron_data(session, rpcs)
        else:
            return {chain: {"status": "暂未实现"}}

    async def get_solana_data(self, session: aiohttp.ClientSession, rpcs: List[str]) -> Dict:
        """获取Solana数据"""
        for rpc in rpcs:
            try:
                # 获取最新槽位
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getSlot",
                    "params": [],
                    "id": 1
                }
                
                async with session.post(rpc, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        slot = data.get("result", 0)
                        
                        return {
                            "solana": {
                                "slot": slot,
                                "rpc_used": rpc,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
            except:
                continue
        
        return {"solana": {"error": "RPC失败"}}

    async def get_tron_data(self, session: aiohttp.ClientSession, rpcs: List[str]) -> Dict:
        """获取Tron数据"""
        for rpc in rpcs:
            try:
                async with session.get(f"{rpc}/wallet/getnowblock", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "tron": {
                                "block_height": data.get("block_header", {}).get("raw_data", {}).get("number", 0),
                                "rpc_used": rpc,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
            except:
                continue
        
        return {"tron": {"error": "RPC失败"}}

    async def get_defi_tvl_data(self) -> Dict:
        """获取DeFi TVL数据"""
        async with aiohttp.ClientSession() as session:
            try:
                # 获取所有协议TVL
                url = f"{self.defi_apis['defillama']['base']}/protocols"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # 提取前20个协议
                        top_protocols = []
                        for protocol in data[:20]:
                            top_protocols.append({
                                "name": protocol.get("name"),
                                "tvl": protocol.get("tvl", 0),
                                "chain": protocol.get("chain", "Multi-Chain"),
                                "category": protocol.get("category", "Unknown"),
                                "change_24h": protocol.get("change_1d", 0)
                            })
                        
                        # 获取链TVL
                        chains_url = f"{self.defi_apis['defillama']['base']}/chains"
                        async with session.get(chains_url, timeout=10) as chains_resp:
                            if chains_resp.status == 200:
                                chains_data = await chains_resp.json()
                                
                                return {
                                    "total_tvl": sum(p["tvl"] for p in top_protocols),
                                    "top_protocols": top_protocols,
                                    "chain_tvl": chains_data[:10],  # 前10条链
                                    "timestamp": datetime.now().isoformat()
                                }
            except Exception as e:
                logger.error(f"获取DeFi TVL失败: {e}")
        
        return {}

    async def get_dex_data(self) -> Dict:
        """获取DEX数据"""
        async with aiohttp.ClientSession() as session:
            try:
                # 获取DEX交易量
                url = f"{self.defi_apis['defillama']['base']}/overview/dexs"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        return {
                            "total_volume_24h": data.get("totalVolume", 0),
                            "top_dexs": data.get("protocols", [])[:10],
                            "timestamp": datetime.now().isoformat()
                        }
            except Exception as e:
                logger.error(f"获取DEX数据失败: {e}")
        
        return {}

    async def get_gas_prices(self) -> Dict:
        """获取各链Gas价格"""
        gas_data = {}
        
        async with aiohttp.ClientSession() as session:
            # 以太坊Gas
            try:
                async with session.get(self.onchain_apis["ethgasstation"]["base"] + 
                                      self.onchain_apis["ethgasstation"]["gas"], 
                                      timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        gas_data["ethereum"] = {
                            "fast": data.get("fast", 0) / 10,  # 转换为Gwei
                            "average": data.get("average", 0) / 10,
                            "slow": data.get("safeLow", 0) / 10
                        }
            except:
                pass
            
            # 其他链的Gas通过RPC获取（已在get_multi_chain_data中实现）
            
        return gas_data

    async def get_trending_tokens(self) -> Dict:
        """获取热门代币"""
        async with aiohttp.ClientSession() as session:
            try:
                # CoinGecko热门
                url = f"{self.price_apis['coingecko']['base']}/search/trending"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        trending = []
                        for coin in data.get("coins", []):
                            item = coin.get("item", {})
                            trending.append({
                                "name": item.get("name"),
                                "symbol": item.get("symbol"),
                                "market_cap_rank": item.get("market_cap_rank"),
                                "price_btc": item.get("price_btc"),
                                "score": item.get("score", 0)
                            })
                        
                        return {
                            "trending_coins": trending,
                            "timestamp": datetime.now().isoformat()
                        }
            except Exception as e:
                logger.error(f"获取热门代币失败: {e}")
        
        return {}

    async def get_stablecoin_data(self) -> Dict:
        """获取稳定币数据"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.defi_apis['defillama']['base']}/stablecoins"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        stablecoins = []
                        for stable in data.get("peggedAssets", [])[:10]:
                            stablecoins.append({
                                "name": stable.get("name"),
                                "symbol": stable.get("symbol"),
                                "circulating": stable.get("circulating", {}).get("total", 0),
                                "chains": list(stable.get("circulating", {}).keys())
                            })
                        
                        return {
                            "total_stablecoin_supply": sum(s["circulating"] for s in stablecoins),
                            "top_stablecoins": stablecoins,
                            "timestamp": datetime.now().isoformat()
                        }
            except Exception as e:
                logger.error(f"获取稳定币数据失败: {e}")
        
        return {}

    async def get_fear_greed_index(self) -> Dict:
        """获取恐慌贪婪指数"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.social_apis['alternative']['base']}/fng/"
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("data"):
                            current = data["data"][0]
                            return {
                                "value": int(current["value"]),
                                "classification": current["value_classification"],
                                "timestamp": current["timestamp"]
                            }
            except Exception as e:
                logger.error(f"获取恐慌贪婪指数失败: {e}")
        
        return {"value": 50, "classification": "Neutral"}

    async def get_mempool_data(self) -> Dict:
        """获取内存池数据"""
        mempool_data = {}
        
        async with aiohttp.ClientSession() as session:
            # 比特币内存池
            try:
                url = f"{self.onchain_apis['blockchain_info']['base']}/unconfirmed-transactions?format=json"
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        mempool_data["bitcoin"] = {
                            "tx_count": len(data.get("txs", [])),
                            "size_mb": sum(tx.get("size", 0) for tx in data.get("txs", [])) / 1024 / 1024
                        }
            except:
                pass
        
        return mempool_data

    async def aggregate_all_free_data(self) -> Dict:
        """
        聚合所有免费数据源
        这是Window 3的核心价值 - 一次调用获取全方位数据
        """
        logger.info("开始聚合所有免费数据源...")
        
        # 并发获取所有数据
        tasks = [
            self.get_multi_chain_data(),
            self.get_defi_tvl_data(),
            self.get_dex_data(),
            self.get_gas_prices(),
            self.get_trending_tokens(),
            self.get_stablecoin_data(),
            self.get_fear_greed_index(),
            self.get_mempool_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整合所有数据
        aggregated_data = {
            "timestamp": datetime.now().isoformat(),
            "data_sources": {
                "multi_chain": results[0] if not isinstance(results[0], Exception) else {},
                "defi_tvl": results[1] if not isinstance(results[1], Exception) else {},
                "dex_volume": results[2] if not isinstance(results[2], Exception) else {},
                "gas_prices": results[3] if not isinstance(results[3], Exception) else {},
                "trending": results[4] if not isinstance(results[4], Exception) else {},
                "stablecoins": results[5] if not isinstance(results[5], Exception) else {},
                "fear_greed": results[6] if not isinstance(results[6], Exception) else {},
                "mempool": results[7] if not isinstance(results[7], Exception) else {}
            },
            "summary": self.generate_summary(results)
        }
        
        logger.info(f"数据聚合完成，包含 {len(aggregated_data['data_sources'])} 个数据源")
        
        return aggregated_data

    def generate_summary(self, results: List) -> Dict:
        """生成数据摘要"""
        summary = {
            "data_quality": "good",
            "active_chains": 0,
            "total_defi_tvl": 0,
            "market_sentiment": "neutral"
        }
        
        # 统计活跃的链
        if not isinstance(results[0], Exception):
            summary["active_chains"] = len(results[0])
        
        # DeFi TVL
        if not isinstance(results[1], Exception) and results[1]:
            summary["total_defi_tvl"] = results[1].get("total_tvl", 0)
        
        # 市场情绪
        if not isinstance(results[6], Exception) and results[6]:
            fg_value = results[6].get("value", 50)
            if fg_value < 25:
                summary["market_sentiment"] = "extreme_fear"
            elif fg_value < 45:
                summary["market_sentiment"] = "fear"
            elif fg_value < 55:
                summary["market_sentiment"] = "neutral"
            elif fg_value < 75:
                summary["market_sentiment"] = "greed"
            else:
                summary["market_sentiment"] = "extreme_greed"
        
        return summary


# 测试函数
async def test_free_apis():
    """测试免费API聚合器"""
    aggregator = FreeApiAggregator()
    
    print("=" * 60)
    print("测试免费API聚合器")
    print("=" * 60)
    
    # 测试多链数据
    print("\n1. 测试多链数据...")
    chain_data = await aggregator.get_multi_chain_data()
    for chain, data in chain_data.items():
        if "error" not in data:
            print(f"  {chain}: 区块高度 {data.get('block_height', 'N/A')}")
    
    # 测试DeFi数据
    print("\n2. 测试DeFi TVL...")
    defi_data = await aggregator.get_defi_tvl_data()
    if defi_data:
        print(f"  总TVL: ${defi_data.get('total_tvl', 0):,.0f}")
        print(f"  顶级协议数: {len(defi_data.get('top_protocols', []))}")
    
    # 测试恐慌贪婪指数
    print("\n3. 测试恐慌贪婪指数...")
    fg_index = await aggregator.get_fear_greed_index()
    print(f"  指数: {fg_index.get('value')} - {fg_index.get('classification')}")
    
    # 测试完整聚合
    print("\n4. 测试完整数据聚合...")
    all_data = await aggregator.aggregate_all_free_data()
    print(f"  数据源数量: {len(all_data['data_sources'])}")
    print(f"  市场情绪: {all_data['summary']['market_sentiment']}")
    print(f"  活跃链数: {all_data['summary']['active_chains']}")
    
    print("\n✅ 所有免费API测试完成！")


if __name__ == "__main__":
    asyncio.run(test_free_apis())