"""
测试付费API连接
"""

import asyncio
import aiohttp
import json

async def test_coinglass():
    """测试Coinglass API"""
    print("测试Coinglass API...")
    
    api_key = "689079f638414a18bac90b722446f3b3"  # 新的API key
    base_url = "https://open-api-v4.coinglass.com"
    
    headers = {
        "coinglassSecret": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试获取资金费率
            url = f"{base_url}/api/futures/funding-rate"
            params = {"symbol": "BTC"}
            
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                print(f"Coinglass响应状态: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Coinglass连接成功")
                    print(f"数据示例: {str(data)[:200]}...")
                else:
                    text = await resp.text()
                    print(f"❌ Coinglass错误: {text[:200]}")
    except Exception as e:
        print(f"❌ Coinglass连接失败: {e}")

async def test_whale_alert():
    """测试WhaleAlert API"""
    print("\n测试WhaleAlert API...")
    
    api_key = "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU"
    base_url = "https://api.whale-alert.io/v1"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试获取状态
            url = f"{base_url}/status"
            params = {"api_key": api_key}
            
            async with session.get(url, params=params, timeout=10) as resp:
                print(f"WhaleAlert响应状态: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ WhaleAlert连接成功")
                    print(f"支持的区块链: {list(data.keys())[:5]}...")
                else:
                    text = await resp.text()
                    print(f"❌ WhaleAlert错误: {text[:200]}")
    except Exception as e:
        print(f"❌ WhaleAlert连接失败: {e}")

async def main():
    print("=" * 60)
    print("付费API连接测试")
    print("=" * 60)
    
    await test_coinglass()
    await test_whale_alert()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main())