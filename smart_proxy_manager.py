#!/usr/bin/env python3
"""
智能代理管理器
只为币安API请求使用VPN，其他请求直连
"""

import os
import requests
import yaml
from pathlib import Path
from typing import Optional, Dict
import json

class SmartProxyManager:
    """
    智能代理管理器
    - 币安相关请求走VPN
    - OKX和其他请求直连
    - 自动切换代理
    """
    
    def __init__(self):
        self.config_file = Path("config/proxy_config.yaml")
        self.load_config()
        
        # 需要代理的域名列表
        self.proxy_domains = [
            'api.binance.com',
            'api.binance.us',
            'stream.binance.com',
            'dstream.binance.com',
            'fapi.binance.com',  # 期货API
            'dapi.binance.com',  # 币本位合约
        ]
        
        # 不需要代理的域名（直连）
        self.direct_domains = [
            'www.okx.com',
            'api.coingecko.com',
            'api.telegram.org',
            'api.reddit.com',
            'etherscan.io',
            'cryptopanic.com',
        ]
    
    def load_config(self):
        """加载已有的VPN配置"""
        # 检查桌面上的VPN配置
        desktop_vpn_configs = [
            Path("/mnt/c/Users/tiger/Desktop/vpn_config.txt"),
            Path("/mnt/c/Users/tiger/Desktop/VPN配置.txt"),
            Path("/mnt/c/Users/tiger/Desktop/binance_vpn.json"),
        ]
        
        vpn_config = None
        for config_path in desktop_vpn_configs:
            if config_path.exists():
                print(f"✅ 找到VPN配置: {config_path}")
                # 读取配置
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if config_path.suffix == '.json':
                        vpn_config = json.loads(content)
                    else:
                        # 解析文本格式配置
                        vpn_config = self.parse_text_config(content)
                break
        
        if vpn_config:
            self.proxy_settings = self.build_proxy_settings(vpn_config)
            print(f"✅ VPN配置已加载")
        else:
            # 使用默认配置
            self.proxy_settings = {
                'http': 'socks5://127.0.0.1:1080',
                'https': 'socks5://127.0.0.1:1080'
            }
            print("⚠️ 使用默认VPN配置 (127.0.0.1:1080)")
    
    def parse_text_config(self, content: str) -> dict:
        """解析文本格式的VPN配置"""
        config = {}
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                config[key.strip().lower()] = value.strip()
        return config
    
    def build_proxy_settings(self, vpn_config: dict) -> dict:
        """构建代理设置"""
        # 支持多种配置格式
        if 'proxy' in vpn_config:
            return {
                'http': vpn_config['proxy'],
                'https': vpn_config['proxy']
            }
        elif 'socks5' in vpn_config:
            return {
                'http': f"socks5://{vpn_config['socks5']}",
                'https': f"socks5://{vpn_config['socks5']}"
            }
        elif 'host' in vpn_config and 'port' in vpn_config:
            return {
                'http': f"socks5://{vpn_config['host']}:{vpn_config['port']}",
                'https': f"socks5://{vpn_config['host']}:{vpn_config['port']}"
            }
        else:
            # 默认本地代理
            return {
                'http': 'socks5://127.0.0.1:1080',
                'https': 'socks5://127.0.0.1:1080'
            }
    
    def need_proxy(self, url: str) -> bool:
        """判断URL是否需要代理"""
        for domain in self.proxy_domains:
            if domain in url:
                return True
        return False
    
    def request(self, url: str, **kwargs) -> requests.Response:
        """
        智能请求函数
        - 币安API自动使用VPN
        - 其他API直连
        """
        # 判断是否需要代理
        if self.need_proxy(url):
            kwargs['proxies'] = self.proxy_settings
            print(f"🔒 使用VPN访问: {url.split('?')[0]}")
        else:
            # 直连
            kwargs['proxies'] = None
            print(f"➡️ 直连访问: {url.split('?')[0]}")
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        
        try:
            return requests.get(url, **kwargs)
        except requests.exceptions.ProxyError:
            print("❌ 代理连接失败，请检查VPN是否运行")
            raise
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            raise


class UnifiedAPIClient:
    """
    统一的API客户端
    自动处理VPN和直连
    """
    
    def __init__(self):
        self.proxy_manager = SmartProxyManager()
        self.test_connections()
    
    def test_connections(self):
        """测试各个API连接"""
        print("\n" + "="*60)
        print("🔍 测试API连接")
        print("-"*60)
        
        # 测试币安（通过VPN）
        try:
            response = self.proxy_manager.request(
                "https://api.binance.com/api/v3/ping"
            )
            if response.status_code == 200:
                # 获取价格
                ticker = self.proxy_manager.request(
                    "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
                )
                if ticker.status_code == 200:
                    price = float(ticker.json()['price'])
                    print(f"✅ 币安(VPN): BTC ${price:,.2f}")
                else:
                    print(f"⚠️ 币安: 连接正常但无法获取数据")
            else:
                print(f"❌ 币安: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 币安: {str(e)[:50]}")
        
        # 测试OKX（直连）
        try:
            response = self.proxy_manager.request(
                "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
            )
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    price = float(data['data'][0]['last'])
                    print(f"✅ OKX(直连): BTC ${price:,.2f}")
            else:
                print(f"❌ OKX: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ OKX: {str(e)[:50]}")
    
    def get_binance_data(self, symbol='BTCUSDT', interval='1h', limit=100):
        """获取币安数据（自动使用VPN）"""
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = self.proxy_manager.request(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"币安API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取币安数据失败: {e}")
            return None
    
    def get_okx_data(self, symbol='BTC-USDT', bar='1H', limit=100):
        """获取OKX数据（直连）"""
        url = f"https://www.okx.com/api/v5/market/candles"
        params = {
            'instId': symbol,
            'bar': bar,
            'limit': limit
        }
        
        try:
            response = self.proxy_manager.request(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    return data['data']
            return None
        except Exception as e:
            print(f"获取OKX数据失败: {e}")
            return None
    
    def save_api_config(self, exchange: str, api_key: str, secret: str, **kwargs):
        """保存API配置"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "api_keys.yaml"
        
        # 读取现有配置
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 更新配置
        if exchange.lower() == 'binance':
            config['binance_api_key'] = api_key
            config['binance_secret'] = secret
            config['binance_use_vpn'] = True  # 标记需要VPN
        elif exchange.lower() == 'okx':
            config['okx_api_key'] = api_key
            config['okx_secret'] = secret
            config['okx_passphrase'] = kwargs.get('passphrase', '')
            config['okx_use_vpn'] = False  # 不需要VPN
        
        # 保存
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"✅ {exchange} API配置已保存")


def setup_apis():
    """配置API向导"""
    print("="*60)
    print("🚀 Tiger系统 - 智能API配置")
    print("="*60)
    print("""
系统将自动处理VPN：
• 币安API → 自动使用VPN
• OKX API → 直接连接
• 其他API → 直接连接

你的VPN已经在桌面配置好了！
""")
    
    client = UnifiedAPIClient()
    
    print("\n" + "="*60)
    print("配置交易所API")
    print("-"*60)
    
    # 配置币安
    print("\n1. 币安API（需要VPN）")
    use_binance = input("配置币安? (y/n) [y]: ") or 'y'
    if use_binance.lower() == 'y':
        print("\n请登录币安获取API密钥：")
        print("https://www.binance.com/zh-CN/my/settings/api-management")
        api_key = input("API Key: ").strip()
        secret = input("Secret Key: ").strip()
        
        if api_key and secret:
            client.save_api_config('binance', api_key, secret)
    
    # 配置OKX
    print("\n2. OKX API（直连）")
    use_okx = input("配置OKX? (y/n) [y]: ") or 'y'
    if use_okx.lower() == 'y':
        print("\n请登录OKX获取API密钥：")
        print("https://www.okx.com/account/my-api")
        api_key = input("API Key: ").strip()
        secret = input("Secret Key: ").strip()
        passphrase = input("Passphrase: ").strip()
        
        if all([api_key, secret, passphrase]):
            client.save_api_config('okx', api_key, secret, passphrase=passphrase)
    
    print("\n" + "="*60)
    print("✅ 配置完成！")
    print("\n系统会自动：")
    print("• 币安请求 → 走VPN")
    print("• OKX请求 → 直连")
    print("• 智能切换，无需手动干预")


if __name__ == "__main__":
    # 检查VPN是否运行
    print("检查VPN状态...")
    
    # 尝试连接本地代理
    try:
        test_proxy = {
            'http': 'socks5://127.0.0.1:1080',
            'https': 'socks5://127.0.0.1:1080'
        }
        response = requests.get(
            'https://api.ipify.org?format=json',
            proxies=test_proxy,
            timeout=5
        )
        if response.status_code == 200:
            ip = response.json()['ip']
            print(f"✅ VPN正在运行，代理IP: {ip}")
    except:
        print("⚠️ VPN未运行或未在1080端口")
        print("请先启动桌面上的VPN程序")
        
    # 运行配置向导
    setup_apis()