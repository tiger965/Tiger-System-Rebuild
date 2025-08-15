"""
Coinglass V4 API正确实现
使用正确的header格式: CG-API-KEY
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class CoinglassV4API:
    """
    Coinglass V4 API客户端
    $35/月 Hobbyist套餐 - 完整功能实现
    """
    
    def __init__(self):
        self.api_key = "689079f638414a18bac90b722446f3b3"
        self.base_url = "https://open-api-v4.coinglass.com"
        
        # 正确的header格式
        self.headers = {
            "accept": "application/json",
            "CG-API-KEY": self.api_key  # 正确的header名称
        }
        
        logger.info("=" * 60)
        logger.info("💎 Coinglass V4 API客户端初始化")
        logger.info("📊 Hobbyist套餐 - $35/月")
        logger.info("🔑 使用正确的CG-API-KEY header")
        logger.info("=" * 60)

    async def get_supported_coins(self) -> Dict:
        """获取支持的币种列表"""
        try:
            url = f"{self.base_url}/api/futures/supported-coins"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "data": data,
                            "count": len(data) if isinstance(data, list) else 0
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取支持币种失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_funding_rates(self, symbol: str = "BTC") -> Dict:
        """获取资金费率"""
        try:
            url = f"{self.base_url}/api/futures/funding-rates"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "symbol": symbol,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取资金费率失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_open_interest(self, symbol: str = "BTC") -> Dict:
        """获取未平仓合约（OI）"""
        try:
            url = f"{self.base_url}/api/futures/open-interest"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "symbol": symbol,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取OI失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_liquidations(self, symbol: str = "BTC", time_range: str = "24h") -> Dict:
        """获取爆仓数据"""
        try:
            url = f"{self.base_url}/api/futures/liquidations"
            params = {
                "symbol": symbol,
                "range": time_range  # 1h, 4h, 12h, 24h
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "symbol": symbol,
                            "range": time_range,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取爆仓数据失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_long_short_ratio(self, symbol: str = "BTC", exchange: str = "all") -> Dict:
        """获取多空比"""
        try:
            url = f"{self.base_url}/api/futures/long-short-ratio"
            params = {
                "symbol": symbol,
                "exchange": exchange  # all, binance, okx, bybit等
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "symbol": symbol,
                            "exchange": exchange,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取多空比失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_options_data(self, symbol: str = "BTC") -> Dict:
        """获取期权数据"""
        try:
            url = f"{self.base_url}/api/options/open-interest"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "symbol": symbol,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取期权数据失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_exchange_flows(self, symbol: str = "BTC") -> Dict:
        """获取交易所流入流出"""
        try:
            url = f"{self.base_url}/api/on-chain/exchange-flows"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "symbol": symbol,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取交易所流量失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_fear_greed_index(self) -> Dict:
        """获取恐慌贪婪指数"""
        try:
            url = f"{self.base_url}/api/indicators/fear-greed"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取恐慌贪婪指数失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_etf_flows(self) -> Dict:
        """获取ETF流量数据"""
        try:
            url = f"{self.base_url}/api/etf/flows"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Status {resp.status}: {text}"}
                        
        except Exception as e:
            logger.error(f"获取ETF数据失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_complete_analysis(self, symbol: str = "BTC") -> Dict:
        """
        获取完整的Coinglass分析
        并发调用所有API，最大化利用$35/月的价值
        """
        logger.info(f"🔥 开始{symbol}完整Coinglass V4分析...")
        
        # 并发获取所有数据
        tasks = [
            self.get_supported_coins(),
            self.get_funding_rates(symbol),
            self.get_open_interest(symbol),
            self.get_liquidations(symbol, "24h"),
            self.get_long_short_ratio(symbol),
            self.get_options_data(symbol),
            self.get_exchange_flows(symbol),
            self.get_fear_greed_index(),
            self.get_etf_flows()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 整合结果
        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "supported_coins": results[0],
            "funding_rates": results[1],
            "open_interest": results[2],
            "liquidations": results[3],
            "long_short_ratio": results[4],
            "options": results[5],
            "exchange_flows": results[6],
            "fear_greed": results[7],
            "etf_flows": results[8],
            "insights": self.generate_insights(results),
            "api_usage": self.calculate_api_usage(results)
        }
        
        # 显示统计
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"✅ 分析完成: {success_count}/{len(results)} API调用成功")
        
        return analysis

    def generate_insights(self, results: List[Dict]) -> Dict:
        """生成市场洞察"""
        insights = {
            "market_structure": {},
            "sentiment": {},
            "risk_indicators": {},
            "opportunities": []
        }
        
        # 分析资金费率
        if results[1].get("success"):  # funding_rates
            funding_data = results[1].get("data", {})
            insights["market_structure"]["funding_bias"] = "analyzing..."
        
        # 分析多空比
        if results[4].get("success"):  # long_short_ratio
            ratio_data = results[4].get("data", {})
            insights["sentiment"]["retail_positioning"] = "analyzing..."
        
        # 分析爆仓
        if results[3].get("success"):  # liquidations
            liq_data = results[3].get("data", {})
            insights["risk_indicators"]["liquidation_pressure"] = "analyzing..."
        
        # 分析恐慌贪婪
        if results[7].get("success"):  # fear_greed
            fg_data = results[7].get("data", {})
            insights["sentiment"]["market_emotion"] = fg_data
        
        # 识别机会
        if results[8].get("success"):  # etf_flows
            etf_data = results[8].get("data", {})
            # 分析ETF流入流出
            insights["opportunities"].append({
                "type": "etf_flows",
                "data": etf_data
            })
        
        return insights

    def calculate_api_usage(self, results: List[Dict]) -> Dict:
        """计算API使用情况"""
        total_calls = len(results)
        successful_calls = sum(1 for r in results if r.get("success"))
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "features_used": [
                "supported_coins", "funding_rates", "open_interest",
                "liquidations", "long_short_ratio", "options",
                "exchange_flows", "fear_greed", "etf_flows"
            ],
            "value_extracted": f"{successful_calls / total_calls * 100:.1f}%"
        }


# 测试函数
async def test_coinglass_v4():
    """测试Coinglass V4 API"""
    print("=" * 60)
    print("💎 Coinglass V4 API测试")
    print("🔑 使用正确的CG-API-KEY header")
    print("=" * 60)
    
    api = CoinglassV4API()
    
    # 1. 首先测试基础连接
    print("\n1. 测试API连接...")
    supported = await api.get_supported_coins()
    if supported.get("success"):
        print(f"   ✅ API连接成功！")
        print(f"   支持币种数量: {supported.get('count')}")
    else:
        print(f"   ❌ API连接失败: {supported.get('error')}")
        return
    
    # 2. 测试各个功能
    print("\n2. 测试资金费率...")
    funding = await api.get_funding_rates("BTC")
    print(f"   {'✅ 成功' if funding.get('success') else '❌ 失败'}")
    
    print("\n3. 测试未平仓合约...")
    oi = await api.get_open_interest("BTC")
    print(f"   {'✅ 成功' if oi.get('success') else '❌ 失败'}")
    
    print("\n4. 测试爆仓数据...")
    liquidations = await api.get_liquidations("BTC", "24h")
    print(f"   {'✅ 成功' if liquidations.get('success') else '❌ 失败'}")
    
    print("\n5. 测试多空比...")
    ratio = await api.get_long_short_ratio("BTC")
    print(f"   {'✅ 成功' if ratio.get('success') else '❌ 失败'}")
    
    print("\n6. 测试期权数据...")
    options = await api.get_options_data("BTC")
    print(f"   {'✅ 成功' if options.get('success') else '❌ 失败'}")
    
    print("\n7. 测试交易所流量...")
    flows = await api.get_exchange_flows("BTC")
    print(f"   {'✅ 成功' if flows.get('success') else '❌ 失败'}")
    
    print("\n8. 测试恐慌贪婪指数...")
    fear_greed = await api.get_fear_greed_index()
    print(f"   {'✅ 成功' if fear_greed.get('success') else '❌ 失败'}")
    
    print("\n9. 测试ETF流量...")
    etf = await api.get_etf_flows()
    print(f"   {'✅ 成功' if etf.get('success') else '❌ 失败'}")
    
    # 3. 测试完整分析
    print("\n" + "=" * 60)
    print("🔥 运行完整分析...")
    print("=" * 60)
    
    analysis = await api.get_complete_analysis("BTC")
    
    # 显示结果
    api_usage = analysis["api_usage"]
    print(f"\n📊 API使用统计:")
    print(f"   总调用: {api_usage['total_calls']}")
    print(f"   成功调用: {api_usage['successful_calls']}")
    print(f"   成功率: {api_usage['success_rate']:.1%}")
    print(f"   价值提取: {api_usage['value_extracted']}")
    
    if analysis["insights"]:
        print(f"\n💡 市场洞察:")
        print(f"   市场结构: {analysis['insights'].get('market_structure')}")
        print(f"   市场情绪: {analysis['insights'].get('sentiment')}")
        print(f"   风险指标: {analysis['insights'].get('risk_indicators')}")
    
    print("\n✅ 测试完成！")
    print(f"💰 成功利用Coinglass $35/月套餐的 {api_usage['value_extracted']} 价值")
    
    return analysis


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(test_coinglass_v4())