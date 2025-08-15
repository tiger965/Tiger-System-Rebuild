#!/usr/bin/env python3
"""
API连接测试工具
"""

import yaml
import requests
import time
from pathlib import Path

def test_all_apis():
    """测试所有配置的API"""
    config_file = Path("config/api_keys.yaml")
    
    if not config_file.exists():
        print("❌ 未找到配置文件，请先运行: python3 auto_api_setup.py")
        return
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f) or {}
    
    print("="*60)
    print("🔍 测试API连接")
    print("="*60)
    
    results = []
    
    # 测试Binance
    if config.get('binance_api_key'):
        print("\n测试 Binance...")
        try:
            r = requests.get("https://api.binance.com/api/v3/time")
            if r.status_code == 200:
                results.append("✅ Binance: 连接正常")
            else:
                results.append(f"❌ Binance: HTTP {r.status_code}")
        except Exception as e:
            results.append(f"❌ Binance: {str(e)}")
    
    # 测试Telegram
    if config.get('telegram_bot_token'):
        print("测试 Telegram Bot...")
        try:
            token = config['telegram_bot_token']
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            if r.status_code == 200 and r.json().get('ok'):
                bot_name = r.json()['result']['username']
                results.append(f"✅ Telegram: @{bot_name}")
            else:
                results.append("❌ Telegram: Token无效")
        except Exception as e:
            results.append(f"❌ Telegram: {str(e)}")
    
    # 测试Etherscan
    if config.get('etherscan_api_key'):
        print("测试 Etherscan...")
        try:
            key = config['etherscan_api_key']
            r = requests.get(f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={key}")
            if r.status_code == 200 and r.json().get('status') == '1':
                price = r.json()['result']['ethusd']
                results.append(f"✅ Etherscan: ETH价格 ${price}")
            else:
                results.append("❌ Etherscan: API密钥无效")
        except Exception as e:
            results.append(f"❌ Etherscan: {str(e)}")
    
    # 测试Reddit
    if config.get('reddit_client_id'):
        print("测试 Reddit...")
        try:
            # Reddit需要OAuth，这里只检查配置存在
            results.append("✅ Reddit: 已配置（需OAuth验证）")
        except Exception as e:
            results.append(f"❌ Reddit: {str(e)}")
    
    # 测试CryptoPanic
    if config.get('cryptopanic_token'):
        print("测试 CryptoPanic...")
        try:
            token = config['cryptopanic_token']
            r = requests.get(f"https://cryptopanic.com/api/v1/posts/?auth_token={token}&public=true")
            if r.status_code == 200:
                results.append("✅ CryptoPanic: 连接正常")
            else:
                results.append(f"❌ CryptoPanic: HTTP {r.status_code}")
        except Exception as e:
            results.append(f"❌ CryptoPanic: {str(e)}")
    
    # 显示结果
    print("\n" + "="*60)
    print("测试结果：")
    print("-"*60)
    for result in results:
        print(result)
    
    # 统计
    success = len([r for r in results if r.startswith('✅')])
    total = len(results)
    
    print("\n" + "="*60)
    print(f"成功: {success}/{total}")
    
    if success == total:
        print("🎉 所有API连接正常！")
    elif success > 0:
        print("⚠️ 部分API需要检查")
    else:
        print("❌ 请先配置API")

if __name__ == "__main__":
    test_all_apis()