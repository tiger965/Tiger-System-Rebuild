#!/usr/bin/env python3
"""
币安(Binance) API配置助手
"""

import requests
import yaml
import json
from pathlib import Path
from datetime import datetime

class BinanceSetup:
    def __init__(self):
        print("="*60)
        print("🪙 币安(Binance) API 配置向导")
        print("="*60)
        
    def test_connection(self, api_key=None):
        """测试币安连接"""
        try:
            # 测试公开接口
            response = requests.get("https://api.binance.com/api/v3/time")
            if response.status_code == 200:
                server_time = datetime.fromtimestamp(response.json()['serverTime']/1000)
                print(f"✅ 连接成功！服务器时间: {server_time}")
                
                # 获取BTC价格
                ticker = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
                if ticker.status_code == 200:
                    price = float(ticker.json()['price'])
                    print(f"   BTC价格: ${price:,.2f}")
                return True
            elif response.status_code == 451:
                print("⚠️ 币安API在您的地区受限")
                print("   建议使用OKX或通过VPN访问")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def setup(self):
        """配置币安API"""
        print("\n📋 币安API配置步骤：")
        print("-"*50)
        print("""
1. 登录币安: https://www.binance.com
2. 进入 用户中心 → API管理
3. 点击 '创建API'
4. 设置API标签: TigerSystem
5. 通过邮件/手机验证
6. 设置权限: 
   ✅ 只勾选"读取信息"（Enable Reading）
   ❌ 不要勾选交易权限
7. 保存API Key和Secret Key
""")
        
        print("\n⚠️ 安全提示：")
        print("• Secret Key只显示一次")
        print("• 建议设置IP白名单")
        print("• 永远不要分享你的Secret Key")
        
        # 先测试连接
        print("\n测试币安API连接...")
        if not self.test_connection():
            print("\n如果在中国大陆，可能需要VPN")
            print("或者使用OKX作为替代")
            
        print("\n" + "-"*50)
        print("请输入币安API信息（直接回车跳过）：")
        
        api_key = input("API Key: ").strip()
        secret = input("Secret Key: ").strip()
        
        if api_key and secret:
            config = {
                'binance_api_key': api_key,
                'binance_secret': secret
            }
            
            # 保存配置
            self.save_config(config)
            
            # 显示功能
            self.show_features()
            
            return config
        else:
            print("\n跳过币安配置")
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
        """显示币安API功能"""
        print("\n" + "="*60)
        print("📊 币安API功能：")
        print("-"*60)
        print("""
实时数据：
• 所有交易对的实时价格
• 1秒到1月的K线数据
• 市场深度（订单簿）
• 24小时统计

优势：
• 全球最大交易所
• 流动性最好
• 币种最全
• API稳定

限制：
• 某些地区需要VPN
• 频率限制：1200权重/分钟
""")

if __name__ == "__main__":
    setup = BinanceSetup()
    setup.setup()