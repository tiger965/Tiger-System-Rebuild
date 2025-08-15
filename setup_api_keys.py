#!/usr/bin/env python3
"""
Tiger系统 - API密钥配置向导
"""

import yaml
import os
from pathlib import Path

def setup_api_keys():
    """配置API密钥"""
    print("=" * 70)
    print("🔑 Tiger系统 - API密钥配置向导")
    print("=" * 70)
    print()
    
    apis = {
        "binance": {
            "name": "币安(Binance)交易所",
            "keys": ["binance_api_key", "binance_secret"],
            "purpose": "获取实时市场数据、K线、深度、交易执行",
            "required": "推荐",
            "get_url": "https://www.binance.com/zh-CN/my/settings/api-management",
            "instructions": """
获取步骤:
1. 登录币安账号
2. 进入 API管理 页面
3. 创建新的API密钥
4. 设置权限：只需勾选"读取"权限（安全）
5. 保存API Key和Secret Key
注意：Secret Key只显示一次，请妥善保存"""
        },
        
        "claude": {
            "name": "Claude AI",
            "keys": ["claude_api_key"],
            "purpose": "AI决策分析、智能预测、策略优化",
            "required": "可选",
            "get_url": "https://console.anthropic.com/settings/keys",
            "instructions": """
获取步骤:
1. 注册Anthropic账号
2. 进入Console -> API Keys
3. 创建新的API密钥
4. 复制密钥
费用：按使用量付费，约$0.003/1K tokens"""
        },
        
        "telegram": {
            "name": "Telegram机器人",
            "keys": ["telegram_bot_token", "telegram_chat_id"],
            "purpose": "实时通知、警报推送、远程控制",
            "required": "推荐",
            "get_url": "https://t.me/botfather",
            "instructions": """
获取步骤:
1. 在Telegram搜索 @BotFather
2. 发送 /newbot 创建机器人
3. 设置机器人名称和用户名
4. 获得Bot Token
5. 搜索你的机器人并发送 /start
6. 访问 https://api.telegram.org/bot<TOKEN>/getUpdates 获取chat_id"""
        },
        
        "coingecko": {
            "name": "CoinGecko",
            "keys": ["coingecko_api_key"],
            "purpose": "获取加密货币基础信息、市值排名、项目数据",
            "required": "可选",
            "get_url": "https://www.coingecko.com/en/api/pricing",
            "instructions": """
获取步骤:
1. 注册CoinGecko账号
2. 选择API计划（有免费版）
3. 获取API密钥
免费版限制：50次/分钟"""
        },
        
        "twitter": {
            "name": "Twitter/X",
            "keys": ["twitter_api_key", "twitter_api_secret", "twitter_bearer_token"],
            "purpose": "社交媒体情绪分析、热点追踪、KOL动态",
            "required": "可选",
            "get_url": "https://developer.twitter.com/en/portal/dashboard",
            "instructions": """
获取步骤:
1. 申请Twitter开发者账号
2. 创建App
3. 获取API Key、Secret和Bearer Token
费用：基础版$100/月"""
        },
        
        "openai": {
            "name": "OpenAI GPT",
            "keys": ["openai_api_key"],
            "purpose": "备用AI分析（如果Claude不可用）",
            "required": "可选",
            "get_url": "https://platform.openai.com/api-keys",
            "instructions": """
获取步骤:
1. 注册OpenAI账号
2. 进入API Keys页面
3. 创建新密钥
费用：按使用量付费"""
        },
        
        "okx": {
            "name": "OKX交易所",
            "keys": ["okx_api_key", "okx_secret", "okx_passphrase"],
            "purpose": "备用交易所数据源",
            "required": "可选",
            "get_url": "https://www.okx.com/account/my-api",
            "instructions": """
获取步骤:
1. 登录OKX账号
2. 进入API管理
3. 创建API（只勾选读取权限）
4. 设置密码短语
5. 保存所有密钥"""
        },
        
        "etherscan": {
            "name": "Etherscan",
            "keys": ["etherscan_api_key"],
            "purpose": "以太坊链上数据、智能合约监控、大额转账追踪",
            "required": "可选",
            "get_url": "https://etherscan.io/apis",
            "instructions": """
获取步骤:
1. 注册Etherscan账号
2. 进入API-KEYs页面
3. 创建新的API Key
免费版：5次/秒"""
        }
    }
    
    # 显示API列表
    print("📋 支持的API列表:\n")
    print("优先级说明: 🔴必需 🟡推荐 🟢可选\n")
    
    for key, api in apis.items():
        icon = "🔴" if api["required"] == "必需" else "🟡" if api["required"] == "推荐" else "🟢"
        print(f"{icon} {api['name']}")
        print(f"   用途: {api['purpose']}")
        print()
    
    # 加载现有配置
    config_file = Path("config/api_keys.yaml")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # 配置向导
    print("-" * 70)
    print("\n开始配置API密钥 (直接回车跳过):\n")
    
    updated = False
    
    # 必需和推荐的API
    priority_apis = ["binance", "telegram", "claude"]
    
    for api_key in priority_apis:
        if api_key in apis:
            api = apis[api_key]
            print(f"\n{'='*50}")
            print(f"配置 {api['name']} ({api['required']})")
            print(f"用途: {api['purpose']}")
            print(f"获取地址: {api['get_url']}")
            print(f"{'='*50}")
            
            for key in api['keys']:
                current = config.get(key, '')
                if current:
                    print(f"{key}: {'*' * 8} (已配置)")
                    change = input("是否修改? (y/n): ")
                    if change.lower() == 'y':
                        value = input(f"请输入新的 {key}: ").strip()
                        if value:
                            config[key] = value
                            updated = True
                else:
                    value = input(f"请输入 {key}: ").strip()
                    if value:
                        config[key] = value
                        updated = True
    
    # 询问是否配置其他API
    print("\n" + "="*50)
    other = input("\n是否配置其他可选API? (y/n): ")
    if other.lower() == 'y':
        print("\n可选API列表:")
        optional = [k for k, v in apis.items() if v["required"] == "可选"]
        for i, key in enumerate(optional, 1):
            print(f"{i}. {apis[key]['name']}")
        
        choices = input("\n请输入要配置的编号（用逗号分隔）: ").strip()
        if choices:
            for choice in choices.split(','):
                try:
                    idx = int(choice.strip()) - 1
                    if 0 <= idx < len(optional):
                        api_key = optional[idx]
                        api = apis[api_key]
                        print(f"\n配置 {api['name']}")
                        print(api['instructions'])
                        for key in api['keys']:
                            value = input(f"请输入 {key}: ").strip()
                            if value:
                                config[key] = value
                                updated = True
                except:
                    pass
    
    # 保存配置
    if updated:
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"\n✅ API密钥已保存到: {config_file}")
    else:
        print("\n未修改任何配置")
    
    # 显示配置状态
    print("\n" + "="*70)
    print("当前API配置状态:")
    print("-" * 70)
    
    status = {
        "binance": "✅ 已配置" if config.get("binance_api_key") else "❌ 未配置",
        "claude": "✅ 已配置" if config.get("claude_api_key") else "❌ 未配置",
        "telegram": "✅ 已配置" if config.get("telegram_bot_token") else "❌ 未配置",
        "coingecko": "✅ 已配置" if config.get("coingecko_api_key") else "❌ 未配置",
        "twitter": "✅ 已配置" if config.get("twitter_api_key") else "❌ 未配置",
        "openai": "✅ 已配置" if config.get("openai_api_key") else "❌ 未配置",
    }
    
    for name, stat in status.items():
        print(f"  {apis.get(name, {}).get('name', name)}: {stat}")
    
    # 功能可用性
    print("\n" + "="*70)
    print("功能可用性:")
    print("-" * 70)
    
    features = {
        "实时市场数据": "✅ 可用" if config.get("binance_api_key") else "⚠️ 需要Binance API",
        "AI决策分析": "✅ 可用" if config.get("claude_api_key") or config.get("openai_api_key") else "⚠️ 需要AI API",
        "实时通知": "✅ 可用" if config.get("telegram_bot_token") else "⚠️ 需要Telegram Bot",
        "社交情绪分析": "✅ 可用" if config.get("twitter_api_key") else "⚠️ 需要Twitter API",
        "链上数据监控": "✅ 可用" if config.get("etherscan_api_key") else "⚠️ 需要Etherscan API",
    }
    
    for feature, status in features.items():
        print(f"  {feature}: {status}")
    
    print("\n" + "="*70)
    print("提示:")
    print("  - 最少需要配置Binance API来获取市场数据")
    print("  - 配置Telegram可以接收实时通知")
    print("  - 配置Claude/OpenAI可以启用AI分析功能")
    print("  - 其他API为可选增强功能")

def test_apis():
    """测试API连接"""
    print("\n测试API连接...")
    
    config_file = Path("config/api_keys.yaml")
    if not config_file.exists():
        print("❌ 请先配置API密钥")
        return
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # 测试Binance
    if config.get("binance_api_key"):
        print("\n测试Binance API...")
        try:
            import requests
            response = requests.get("https://api.binance.com/api/v3/time")
            if response.status_code == 200:
                print("  ✅ Binance API连接成功")
            else:
                print("  ❌ Binance API连接失败")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    print("\n✅ API测试完成")

if __name__ == "__main__":
    setup_api_keys()
    
    print("\n是否测试API连接? (y/n): ", end='')
    if input().lower() == 'y':
        test_apis()