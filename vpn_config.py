#!/usr/bin/env python3
"""
VPN配置管理器
安全访问受限API（如币安）
"""

import os
import json
import socket
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict
import yaml

class VPNManager:
    """VPN管理器 - 支持多种VPN协议"""
    
    def __init__(self):
        self.config_file = Path("config/vpn_config.yaml")
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """加载VPN配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def save_config(self):
        """保存VPN配置"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def setup_vpn(self):
        """配置VPN"""
        print("="*60)
        print("🔒 VPN配置向导")
        print("="*60)
        print("""
为什么需要VPN？
--------------
• 币安在美国/中国等地区受限
• 避免IP被标记或封禁
• 保护API请求的隐私
• 访问更多交易所

支持的VPN类型：
""")
        
        print("1. SOCKS5代理（推荐）")
        print("2. HTTP/HTTPS代理")
        print("3. Shadowsocks")
        print("4. V2Ray")
        print("5. 系统VPN（OpenVPN/WireGuard）")
        print("6. 不使用VPN（使用OKX等替代）")
        
        choice = input("\n选择VPN类型 (1-6) [6]: ") or "6"
        
        if choice == "1":
            self.setup_socks5()
        elif choice == "2":
            self.setup_http_proxy()
        elif choice == "3":
            self.setup_shadowsocks()
        elif choice == "4":
            self.setup_v2ray()
        elif choice == "5":
            self.setup_system_vpn()
        else:
            print("\n不使用VPN，将只使用不受限的交易所")
            self.config['use_vpn'] = False
            self.save_config()
    
    def setup_socks5(self):
        """配置SOCKS5代理"""
        print("\n配置SOCKS5代理")
        print("-"*40)
        
        host = input("代理地址 [127.0.0.1]: ") or "127.0.0.1"
        port = input("代理端口 [1080]: ") or "1080"
        username = input("用户名（可选）: ")
        password = input("密码（可选）: ")
        
        self.config['vpn_type'] = 'socks5'
        self.config['socks5'] = {
            'host': host,
            'port': int(port),
            'username': username,
            'password': password
        }
        
        # 测试连接
        if self.test_socks5_connection():
            print("✅ SOCKS5代理配置成功")
            self.config['use_vpn'] = True
        else:
            print("❌ SOCKS5代理连接失败")
            self.config['use_vpn'] = False
        
        self.save_config()
    
    def setup_http_proxy(self):
        """配置HTTP代理"""
        print("\n配置HTTP/HTTPS代理")
        print("-"*40)
        
        http_proxy = input("HTTP代理 (如 http://127.0.0.1:7890): ")
        https_proxy = input("HTTPS代理 [同HTTP]: ") or http_proxy
        
        self.config['vpn_type'] = 'http'
        self.config['http_proxy'] = {
            'http': http_proxy,
            'https': https_proxy
        }
        
        # 测试连接
        if self.test_http_proxy():
            print("✅ HTTP代理配置成功")
            self.config['use_vpn'] = True
        else:
            print("❌ HTTP代理连接失败")
            self.config['use_vpn'] = False
        
        self.save_config()
    
    def setup_shadowsocks(self):
        """配置Shadowsocks"""
        print("\n配置Shadowsocks")
        print("-"*40)
        
        server = input("服务器地址: ")
        port = input("服务器端口: ")
        password = input("密码: ")
        method = input("加密方式 [aes-256-gcm]: ") or "aes-256-gcm"
        local_port = input("本地端口 [1080]: ") or "1080"
        
        self.config['vpn_type'] = 'shadowsocks'
        self.config['shadowsocks'] = {
            'server': server,
            'server_port': int(port),
            'password': password,
            'method': method,
            'local_port': int(local_port)
        }
        
        print("\n需要启动Shadowsocks客户端")
        print(f"本地SOCKS5代理将在 127.0.0.1:{local_port}")
        
        self.config['use_vpn'] = True
        self.save_config()
    
    def setup_v2ray(self):
        """配置V2Ray"""
        print("\n配置V2Ray")
        print("-"*40)
        
        config_path = input("V2Ray配置文件路径: ")
        local_port = input("本地SOCKS端口 [1080]: ") or "1080"
        
        self.config['vpn_type'] = 'v2ray'
        self.config['v2ray'] = {
            'config_path': config_path,
            'local_port': int(local_port)
        }
        
        print("\n需要启动V2Ray客户端")
        print(f"本地SOCKS5代理将在 127.0.0.1:{local_port}")
        
        self.config['use_vpn'] = True
        self.save_config()
    
    def setup_system_vpn(self):
        """配置系统VPN"""
        print("\n配置系统VPN（OpenVPN/WireGuard）")
        print("-"*40)
        print("""
请确保系统VPN已经连接：
1. OpenVPN: sudo openvpn --config your-config.ovpn
2. WireGuard: sudo wg-quick up wg0
3. 或使用系统网络管理器

系统VPN会自动路由所有流量，无需额外配置。
""")
        
        # 检查VPN状态
        if self.check_system_vpn():
            print("✅ 检测到系统VPN已连接")
            self.config['vpn_type'] = 'system'
            self.config['use_vpn'] = True
        else:
            print("⚠️ 未检测到VPN连接")
            self.config['use_vpn'] = False
        
        self.save_config()
    
    def test_socks5_connection(self) -> bool:
        """测试SOCKS5连接"""
        try:
            import socks
            import socket
            
            socks.set_default_proxy(
                socks.SOCKS5,
                self.config['socks5']['host'],
                self.config['socks5']['port'],
                username=self.config['socks5'].get('username'),
                password=self.config['socks5'].get('password')
            )
            socket.socket = socks.socksocket
            
            # 测试连接
            response = requests.get('https://api.ipify.org?format=json', timeout=10)
            if response.status_code == 200:
                ip = response.json()['ip']
                print(f"  代理IP: {ip}")
                return True
        except Exception as e:
            print(f"  错误: {e}")
        return False
    
    def test_http_proxy(self) -> bool:
        """测试HTTP代理"""
        try:
            proxies = self.config['http_proxy']
            response = requests.get(
                'https://api.ipify.org?format=json',
                proxies=proxies,
                timeout=10
            )
            if response.status_code == 200:
                ip = response.json()['ip']
                print(f"  代理IP: {ip}")
                return True
        except Exception as e:
            print(f"  错误: {e}")
        return False
    
    def check_system_vpn(self) -> bool:
        """检查系统VPN状态"""
        try:
            # 获取当前IP
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            current_ip = response.json()['ip']
            
            # 获取IP位置
            geo = requests.get(f'http://ip-api.com/json/{current_ip}', timeout=5)
            if geo.status_code == 200:
                data = geo.json()
                country = data.get('country', 'Unknown')
                print(f"  当前IP: {current_ip} ({country})")
                
                # 如果不是中国/美国IP，可能使用了VPN
                if country not in ['China', 'United States']:
                    return True
        except:
            pass
        return False
    
    def get_proxy_settings(self) -> Optional[Dict]:
        """获取代理设置"""
        if not self.config.get('use_vpn'):
            return None
        
        vpn_type = self.config.get('vpn_type')
        
        if vpn_type == 'socks5':
            socks5 = self.config['socks5']
            return {
                'http': f"socks5://{socks5['host']}:{socks5['port']}",
                'https': f"socks5://{socks5['host']}:{socks5['port']}"
            }
        
        elif vpn_type == 'http':
            return self.config['http_proxy']
        
        elif vpn_type in ['shadowsocks', 'v2ray']:
            # 这些通常提供本地SOCKS5代理
            port = self.config.get(vpn_type, {}).get('local_port', 1080)
            return {
                'http': f"socks5://127.0.0.1:{port}",
                'https': f"socks5://127.0.0.1:{port}"
            }
        
        return None


class SafeBinanceAPI:
    """安全的币安API访问（通过VPN）"""
    
    def __init__(self):
        self.vpn = VPNManager()
        self.proxies = self.vpn.get_proxy_settings()
        
        if self.proxies:
            print(f"✅ 使用VPN访问币安API")
        else:
            print("⚠️ 直接访问币安API（可能受限）")
    
    def request(self, url: str, **kwargs) -> requests.Response:
        """发送请求（自动使用代理）"""
        if self.proxies:
            kwargs['proxies'] = self.proxies
        
        # 添加超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        
        return requests.get(url, **kwargs)
    
    def get_ticker(self, symbol='BTCUSDT'):
        """获取实时价格"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = self.request(url)
            
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            elif response.status_code == 451:
                print("❌ 币安API在您的地区受限，请配置VPN")
                return None
            else:
                print(f"❌ API错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def get_klines(self, symbol='BTCUSDT', interval='1h', limit=100):
        """获取K线数据"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self.request(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 无法获取K线: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None


def main():
    """主函数"""
    print("="*60)
    print("🔒 Tiger系统 - VPN配置")
    print("="*60)
    
    vpn = VPNManager()
    
    # 检查现有配置
    if vpn.config.get('use_vpn'):
        print(f"\n✅ 已配置VPN: {vpn.config.get('vpn_type')}")
        print("1. 测试当前VPN")
        print("2. 重新配置VPN")
        print("3. 禁用VPN")
        
        choice = input("\n选择 (1-3) [1]: ") or "1"
        
        if choice == "1":
            # 测试VPN
            print("\n测试VPN连接...")
            api = SafeBinanceAPI()
            price = api.get_ticker('BTCUSDT')
            if price:
                print(f"✅ 币安API可访问，BTC价格: ${price:,.2f}")
            else:
                print("❌ 无法访问币安API")
                
        elif choice == "2":
            vpn.setup_vpn()
            
        elif choice == "3":
            vpn.config['use_vpn'] = False
            vpn.save_config()
            print("✅ 已禁用VPN")
    else:
        print("\n未配置VPN")
        vpn.setup_vpn()
    
    # 测试连接
    print("\n" + "="*60)
    print("测试API连接...")
    print("-"*40)
    
    # 测试币安（可能需要VPN）
    api = SafeBinanceAPI()
    btc_price = api.get_ticker('BTCUSDT')
    if btc_price:
        print(f"✅ 币安: BTC ${btc_price:,.2f}")
    else:
        print("❌ 币安: 无法访问（需要VPN或使用OKX）")
    
    # 测试OKX（通常不需要VPN）
    try:
        okx_response = requests.get(
            "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT",
            timeout=10
        )
        if okx_response.status_code == 200:
            okx_price = float(okx_response.json()['data'][0]['last'])
            print(f"✅ OKX: BTC ${okx_price:,.2f}")
    except:
        print("❌ OKX: 无法访问")
    
    print("\n" + "="*60)
    print("建议：")
    if not btc_price:
        print("• 配置VPN访问币安")
        print("• 或使用OKX作为主要数据源")
    else:
        print("• API访问正常")
        print("• 可以开始配置交易所API")

if __name__ == "__main__":
    # 检查是否需要安装依赖
    try:
        import socks
    except ImportError:
        print("如需SOCKS5支持，请安装: pip install pysocks")
    
    main()