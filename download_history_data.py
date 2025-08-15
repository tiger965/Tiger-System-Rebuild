#!/usr/bin/env python3
"""
历史数据下载工具
从交易所API免费下载完整历史K线数据
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

class HistoryDataDownloader:
    """历史数据下载器"""
    
    def __init__(self):
        self.data_dir = Path("data/history")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def download_okx_klines(self, symbol='BTC-USDT', interval='1m', days=30):
        """
        从OKX下载历史K线数据
        
        参数:
        - symbol: 交易对 (BTC-USDT, ETH-USDT等)
        - interval: 时间周期
            - 1s, 5s, 15s, 30s (秒级)
            - 1m, 3m, 5m, 15m, 30m (分钟级)
            - 1H, 2H, 4H (小时级)
            - 1D, 1W, 1M (日/周/月)
        - days: 下载多少天的数据
        """
        print(f"\n📥 下载 {symbol} {interval} 历史数据...")
        
        # OKX API端点
        url = "https://www.okx.com/api/v5/market/candles"
        
        # 计算时间范围
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        all_data = []
        
        # OKX每次最多返回300根K线
        while start_time < end_time:
            params = {
                'instId': symbol,
                'bar': interval,
                'before': start_time,
                'limit': 300
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == '0':
                        klines = data['data']
                        if not klines:
                            break
                        
                        all_data.extend(klines)
                        
                        # 更新时间戳（获取最后一根K线的时间）
                        start_time = int(klines[-1][0])
                        
                        print(f"  已下载 {len(all_data)} 根K线...")
                        time.sleep(0.1)  # 避免频率限制
                    else:
                        print(f"❌ API错误: {data}")
                        break
            except Exception as e:
                print(f"❌ 请求失败: {e}")
                break
        
        # 转换为DataFrame
        if all_data:
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'volume_currency'
            ])
            
            # 转换数据类型
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # 排序
            df = df.sort_values('timestamp')
            
            # 保存到CSV
            filename = self.data_dir / f"{symbol}_{interval}_{days}days.csv"
            df.to_csv(filename, index=False)
            
            print(f"✅ 下载完成！")
            print(f"  文件: {filename}")
            print(f"  数据量: {len(df)} 根K线")
            print(f"  时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
            
            return df
        
        return None
    
    def download_binance_klines(self, symbol='BTCUSDT', interval='1m', days=30):
        """
        从币安下载历史K线数据
        
        币安的优势：
        - 每次可以获取1000根K线（比OKX多）
        - 历史数据更完整
        """
        print(f"\n📥 下载币安 {symbol} {interval} 历史数据...")
        
        url = "https://api.binance.com/api/v3/klines"
        
        # 币安的时间间隔格式
        interval_map = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
            '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
        }
        
        # 计算时间
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        all_data = []
        
        while start_time < end_time:
            params = {
                'symbol': symbol,
                'interval': interval_map.get(interval, interval),
                'startTime': start_time,
                'limit': 1000  # 币安最多1000根
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    klines = response.json()
                    if not klines:
                        break
                    
                    all_data.extend(klines)
                    
                    # 更新开始时间
                    start_time = klines[-1][0] + 1
                    
                    print(f"  已下载 {len(all_data)} 根K线...")
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"❌ 请求失败: {e}")
                break
        
        # 转换为DataFrame
        if all_data:
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 转换数据类型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # 只保留需要的列
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # 保存
            filename = self.data_dir / f"binance_{symbol}_{interval}_{days}days.csv"
            df.to_csv(filename, index=False)
            
            print(f"✅ 下载完成！")
            print(f"  文件: {filename}")
            print(f"  数据量: {len(df)} 根K线")
            
            return df
        
        return None
    
    def download_multiple_symbols(self, exchange='okx'):
        """批量下载多个交易对的数据"""
        
        symbols_okx = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'BNB-USDT']
        symbols_binance = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
        
        intervals = ['1m', '5m', '15m', '1h', '4h', '1d']
        
        print("="*60)
        print("📊 批量下载历史数据")
        print("="*60)
        
        if exchange == 'okx':
            for symbol in symbols_okx:
                for interval in intervals:
                    self.download_okx_klines(symbol, interval, days=30)
                    time.sleep(1)  # 避免频率限制
        else:
            for symbol in symbols_binance:
                for interval in intervals:
                    self.download_binance_klines(symbol, interval, days=30)
                    time.sleep(1)
        
        print("\n✅ 批量下载完成！")
        self.show_statistics()
    
    def download_long_history(self, symbol='BTC-USDT', interval='1d'):
        """
        下载长期历史数据（1-2年）
        用于机器学习训练
        """
        print(f"\n📊 下载长期历史数据 {symbol}")
        print("这可能需要几分钟...")
        
        # 下载2年的日线数据
        df = self.download_okx_klines(symbol, interval, days=730)
        
        if df is not None:
            # 计算技术指标
            self.add_indicators(df)
            
            # 保存增强版数据
            filename = self.data_dir / f"{symbol}_{interval}_2years_with_indicators.csv"
            df.to_csv(filename, index=False)
            
            print(f"\n✅ 长期数据已保存: {filename}")
            
            return df
    
    def add_indicators(self, df):
        """添加技术指标"""
        # 移动平均线
        df['MA_7'] = df['close'].rolling(window=7).mean()
        df['MA_25'] = df['close'].rolling(window=25).mean()
        df['MA_99'] = df['close'].rolling(window=99).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # 成交量指标
        df['Volume_MA'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def show_statistics(self):
        """显示下载的数据统计"""
        print("\n" + "="*60)
        print("📈 数据统计")
        print("-"*60)
        
        total_size = 0
        file_count = 0
        
        for file in self.data_dir.glob("*.csv"):
            size = file.stat().st_size / (1024 * 1024)  # MB
            total_size += size
            file_count += 1
            
            # 读取数据行数
            df = pd.read_csv(file, nrows=1)
            total_rows = sum(1 for _ in open(file)) - 1
            
            print(f"  {file.name}")
            print(f"    - 数据量: {total_rows:,} 根K线")
            print(f"    - 文件大小: {size:.2f} MB")
        
        print(f"\n总计:")
        print(f"  文件数: {file_count}")
        print(f"  总大小: {total_size:.2f} MB")

def main():
    """主函数"""
    downloader = HistoryDataDownloader()
    
    print("="*60)
    print("📊 历史数据下载工具")
    print("="*60)
    
    print("\n选择功能：")
    print("1. 下载单个交易对数据")
    print("2. 批量下载主流币数据")
    print("3. 下载长期历史数据（2年）")
    print("4. 自定义下载")
    
    choice = input("\n选择 (1-4): ")
    
    if choice == "1":
        # 单个下载
        print("\n输入参数（直接回车使用默认值）：")
        symbol = input("交易对 [BTC-USDT]: ") or "BTC-USDT"
        interval = input("K线周期 [1m]: ") or "1m"
        days = int(input("天数 [30]: ") or "30")
        
        downloader.download_okx_klines(symbol, interval, days)
        
    elif choice == "2":
        # 批量下载
        exchange = input("选择交易所 (okx/binance) [okx]: ") or "okx"
        downloader.download_multiple_symbols(exchange)
        
    elif choice == "3":
        # 长期数据
        symbol = input("交易对 [BTC-USDT]: ") or "BTC-USDT"
        downloader.download_long_history(symbol)
        
    elif choice == "4":
        # 自定义
        print("\n自定义下载参数：")
        exchange = input("交易所 (okx/binance): ")
        symbol = input("交易对: ")
        interval = input("K线周期 (1m/5m/15m/1h/4h/1d): ")
        days = int(input("天数: "))
        
        if exchange == "binance":
            downloader.download_binance_klines(symbol, interval, days)
        else:
            downloader.download_okx_klines(symbol, interval, days)
    
    # 显示统计
    downloader.show_statistics()

if __name__ == "__main__":
    # 检查是否安装pandas
    try:
        import pandas
    except ImportError:
        print("需要安装pandas: pip install pandas")
        exit(1)
    
    main()