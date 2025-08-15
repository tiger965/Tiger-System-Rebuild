"""
测试Coinglass API不同的端点格式
"""

import asyncio
import aiohttp
import json

async def test_endpoints():
    """测试不同的API端点"""
    api_key = "689079f638414a18bac90b722446f3b3"
    
    # 测试不同的base URL和端点组合
    test_cases = [
        {
            "name": "测试1: 原始格式",
            "url": "https://open-api-v4.coinglass.com/api/futures/funding-rate",
            "headers": {"coinglassSecret": api_key}
        },
        {
            "name": "测试2: 不同的header名称",
            "url": "https://open-api-v4.coinglass.com/api/futures/funding-rate",
            "headers": {"api-key": api_key}
        },
        {
            "name": "测试3: 不同的header名称2",
            "url": "https://open-api-v4.coinglass.com/api/futures/funding-rate",
            "headers": {"x-api-key": api_key}
        },
        {
            "name": "测试4: 公开接口测试",
            "url": "https://open-api.coinglass.com/public/v2/indicator/bitcoin-fear-greed",
            "headers": {"coinglassSecret": api_key}
        },
        {
            "name": "测试5: v2版本",
            "url": "https://open-api.coinglass.com/api/pro/v1/futures/funding_rates_chart",
            "headers": {"coinglassSecret": api_key}
        },
        {
            "name": "测试6: 不同路径",
            "url": "https://api.coinglass.com/api/futures/funding-rate",
            "headers": {"coinglassSecret": api_key}
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test in test_cases:
            print(f"\n{test['name']}:")
            print(f"  URL: {test['url']}")
            try:
                async with session.get(
                    test['url'], 
                    headers=test['headers'],
                    params={"symbol": "BTC"},
                    timeout=5
                ) as resp:
                    print(f"  状态码: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"  ✅ 成功！数据: {str(data)[:100]}...")
                    else:
                        text = await resp.text()
                        print(f"  ❌ 错误: {text[:100]}")
            except Exception as e:
                print(f"  ❌ 异常: {e}")

async def test_simple_request():
    """测试最简单的请求"""
    print("\n测试简单请求（不带参数）:")
    
    api_key = "689079f638414a18bac90b722446f3b3"
    
    # 测试不同的URL
    urls = [
        "https://open-api.coinglass.com/public/v2/indicator/bitcoin-fear-greed",
        "https://api.coinglass.com/api/futures/home/liquidation_coin",
        "https://open-api.coinglass.com/public/v2/open_interest/bitcoin/history"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            print(f"\nURL: {url}")
            try:
                # 先试不带header
                async with session.get(url, timeout=5) as resp:
                    print(f"  无header状态: {resp.status}")
                    if resp.status == 200:
                        print(f"  ✅ 公开API可访问")
                
                # 再试带header
                headers = {"coinglassSecret": api_key}
                async with session.get(url, headers=headers, timeout=5) as resp:
                    print(f"  带header状态: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"  ✅ 数据获取成功")
                        if isinstance(data, dict):
                            print(f"  数据keys: {list(data.keys())[:5]}")
            except Exception as e:
                print(f"  ❌ 错误: {e}")

async def main():
    print("=" * 60)
    print("Coinglass API端点测试")
    print("=" * 60)
    
    await test_endpoints()
    await test_simple_request()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main())