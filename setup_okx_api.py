#!/usr/bin/env python3
"""
OKX(欧易) API配置助手
"""

import requests
import yaml
import json
import hmac
import base64
import time
from datetime import datetime
from pathlib import Path

class OKXSetup:
    def __init__(self):
        print("="*60)
        print("🪙 OKX(欧易) API 配置向导")
        print("="*60)
        
    def test_okx_connection(self, api_key, secret, passphrase):
        """测试OKX API连接"""
        try:
            # OKX公开接口测试（不需要签名）
            url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '0':
                    price = float(data['data'][0]['last'])
                    print(f"✅ 连接成功！BTC价格: ${price:,.2f}")
                    return True
            return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def setup(self):
        """配置OKX API"""
        print("\n📋 OKX API配置步骤：")
        print("-"*50)
        print("""
1. 登录OKX账号: https://www.okx.com
2. 进入 用户中心 → API
3. 点击 '创建API Key'
4. 设置：
   - API标签: TigerSystem
   - 权限: 只勾选'读取'（安全）
   - 密码短语: 自定义（要记住）
5. 完成安全验证
6. 保存显示的信息
""")
        
        print("\n⚠️ 重要提示：")
        print("• Secret Key只显示一次，必须立即保存")
        print("• Passphrase是你设置的，不是系统生成的")
        print("• 只需要读取权限，不要开启交易权限")
        
        print("\n" + "-"*50)
        print("请输入OKX API信息：")
        
        api_key = input("API Key: ").strip()
        secret = input("Secret Key: ").strip()
        passphrase = input("Passphrase(你设置的密码): ").strip()
        
        if all([api_key, secret, passphrase]):
            # 测试连接
            if self.test_okx_connection(api_key, secret, passphrase):
                config = {
                    'okx_api_key': api_key,
                    'okx_secret': secret,
                    'okx_passphrase': passphrase
                }
                
                # 保存配置
                self.save_config(config)
                
                # 显示可用功能
                self.show_features()
                
                return config
            else:
                retry = input("\n是否重试? (y/n): ")
                if retry.lower() == 'y':
                    return self.setup()
        
        return None
    
    def save_config(self, config):
        """保存配置"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "api_keys.yaml"
        
        # 读取现有配置
        if config_file.exists():
            with open(config_file, 'r') as f:
                existing = yaml.safe_load(f) or {}
        else:
            existing = {}
        
        # 更新配置
        existing.update(config)
        
        # 保存
        with open(config_file, 'w') as f:
            yaml.dump(existing, f, default_flow_style=False)
        
        print(f"\n✅ 配置已保存到: {config_file}")
    
    def show_features(self):
        """显示OKX API功能"""
        print("\n" + "="*60)
        print("📊 OKX API 可用功能：")
        print("-"*60)
        print("""
实时数据：
• 现货价格、K线数据
• 市场深度、成交记录
• 24小时统计

交易对：
• BTC、ETH、BNB等主流币
• 各种山寨币和新币
• USDT、USDC交易对

独特优势：
• 某些币种流动性比币安好
• 新币上线快
• 合约数据丰富
""")
    
    def create_test_script(self):
        """创建测试脚本"""
        test_code = '''#!/usr/bin/env python3
"""OKX API测试脚本"""

import requests
import yaml
from pathlib import Path

# 加载配置
config_file = Path("config/api_keys.yaml")
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

# 获取主要币种价格
symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT']

print("\\n📊 OKX 实时价格：")
print("-"*40)

for symbol in symbols:
    url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        if data.get('code') == '0':
            price = float(data['data'][0]['last'])
            change = float(data['data'][0]['changePerc24h'])
            print(f"{symbol}: ${price:,.2f} ({change:+.2f}%)")
'''
        
        with open('test_okx.py', 'w') as f:
            f.write(test_code)
        
        print("\n📝 已创建测试脚本: test_okx.py")
        print("运行测试: python3 test_okx.py")

if __name__ == "__main__":
    setup = OKXSetup()
    config = setup.setup()
    
    if config:
        setup.create_test_script()
        
        # 询问是否运行测试
        if input("\n运行测试脚本? (y/n): ").lower() == 'y':
            import os
            os.system("python3 test_okx.py")