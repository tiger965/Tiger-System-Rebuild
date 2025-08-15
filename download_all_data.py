#!/usr/bin/env python3
"""
批量下载所有历史数据
从CryptoDataDownload获取免费的完整历史数据
"""

import os
import time
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

class DataDownloader:
    def __init__(self):
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # CryptoDataDownload的数据链接（2025年8月可用）
        self.download_urls = {
            # BTC数据
            'BTC_USDT_1m': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_minute.csv',
            'BTC_USDT_5m': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_5m.csv',
            'BTC_USDT_15m': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_15m.csv',
            'BTC_USDT_1h': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_1h.csv',
            'BTC_USDT_4h': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_4h.csv',
            'BTC_USDT_1d': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_d.csv',
            
            # ETH数据
            'ETH_USDT_1m': 'https://www.cryptodatadownload.com/cdd/Binance_ETHUSDT_minute.csv',
            'ETH_USDT_5m': 'https://www.cryptodatadownload.com/cdd/Binance_ETHUSDT_5m.csv',
            'ETH_USDT_1h': 'https://www.cryptodatadownload.com/cdd/Binance_ETHUSDT_1h.csv',
            'ETH_USDT_1d': 'https://www.cryptodatadownload.com/cdd/Binance_ETHUSDT_d.csv',
            
            # BNB数据
            'BNB_USDT_1h': 'https://www.cryptodatadownload.com/cdd/Binance_BNBUSDT_1h.csv',
            'BNB_USDT_1d': 'https://www.cryptodatadownload.com/cdd/Binance_BNBUSDT_d.csv',
            
            # SOL数据（如果有）
            'SOL_USDT_1h': 'https://www.cryptodatadownload.com/cdd/Binance_SOLUSDT_1h.csv',
            'SOL_USDT_1d': 'https://www.cryptodatadownload.com/cdd/Binance_SOLUSDT_d.csv',
        }
        
    def download_file(self, url, filename):
        """下载单个文件"""
        try:
            print(f"📥 下载: {filename}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # 保存原始CSV
                file_path = self.data_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # 尝试读取并验证数据
                try:
                    df = pd.read_csv(file_path, skiprows=1)
                    print(f"  ✅ 成功: {len(df)} 条记录")
                    return True
                except:
                    # 如果读取失败，尝试不跳过第一行
                    try:
                        df = pd.read_csv(file_path)
                        print(f"  ✅ 成功: {len(df)} 条记录")
                        return True
                    except Exception as e:
                        print(f"  ⚠️ 数据格式问题: {e}")
                        return False
            else:
                print(f"  ❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False
    
    def download_from_binance_api(self, symbol='BTCUSDT', interval='1h', limit=1000):
        """从币安API下载最新数据"""
        url = 'https://api.binance.com/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                # 转换为DataFrame
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                # 转换时间戳
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # 只保留需要的列
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                # 转换数值类型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])
                
                # 保存
                filename = f"binance_{symbol}_{interval}_latest.csv"
                df.to_csv(self.data_dir / filename, index=False)
                
                print(f"✅ 币安API: {symbol} {interval} - {len(df)} 条最新数据")
                return df
            else:
                print(f"❌ 币安API错误: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 币安API失败: {e}")
            return None
    
    def download_all(self):
        """下载所有数据"""
        print("="*60)
        print("🚀 开始批量下载历史数据")
        print("="*60)
        print(f"目标目录: {self.data_dir}")
        print()
        
        success_count = 0
        fail_count = 0
        
        # 1. 尝试从CryptoDataDownload下载
        print("📊 从CryptoDataDownload下载历史数据...")
        print("-"*40)
        
        for name, url in self.download_urls.items():
            filename = f"{name}.csv"
            if self.download_file(url, filename):
                success_count += 1
            else:
                fail_count += 1
            time.sleep(1)  # 避免请求过快
        
        print()
        print("📊 从币安API获取最新数据...")
        print("-"*40)
        
        # 2. 从币安API获取最新数据
        binance_pairs = [
            ('BTCUSDT', '1m'), ('BTCUSDT', '5m'), ('BTCUSDT', '15m'),
            ('BTCUSDT', '1h'), ('BTCUSDT', '4h'), ('BTCUSDT', '1d'),
            ('ETHUSDT', '1h'), ('ETHUSDT', '1d'),
            ('BNBUSDT', '1h'), ('BNBUSDT', '1d'),
            ('SOLUSDT', '1h'), ('SOLUSDT', '1d'),
        ]
        
        for symbol, interval in binance_pairs:
            if self.download_from_binance_api(symbol, interval):
                success_count += 1
            else:
                fail_count += 1
            time.sleep(0.5)
        
        # 3. 显示统计
        print()
        print("="*60)
        print("📈 下载统计")
        print("-"*40)
        print(f"✅ 成功: {success_count} 个文件")
        print(f"❌ 失败: {fail_count} 个文件")
        
        # 4. 显示已下载的文件
        self.show_downloaded_files()
    
    def show_downloaded_files(self):
        """显示已下载的文件"""
        print()
        print("📁 已下载的数据文件:")
        print("-"*40)
        
        total_size = 0
        file_count = 0
        
        for file_path in sorted(self.data_dir.glob("*.csv")):
            size_mb = file_path.stat().st_size / (1024 * 1024)
            total_size += size_mb
            file_count += 1
            
            # 尝试读取文件信息
            try:
                df = pd.read_csv(file_path, nrows=5)
                rows = sum(1 for _ in open(file_path)) - 1
                print(f"  {file_path.name}")
                print(f"    大小: {size_mb:.2f} MB | 记录: {rows:,}")
            except:
                print(f"  {file_path.name} ({size_mb:.2f} MB)")
        
        print()
        print(f"总计: {file_count} 个文件, {total_size:.2f} MB")
    
    def create_data_summary(self):
        """创建数据摘要"""
        summary = {
            'download_time': datetime.now().isoformat(),
            'files': [],
            'total_records': 0,
            'total_size_mb': 0
        }
        
        for file_path in self.data_dir.glob("*.csv"):
            try:
                df = pd.read_csv(file_path, nrows=1)
                rows = sum(1 for _ in open(file_path)) - 1
                size_mb = file_path.stat().st_size / (1024 * 1024)
                
                summary['files'].append({
                    'name': file_path.name,
                    'records': rows,
                    'size_mb': round(size_mb, 2)
                })
                summary['total_records'] += rows
                summary['total_size_mb'] += size_mb
            except:
                pass
        
        # 保存摘要
        import json
        with open(self.data_dir / 'data_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 数据摘要已保存: data_summary.json")

def main():
    """主函数"""
    downloader = DataDownloader()
    
    print("🔍 检查网络连接...")
    
    # 测试网络
    try:
        response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
        print("✅ 币安API可访问")
    except:
        print("⚠️ 币安API连接问题，继续尝试...")
    
    # 开始下载
    downloader.download_all()
    
    # 创建摘要
    downloader.create_data_summary()
    
    print("\n✅ 数据下载完成！")
    print("\n下一步：")
    print("1. 配置币安API: python3 setup_binance_api.py")
    print("2. 配置OKX API: python3 setup_okx_api.py")
    print("3. 启动系统: python3 start.py")

if __name__ == "__main__":
    main()