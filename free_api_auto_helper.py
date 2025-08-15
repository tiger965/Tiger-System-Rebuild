#!/usr/bin/env python3
"""
免费API自动配置助手
帮助用户快速完成免费API的配置
"""

import os
import time
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

class FreeAPIHelper:
    def __init__(self):
        self.free_apis = {
            'telegram': {
                'name': 'Telegram Bot',
                'cost': '完全免费',
                'difficulty': '简单',
                'time': '5分钟'
            },
            'reddit': {
                'name': 'Reddit API',
                'cost': '完全免费',
                'difficulty': '简单', 
                'time': '5分钟'
            },
            'etherscan': {
                'name': 'Etherscan',
                'cost': '免费(5次/秒)',
                'difficulty': '简单',
                'time': '5分钟'
            },
            'binance': {
                'name': 'Binance API',
                'cost': '完全免费',
                'difficulty': '需要KYC',
                'time': '10分钟'
            }
        }
        
    def create_telegram_bot_script(self):
        """创建Telegram Bot自动化脚本"""
        script = """#!/usr/bin/env python3
import requests
import time

def create_telegram_bot():
    print("📱 Telegram Bot 快速创建指南")
    print("="*50)
    
    # 步骤1：生成命令
    bot_name = input("给你的机器人起个名字（如：Tiger交易助手）: ") or "Tiger交易助手"
    bot_username = input("机器人用户名（必须以bot结尾，如：tiger_trading_bot）: ") or "tiger_trading_bot"
    
    print("\\n📋 复制以下命令到Telegram：")
    print("-"*50)
    commands = f'''
/newbot
{bot_name}
{bot_username}
'''
    print(commands)
    print("-"*50)
    
    print("\\n步骤：")
    print("1. 打开Telegram，搜索 @BotFather")
    print("2. 粘贴上面的命令")
    print("3. 获得Bot Token后粘贴到下面")
    
    token = input("\\n请粘贴Bot Token: ").strip()
    
    if token:
        # 测试token
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if r.status_code == 200:
            print("✅ Bot创建成功！")
            
            # 获取chat_id
            print("\\n获取Chat ID:")
            print("1. 在Telegram搜索你的bot: @" + bot_username)
            print("2. 发送 /start")
            print("3. 等待3秒...")
            
            input("按回车继续...")
            
            # 自动获取chat_id
            r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
            if r.status_code == 200:
                data = r.json()
                if data.get('result'):
                    chat_id = data['result'][0]['message']['chat']['id']
                    print(f"✅ 找到Chat ID: {chat_id}")
                    
                    # 发送测试消息
                    test_msg = "🎉 Tiger系统连接成功！"
                    requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={'chat_id': chat_id, 'text': test_msg}
                    )
                    print("✅ 已发送测试消息")
                    
                    # 保存配置
                    return {
                        'telegram_bot_token': token,
                        'telegram_chat_id': str(chat_id)
                    }
                else:
                    print("⚠️ 请先给bot发送 /start")
    
    return None

if __name__ == "__main__":
    config = create_telegram_bot()
    if config:
        print(f"\\n配置信息：")
        print(json.dumps(config, indent=2))
"""
        
        with open('/tmp/create_telegram_bot.py', 'w') as f:
            f.write(script)
        
        print("✅ 已创建Telegram Bot助手: /tmp/create_telegram_bot.py")
        return '/tmp/create_telegram_bot.py'
    
    def create_reddit_script(self):
        """创建Reddit API配置脚本"""
        script = """#!/usr/bin/env python3
import webbrowser
import time

print("🤖 Reddit API 自动配置")
print("="*50)

# 生成随机应用名
import random
app_name = f"TigerSystem_{random.randint(1000, 9999)}"

print(f"\\n将为你创建Reddit应用: {app_name}")
print("\\n请按照以下步骤操作：")

steps = '''
1. 浏览器将打开Reddit应用创建页面
2. 如果没有Reddit账号，先注册一个（免费）
3. 在创建应用页面填写：
   - name: {app_name}
   - App type: 选择 "script"
   - description: Market analysis bot
   - about url: 留空
   - redirect uri: http://localhost:8080
   - permissions: 留空
4. 点击 "create app"
5. 记录下面两个值：
   - Client ID: 在应用名称下方的一串字符
   - Secret: 在 "secret" 后面的一串字符
'''.format(app_name=app_name)

print(steps)

# 打开浏览器
url = "https://www.reddit.com/prefs/apps"
print(f"\\n正在打开: {url}")
webbrowser.open(url)

print("\\n" + "="*50)
client_id = input("请输入 Client ID: ").strip()
secret = input("请输入 Secret: ").strip()

if client_id and secret:
    config = {
        'reddit_client_id': client_id,
        'reddit_secret': secret,
        'reddit_user_agent': app_name
    }
    
    print("\\n✅ Reddit API配置成功！")
    print("配置信息：")
    import json
    print(json.dumps(config, indent=2))
    
    # 测试代码
    print("\\n测试代码示例：")
    test_code = f'''
import praw
reddit = praw.Reddit(
    client_id="{client_id}",
    client_secret="{secret}",
    user_agent="{app_name}"
)
for submission in reddit.subreddit("cryptocurrency").hot(limit=5):
    print(submission.title)
'''
    print(test_code)
"""
        
        with open('/tmp/setup_reddit_api.py', 'w') as f:
            f.write(script)
        
        print("✅ 已创建Reddit API助手: /tmp/setup_reddit_api.py")
        return '/tmp/setup_reddit_api.py'
    
    def create_etherscan_script(self):
        """创建Etherscan快速配置脚本"""
        script = """#!/usr/bin/env python3
import webbrowser
import requests
import time

print("⛓️ Etherscan API 快速配置")
print("="*50)

print("\\nEtherscan提供免费的以太坊链上数据API")
print("限制：5次/秒，100,000次/天（足够使用）")

print("\\n自动注册流程：")
print("1. 打开注册页面")
print("2. 填写邮箱和密码")
print("3. 验证邮箱")
print("4. 获取API Key")

# 打开注册页面
url = "https://etherscan.io/register"
print(f"\\n正在打开: {url}")
webbrowser.open(url)

print("\\n请完成注册后，访问API页面获取密钥")
time.sleep(3)

# 打开API页面
api_url = "https://etherscan.io/myapikey"
print(f"正在打开: {api_url}")
webbrowser.open(api_url)

print("\\n" + "="*50)
api_key = input("请粘贴你的 Etherscan API Key: ").strip()

if api_key:
    # 测试API
    print("\\n测试API连接...")
    test_url = f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={api_key}"
    
    try:
        r = requests.get(test_url)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == '1':
                eth_price = data['result']['ethusd']
                print(f"✅ API测试成功！")
                print(f"当前ETH价格: ${eth_price}")
                
                config = {'etherscan_api_key': api_key}
                
                # 询问是否配置其他链
                print("\\n是否同时配置BSC链? (使用同一个账号)")
                if input("配置BSCScan? (y/n): ").lower() == 'y':
                    webbrowser.open("https://bscscan.com/myapikey")
                    bsc_key = input("BSCScan API Key: ").strip()
                    if bsc_key:
                        config['bscscan_api_key'] = bsc_key
                
                print("\\n✅ 配置完成！")
                import json
                print(json.dumps(config, indent=2))
            else:
                print("❌ API Key无效")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
"""
        
        with open('/tmp/setup_etherscan_api.py', 'w') as f:
            f.write(script)
            
        print("✅ 已创建Etherscan API助手: /tmp/setup_etherscan_api.py")
        return '/tmp/setup_etherscan_api.py'
    
    def create_master_config(self):
        """创建主配置脚本"""
        master = """#!/usr/bin/env python3
'''
Tiger系统 - 免费API一键配置
自动完成所有免费API的配置
'''

import os
import yaml
import json
import subprocess
from pathlib import Path

def run_script(script_path):
    \"\"\"运行配置脚本并获取结果\"\"\"
    result = subprocess.run(['python3', script_path], capture_output=True, text=True)
    # 从输出中提取配置
    output = result.stdout
    if '{' in output and '}' in output:
        start = output.rfind('{')
        end = output.rfind('}') + 1
        try:
            config = json.loads(output[start:end])
            return config
        except:
            pass
    return {}

def main():
    print("="*60)
    print("🚀 Tiger系统 - 免费API一键配置")
    print("="*60)
    
    all_configs = {}
    
    print("\\n将配置以下免费API：")
    print("1. ✅ Telegram Bot - 实时通知")
    print("2. ✅ Reddit API - 社区情绪")  
    print("3. ✅ Etherscan - 链上数据")
    print("4. ⚠️ Binance API - 需要KYC")
    
    print("\\n" + "-"*60)
    
    # 1. Telegram Bot
    print("\\n[1/3] 配置Telegram Bot...")
    if input("配置Telegram? (y/n) [y]: ").lower() != 'n':
        os.system("python3 /tmp/create_telegram_bot.py")
        config = input("\\n粘贴配置JSON: ")
        if config:
            all_configs.update(json.loads(config))
    
    # 2. Reddit API
    print("\\n[2/3] 配置Reddit API...")
    if input("配置Reddit? (y/n) [y]: ").lower() != 'n':
        os.system("python3 /tmp/setup_reddit_api.py")
        config = input("\\n粘贴配置JSON: ")
        if config:
            all_configs.update(json.loads(config))
    
    # 3. Etherscan
    print("\\n[3/3] 配置Etherscan...")
    if input("配置Etherscan? (y/n) [y]: ").lower() != 'n':
        os.system("python3 /tmp/setup_etherscan_api.py")
        config = input("\\n粘贴配置JSON: ")
        if config:
            all_configs.update(json.loads(config))
    
    # 保存配置
    if all_configs:
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # 更新现有配置
        config_file = config_dir / "api_keys.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                existing = yaml.safe_load(f) or {}
            existing.update(all_configs)
            all_configs = existing
        
        with open(config_file, 'w') as f:
            yaml.dump(all_configs, f, default_flow_style=False)
        
        print("\\n" + "="*60)
        print("✅ 配置完成！")
        print(f"已配置 {len(all_configs)} 个API")
        print(f"配置文件: {config_file}")
        
        # 生成报告
        report = f\"\"\"
Tiger系统 - API配置成功
========================

已配置的免费API:
\"\"\"
        for key in all_configs:
            if 'telegram' in key:
                report += "\\n✅ Telegram Bot - 实时通知"
            elif 'reddit' in key:
                report += "\\n✅ Reddit API - 社区分析"
            elif 'etherscan' in key:
                report += "\\n✅ Etherscan - 以太坊数据"
            elif 'bscscan' in key:
                report += "\\n✅ BSCScan - BSC链数据"
        
        report += \"\"\"

下一步：
1. 配置Binance API（需要先完成KYC）
2. 运行系统: python3 main.py
3. 测试连接: python3 test_api_connections.py

提醒：
- 这些API都是完全免费的
- 不需要信用卡
- 立即可用
\"\"\"
        
        print(report)
        
        with open("API配置成功.txt", 'w', encoding='utf-8') as f:
            f.write(report)

if __name__ == "__main__":
    main()
"""
        
        with open('/mnt/c/Users/tiger/TigerSystem/configure_free_apis.py', 'w') as f:
            f.write(master)
        
        print("✅ 已创建主配置脚本: configure_free_apis.py")
    
    def run(self):
        """执行配置流程"""
        print("="*60)
        print("🆓 免费API自动配置助手")
        print("="*60)
        
        print("\n可以自动配置的免费API：")
        for key, api in self.free_apis.items():
            print(f"• {api['name']}: {api['cost']} | 难度:{api['difficulty']} | 耗时:{api['time']}")
        
        print("\n" + "-"*60)
        print("正在创建配置脚本...")
        
        # 创建各个脚本
        self.create_telegram_bot_script()
        self.create_reddit_script()
        self.create_etherscan_script()
        self.create_master_config()
        
        print("\n" + "="*60)
        print("✅ 所有脚本已创建完成！")
        print("\n使用方法：")
        print("1. 一键配置所有免费API:")
        print("   python3 configure_free_apis.py")
        print("\n2. 或单独配置:")
        print("   python3 /tmp/create_telegram_bot.py  # Telegram")
        print("   python3 /tmp/setup_reddit_api.py     # Reddit")
        print("   python3 /tmp/setup_etherscan_api.py  # Etherscan")
        
        print("\n是否立即开始配置? (y/n): ", end='')
        if input().lower() == 'y':
            os.system("python3 configure_free_apis.py")

if __name__ == "__main__":
    helper = FreeAPIHelper()
    helper.run()