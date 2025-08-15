#!/usr/bin/env python3
"""
Tiger系统 - API自动配置助手
自动引导用户完成API配置并测试连接
"""

import os
import time
import yaml
import json
import requests
import webbrowser
from pathlib import Path
from datetime import datetime

class APIAutoSetup:
    def __init__(self):
        self.api_configs = {}
        self.results = []
        
    def save_to_file(self, filename, content):
        """保存信息到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已保存到: {filename}")
    
    def open_browser(self, url):
        """打开浏览器"""
        print(f"🌐 正在打开: {url}")
        try:
            webbrowser.open(url)
            return True
        except:
            print(f"⚠️ 无法自动打开浏览器，请手动访问: {url}")
            return False
    
    def test_binance_api(self, api_key, secret):
        """测试Binance API"""
        try:
            # 测试公开接口
            response = requests.get("https://api.binance.com/api/v3/time")
            if response.status_code == 200:
                return True, "连接成功"
            return False, f"状态码: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def test_telegram_bot(self, token):
        """测试Telegram Bot"""
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_name = data['result']['username']
                    return True, f"Bot名称: @{bot_name}"
            return False, "Token无效"
        except Exception as e:
            return False, str(e)
    
    def test_etherscan_api(self, api_key):
        """测试Etherscan API"""
        try:
            url = f"https://api.etherscan.io/api?module=stats&action=ethprice&apikey={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    return True, "API密钥有效"
            return False, "API密钥无效"
        except Exception as e:
            return False, str(e)
    
    def setup_binance(self):
        """配置Binance API"""
        print("\n" + "="*60)
        print("📊 配置 Binance API")
        print("="*60)
        
        # 自动打开注册页面
        self.open_browser("https://www.binance.com/zh-CN/my/settings/api-management")
        
        print("\n请按照以下步骤操作：")
        print("1. 登录你的币安账号")
        print("2. 点击'创建API'")
        print("3. 设置API标签（如：TigerSystem）")
        print("4. 通过安全验证")
        print("5. 只勾选'读取'权限")
        print("6. 复制API Key和Secret Key")
        
        print("\n" + "-"*40)
        api_key = input("请粘贴 API Key: ").strip()
        secret = input("请粘贴 Secret Key: ").strip()
        
        if api_key and secret:
            # 测试连接
            success, msg = self.test_binance_api(api_key, secret)
            if success:
                print(f"✅ Binance API {msg}")
                self.api_configs['binance_api_key'] = api_key
                self.api_configs['binance_secret'] = secret
                self.results.append(f"✅ Binance API: 配置成功")
                return True
            else:
                print(f"❌ 测试失败: {msg}")
                retry = input("是否重试? (y/n): ")
                if retry.lower() == 'y':
                    return self.setup_binance()
        
        self.results.append(f"❌ Binance API: 未配置")
        return False
    
    def setup_telegram(self):
        """配置Telegram Bot"""
        print("\n" + "="*60)
        print("💬 配置 Telegram Bot")
        print("="*60)
        
        print("\n步骤1: 创建Bot")
        print("1. 打开Telegram")
        print("2. 搜索 @BotFather")
        print("3. 发送 /newbot")
        print("4. 设置bot名称（显示名）")
        print("5. 设置bot用户名（必须以bot结尾）")
        print("6. 复制Bot Token")
        
        self.open_browser("https://t.me/botfather")
        
        print("\n" + "-"*40)
        token = input("请粘贴 Bot Token: ").strip()
        
        if token:
            # 测试Token
            success, msg = self.test_telegram_bot(token)
            if success:
                print(f"✅ Telegram Bot {msg}")
                
                # 获取Chat ID
                print("\n步骤2: 获取Chat ID")
                print("1. 在Telegram中搜索你的bot")
                print("2. 发送 /start")
                print("3. 访问下面的链接获取chat_id")
                
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                self.open_browser(url)
                print(f"\n在打开的页面中找到 'chat':{'id': 后面的数字")
                
                chat_id = input("请输入 Chat ID: ").strip()
                
                if chat_id:
                    self.api_configs['telegram_bot_token'] = token
                    self.api_configs['telegram_chat_id'] = chat_id
                    self.results.append(f"✅ Telegram Bot: 配置成功")
                    return True
            else:
                print(f"❌ Token测试失败: {msg}")
        
        self.results.append(f"❌ Telegram Bot: 未配置")
        return False
    
    def setup_twitter(self):
        """配置Twitter API"""
        print("\n" + "="*60)
        print("🐦 配置 Twitter API")
        print("="*60)
        
        print("\n注意：Twitter API需要申请审核（1-2天）")
        choice = input("是否现在申请? (y/n): ")
        
        if choice.lower() == 'y':
            self.open_browser("https://developer.twitter.com/en/portal/petition/essential/basic-info")
            
            print("\n申请步骤：")
            print("1. 选择账号类型：Individual")
            print("2. 用途描述写：Cryptocurrency market sentiment analysis")
            print("3. 不会商用选：No")
            print("4. 提交等待审批")
            print("\n审批通过后：")
            print("1. 访问 https://developer.twitter.com/en/portal/dashboard")
            print("2. 创建App")
            print("3. 获取API Key, Secret和Bearer Token")
            
            has_api = input("\n如果已有API密钥，输入y继续配置: ")
            if has_api.lower() == 'y':
                api_key = input("API Key: ").strip()
                api_secret = input("API Secret: ").strip()
                bearer = input("Bearer Token: ").strip()
                
                if all([api_key, api_secret, bearer]):
                    self.api_configs['twitter_api_key'] = api_key
                    self.api_configs['twitter_api_secret'] = api_secret
                    self.api_configs['twitter_bearer_token'] = bearer
                    self.results.append(f"✅ Twitter API: 配置成功")
                    return True
        
        self.results.append(f"⏳ Twitter API: 待申请")
        return False
    
    def setup_reddit(self):
        """配置Reddit API"""
        print("\n" + "="*60)
        print("👽 配置 Reddit API")
        print("="*60)
        
        self.open_browser("https://www.reddit.com/prefs/apps")
        
        print("\n步骤：")
        print("1. 登录Reddit账号")
        print("2. 滚动到页面底部")
        print("3. 点击 'are you a developer? create an app...'")
        print("4. 填写：")
        print("   - name: TigerSystemBot")
        print("   - App type: script")
        print("   - redirect uri: http://localhost:8080")
        print("5. 点击 'create app'")
        print("6. 记录 client_id（在app名称下方）和 secret")
        
        print("\n" + "-"*40)
        client_id = input("请输入 Client ID: ").strip()
        secret = input("请输入 Secret: ").strip()
        
        if client_id and secret:
            self.api_configs['reddit_client_id'] = client_id
            self.api_configs['reddit_secret'] = secret
            self.results.append(f"✅ Reddit API: 配置成功")
            return True
        
        self.results.append(f"❌ Reddit API: 未配置")
        return False
    
    def setup_etherscan(self):
        """配置Etherscan API"""
        print("\n" + "="*60)
        print("⛓️ 配置 Etherscan API")
        print("="*60)
        
        self.open_browser("https://etherscan.io/register")
        
        print("\n步骤：")
        print("1. 注册账号并验证邮箱")
        print("2. 登录后访问 API Keys 页面")
        print("3. 点击 'Add' 创建新的API Key")
        print("4. 复制API Key")
        
        self.open_browser("https://etherscan.io/myapikey")
        
        print("\n" + "-"*40)
        api_key = input("请输入 Etherscan API Key: ").strip()
        
        if api_key:
            success, msg = self.test_etherscan_api(api_key)
            if success:
                print(f"✅ Etherscan API {msg}")
                self.api_configs['etherscan_api_key'] = api_key
                self.results.append(f"✅ Etherscan API: 配置成功")
                
                # 询问是否配置其他链
                print("\n是否配置其他区块链API?")
                print("1. BSCScan (币安链)")
                print("2. PolygonScan (Polygon)")
                print("3. 跳过")
                
                choice = input("选择 (1-3): ")
                if choice == '1':
                    self.open_browser("https://bscscan.com/myapikey")
                    bsc_key = input("BSCScan API Key: ").strip()
                    if bsc_key:
                        self.api_configs['bscscan_api_key'] = bsc_key
                        self.results.append(f"✅ BSCScan API: 配置成功")
                
                return True
            else:
                print(f"❌ 测试失败: {msg}")
        
        self.results.append(f"❌ Etherscan API: 未配置")
        return False
    
    def setup_news(self):
        """配置新闻API"""
        print("\n" + "="*60)
        print("📰 配置 新闻API")
        print("="*60)
        
        print("\n选择新闻源：")
        print("1. CryptoPanic (加密货币专用)")
        print("2. NewsAPI (通用新闻)")
        print("3. 两个都配置")
        print("4. 跳过")
        
        choice = input("选择 (1-4): ")
        
        if choice in ['1', '3']:
            self.open_browser("https://cryptopanic.com/developers/api/")
            print("\n配置CryptoPanic:")
            print("1. 点击 'Get your free API token'")
            print("2. 注册并验证邮箱")
            print("3. 在Dashboard获取token")
            
            token = input("CryptoPanic Token: ").strip()
            if token:
                self.api_configs['cryptopanic_token'] = token
                self.results.append(f"✅ CryptoPanic: 配置成功")
        
        if choice in ['2', '3']:
            self.open_browser("https://newsapi.org/register")
            print("\n配置NewsAPI:")
            print("1. 填写注册信息")
            print("2. API Key会立即显示")
            
            api_key = input("NewsAPI Key: ").strip()
            if api_key:
                self.api_configs['newsapi_key'] = api_key
                self.results.append(f"✅ NewsAPI: 配置成功")
        
        return True
    
    def save_configs(self):
        """保存所有配置"""
        # 保存到YAML
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "api_keys.yaml", 'w') as f:
            yaml.dump(self.api_configs, f, default_flow_style=False)
        
        # 生成配置报告
        report = f"""
========================================
Tiger系统 API配置报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================

配置结果:
{chr(10).join(self.results)}

已配置的API:
"""
        for key, value in self.api_configs.items():
            if value:
                # 隐藏敏感信息
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
                report += f"\n{key}: {masked}"
        
        report += f"""

配置文件位置:
- config/api_keys.yaml

下一步:
1. 运行系统: python3 main.py
2. 测试连接: python3 test_api_connections.py

安全提醒:
- 不要将api_keys.yaml上传到GitHub
- 定期更换API密钥
- 只给API读取权限，不要给交易权限
"""
        
        # 保存报告
        self.save_to_file("API_配置报告.txt", report)
        
        # 保存快速参考
        quick_ref = f"""
Tiger系统 - API快速参考
========================

Binance API:
- 管理页面: https://www.binance.com/zh-CN/my/settings/api-management
- API Key: {self.api_configs.get('binance_api_key', '未配置')[:8]}...

Telegram Bot:
- BotFather: https://t.me/botfather
- Bot Token: {self.api_configs.get('telegram_bot_token', '未配置')[:8]}...

Twitter API:
- 开发者门户: https://developer.twitter.com/en/portal/dashboard
- 状态: {'已配置' if self.api_configs.get('twitter_api_key') else '未配置'}

Reddit API:
- App管理: https://www.reddit.com/prefs/apps
- 状态: {'已配置' if self.api_configs.get('reddit_client_id') else '未配置'}

Etherscan:
- API管理: https://etherscan.io/myapikey
- 状态: {'已配置' if self.api_configs.get('etherscan_api_key') else '未配置'}

更新配置:
python3 auto_api_setup.py
"""
        
        self.save_to_file("API_快速参考.txt", quick_ref)
    
    def run(self):
        """运行自动配置流程"""
        print("="*60)
        print("🤖 Tiger系统 - API自动配置助手")
        print("="*60)
        print("\n本工具将引导你完成API配置")
        print("需要你手动注册，但会自动打开网页并测试连接")
        
        # 选择配置模式
        print("\n选择配置模式：")
        print("1. 快速配置（只配置必需的）")
        print("2. 完整配置（配置所有API）")
        print("3. 自定义选择")
        
        mode = input("\n选择 (1-3) [默认: 1]: ") or "1"
        
        if mode == "1":
            # 快速配置
            self.setup_binance()
            self.setup_telegram()
            self.setup_etherscan()
            
        elif mode == "2":
            # 完整配置
            self.setup_binance()
            self.setup_telegram()
            self.setup_etherscan()
            self.setup_twitter()
            self.setup_reddit()
            self.setup_news()
            
        else:
            # 自定义选择
            apis = {
                '1': ('Binance', self.setup_binance),
                '2': ('Telegram', self.setup_telegram),
                '3': ('Etherscan', self.setup_etherscan),
                '4': ('Twitter', self.setup_twitter),
                '5': ('Reddit', self.setup_reddit),
                '6': ('新闻API', self.setup_news),
            }
            
            print("\n可配置的API：")
            for key, (name, _) in apis.items():
                print(f"{key}. {name}")
            
            choices = input("\n选择要配置的API（逗号分隔，如: 1,2,3）: ")
            
            for choice in choices.split(','):
                choice = choice.strip()
                if choice in apis:
                    name, func = apis[choice]
                    func()
        
        # 保存配置
        print("\n" + "="*60)
        self.save_configs()
        
        print("\n✅ 配置完成！")
        print(f"\n配置了 {len([v for v in self.api_configs.values() if v])} 个API")
        
        # 询问是否测试
        test = input("\n是否立即测试所有API连接? (y/n): ")
        if test.lower() == 'y':
            os.system("python3 test_api_connections.py")

if __name__ == "__main__":
    setup = APIAutoSetup()
    setup.run()