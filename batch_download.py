#!/usr/bin/env python3
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

print("\n✅ 下载完成！")
