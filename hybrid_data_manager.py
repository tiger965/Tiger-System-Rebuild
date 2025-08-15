#!/usr/bin/env python3
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
