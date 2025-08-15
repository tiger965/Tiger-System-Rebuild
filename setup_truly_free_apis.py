#!/usr/bin/env python3
"""
真正免费的API配置助手
只配置100%免费、无需付费的API
"""

import os
import yaml
import requests
import webbrowser
from pathlib import Path
from datetime import datetime

print("="*60)
print("🆓 真正免费的API配置")
print("="*60)

print("""
完全免费的API清单：
1. ✅ OKX/欧易 - 交易所数据（完全免费）
2. ✅ Telegram Bot - 通知系统（完全免费）
3. ✅ Etherscan - 以太坊数据（免费5次/秒）
4. ✅ BSCScan - BSC链数据（免费5次/秒）
5. ✅ Reddit API - 社区数据（免费60次/分）
6. ✅ CoinGecko - 币种信息（免费50次/分）

不是真正免费的：
❌ Twitter - Free版本不能读数据，Basic要$100/月
❌ Claude/OpenAI - 按使用量收费
❌ 新闻API - 有限制，专业版收费
""")

def setup_telegram():
    """配置Telegram（完全免费）"""
    print("\n" + "="*50)
    print("1️⃣ 配置Telegram Bot（完全免费）")
    print("-"*50)
    
    print("""
步骤：
1. 打开Telegram，搜索 @BotFather
2. 发送 /newbot
3. 设置机器人名称
4. 获得Bot Token
""")
    
    webbrowser.open("https://t.me/botfather")
    
    token = input("\nBot Token (直接回车跳过): ").strip()
    
    if token:
        # 测试token
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if r.status_code == 200 and r.json().get('ok'):
            print("✅ Telegram配置成功")
            
            # 获取chat_id
            print("\n获取Chat ID：")
            print("1. 给你的机器人发送 /start")
            input("2. 按回车继续...")
            
            r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
            if r.json().get('result'):
                chat_id = r.json()['result'][0]['message']['chat']['id']
                print(f"✅ Chat ID: {chat_id}")
                return {
                    'telegram_bot_token': token,
                    'telegram_chat_id': str(chat_id)
                }
    
    return {}

def setup_reddit():
    """配置Reddit（完全免费）"""
    print("\n" + "="*50)
    print("2️⃣ 配置Reddit API（完全免费）")
    print("-"*50)
    
    print("""
步骤：
1. 登录Reddit账号
2. 访问应用页面
3. 创建script类型应用
4. 获取client_id和secret
""")
    
    webbrowser.open("https://www.reddit.com/prefs/apps")
    
    client_id = input("\nClient ID (直接回车跳过): ").strip()
    secret = input("Secret: ").strip()
    
    if client_id and secret:
        print("✅ Reddit配置成功")
        return {
            'reddit_client_id': client_id,
            'reddit_secret': secret
        }
    
    return {}

def setup_etherscan():
    """配置Etherscan（免费版够用）"""
    print("\n" + "="*50)
    print("3️⃣ 配置Etherscan（免费5次/秒）")
    print("-"*50)
    
    print("""
步骤：
1. 注册Etherscan账号
2. 验证邮箱
3. 创建API Key
""")
    
    webbrowser.open("https://etherscan.io/register")
    
    api_key = input("\nEtherscan API Key (直接回车跳过): ").strip()
    
    if api_key:
        # 测试API
        r = requests.get(f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={api_key}")
        if r.status_code == 200 and r.json().get('status') == '1':
            price = r.json()['result']['ethusd']
            print(f"✅ Etherscan配置成功，ETH价格: ${price}")
            return {'etherscan_api_key': api_key}
    
    return {}

def setup_coingecko():
    """配置CoinGecko（免费版）"""
    print("\n" + "="*50)
    print("4️⃣ 配置CoinGecko（免费50次/分）")
    print("-"*50)
    
    print("""
CoinGecko提供：
• 币种基本信息、市值排名
• 历史价格、ATH/ATL
• 项目信息、社交数据

注意：Demo API不需要密钥，直接可用
Pro API需要注册（有免费额度）
""")
    
    choice = input("\n使用Demo API（无需注册）? (y/n) [y]: ") or 'y'
    
    if choice.lower() == 'y':
        print("✅ 将使用CoinGecko Demo API（无需密钥）")
        return {'coingecko_demo': 'true'}
    else:
        webbrowser.open("https://www.coingecko.com/api/pricing")
        api_key = input("CoinGecko API Key: ").strip()
        if api_key:
            return {'coingecko_api_key': api_key}
    
    return {}

def main():
    """主配置流程"""
    all_configs = {}
    
    print("\n" + "="*60)
    print("开始配置免费API")
    print("="*60)
    
    # 1. OKX（必需）
    print("\n必需配置：OKX交易所API")
    if input("配置OKX? (y/n) [y]: ").lower() != 'n':
        os.system("python3 setup_okx_api.py")
    
    # 2. Telegram（推荐）
    if input("\n配置Telegram通知? (y/n) [y]: ").lower() != 'n':
        config = setup_telegram()
        all_configs.update(config)
    
    # 3. Reddit（可选）
    if input("\n配置Reddit? (y/n) [n]: ").lower() == 'y':
        config = setup_reddit()
        all_configs.update(config)
    
    # 4. Etherscan（可选）
    if input("\n配置Etherscan? (y/n) [n]: ").lower() == 'y':
        config = setup_etherscan()
        all_configs.update(config)
    
    # 5. CoinGecko（可选）
    if input("\n配置CoinGecko? (y/n) [n]: ").lower() == 'y':
        config = setup_coingecko()
        all_configs.update(config)
    
    # 保存配置
    if all_configs:
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "api_keys.yaml"
        
        # 合并现有配置
        if config_file.exists():
            with open(config_file, 'r') as f:
                existing = yaml.safe_load(f) or {}
            existing.update(all_configs)
            all_configs = existing
        
        with open(config_file, 'w') as f:
            yaml.dump(all_configs, f, default_flow_style=False)
        
        print("\n" + "="*60)
        print("✅ 配置完成！")
        print(f"配置文件: {config_file}")
        
        # 生成报告
        report = f"""
免费API配置报告
====================
时间: {datetime.now()}

已配置的免费API:
"""
        if 'okx_api_key' in all_configs:
            report += "\n✅ OKX交易所 - 市场数据"
        if 'telegram_bot_token' in all_configs:
            report += "\n✅ Telegram - 实时通知"
        if 'reddit_client_id' in all_configs:
            report += "\n✅ Reddit - 社区分析"
        if 'etherscan_api_key' in all_configs:
            report += "\n✅ Etherscan - 链上数据"
        if 'coingecko_api_key' in all_configs or 'coingecko_demo' in all_configs:
            report += "\n✅ CoinGecko - 币种信息"
        
        report += """

这些API的特点：
• 完全免费或有充足的免费额度
• 无需信用卡
• 立即可用

下一步：
python3 start.py  # 启动系统
"""
        
        with open("免费API配置报告.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)

if __name__ == "__main__":
    main()