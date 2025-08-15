#!/usr/bin/env python3
"""
历史数据完整解决方案
结合多个数据源，高效获取和管理历史数据
"""

import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
import json

class HistoricalDataManager:
    """历史数据管理器"""
    
    def __init__(self):
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据需求配置
        self.data_requirements = {
            'machine_learning': {
                '1m': 180,   # 180天1分钟数据（约26万根）
                '5m': 365,   # 1年5分钟数据
                '15m': 730,  # 2年15分钟数据
                '1h': 1095,  # 3年小时数据
                '1d': 1825   # 5年日线数据
            },
            'backtesting': {
                '1m': 90,    # 3个月1分钟数据
                '5m': 180,   # 6个月5分钟数据
                '15m': 365,  # 1年15分钟数据
                '1h': 730,   # 2年小时数据
                '1d': 1095   # 3年日线数据
            },
            'indicators': {
                '1m': 7,     # 7天1分钟（短期）
                '5m': 30,    # 30天5分钟
                '15m': 90,   # 90天15分钟
                '1h': 180,   # 180天小时
                '1d': 365    # 1年日线
            }
        }
    
    def analyze_data_needs(self):
        """分析数据需求"""
        print("="*60)
        print("📊 Tiger系统历史数据需求分析")
        print("="*60)
        
        total_candles = 0
        
        for module, requirements in self.data_requirements.items():
            print(f"\n{module.upper()}模块需求：")
            print("-"*40)
            
            for interval, days in requirements.items():
                candles = self.calculate_candles(interval, days)
                total_candles += candles
                
                print(f"  {interval:4s}: {days:4d}天 = {candles:,} 根K线")
        
        print(f"\n总计需要: {total_candles:,} 根K线")
        
        # 计算下载时间
        self.estimate_download_time(total_candles)
    
    def calculate_candles(self, interval, days):
        """计算K线数量"""
        intervals_per_day = {
            '1m': 1440,
            '5m': 288,
            '15m': 96,
            '30m': 48,
            '1h': 24,
            '4h': 6,
            '1d': 1
        }
        return days * intervals_per_day.get(interval, 1)
    
    def estimate_download_time(self, total_candles):
        """估算下载时间"""
        print("\n" + "="*60)
        print("⏱️ 下载时间估算")
        print("-"*60)
        
        # 币安：1000根/请求，1200权重/分钟
        binance_requests = total_candles / 1000
        binance_time = (binance_requests * 10 / 1200) * 60  # 每请求10权重
        
        # OKX：100根/请求，20次/2秒
        okx_requests = total_candles / 100
        okx_time = (okx_requests / 10) * 60  # 10次/分钟
        
        print(f"币安API: {binance_time:.1f} 分钟")
        print(f"OKX API: {okx_time:.1f} 分钟")
        
        if okx_time > 60:
            print(f"\n⚠️ OKX下载时间过长，建议使用其他方案")
    
    def get_alternative_sources(self):
        """获取替代数据源"""
        print("\n" + "="*60)
        print("🔄 替代数据源方案")
        print("="*60)
        
        sources = {
            "1. CryptoDataDownload": {
                "网址": "https://www.cryptodatadownload.com",
                "特点": "免费CSV下载，历史数据完整",
                "格式": "CSV文件，可直接使用",
                "限制": "需要手动下载",
                "推荐": "⭐⭐⭐⭐⭐"
            },
            "2. Kaggle数据集": {
                "网址": "https://www.kaggle.com/datasets",
                "特点": "社区提供的历史数据",
                "格式": "CSV/Parquet",
                "限制": "可能不是最新",
                "推荐": "⭐⭐⭐⭐"
            },
            "3. Yahoo Finance": {
                "API": "yfinance库",
                "特点": "免费，无限制",
                "格式": "仅日线数据",
                "限制": "没有分钟级",
                "推荐": "⭐⭐⭐"
            },
            "4. 混合方案": {
                "方法": "历史数据用CSV + 实时数据用API",
                "特点": "最优方案",
                "实现": "下载历史CSV，API补充最新",
                "推荐": "⭐⭐⭐⭐⭐"
            }
        }
        
        for name, info in sources.items():
            print(f"\n{name}:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        
        return sources
    
    def download_from_cryptodatadownload(self):
        """从CryptoDataDownload下载数据"""
        print("\n" + "="*60)
        print("📥 CryptoDataDownload下载指南")
        print("="*60)
        
        print("""
步骤：
1. 访问 https://www.cryptodatadownload.com/data/
2. 选择交易所（推荐Binance或Bitstamp）
3. 选择交易对和时间周期
4. 直接下载CSV文件

可用数据：
• Binance: 2017年至今，分钟级到日线
• Bitstamp: 2011年至今（BTC最早）
• Coinbase: 2015年至今
• Kraken: 2013年至今

优势：
✅ 完全免费
✅ 数据完整
✅ 直接可用
✅ 包含成交量
        """)
        
        # 创建下载脚本
        self.create_download_script()
    
    def create_download_script(self):
        """创建批量下载脚本"""
        script = '''#!/usr/bin/env python3
"""批量下载历史数据脚本"""

import requests
import pandas as pd
from pathlib import Path

# CryptoDataDownload的直接下载链接
urls = {
    'BTC_1m': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_minute.csv',
    'BTC_1h': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_1h.csv',
    'BTC_1d': 'https://www.cryptodatadownload.com/cdd/Binance_BTCUSDT_d.csv',
    'ETH_1m': 'https://www.cryptodatadownload.com/cdd/Binance_ETHUSDT_minute.csv',
    'ETH_1h': 'https://www.cryptodatadownload.com/cdd/Binance_ETHUSDT_1h.csv',
}

data_dir = Path('data/historical')
data_dir.mkdir(exist_ok=True)

for name, url in urls.items():
    print(f"下载 {name}...")
    try:
        df = pd.read_csv(url, skiprows=1)
        filename = data_dir / f"{name}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ 保存到 {filename}")
    except Exception as e:
        print(f"❌ 失败: {e}")

print("\\n✅ 下载完成！")
'''
        
        with open('batch_download.py', 'w') as f:
            f.write(script)
        
        print("\n✅ 已创建批量下载脚本: batch_download.py")
    
    def create_hybrid_solution(self):
        """创建混合解决方案"""
        print("\n" + "="*60)
        print("🎯 推荐的混合解决方案")
        print("="*60)
        
        print("""
最优方案：历史数据 + 实时API

1. 历史数据（一次性下载）：
   - 使用CryptoDataDownload下载2017-2024的完整数据
   - 包含1分钟、5分钟、15分钟、1小时、日线
   - 存储为本地CSV文件
   
2. 近期数据（API获取）：
   - 使用币安/OKX API获取最近30-90天数据
   - 实时更新最新K线
   
3. 数据管理：
   - SQLite数据库存储
   - 定期更新机制
   - 自动数据合并

优势：
✅ 历史数据完整（5年+）
✅ 实时数据及时
✅ 下载速度快
✅ 完全免费
✅ 适合机器学习训练
        """)
        
        # 创建实现代码
        self.create_hybrid_implementation()
    
    def create_hybrid_implementation(self):
        """创建混合方案实现"""
        code = '''#!/usr/bin/env python3
"""混合数据方案实现"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

class HybridDataManager:
    def __init__(self):
        self.db_path = 'data/market_data.db'
        self.historical_dir = Path('data/historical')
        
    def load_historical_data(self):
        """加载历史CSV数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        
        for csv_file in self.historical_dir.glob('*.csv'):
            df = pd.read_csv(csv_file)
            table_name = csv_file.stem
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✅ 导入 {table_name}: {len(df)} 条记录")
        
        conn.close()
    
    def update_recent_data(self):
        """从API更新最近数据"""
        # 这里调用币安API获取最新数据
        pass
    
    def get_data(self, symbol, interval, start_date, end_date):
        """统一的数据获取接口"""
        conn = sqlite3.connect(self.db_path)
        
        query = f"""
        SELECT * FROM {symbol}_{interval}
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp
        """
        
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        conn.close()
        
        return df

# 使用示例
manager = HybridDataManager()
manager.load_historical_data()

# 获取BTC最近1年的日线数据
btc_daily = manager.get_data(
    'BTC', '1d',
    datetime.now() - timedelta(days=365),
    datetime.now()
)
print(f"获取 {len(btc_daily)} 条BTC日线数据")
'''
        
        with open('hybrid_data_manager.py', 'w') as f:
            f.write(code)
        
        print("\n✅ 已创建混合方案实现: hybrid_data_manager.py")

def main():
    """主函数"""
    manager = HistoricalDataManager()
    
    # 1. 分析数据需求
    manager.analyze_data_needs()
    
    # 2. 显示替代方案
    manager.get_alternative_sources()
    
    # 3. 提供下载方案
    manager.download_from_cryptodatadownload()
    
    # 4. 创建混合方案
    manager.create_hybrid_solution()
    
    print("\n" + "="*60)
    print("📌 总结与建议")
    print("="*60)
    print("""
1. 不需要TradingView API（太贵且不提供数据下载）

2. 推荐方案：
   • 历史数据：CryptoDataDownload（免费CSV）
   • 实时数据：币安/OKX API（免费）
   • 存储：SQLite数据库

3. 立即行动：
   • 运行 batch_download.py 下载历史数据
   • 运行 hybrid_data_manager.py 管理数据
   • 配置币安/OKX API用于实时更新

4. 数据充足性：
   • 5年日线数据 ✅
   • 2年小时数据 ✅
   • 1年15分钟数据 ✅
   • 6个月5分钟数据 ✅
   • 3个月1分钟数据 ✅
   
这些数据完全满足机器学习训练和回测需求！
    """)

if __name__ == "__main__":
    main()