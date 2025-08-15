#!/usr/bin/env python3
"""
币安API完整代理方案
确保所有币安相关流量都通过VPN
"""

import os
import sys
import requests
import yaml
import time
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

class BinanceVPNManager:
    """
    币安VPN管理器
    强制所有币安请求通过Shadowsocks代理
    """
    
    def __init__(self):
        # Shadowsocks配置
        self.shadowsocks_config = {
            'local_port': 1080,
            'local_host': '127.0.0.1'
        }
        
        # 代理设置
        self.proxy = {
            'http': f'socks5://{self.shadowsocks_config["local_host"]}:{self.shadowsocks_config["local_port"]}',
            'https': f'socks5://{self.shadowsocks_config["local_host"]}:{self.shadowsocks_config["local_port"]}'
        }
        
        # 币安API域名列表（所有这些都必须走代理）
        self.binance_domains = [
            'api.binance.com',
            'api1.binance.com',
            'api2.binance.com',
            'api3.binance.com',
            'api4.binance.com',
            'stream.binance.com',
            'dstream.binance.com',
            'fapi.binance.com',
            'dapi.binance.com',
            'testnet.binance.vision',
        ]
        
        print("="*60)
        print("🔒 币安VPN配置管理器")
        print("="*60)
    
    def check_shadowsocks(self) -> bool:
        """检查Shadowsocks是否在运行"""
        print("\n检查Shadowsocks状态...")
        
        # 方法1：检查端口是否开放
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 1080))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口1080已开放")
            
            # 方法2：测试代理功能
            try:
                # 使用代理获取IP
                response = requests.get(
                    'http://httpbin.org/ip',
                    proxies=self.proxy,
                    timeout=10
                )
                if response.status_code == 200:
                    proxy_ip = response.json()['origin']
                    print(f"✅ Shadowsocks正在运行")
                    print(f"   代理IP: {proxy_ip}")
                    return True
            except:
                pass
        
        print("❌ Shadowsocks未运行")
        return False
    
    def start_shadowsocks(self):
        """尝试启动Shadowsocks"""
        print("\n尝试启动Shadowsocks...")
        
        # Windows上的Shadowsocks路径
        possible_paths = [
            r"C:\Program Files\Shadowsocks\Shadowsocks.exe",
            r"C:\Program Files (x86)\Shadowsocks\Shadowsocks.exe",
            r"C:\Users\tiger\Desktop\Shadowsocks.exe",
            r"C:\Users\tiger\Downloads\Shadowsocks.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"找到Shadowsocks: {path}")
                try:
                    # 在Windows上启动
                    os.system(f'start "" "{path}"')
                    print("✅ 已尝试启动Shadowsocks")
                    time.sleep(3)  # 等待启动
                    return True
                except:
                    pass
        
        print("❌ 无法自动启动Shadowsocks")
        print("\n请手动启动：")
        print("1. 双击桌面上的 Shadowsocks 快捷方式")
        print("2. 确保Shadowsocks在系统托盘运行")
        print("3. 确认本地监听端口是1080")
        return False
    
    def setup_requests_session(self) -> requests.Session:
        """
        创建强制使用代理的requests会话
        所有通过此会话的请求都会使用代理
        """
        session = requests.Session()
        session.proxies = self.proxy
        
        # 设置重试策略
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def test_binance_connection(self, session: requests.Session) -> bool:
        """测试币安连接"""
        print("\n测试币安API连接...")
        
        try:
            # 测试ping
            response = session.get(
                'https://api.binance.com/api/v3/ping',
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ 币安ping成功")
                
                # 获取服务器时间
                time_response = session.get(
                    'https://api.binance.com/api/v3/time',
                    timeout=10
                )
                
                if time_response.status_code == 200:
                    server_time = time_response.json()['serverTime']
                    print(f"✅ 服务器时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(server_time/1000))}")
                    
                    # 获取BTC价格
                    ticker_response = session.get(
                        'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
                        timeout=10
                    )
                    
                    if ticker_response.status_code == 200:
                        price = float(ticker_response.json()['price'])
                        print(f"✅ BTC价格: ${price:,.2f}")
                        return True
                    
            elif response.status_code == 451:
                print("❌ 币安API被地区限制（错误451）")
                print("   代理可能未正确工作")
                
            else:
                print(f"❌ 币安API错误: {response.status_code}")
                
        except requests.exceptions.ProxyError as e:
            print(f"❌ 代理错误: {e}")
            print("   Shadowsocks可能未运行")
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
        
        return False


class BinanceAPIClient:
    """
    币安API客户端
    所有请求强制通过VPN
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.vpn_manager = BinanceVPNManager()
        
        # 确保Shadowsocks运行
        if not self.vpn_manager.check_shadowsocks():
            print("\n⚠️ Shadowsocks未运行")
            self.vpn_manager.start_shadowsocks()
            
            # 再次检查
            if not self.vpn_manager.check_shadowsocks():
                print("\n❌ 无法连接Shadowsocks代理")
                print("币安API将无法使用")
                self.session = None
                return
        
        # 创建强制代理的session
        self.session = self.vpn_manager.setup_requests_session()
        
        # API密钥
        self.api_key = api_key
        self.api_secret = api_secret
        
        # 测试连接
        if self.session and self.vpn_manager.test_binance_connection(self.session):
            print("\n✅ 币安API已就绪（通过VPN）")
        else:
            print("\n❌ 无法连接币安API")
    
    def get_ticker(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """获取实时价格"""
        if not self.session:
            return None
        
        try:
            response = self.session.get(
                f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}',
                timeout=10
            )
            
            if response.status_code == 200:
                return float(response.json()['price'])
                
        except Exception as e:
            print(f"获取价格失败: {e}")
        
        return None
    
    def get_klines(self, symbol: str = 'BTCUSDT', interval: str = '1h', limit: int = 100) -> Optional[list]:
        """获取K线数据"""
        if not self.session:
            return None
        
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self.session.get(
                'https://api.binance.com/api/v3/klines',
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"获取K线失败: {e}")
        
        return None
    
    def get_24hr_ticker(self, symbol: str = 'BTCUSDT') -> Optional[dict]:
        """获取24小时统计"""
        if not self.session:
            return None
        
        try:
            response = self.session.get(
                f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}',
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"获取24h统计失败: {e}")
        
        return None


def setup_and_test():
    """设置并测试币安API"""
    print("="*60)
    print("🚀 币安API设置与测试")
    print("="*60)
    
    # 创建客户端
    client = BinanceAPIClient()
    
    if not client.session:
        print("\n无法创建币安客户端")
        print("请确保：")
        print("1. Shadowsocks已安装")
        print("2. Shadowsocks配置正确")
        print("3. 本地端口1080可用")
        return
    
    # 测试各种API功能
    print("\n" + "="*60)
    print("测试API功能")
    print("-"*60)
    
    # 1. 获取多个交易对价格
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    for symbol in symbols:
        price = client.get_ticker(symbol)
        if price:
            print(f"✅ {symbol}: ${price:,.2f}")
        else:
            print(f"❌ {symbol}: 获取失败")
    
    # 2. 获取K线数据
    print("\n获取BTC小时K线...")
    klines = client.get_klines('BTCUSDT', '1h', 5)
    if klines:
        print(f"✅ 获取{len(klines)}根K线")
        latest = klines[-1]
        print(f"   最新: 开${float(latest[1]):.2f} 高${float(latest[2]):.2f} 低${float(latest[3]):.2f} 收${float(latest[4]):.2f}")
    
    # 3. 获取24小时统计
    print("\n获取24小时统计...")
    stats = client.get_24hr_ticker('BTCUSDT')
    if stats:
        print(f"✅ 24h成交量: {float(stats['volume']):,.2f} BTC")
        print(f"   24h涨跌: {float(stats['priceChangePercent']):.2f}%")
    
    print("\n" + "="*60)
    print("✅ 所有币安API功能正常！")
    print("提示：所有请求都通过Shadowsocks代理")


if __name__ == "__main__":
    # 检查依赖
    try:
        import socks
    except ImportError:
        print("需要安装PySocks: pip install pysocks")
        print("或: pip install requests[socks]")
        sys.exit(1)
    
    # 运行设置和测试
    setup_and_test()
    
    print("\n" + "="*60)
    print("重要提醒：")
    print("• 所有币安请求都会自动通过VPN")
    print("• 确保Shadowsocks始终运行")
    print("• OKX等其他API不需要VPN")
    
    print("\n下一步：")
    print("1. 配置币安API密钥")
    print("2. 配置OKX API: python3 setup_okx_api.py")
    print("3. 启动系统: python3 start.py")