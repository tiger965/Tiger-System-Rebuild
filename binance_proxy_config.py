#!/usr/bin/env python3
"""
币安专用代理配置
使用桌面上的Shadowsocks，只为币安流量配置代理
"""

import requests
import yaml
import json
from pathlib import Path
from typing import Optional

class BinanceProxyClient:
    """
    币安专用代理客户端
    - 使用Shadowsocks代理访问币安
    - OKX和其他API直连
    """
    
    def __init__(self):
        # Shadowsocks本地代理端口（默认配置）
        self.proxy = {
            'http': 'socks5://127.0.0.1:1080',
            'https': 'socks5://127.0.0.1:1080'
        }
        
        print("="*60)
        print("🔒 币安代理配置")
        print("="*60)
        print("使用Shadowsocks代理访问币安API")
        print(f"代理地址: 127.0.0.1:1080")
        print("-"*60)
        
        # 测试代理
        self.test_proxy()
    
    def test_proxy(self):
        """测试Shadowsocks代理"""
        print("\n检查Shadowsocks状态...")
        
        try:
            # 测试代理连接
            response = requests.get(
                'https://api.ipify.org?format=json',
                proxies=self.proxy,
                timeout=10
            )
            
            if response.status_code == 200:
                proxy_ip = response.json()['ip']
                print(f"✅ Shadowsocks正在运行")
                print(f"   代理IP: {proxy_ip}")
                
                # 获取IP位置信息
                try:
                    geo = requests.get(
                        f'http://ip-api.com/json/{proxy_ip}',
                        timeout=5
                    )
                    if geo.status_code == 200:
                        location = geo.json()
                        country = location.get('country', 'Unknown')
                        city = location.get('city', '')
                        print(f"   位置: {country} {city}")
                except:
                    pass
                
                return True
            else:
                print("❌ 代理连接失败")
                return False
                
        except requests.exceptions.ProxyError:
            print("❌ Shadowsocks未运行")
            print("\n请启动Shadowsocks：")
            print("1. 双击桌面上的 'Shadowsocks.exe - 快捷方式'")
            print("2. 确保Shadowsocks在系统托盘运行")
            print("3. 确认本地端口是1080")
            return False
            
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False
    
    def get_binance_ticker(self, symbol='BTCUSDT'):
        """获取币安价格（通过代理）"""
        try:
            print(f"\n📊 获取币安 {symbol} 价格...")
            
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            
            # 使用代理访问币安
            response = requests.get(
                url,
                proxies=self.proxy,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                print(f"✅ 币安(代理): {symbol} = ${price:,.2f}")
                return price
                
            elif response.status_code == 451:
                print("❌ 币安API被限制（451错误）")
                print("   请检查Shadowsocks是否正常工作")
                return None
                
            else:
                print(f"❌ API错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            return None
    
    def get_okx_ticker(self, symbol='BTC-USDT'):
        """获取OKX价格（直连，不用代理）"""
        try:
            print(f"\n📊 获取OKX {symbol} 价格...")
            
            url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
            
            # 直连，不使用代理
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    price = float(data['data'][0]['last'])
                    print(f"✅ OKX(直连): {symbol} = ${price:,.2f}")
                    return price
            
            print(f"❌ OKX API错误: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            return None
    
    def get_binance_klines(self, symbol='BTCUSDT', interval='1h', limit=100):
        """获取币安K线数据（通过代理）"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            # 使用代理
            response = requests.get(
                url,
                params=params,
                proxies=self.proxy,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取K线失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"请求失败: {e}")
            return None


def setup_binance_with_proxy():
    """配置币安API（使用Shadowsocks）"""
    print("="*60)
    print("🪙 币安API配置（Shadowsocks代理）")
    print("="*60)
    
    # 创建代理客户端
    client = BinanceProxyClient()
    
    # 如果代理不可用，提示启动
    if not client.test_proxy():
        print("\n" + "="*60)
        print("请先启动Shadowsocks，然后重新运行此脚本")
        return False
    
    # 测试币安连接
    print("\n" + "-"*60)
    print("测试币安API连接...")
    
    btc_price = client.get_binance_ticker('BTCUSDT')
    
    if btc_price:
        print("\n✅ 币安API可以正常访问！")
        
        # 保存配置
        print("\n" + "-"*60)
        print("配置币安API密钥")
        print("\n访问: https://www.binance.com/zh-CN/my/settings/api-management")
        print("创建API密钥（只需要读取权限）")
        
        api_key = input("\nAPI Key: ").strip()
        secret = input("Secret Key: ").strip()
        
        if api_key and secret:
            # 保存配置
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / "api_keys.yaml"
            
            # 读取现有配置
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}
            
            # 更新币安配置
            config.update({
                'binance_api_key': api_key,
                'binance_secret': secret,
                'binance_use_proxy': True,
                'binance_proxy_type': 'shadowsocks',
                'binance_proxy_port': 1080
            })
            
            # 保存
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"\n✅ 币安API配置已保存")
            print(f"   配置文件: {config_file}")
            
            return True
    else:
        print("\n❌ 无法访问币安API")
        print("可能的原因：")
        print("1. Shadowsocks未正确配置")
        print("2. 代理服务器无法访问币安")
        print("3. 网络连接问题")
        
        print("\n建议使用OKX作为替代")
        
        return False


def test_all_exchanges():
    """测试所有交易所连接"""
    print("="*60)
    print("🔍 测试所有交易所连接")
    print("="*60)
    
    client = BinanceProxyClient()
    
    # 测试币安（代理）
    binance_price = client.get_binance_ticker('BTCUSDT')
    
    # 测试OKX（直连）
    okx_price = client.get_okx_ticker('BTC-USDT')
    
    print("\n" + "="*60)
    print("测试结果：")
    print("-"*60)
    
    if binance_price:
        print(f"✅ 币安: 可用 (通过Shadowsocks)")
    else:
        print(f"❌ 币安: 不可用")
    
    if okx_price:
        print(f"✅ OKX: 可用 (直连)")
    else:
        print(f"❌ OKX: 不可用")
    
    if binance_price or okx_price:
        print("\n✅ 至少有一个交易所可用，系统可以运行")
    else:
        print("\n❌ 没有可用的交易所API")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # 测试模式
        test_all_exchanges()
    else:
        # 配置模式
        success = setup_binance_with_proxy()
        
        if success:
            print("\n下一步：")
            print("1. 配置OKX: python3 setup_okx_api.py")
            print("2. 测试连接: python3 binance_proxy_config.py test")
            print("3. 启动系统: python3 start.py")