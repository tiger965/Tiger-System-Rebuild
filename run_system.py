#!/usr/bin/env python3
"""
Tiger系统 - 完整运行脚本
整合所有功能，使用真实数据运行
"""

import os
import sys
import yaml
import requests
import pandas as pd
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import time

class TigerSystemRunner:
    """Tiger系统运行器"""
    
    def __init__(self):
        print("="*60)
        print("🐯 Tiger智能交易分析系统")
        print("="*60)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 加载配置
        self.config = self.load_config()
        self.check_status()
    
    def load_config(self):
        """加载API配置"""
        config_file = Path("config/api_keys.yaml")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                
            # 加载币安代理配置
            binance_config = Path("config/binance_config.yaml")
            if binance_config.exists():
                with open(binance_config, 'r') as f:
                    bn_conf = yaml.safe_load(f) or {}
                    config.update(bn_conf)
                    
            return config
        return {}
    
    def check_status(self):
        """检查系统状态"""
        print("\n系统状态检查:")
        print("-"*40)
        
        # 检查历史数据
        history_dir = Path("data/historical")
        if history_dir.exists():
            csv_files = list(history_dir.glob("*.csv"))
            print(f"✅ 历史数据: {len(csv_files)} 个文件")
        else:
            print("❌ 历史数据: 未下载")
        
        # 检查OKX API
        if self.config.get('okx_api_key'):
            print(f"✅ OKX API: 已配置")
            self.test_okx()
        else:
            print("❌ OKX API: 未配置")
        
        # 检查币安API
        if self.config.get('binance_api_key'):
            print(f"✅ 币安API: 已配置（需要VPN）")
        else:
            print("⚠️ 币安API: 未配置")
    
    def test_okx(self):
        """测试OKX连接"""
        try:
            r = requests.get('https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT', timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data['code'] == '0':
                    price = float(data['data'][0]['last'])
                    print(f"   实时BTC: ${price:,.2f}")
        except:
            pass
    
    def get_both_exchanges_data(self):
        """同时获取OKX和币安数据"""
        import threading
        
        okx_data = [None]
        binance_data = [None]
        
        def fetch_okx():
            try:
                r = requests.get('https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT', timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data['code'] == '0':
                        okx_data[0] = float(data['data'][0]['last'])
            except:
                pass
        
        def fetch_binance():
            try:
                # 检查代理
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', 1080))
                sock.close()
                
                if result == 0:
                    proxy = {'http': 'socks5://127.0.0.1:1080', 'https': 'socks5://127.0.0.1:1080'}
                    r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', 
                                   proxies=proxy, timeout=10)
                    if r.status_code == 200:
                        binance_data[0] = float(r.json()['price'])
            except:
                pass
        
        # 并行执行
        t1 = threading.Thread(target=fetch_okx)
        t2 = threading.Thread(target=fetch_binance)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=10)
        
        return {'okx': okx_data[0], 'binance': binance_data[0]}
    
    def get_market_data(self):
        """获取市场数据"""
        print("\n" + "="*60)
        print("📊 实时市场数据")
        print("-"*60)
        
        symbols = {
            'BTC-USDT': 'BTC',
            'ETH-USDT': 'ETH', 
            'SOL-USDT': 'SOL',
            'BNB-USDT': 'BNB'
        }
        
        market_data = {}
        
        for symbol, name in symbols.items():
            try:
                url = f'https://www.okx.com/api/v5/market/ticker?instId={symbol}'
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == '0':
                        ticker = data['data'][0]
                        
                        market_data[name] = {
                            'price': float(ticker['last']),
                            'change_24h': float(ticker.get('sodUtc8', 0)),
                            'volume_24h': float(ticker.get('vol24h', 0)),
                            'high_24h': float(ticker.get('high24h', 0)),
                            'low_24h': float(ticker.get('low24h', 0))
                        }
                        
                        price = market_data[name]['price']
                        change = market_data[name]['change_24h']
                        volume = market_data[name]['volume_24h']
                        
                        # 显示数据
                        print(f"\n{name}:")
                        print(f"  价格: ${price:,.2f}")
                        print(f"  24h涨跌: {change:+.2f}%")
                        print(f"  24h成交量: {volume:,.0f}")
            except Exception as e:
                print(f"❌ {name}: 获取失败")
        
        return market_data
    
    def analyze_indicators(self, market_data):
        """分析技术指标"""
        print("\n" + "="*60)
        print("📈 技术分析")
        print("-"*60)
        
        for symbol, data in market_data.items():
            print(f"\n{symbol}:")
            
            # 简单的技术分析
            price = data['price']
            high = data['high_24h']
            low = data['low_24h']
            
            # 计算位置（0-100）
            if high != low:
                position = ((price - low) / (high - low)) * 100
            else:
                position = 50
            
            # RSI近似（基于24h变化）
            change = data['change_24h']
            rsi_estimate = 50 + (change * 2)  # 简化计算
            rsi_estimate = max(0, min(100, rsi_estimate))
            
            print(f"  24h区间位置: {position:.1f}%")
            print(f"  RSI估算: {rsi_estimate:.1f}")
            
            # 生成信号
            if position < 30 and rsi_estimate < 40:
                print(f"  信号: 🟢 超卖，可能反弹")
            elif position > 70 and rsi_estimate > 60:
                print(f"  信号: 🔴 超买，可能回调")
            else:
                print(f"  信号: ⚪ 中性")
    
    def check_opportunities(self, market_data):
        """检查交易机会"""
        print("\n" + "="*60)
        print("💡 交易机会")
        print("-"*60)
        
        opportunities = []
        
        for symbol, data in market_data.items():
            change = data['change_24h']
            
            # 大涨大跌
            if change > 5:
                opportunities.append(f"{symbol}: 强势上涨 +{change:.2f}%")
            elif change < -5:
                opportunities.append(f"{symbol}: 大幅下跌 {change:.2f}%")
            
            # 成交量异常
            if symbol == 'BTC' and data['volume_24h'] > 10000:
                opportunities.append(f"{symbol}: 成交量放大")
        
        if opportunities:
            for opp in opportunities:
                print(f"• {opp}")
        else:
            print("暂无特殊机会")
    
    def show_risk_alerts(self, market_data):
        """风险提醒"""
        print("\n" + "="*60)
        print("⚠️ 风险提醒")
        print("-"*60)
        
        # 计算整体市场情绪
        total_change = sum(d['change_24h'] for d in market_data.values())
        avg_change = total_change / len(market_data)
        
        if avg_change < -3:
            print("🔴 市场整体下跌，注意风险")
        elif avg_change > 3:
            print("🟡 市场过热，注意回调风险")
        else:
            print("🟢 市场平稳")
        
        # BTC主导地位
        if 'BTC' in market_data:
            btc_change = market_data['BTC']['change_24h']
            print(f"\nBTC主导: {btc_change:+.2f}%")
            if abs(btc_change) > 5:
                print("⚠️ BTC波动较大，可能影响整体市场")
    
    def run_continuous(self):
        """连续运行模式"""
        print("\n" + "="*60)
        print("🔄 进入实时监控模式")
        print("按 Ctrl+C 停止")
        print("="*60)
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                print(f"\n\n{'='*60}")
                print(f"周期 #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                print("="*60)
                
                # 获取市场数据
                market_data = self.get_market_data()
                
                if market_data:
                    # 技术分析
                    self.analyze_indicators(market_data)
                    
                    # 机会扫描
                    self.check_opportunities(market_data)
                    
                    # 风险提醒
                    self.show_risk_alerts(market_data)
                
                # 等待60秒
                print(f"\n⏳ 等待60秒后更新...")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n\n✅ 监控已停止")
    
    def run_once(self):
        """运行一次"""
        # 获取市场数据
        market_data = self.get_market_data()
        
        if market_data:
            # 技术分析
            self.analyze_indicators(market_data)
            
            # 机会扫描
            self.check_opportunities(market_data)
            
            # 风险提醒
            self.show_risk_alerts(market_data)
        
        # 总结
        print("\n" + "="*60)
        print("📋 运行总结")
        print("-"*60)
        print(f"✅ 分析了 {len(market_data)} 个交易对")
        print(f"✅ 使用OKX实时数据")
        print(f"✅ 完成技术分析和风险评估")
        
        print("\n选项：")
        print("1. 进入实时监控模式")
        print("2. 退出")
        
        try:
            choice = input("\n选择 (1-2) [2]: ") or "2"
            if choice == "1":
                self.run_continuous()
        except:
            pass


def main():
    """主函数"""
    runner = TigerSystemRunner()
    
    print("\n" + "="*60)
    print("系统就绪")
    print("-"*60)
    
    print("\n运行模式：")
    print("1. 单次分析")
    print("2. 实时监控")
    print("3. 退出")
    
    try:
        choice = input("\n选择 (1-3) [1]: ") or "1"
        
        if choice == "1":
            runner.run_once()
        elif choice == "2":
            runner.run_continuous()
        else:
            print("\n👋 再见！")
    except:
        # 默认运行一次
        runner.run_once()


if __name__ == "__main__":
    main()