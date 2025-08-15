"""
调试Coinglass API，查看具体错误
"""

import asyncio
import aiohttp

async def debug_coinglass():
    api_key = "689079f638414a18bac90b722446f3b3"
    base_url = "https://open-api-v4.coinglass.com"
    
    headers = {
        "accept": "application/json",
        "CG-API-KEY": api_key
    }
    
    # 测试不同的端点
    endpoints = [
        "/api/futures/supported-coins",
        "/api/futures/funding-rates?symbol=BTC",
        "/api/futures/open-interest?symbol=BTC",
        "/api/futures/liquidations?symbol=BTC&range=24h"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n测试: {endpoint}")
            print(f"URL: {url}")
            
            try:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    print(f"状态码: {resp.status}")
                    text = await resp.text()
                    print(f"响应: {text[:200]}")
                    
                    if resp.status == 200:
                        try:
                            import json
                            data = json.loads(text)
                            if isinstance(data, dict) and "code" in data:
                                print(f"API返回码: {data.get('code')}")
                                print(f"消息: {data.get('msg')}")
                        except:
                            pass
            except Exception as e:
                print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(debug_coinglass())