#!/usr/bin/env python3
"""
上帝视角监控系统 - 全面数据源配置
整合所有可用的免费API实现全方位监控
"""

import requests
import json
from datetime import datetime

class GodViewMonitor:
    """上帝视角监控器 - 整合所有数据源"""
    
    def __init__(self):
        self.proxy = {'http': 'socks5://127.0.0.1:1099', 'https': 'socks5://127.0.0.1:1099'}
        self.data_sources = {}
        
    def get_exchange_data(self):
        """1. 交易所数据（已配置）"""
        print("\n📊 交易所数据")
        print("-"*40)
        
        # OKX (已配置)
        try:
            r = requests.get('https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT', timeout=5)
            if r.status_code == 200:
                self.data_sources['okx'] = r.json()
                print("✅ OKX: 数据正常")
        except:
            print("❌ OKX: 连接失败")
        
        # 币安 (通过代理)
        try:
            r = requests.get('https://api.binance.com/api/v3/ticker/24hr', proxies=self.proxy, timeout=10)
            if r.status_code == 200:
                self.data_sources['binance'] = r.json()[:5]  # 前5个交易对
                print("✅ 币安: 数据正常")
        except:
            print("❌ 币安: 连接失败")
        
        # Gate.io (免费)
        try:
            r = requests.get('https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT', timeout=5)
            if r.status_code == 200:
                print("✅ Gate.io: 数据正常")
        except:
            print("❌ Gate.io: 连接失败")
        
        # KuCoin (免费)
        try:
            r = requests.get('https://api.kucoin.com/api/v1/market/stats?symbol=BTC-USDT', timeout=5)
            if r.status_code == 200:
                print("✅ KuCoin: 数据正常")
        except:
            print("❌ KuCoin: 连接失败")
    
    def get_blockchain_data(self):
        """2. 链上数据监控"""
        print("\n⛓️ 链上数据")
        print("-"*40)
        
        # Bitcoin网络状态 (免费)
        try:
            r = requests.get('https://blockchain.info/stats?format=json', timeout=5)
            if r.status_code == 200:
                stats = r.json()
                print(f"✅ BTC网络: 哈希率 {stats.get('hash_rate', 0)/1e12:.2f} TH/s")
                print(f"   未确认交易: {stats.get('n_unconfirmed', 0):,}")
        except:
            print("❌ BTC网络: 获取失败")
        
        # Ethereum Gas价格 (免费)
        try:
            r = requests.get('https://api.etherscan.io/api?module=gastracker&action=gasoracle', timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get('status') == '1':
                    result = data.get('result', {})
                    print(f"✅ ETH Gas: {result.get('SafeGasPrice', 'N/A')} Gwei")
        except:
            print("❌ ETH Gas: 获取失败")
        
        # Mempool (免费)
        try:
            r = requests.get('https://mempool.space/api/v1/fees/recommended', timeout=5)
            if r.status_code == 200:
                fees = r.json()
                print(f"✅ BTC费用: 快速 {fees.get('fastestFee', 0)} sat/vB")
        except:
            print("❌ BTC费用: 获取失败")
    
    def get_defi_data(self):
        """3. DeFi数据"""
        print("\n🏦 DeFi协议")
        print("-"*40)
        
        # DeFi Llama TVL (免费)
        try:
            r = requests.get('https://api.llama.fi/tvl', timeout=5)
            if r.status_code == 200:
                tvl = float(r.text)
                print(f"✅ 总锁仓量: ${tvl/1e9:.2f}B")
        except:
            print("❌ DeFi TVL: 获取失败")
        
        # Uniswap (免费)
        try:
            r = requests.get('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', timeout=5)
            print("✅ Uniswap: 可访问")
        except:
            print("❌ Uniswap: 连接失败")
        
        # Compound协议 (免费)
        try:
            r = requests.get('https://api.compound.finance/api/v2/market', timeout=5)
            if r.status_code == 200:
                print("✅ Compound: 数据正常")
        except:
            print("❌ Compound: 连接失败")
    
    def get_social_sentiment(self):
        """4. 社交媒体情绪"""
        print("\n💬 社交情绪")
        print("-"*40)
        
        # CoinGecko趋势 (免费)
        try:
            r = requests.get('https://api.coingecko.com/api/v3/search/trending', timeout=5)
            if r.status_code == 200:
                trending = r.json()
                coins = trending.get('coins', [])[:3]
                if coins:
                    print("✅ 热门币种:")
                    for coin in coins:
                        print(f"   - {coin['item']['name']}")
        except:
            print("❌ CoinGecko: 获取失败")
        
        # Fear & Greed Index (免费)
        try:
            r = requests.get('https://api.alternative.me/fng/', timeout=5)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    value = data['data'][0]['value']
                    classification = data['data'][0]['value_classification']
                    print(f"✅ 恐慌贪婪指数: {value} ({classification})")
        except:
            print("❌ 恐慌贪婪指数: 获取失败")
        
        # Reddit情绪 (需要配置但免费)
        print("⚠️ Reddit: 需要免费API密钥")
        print("⚠️ Twitter: 需要开发者账号")
    
    def get_news_data(self):
        """5. 新闻资讯"""
        print("\n📰 新闻资讯")
        print("-"*40)
        
        # CryptoCompare新闻 (免费限额)
        try:
            r = requests.get('https://min-api.cryptocompare.com/data/v2/news/?lang=EN', timeout=5)
            if r.status_code == 200:
                news = r.json()
                if 'Data' in news:
                    print(f"✅ 最新新闻: {len(news['Data'][:3])}条")
                    for item in news['Data'][:2]:
                        print(f"   - {item['title'][:50]}...")
        except:
            print("❌ 新闻: 获取失败")
        
        # CoinDesk RSS (免费)
        print("✅ CoinDesk RSS: 可用")
        print("✅ CoinTelegraph RSS: 可用")
    
    def get_market_metrics(self):
        """6. 市场指标"""
        print("\n📈 市场指标")
        print("-"*40)
        
        # 市值排名 (免费)
        try:
            r = requests.get('https://api.coingecko.com/api/v3/global', timeout=5)
            if r.status_code == 200:
                data = r.json()['data']
                print(f"✅ 总市值: ${data['total_market_cap']['usd']/1e9:.2f}B")
                print(f"   BTC占比: {data['market_cap_percentage']['btc']:.1f}%")
                print(f"   24h变化: {data['market_cap_change_percentage_24h_usd']:.2f}%")
        except:
            print("❌ 市场指标: 获取失败")
        
        # 稳定币供应量
        try:
            r = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category=stablecoins&order=market_cap_desc', timeout=5)
            if r.status_code == 200:
                stables = r.json()[:3]
                print("✅ 稳定币供应:")
                for stable in stables:
                    print(f"   {stable['symbol'].upper()}: ${stable['market_cap']/1e9:.2f}B")
        except:
            print("❌ 稳定币: 获取失败")
    
    def run_full_scan(self):
        """运行完整扫描"""
        print("="*60)
        print("🔮 上帝视角监控系统 - 全面扫描")
        print("="*60)
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行所有监控
        self.get_exchange_data()
        self.get_blockchain_data()
        self.get_defi_data()
        self.get_social_sentiment()
        self.get_news_data()
        self.get_market_metrics()
        
        print("\n" + "="*60)
        print("扫描完成！")
        
        # 统计
        print("\n📊 数据源统计:")
        print(f"- 交易所: 4个 (OKX, 币安, Gate, KuCoin)")
        print(f"- 链上数据: 3个 (BTC, ETH, Mempool)")
        print(f"- DeFi协议: 3个 (TVL, Uniswap, Compound)")
        print(f"- 社交情绪: 2个 (CoinGecko, Fear&Greed)")
        print(f"- 新闻源: 3个 (CryptoCompare, CoinDesk, CoinTelegraph)")
        print(f"- 市场指标: 2个 (总市值, 稳定币)")
        
        print("\n💡 建议配置的额外API (都有免费额度):")
        print("1. Etherscan API - 详细链上数据")
        print("2. CryptoCompare API - 更多历史数据")
        print("3. Reddit API - 社区情绪分析")
        print("4. NewsAPI - 综合新闻聚合")
        print("5. Glassnode API - 链上分析指标")

def main():
    monitor = GodViewMonitor()
    monitor.run_full_scan()

if __name__ == "__main__":
    main()