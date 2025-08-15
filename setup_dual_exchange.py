#!/usr/bin/env python3
"""
双交易所配置向导
同时配置币安和OKX，实现数据互补
"""

import os
import sys
import yaml
import requests
import time
from pathlib import Path
from datetime import datetime
import subprocess

class DualExchangeSetup:
    """双交易所配置管理"""
    
    def __init__(self):
        self.config_file = Path("config/api_keys.yaml")
        self.config = self.load_config()
        
        # Shadowsocks代理（仅币安使用）
        self.proxy = {
            'http': 'socks5://127.0.0.1:1080',
            'https': 'socks5://127.0.0.1:1080'
        }
        
        print("="*60)
        print("🏦 双交易所配置向导")
        print("="*60)
        print("""
配置策略：
• 币安 - 通过Shadowsocks代理访问
• OKX - 直接连接
• 数据互补，风险分散
""")
    
    def load_config(self):
        """加载现有配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def save_config(self):
        """保存配置"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        print(f"✅ 配置已保存: {self.config_file}")
    
    def check_shadowsocks(self):
        """检查Shadowsocks状态"""
        print("\n检查Shadowsocks状态...")
        
        try:
            # 测试代理
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=self.proxy,
                timeout=5
            )
            if response.status_code == 200:
                ip = response.json()['origin']
                print(f"✅ Shadowsocks正在运行 (IP: {ip})")
                return True
        except:
            pass
        
        print("❌ Shadowsocks未运行")
        print("\n请启动Shadowsocks：")
        print("1. 双击桌面上的 Shadowsocks.exe 快捷方式")
        print("2. 确保在系统托盘运行")
        print("3. 本地端口应该是1080")
        
        retry = input("\n已启动Shadowsocks? (y/n): ")
        if retry.lower() == 'y':
            return self.check_shadowsocks()
        
        return False
    
    def test_binance(self):
        """测试币安连接"""
        print("\n测试币安API...")
        
        if not self.check_shadowsocks():
            print("⚠️ 跳过币安（需要Shadowsocks）")
            return False
        
        try:
            # 通过代理访问币安
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
                proxies=self.proxy,
                timeout=10
            )
            
            if response.status_code == 200:
                price = float(response.json()['price'])
                print(f"✅ 币安连接成功: BTC ${price:,.2f}")
                return True
            elif response.status_code == 451:
                print("❌ 币安被限制（需要VPN）")
            else:
                print(f"❌ 币安错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 币安连接失败: {str(e)[:50]}")
        
        return False
    
    def test_okx(self):
        """测试OKX连接"""
        print("\n测试OKX API...")
        
        try:
            # 直连OKX
            response = requests.get(
                'https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    price = float(data['data'][0]['last'])
                    print(f"✅ OKX连接成功: BTC ${price:,.2f}")
                    return True
            else:
                print(f"❌ OKX错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ OKX连接失败: {str(e)[:50]}")
        
        return False
    
    def setup_binance(self):
        """配置币安API"""
        print("\n" + "="*50)
        print("配置币安API")
        print("-"*50)
        
        if not self.test_binance():
            skip = input("\n币安不可用，是否跳过? (y/n) [y]: ") or 'y'
            if skip.lower() == 'y':
                return False
        
        print("\n访问: https://www.binance.com/zh-CN/my/settings/api-management")
        print("创建API（只需要读取权限）")
        
        api_key = input("\nAPI Key (直接回车跳过): ").strip()
        secret = input("Secret Key: ").strip()
        
        if api_key and secret:
            self.config.update({
                'binance_api_key': api_key,
                'binance_secret': secret,
                'binance_use_proxy': True,
                'binance_proxy_type': 'shadowsocks'
            })
            print("✅ 币安API已配置")
            return True
        
        return False
    
    def setup_okx(self):
        """配置OKX API"""
        print("\n" + "="*50)
        print("配置OKX API")
        print("-"*50)
        
        if not self.test_okx():
            print("⚠️ OKX连接有问题，但可以继续配置")
        
        print("\n访问: https://www.okx.com/account/my-api")
        print("创建API（只需要读取权限）")
        
        api_key = input("\nAPI Key (直接回车跳过): ").strip()
        secret = input("Secret Key: ").strip()
        passphrase = input("Passphrase: ").strip()
        
        if all([api_key, secret, passphrase]):
            self.config.update({
                'okx_api_key': api_key,
                'okx_secret': secret,
                'okx_passphrase': passphrase,
                'okx_use_proxy': False
            })
            print("✅ OKX API已配置")
            return True
        
        return False
    
    def setup_all(self):
        """配置所有交易所"""
        binance_ok = self.setup_binance()
        okx_ok = self.setup_okx()
        
        if binance_ok or okx_ok:
            self.save_config()
            
            print("\n" + "="*60)
            print("配置结果")
            print("-"*60)
            
            if binance_ok:
                print("✅ 币安: 已配置（通过VPN）")
            else:
                print("⚠️ 币安: 未配置")
            
            if okx_ok:
                print("✅ OKX: 已配置（直连）")
            else:
                print("⚠️ OKX: 未配置")
            
            if binance_ok and okx_ok:
                print("\n🎉 双交易所配置完成！")
                print("优势：")
                print("• 数据互补")
                print("• 价差监控")
                print("• 故障备份")
            elif binance_ok or okx_ok:
                print("\n✅ 至少一个交易所可用")
            
            return True
        
        print("\n❌ 没有配置任何交易所")
        return False


class DualExchangeClient:
    """双交易所数据客户端"""
    
    def __init__(self):
        self.config = self.load_config()
        self.setup_clients()
    
    def load_config(self):
        """加载配置"""
        config_file = Path("config/api_keys.yaml")
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def setup_clients(self):
        """设置客户端"""
        # 币安客户端（使用代理）
        self.binance_session = None
        if self.config.get('binance_api_key'):
            session = requests.Session()
            if self.config.get('binance_use_proxy'):
                session.proxies = {
                    'http': 'socks5://127.0.0.1:1080',
                    'https': 'socks5://127.0.0.1:1080'
                }
            self.binance_session = session
        
        # OKX客户端（直连）
        self.okx_session = requests.Session() if self.config.get('okx_api_key') else None
    
    def get_price_comparison(self, symbol='BTC'):
        """获取价格对比"""
        prices = {}
        
        # 币安价格
        if self.binance_session:
            try:
                response = self.binance_session.get(
                    f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT',
                    timeout=10
                )
                if response.status_code == 200:
                    prices['binance'] = float(response.json()['price'])
            except:
                pass
        
        # OKX价格
        if self.okx_session:
            try:
                response = self.okx_session.get(
                    f'https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == '0':
                        prices['okx'] = float(data['data'][0]['last'])
            except:
                pass
        
        return prices
    
    def show_arbitrage_opportunity(self):
        """显示套利机会"""
        print("\n" + "="*60)
        print("💰 套利机会扫描")
        print("-"*60)
        
        symbols = ['BTC', 'ETH', 'BNB', 'SOL']
        
        for symbol in symbols:
            prices = self.get_price_comparison(symbol)
            
            if len(prices) == 2:
                binance_price = prices.get('binance', 0)
                okx_price = prices.get('okx', 0)
                
                if binance_price and okx_price:
                    diff = abs(binance_price - okx_price)
                    diff_pct = (diff / min(binance_price, okx_price)) * 100
                    
                    print(f"\n{symbol}:")
                    print(f"  币安: ${binance_price:,.2f}")
                    print(f"  OKX:  ${okx_price:,.2f}")
                    print(f"  差价: ${diff:.2f} ({diff_pct:.3f}%)")
                    
                    if diff_pct > 0.1:  # 超过0.1%
                        if binance_price > okx_price:
                            print(f"  📈 机会: OKX买入 → 币安卖出")
                        else:
                            print(f"  📈 机会: 币安买入 → OKX卖出")
            elif len(prices) == 1:
                exchange = list(prices.keys())[0]
                price = list(prices.values())[0]
                print(f"\n{symbol}: 仅{exchange} ${price:,.2f}")


def main():
    """主函数"""
    print("🚀 Tiger系统 - 双交易所配置")
    print("\n选择操作：")
    print("1. 配置双交易所")
    print("2. 测试连接")
    print("3. 查看套利机会")
    print("4. 退出")
    
    choice = input("\n选择 (1-4) [1]: ") or "1"
    
    if choice == "1":
        setup = DualExchangeSetup()
        if setup.setup_all():
            # 测试配置
            client = DualExchangeClient()
            client.show_arbitrage_opportunity()
    
    elif choice == "2":
        setup = DualExchangeSetup()
        setup.test_binance()
        setup.test_okx()
    
    elif choice == "3":
        client = DualExchangeClient()
        client.show_arbitrage_opportunity()
    
    print("\n" + "="*60)
    print("提示：")
    print("• 币安需要Shadowsocks代理")
    print("• OKX直接连接")
    print("• 两个交易所数据互补最佳")


if __name__ == "__main__":
    main()