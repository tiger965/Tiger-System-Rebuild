"""
测试新的Coinglass API key
"""

import asyncio
import aiohttp
import json

async def test_new_key():
    api_key = "9ac3153a98924877a863d41986231e36"
    base_url = "https://open-api-v4.coinglass.com"
    
    headers = {
        "accept": "application/json",
        "CG-API-KEY": api_key
    }
    
    print("=" * 60)
    print("测试新的Coinglass API Key")
    print("=" * 60)
    
    # 测试端点列表
    test_endpoints = [
        ("/api/futures/supported-coins", None, "支持币种"),
        ("/api/futures/coins-markets", {"symbol": "BTC"}, "币种市场"),
        ("/api/futures/funding-rates-chart", {"symbol": "BTC"}, "资金费率图表"),
        ("/api/futures/open-interest-history", {"symbol": "BTC", "time_type": "h1"}, "OI历史"),
        ("/api/futures/liquidation-history", {"symbol": "BTC", "time_type": "h1"}, "爆仓历史"),
        ("/api/futures/long-short-history", {"symbol": "BTC", "time_type": "h1"}, "多空比历史"),
        ("/api/index/fear-greed", None, "恐慌贪婪指数"),
        ("/api/index/bitcoin-rainbow-chart", None, "比特币彩虹图"),
    ]
    
    async with aiohttp.ClientSession() as session:
        success_count = 0
        
        for endpoint, params, description in test_endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n测试: {description}")
            print(f"  端点: {endpoint}")
            
            try:
                async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                    print(f"  状态码: {resp.status}")
                    
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            data = json.loads(text)
                            if isinstance(data, dict):
                                if data.get("code") == "0":
                                    print(f"  ✅ 成功！")
                                    if data.get("data"):
                                        # 显示部分数据
                                        data_str = str(data["data"])
                                        if len(data_str) > 100:
                                            print(f"  数据预览: {data_str[:100]}...")
                                        else:
                                            print(f"  数据: {data_str}")
                                    success_count += 1
                                else:
                                    print(f"  ❌ API错误: {data.get('msg', 'Unknown')}")
                        except json.JSONDecodeError:
                            print(f"  ❌ JSON解析失败")
                    else:
                        text = await resp.text()
                        print(f"  ❌ HTTP错误: {text[:100]}")
                        
            except Exception as e:
                print(f"  ❌ 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {success_count}/{len(test_endpoints)} 成功")
    print("=" * 60)
    
    if success_count > 0:
        print("✅ 新API key可用！")
    else:
        print("❌ 新API key可能有问题")
    
    return success_count

if __name__ == "__main__":
    asyncio.run(test_new_key())