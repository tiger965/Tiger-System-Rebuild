"""
Coinglass API正确实现
基于测试结果调整
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CoinglassAPI:
    """
    Coinglass API客户端
    $35/月 Hobbyist套餐
    """
    
    def __init__(self):
        self.api_key = "689079f638414a18bac90b722446f3b3"
        
        # 基于测试，使用正确的URL
        self.base_url = "https://api.coinglass.com"
        
        # 正确的headers格式
        self.headers = {
            "accept": "application/json",
            "coinglassSecret": self.api_key
        }
        
        logger.info("💎 Coinglass API客户端初始化")
        logger.info("📊 Hobbyist套餐 - $35/月")

    async def get_liquidation_data(self) -> Dict:
        """获取爆仓数据"""
        try:
            url = f"{self.base_url}/api/futures/home/liquidation_coin"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        # 处理text/plain响应
                        text = await resp.text()
                        try:
                            data = json.loads(text)
                            return {
                                "success": True,
                                "data": data,
                                "timestamp": datetime.now().isoformat()
                            }
                        except json.JSONDecodeError:
                            logger.error(f"JSON解析失败: {text[:100]}")
                            return {"success": False, "error": "Invalid JSON"}
                    else:
                        return {"success": False, "error": f"Status {resp.status}"}
                        
        except Exception as e:
            logger.error(f"获取爆仓数据失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_funding_rates(self, symbol: str = "BTC") -> Dict:
        """获取资金费率"""
        try:
            # 尝试不同的端点
            endpoints = [
                f"/api/futures/funding-rates-chart",
                f"/api/futures/funding_rates_chart",
                f"/api/pro/v1/futures/funding-rates-chart"
            ]
            
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    url = f"{self.base_url}{endpoint}"
                    params = {"symbol": symbol}
                    
                    try:
                        async with session.get(
                            url, 
                            headers=self.headers,
                            params=params,
                            timeout=5
                        ) as resp:
                            if resp.status == 200:
                                content_type = resp.headers.get('content-type', '')
                                
                                if 'json' in content_type:
                                    data = await resp.json()
                                else:
                                    text = await resp.text()
                                    data = json.loads(text)
                                
                                return {
                                    "success": True,
                                    "endpoint": endpoint,
                                    "data": data
                                }
                    except Exception as e:
                        continue
                
                return {"success": False, "error": "All endpoints failed"}
                
        except Exception as e:
            logger.error(f"获取资金费率失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_open_interest(self, symbol: str = "BTC") -> Dict:
        """获取未平仓合约"""
        try:
            url = f"{self.base_url}/api/futures/open-interest-chart"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            data = json.loads(text)
                            return {
                                "success": True,
                                "data": data
                            }
                        except:
                            return {"success": False, "error": "JSON parse error"}
                    else:
                        return {"success": False, "error": f"Status {resp.status}"}
                        
        except Exception as e:
            logger.error(f"获取OI失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_long_short_ratio(self, symbol: str = "BTC") -> Dict:
        """获取多空比"""
        try:
            url = f"{self.base_url}/api/futures/long-short-chart"
            params = {"symbol": symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            data = json.loads(text)
                            return {
                                "success": True,
                                "data": data
                            }
                        except:
                            return {"success": False, "error": "JSON parse error"}
                    else:
                        return {"success": False, "error": f"Status {resp.status}"}
                        
        except Exception as e:
            logger.error(f"获取多空比失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_all_data(self, symbol: str = "BTC") -> Dict:
        """获取所有可用数据"""
        logger.info(f"🔥 获取{symbol}完整Coinglass数据...")
        
        # 并发获取所有数据
        tasks = [
            self.get_liquidation_data(),
            self.get_funding_rates(symbol),
            self.get_open_interest(symbol),
            self.get_long_short_ratio(symbol)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 整合结果
        all_data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "liquidations": results[0],
            "funding_rates": results[1],
            "open_interest": results[2],
            "long_short_ratio": results[3],
            "summary": self.generate_summary(results)
        }
        
        # 统计成功率
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"✅ 数据获取完成: {success_count}/4 成功")
        
        return all_data

    def generate_summary(self, results: list) -> Dict:
        """生成数据摘要"""
        summary = {
            "data_quality": "unknown",
            "market_sentiment": "neutral",
            "key_metrics": {}
        }
        
        # 检查数据质量
        success_count = sum(1 for r in results if r.get("success"))
        if success_count == len(results):
            summary["data_quality"] = "excellent"
        elif success_count >= len(results) * 0.7:
            summary["data_quality"] = "good"
        elif success_count >= len(results) * 0.5:
            summary["data_quality"] = "fair"
        else:
            summary["data_quality"] = "poor"
        
        # 分析市场情绪（如果有数据）
        if results[3].get("success"):  # 多空比
            # 这里可以加入更复杂的分析逻辑
            summary["market_sentiment"] = "analyzing..."
        
        return summary


# 测试函数
async def test_coinglass():
    """测试Coinglass API"""
    print("=" * 60)
    print("测试Coinglass API - 正确实现")
    print("=" * 60)
    
    api = CoinglassAPI()
    
    # 测试各个功能
    print("\n1. 测试爆仓数据...")
    liquidation = await api.get_liquidation_data()
    print(f"   状态: {'✅ 成功' if liquidation.get('success') else '❌ 失败'}")
    if liquidation.get("success"):
        print(f"   数据: {str(liquidation.get('data', ''))[:100]}...")
    
    print("\n2. 测试资金费率...")
    funding = await api.get_funding_rates("BTC")
    print(f"   状态: {'✅ 成功' if funding.get('success') else '❌ 失败'}")
    if funding.get("success"):
        print(f"   使用端点: {funding.get('endpoint')}")
    
    print("\n3. 测试未平仓合约...")
    oi = await api.get_open_interest("BTC")
    print(f"   状态: {'✅ 成功' if oi.get('success') else '❌ 失败'}")
    
    print("\n4. 测试多空比...")
    ratio = await api.get_long_short_ratio("BTC")
    print(f"   状态: {'✅ 成功' if ratio.get('success') else '❌ 失败'}")
    
    print("\n5. 测试完整数据获取...")
    all_data = await api.get_all_data("BTC")
    print(f"   数据质量: {all_data['summary']['data_quality']}")
    
    # 统计
    success_apis = sum(1 for key in ["liquidations", "funding_rates", "open_interest", "long_short_ratio"]
                      if all_data[key].get("success"))
    
    print(f"\n📊 测试结果: {success_apis}/4 个API可用")
    print("✅ 测试完成！")
    
    return all_data


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(test_coinglass())