#!/usr/bin/env python3
"""
OKX Passphrase 查找助手
测试常见的Passphrase
"""

import requests
import hmac
import base64
import yaml
from datetime import datetime
from pathlib import Path

def test_passphrase(api_key, secret, passphrase):
    """测试Passphrase是否正确"""
    # 生成签名
    timestamp = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    request_path = "/api/v5/account/balance"
    message = timestamp + 'GET' + request_path
    
    mac = hmac.new(
        bytes(secret, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    signature = base64.b64encode(mac.digest()).decode()
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    url = f"https://www.okx.com{request_path}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == '0':
                return True
            elif data['code'] == '50111':
                # Passphrase错误
                return False
        return False
    except:
        return False

def main():
    print("="*60)
    print("🔍 OKX Passphrase 查找助手")
    print("="*60)
    
    # 加载配置
    config_file = Path("config/api_keys.yaml")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    api_key = config['okx_api_key']
    secret = config['okx_secret']
    
    print(f"API Key: {api_key[:10]}...")
    print("\n测试常见的Passphrase...")
    print("-"*40)
    
    # 常见的Passphrase列表
    common_passphrases = [
        # 简单数字
        '123456', '888888', '666666', '111111', '000000',
        '12345678', '88888888', '123123', '112233',
        
        # 项目相关
        'Tiger', 'tiger', 'TIGER',
        'Tiger123', 'tiger123', 'Tiger888',
        'TigerSystem', 'tigersystem',
        'okx', 'OKX', 'okx123', 'OKX123',
        'api', 'API', 'myapi', '我的api',
        
        # 常见密码
        'password', 'Password', 'Password123',
        'admin', 'Admin', 'admin123',
        'test', 'Test', 'test123',
        
        # 日期相关
        '20240811', '20250811', '2024', '2025',
        '0811', '811', '11082024', '11082025',
        
        # 拼音
        'wodemima', 'mima', 'wodeapi',
        
        # 符号组合
        'Tiger@123', 'tiger@123', 'Tiger#123',
        'Tiger!', 'tiger!', 'Tiger$',
    ]
    
    found = False
    
    for passphrase in common_passphrases:
        print(f"测试: {passphrase}...", end=' ')
        
        if test_passphrase(api_key, secret, passphrase):
            print("✅ 找到了！")
            found = True
            
            # 保存到配置
            config['okx_passphrase'] = passphrase
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"\n🎉 Passphrase是: {passphrase}")
            print(f"✅ 已保存到配置文件")
            break
        else:
            print("❌")
    
    if not found:
        print("\n" + "="*60)
        print("未找到Passphrase")
        print("\n可能的Passphrase提示：")
        print("• 你创建API时设置的密码")
        print("• 可能是你的常用密码")
        print("• 检查是否有保存在其他地方")
        print("• 或者重新创建一个API")
        
        print("\n手动输入Passphrase：")
        passphrase = input("Passphrase: ").strip()
        
        if passphrase:
            print(f"\n测试: {passphrase}...", end=' ')
            if test_passphrase(api_key, secret, passphrase):
                print("✅ 正确！")
                
                # 保存
                config['okx_passphrase'] = passphrase
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
                print(f"✅ 已保存到配置文件")
            else:
                print("❌ 错误")
    
    print("\n" + "="*60)
    
    # 如果找到了，测试完整功能
    if config.get('okx_passphrase'):
        print("测试完整API功能...")
        import os
        os.system("python3 test_okx_api.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")