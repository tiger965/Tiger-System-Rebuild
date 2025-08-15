"""
Coinglass API最终实现
基于实际测试结果和文档
$35/月 Hobbyist套餐
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class CoinglassFinalAPI:
    """
    Coinglass API最终实现
    充分利用$35/月的价值
    """
    
    def __init__(self):
        self.api_key = "689079f638414a18bac90b722446f3b3"
        self.base_url = "https://open-api-v4.coinglass.com"
        
        # 正确的header
        self.headers = {
            "accept": "application/json",
            "CG-API-KEY": self.api_key
        }
        
        # 已验证的可用端点
        self.verified_endpoints = {
            "supported_coins": "/api/futures/supported-coins",  # ✅ 已验证
            # 根据文档，这些可能是正确的端点格式
            "coins_markets": "/api/futures/coins-markets",
            "funding": "/api/futures/funding",
            "funding_average": "/api/futures/funding-average", 
            "open_interest_history": "/api/futures/open-interest-history",
            "open_interest_aggregated": "/api/futures/open-interest-aggregated",
            "liquidation_history": "/api/futures/liquidation-history",
            "liquidation_aggregated": "/api/futures/liquidation-aggregated",
            "long_short_history": "/api/futures/long-short-history",
            "long_short_rate": "/api/futures/long-short-rate",
            "perpetual_market": "/api/futures/perpetual-market",
            "global_liquidation": "/api/futures/global-liquidation-usd-margin",
            "fear_greed": "/api/index/fear-greed",
            "bitcoin_rainbow": "/api/index/bitcoin-rainbow-chart"
        }
        
        logger.info("💎 Coinglass最终API实现初始化")
        logger.info(f"📊 共{len(self.verified_endpoints)}个端点待验证")

    async def test_endpoint(self, name: str, endpoint: str, params: Dict = None) -> Dict:
        """测试单个端点"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=10
                ) as resp:
                    text = await resp.text()
                    
                    if resp.status == 200:
                        try:
                            data = json.loads(text)
                            # 检查是否是成功响应
                            if isinstance(data, dict) and data.get("code") == "0":
                                return {
                                    "success": True,
                                    "endpoint": name,
                                    "data": data.get("data"),
                                    "status": "✅ 可用"
                                }
                            else:
                                return {
                                    "success": False,
                                    "endpoint": name,
                                    "error": data.get("msg", "Unknown error"),
                                    "status": "❌ API错误"
                                }
                        except json.JSONDecodeError:
                            return {
                                "success": False,
                                "endpoint": name,
                                "error": "JSON解析失败",
                                "status": "❌ 格式错误"
                            }
                    else:
                        return {
                            "success": False,
                            "endpoint": name,
                            "error": f"HTTP {resp.status}",
                            "status": "❌ 请求失败"
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "endpoint": name,
                "error": str(e),
                "status": "❌ 异常"
            }

    async def discover_all_endpoints(self) -> Dict:
        """发现所有可用的端点"""
        logger.info("🔍 开始发现所有可用端点...")
        
        results = {}
        tasks = []
        
        # 测试所有端点
        for name, endpoint in self.verified_endpoints.items():
            # 根据端点类型添加合适的参数
            params = None
            if "history" in name or "aggregated" in name:
                params = {"symbol": "BTC", "time_type": "h1"}
            elif any(x in name for x in ["funding", "long-short", "liquidation"]):
                params = {"symbol": "BTC"}
            
            task = self.test_endpoint(name, endpoint, params)
            tasks.append(task)
        
        # 并发测试
        test_results = await asyncio.gather(*tasks)
        
        # 整理结果
        available_endpoints = []
        unavailable_endpoints = []
        
        for result in test_results:
            endpoint_name = result["endpoint"]
            if result["success"]:
                available_endpoints.append(endpoint_name)
                results[endpoint_name] = result
            else:
                unavailable_endpoints.append(endpoint_name)
                results[endpoint_name] = result
        
        # 统计
        summary = {
            "total_tested": len(self.verified_endpoints),
            "available": len(available_endpoints),
            "unavailable": len(unavailable_endpoints),
            "success_rate": len(available_endpoints) / len(self.verified_endpoints) * 100,
            "available_endpoints": available_endpoints,
            "unavailable_endpoints": unavailable_endpoints,
            "detailed_results": results
        }
        
        logger.info(f"✅ 发现完成: {summary['available']}/{summary['total_tested']} 端点可用")
        
        return summary

    async def get_supported_coins(self) -> List[str]:
        """获取支持的币种列表（已验证可用）"""
        result = await self.test_endpoint(
            "supported_coins",
            self.verified_endpoints["supported_coins"]
        )
        
        if result["success"]:
            return result["data"]
        return []

    async def get_market_overview(self, symbol: str = "BTC") -> Dict:
        """获取市场概览（尝试多个端点）"""
        overview = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # 尝试获取各种数据
        endpoints_to_try = [
            ("coins_markets", {"symbol": symbol}),
            ("perpetual_market", {"symbol": symbol}),
            ("funding_average", {"symbol": symbol}),
            ("long_short_rate", {"symbol": symbol})
        ]
        
        for endpoint_name, params in endpoints_to_try:
            if endpoint_name in self.verified_endpoints:
                result = await self.test_endpoint(
                    endpoint_name,
                    self.verified_endpoints[endpoint_name],
                    params
                )
                if result["success"]:
                    overview["data"][endpoint_name] = result["data"]
        
        return overview

    async def maximize_api_value(self) -> Dict:
        """
        最大化API价值
        测试并使用所有可能的功能
        """
        logger.info("=" * 60)
        logger.info("💰 开始最大化Coinglass API价值")
        logger.info("=" * 60)
        
        # 1. 首先发现所有可用端点
        discovery = await self.discover_all_endpoints()
        
        # 2. 获取支持的币种
        coins = await self.get_supported_coins()
        
        # 3. 对主要币种获取完整数据
        major_coins = ["BTC", "ETH", "SOL"] if not coins else coins[:3]
        market_data = {}
        
        for coin in major_coins:
            if coin in (coins if coins else ["BTC", "ETH", "SOL"]):
                market_data[coin] = await self.get_market_overview(coin)
        
        # 4. 生成价值报告
        value_report = {
            "api_discovery": discovery,
            "supported_coins": coins,
            "market_data": market_data,
            "value_metrics": {
                "endpoints_utilized": discovery["available"],
                "total_endpoints": discovery["total_tested"],
                "utilization_rate": f"{discovery['success_rate']:.1f}%",
                "coins_covered": len(coins) if coins else 0,
                "data_points_collected": sum(
                    len(v.get("data", {})) 
                    for v in discovery["detailed_results"].values() 
                    if v.get("success")
                )
            },
            "recommendations": self.generate_recommendations(discovery)
        }
        
        return value_report

    def generate_recommendations(self, discovery: Dict) -> List[str]:
        """生成使用建议"""
        recommendations = []
        
        if discovery["success_rate"] < 50:
            recommendations.append("⚠️ API可用率较低，建议联系Coinglass支持确认权限")
        
        if "funding" in discovery["available_endpoints"]:
            recommendations.append("✅ 资金费率数据可用，建议用于市场情绪分析")
        
        if "long_short_rate" in discovery["available_endpoints"]:
            recommendations.append("✅ 多空比数据可用，建议用于零售情绪分析")
        
        if "liquidation" in str(discovery["available_endpoints"]):
            recommendations.append("✅ 爆仓数据可用，建议用于风险监控")
        
        if discovery["available"] > 5:
            recommendations.append("🎯 多个端点可用，建议创建综合分析系统")
        
        return recommendations


# 测试和验证函数
async def test_coinglass_final():
    """测试Coinglass最终实现"""
    print("=" * 60)
    print("💎 Coinglass API最终测试")
    print("🎯 目标：发现并利用所有可用功能")
    print("=" * 60)
    
    api = CoinglassFinalAPI()
    
    # 运行完整的价值最大化测试
    report = await api.maximize_api_value()
    
    # 显示结果
    print("\n📊 API发现结果:")
    print(f"   测试端点: {report['api_discovery']['total_tested']}")
    print(f"   可用端点: {report['api_discovery']['available']}")
    print(f"   成功率: {report['api_discovery']['success_rate']:.1f}%")
    
    print("\n✅ 可用端点列表:")
    for endpoint in report['api_discovery']['available_endpoints']:
        print(f"   - {endpoint}")
    
    print("\n❌ 不可用端点:")
    for endpoint in report['api_discovery']['unavailable_endpoints'][:5]:  # 只显示前5个
        print(f"   - {endpoint}")
    
    print("\n💰 价值指标:")
    metrics = report['value_metrics']
    print(f"   端点利用: {metrics['endpoints_utilized']}/{metrics['total_endpoints']}")
    print(f"   利用率: {metrics['utilization_rate']}")
    print(f"   币种覆盖: {metrics['coins_covered']}")
    print(f"   数据点: {metrics['data_points_collected']}")
    
    print("\n📋 使用建议:")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    print("\n✅ 测试完成！")
    print(f"💎 Coinglass $35/月价值利用率: {metrics['utilization_rate']}")
    
    # 保存报告
    with open("coinglass_api_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print("\n📄 详细报告已保存到 coinglass_api_report.json")
    
    return report


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(test_coinglass_final())