#!/usr/bin/env python3
"""
Tiger系统 - 双交易所同时监控
完全独立运行，不依赖Windows
"""

import requests
import time
import subprocess
import socket
from datetime import datetime

def start_proxy():
    """启动WSL独立代理"""
    # 检查是否已运行
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 1099))
    sock.close()
    
    if result == 0:
        print("✅ WSL代理已运行(端口1099)")
        return True
    
    print("启动WSL独立代理...")
    cmd = "pproxy -l socks5://127.0.0.1:1099 -r ss://aes-256-gcm:kcS95i51Wt4PPu01@43.160.195.89:443 > /tmp/proxy.log 2>&1 &"
    subprocess.run(cmd, shell=True)
    time.sleep(3)
    
    # 验证
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 1099))
    sock.close()
    
    if result == 0:
        print("✅ 代理启动成功")
        return True
    else:
        print("❌ 代理启动失败")
        return False

def get_data():
    """同时获取两个交易所数据"""
    data = {}
    
    # OKX - 直连
    try:
        r = requests.get('https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT', timeout=5)
        if r.status_code == 200:
            result = r.json()
            if result['code'] == '0':
                data['okx'] = float(result['data'][0]['last'])
    except:
        pass
    
    # 币安 - 通过代理
    proxy = {'http': 'socks5://127.0.0.1:1099', 'https': 'socks5://127.0.0.1:1099'}
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', 
                        proxies=proxy, timeout=10)
        if r.status_code == 200:
            data['binance'] = float(r.json()['price'])
    except:
        pass
    
    return data

def main():
    print("="*60)
    print("🐯 Tiger双交易所监控系统")
    print("="*60)
    
    # 启动代理
    if not start_proxy():
        print("系统将只使用OKX数据")
    
    print("\n开始监控...")
    print("-"*60)
    
    cycle = 0
    while True:
        cycle += 1
        data = get_data()
        
        print(f"\n#{cycle} {datetime.now().strftime('%H:%M:%S')}")
        
        if 'okx' in data:
            print(f"OKX    : ${data['okx']:,.2f}")
        else:
            print("OKX    : 无数据")
        
        if 'binance' in data:
            print(f"Binance: ${data['binance']:,.2f}")
        else:
            print("Binance: 无数据")
        
        if 'okx' in data and 'binance' in data:
            diff = abs(data['okx'] - data['binance'])
            diff_pct = (diff / min(data['okx'], data['binance'])) * 100
            print(f"价差   : ${diff:.2f} ({diff_pct:.3f}%)")
            
            if diff_pct > 0.1:
                if data['okx'] < data['binance']:
                    print("💰 套利: OKX买 → Binance卖")
                else:
                    print("💰 套利: Binance买 → OKX卖")
        
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n停止监控")
        subprocess.run("pkill -f pproxy", shell=True, stderr=subprocess.DEVNULL)