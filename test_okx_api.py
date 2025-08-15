#!/usr/bin/env python3
"""
测试OKX API连接
"""

import requests
import yaml
import json
import hmac
import base64
import time
from datetime import datetime
from pathlib import Path

class OKXTester:
    def __init__(self):
        # 加载配置
        config_file = Path("config/api_keys.yaml")
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.api_key = self.config['okx_api_key']
        self.secret = self.config['okx_secret']
        self.passphrase = self.config.get('okx_passphrase', '')
        
        print("="*60)
        print("🔍 OKX API 测试")
        print("="*60)
        print(f"API Key: {self.api_key[:10]}...")
        print(f"API名称: {self.config.get('okx_api_name', 'Unknown')}")
        print(f"权限: {self.config.get('okx_permissions', 'Unknown')}")
        
        if not self.passphrase:
            print("\n⚠️ 警告：未设置Passphrase")
            print("请输入你在创建API时设置的Passphrase")
            self.passphrase = input("Passphrase: ").strip()
            
            if self.passphrase:
                # 保存到配置
                self.config['okx_passphrase'] = self.passphrase
                with open(config_file, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                print("✅ Passphrase已保存")
    
    def test_public_api(self):
        """测试公开API（不需要认证）"""
        print("\n" + "-"*60)
        print("1. 测试公开API（不需要认证）")
        print("-"*60)
        
        # 获取BTC价格
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    ticker = data['data'][0]
                    price = float(ticker['last'])
                    vol = float(ticker['vol24h'])
                    change = float(ticker['sodUtc8'])
                    
                    print(f"✅ 公开API连接成功")
                    print(f"   BTC-USDT: ${price:,.2f}")
                    print(f"   24h成交量: {vol:,.0f} BTC")
                    print(f"   24h涨跌: {change:.2f}%")
                    return True
                else:
                    print(f"❌ API返回错误: {data}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
        
        return False
    
    def get_signature(self, timestamp, method, request_path, body=''):
        """生成OKX API签名"""
        if body:
            message = timestamp + method + request_path + body
        else:
            message = timestamp + method + request_path
        
        mac = hmac.new(
            bytes(self.secret, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        d = mac.digest()
        return base64.b64encode(d).decode()
    
    def test_private_api(self):
        """测试私有API（需要认证）"""
        print("\n" + "-"*60)
        print("2. 测试私有API（需要认证）")
        print("-"*60)
        
        if not self.passphrase:
            print("❌ 需要Passphrase才能访问私有API")
            return False
        
        # 获取账户信息
        timestamp = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
        request_path = "/api/v5/account/balance"
        
        signature = self.get_signature(timestamp, 'GET', request_path)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        url = f"https://www.okx.com{request_path}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    print(f"✅ 私有API认证成功")
                    
                    # 显示账户信息
                    if data['data']:
                        print(f"   账户信息获取成功")
                        # 这里可以显示余额等信息
                    return True
                else:
                    print(f"❌ API错误: {data.get('msg', 'Unknown error')}")
                    if data['code'] == '50111':
                        print("   提示：Passphrase错误")
                    elif data['code'] == '50103':
                        print("   提示：API Key无效")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
        
        return False
    
    def test_market_data(self):
        """测试市场数据获取"""
        print("\n" + "-"*60)
        print("3. 测试市场数据获取")
        print("-"*60)
        
        # 获取多个交易对
        symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT']
        
        for symbol in symbols:
            url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == '0':
                        price = float(data['data'][0]['last'])
                        print(f"✅ {symbol}: ${price:,.2f}")
            except:
                print(f"❌ {symbol}: 获取失败")
        
        # 获取K线数据
        print("\n获取BTC 1小时K线...")
        url = "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=1H&limit=5"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    candles = data['data']
                    print(f"✅ 获取{len(candles)}根K线")
                    latest = candles[0]
                    print(f"   最新: 开${float(latest[1]):.2f} 高${float(latest[2]):.2f} 低${float(latest[3]):.2f} 收${float(latest[4]):.2f}")
        except:
            print("❌ K线获取失败")
    
    def run_all_tests(self):
        """运行所有测试"""
        # 1. 测试公开API
        public_ok = self.test_public_api()
        
        # 2. 测试私有API
        private_ok = self.test_private_api()
        
        # 3. 测试市场数据
        self.test_market_data()
        
        # 总结
        print("\n" + "="*60)
        print("📊 测试总结")
        print("-"*60)
        
        if public_ok:
            print("✅ 公开API: 正常")
        else:
            print("❌ 公开API: 失败")
        
        if private_ok:
            print("✅ 私有API: 正常（可以获取账户信息）")
        elif self.passphrase:
            print("❌ 私有API: 认证失败（检查Passphrase）")
        else:
            print("⚠️ 私有API: 未测试（需要Passphrase）")
        
        if public_ok:
            print("\n🎉 OKX API可以使用！")
            print("   • 可以获取实时行情")
            print("   • 可以获取K线数据")
            if private_ok:
                print("   • 可以获取账户信息")
            
            return True
        
        return False


def main():
    """主函数"""
    tester = OKXTester()
    
    # 运行所有测试
    success = tester.run_all_tests()
    
    if success:
        print("\n" + "="*60)
        print("下一步：")
        print("1. 配置币安API（需要Shadowsocks）")
        print("2. 启动完整系统: python3 start.py")
    else:
        print("\n请检查网络连接和API配置")

if __name__ == "__main__":
    main()