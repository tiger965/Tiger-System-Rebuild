"""
Window 2 - 榜单监控系统
负责获取交易所热门榜、涨跌榜、新币榜等数据
"""

import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import ccxt
import pandas as pd
from loguru import logger
from .vpn_checker import ensure_binance_vpn


class RankingMonitor:
    """热门榜/涨跌榜/新币榜监控"""
    
    def __init__(self):
        """初始化榜单监控器"""
        self.okx_client = None
        self.binance_client = None
        self._init_exchanges()
        self.cache = {}
        self.cache_duration = 60  # 缓存60秒
        
    def _init_exchanges(self):
        """初始化交易所客户端"""
        try:
            # OKX配置
            self.okx_client = ccxt.okx({
                'apiKey': '79d7b5b4-2e9b-4a31-be9c-95527d618739',
                'secret': '070B16A29AF22C13A67D9CB807B5693D',
                'password': 'Yzh198796&',
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            # 🔒 币安需要强制VPN检查 - 防止封号
            logger.info("🔒 检查币安VPN连接...")
            try:
                ensure_binance_vpn()
                logger.info("✅ 币安VPN检查通过")
            except Exception as vpn_error:
                logger.error(f"🚨 币安VPN检查失败: {vpn_error}")
                logger.error("🚨 为防止封号，币安客户端将不可用")
                raise Exception(f"币安VPN必须连接！{vpn_error}")
            
            # Binance配置（通过VPN代理）
            self.binance_client = ccxt.binance({
                'apiKey': 'cKnsfwbBg9nYj1lsPfoK26UtAYf8Oiq7TALPIBQC6UYfJ2p4sMJu5nRRfooVSN4t',
                'secret': 'iKWUuPcvWrCs3QGMd3it9LuN408TQaRdh7amTpY4mbLQo5K8kvDOVyaQoN7P1NYj',
                'enableRateLimit': True,
                'proxies': {
                    'http': 'http://127.0.0.1:1080',
                    'https': 'http://127.0.0.1:1080'
                },
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            logger.info("✅ 交易所客户端初始化成功（含VPN保护）")
            
        except Exception as e:
            logger.error(f"初始化交易所失败: {e}")
            
    def get_hot_ranking(self, exchange: str, top: int = 15) -> List[Dict]:
        """
        获取热门榜
        Window 6主动扫描时调用
        
        Args:
            exchange: 交易所名称 (okx/binance)
            top: 返回前N名
            
        Returns:
            [{
                'symbol': 'BTC/USDT',
                'rank': 1,
                'rank_change': 0,  # 排名变化
                'volume_24h': 1234567890,
                'volume_change': 0.15,  # 15%成交量变化
                'price': 67500.00,
                'price_change_24h': 0.025  # 2.5%价格变化
            }]
        """
        cache_key = f"hot_{exchange}_{top}"
        
        # 检查缓存
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return data
                
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取所有交易对的24小时行情
            tickers = client.fetch_tickers()
            
            # 转换为DataFrame便于排序
            df = pd.DataFrame([
                {
                    'symbol': symbol,
                    'volume_24h': ticker['quoteVolume'],  # USDT成交量
                    'price': ticker['last'],
                    'price_change_24h': ticker['percentage'] / 100,
                    'bid': ticker['bid'],
                    'ask': ticker['ask']
                }
                for symbol, ticker in tickers.items()
                if symbol.endswith('/USDT')
            ])
            
            # 按成交量排序
            df = df.sort_values('volume_24h', ascending=False)
            
            # 获取前N名
            top_coins = df.head(top).reset_index(drop=True)
            
            # 添加排名信息
            result = []
            for idx, row in top_coins.iterrows():
                result.append({
                    'symbol': row['symbol'],
                    'rank': idx + 1,
                    'rank_change': 0,  # TODO: 需要历史数据计算
                    'volume_24h': row['volume_24h'],
                    'volume_change': 0,  # TODO: 需要历史数据计算
                    'price': row['price'],
                    'price_change_24h': row['price_change_24h'],
                    'bid': row['bid'],
                    'ask': row['ask'],
                    'spread': (row['ask'] - row['bid']) / row['price'] * 100  # 买卖价差百分比
                })
                
            # 更新缓存
            self.cache[cache_key] = (time.time(), result)
            
            logger.info(f"获取{exchange}热门榜成功，前{top}名")
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}热门榜失败: {e}")
            return []
            
    def get_gainers_ranking(self, exchange: str, top: int = 5) -> List[Dict]:
        """
        获取涨幅榜
        
        Returns:
            [{
                'symbol': 'XXX/USDT',
                'price': 1.234,
                'price_change_24h': 0.456,  # 45.6%涨幅
                'volume_24h': 1234567,
                'volume_change': 2.5,  # 成交量放大2.5倍
                'is_pumping': True  # 是否在爆拉
            }]
        """
        cache_key = f"gainers_{exchange}_{top}"
        
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return data
                
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取所有交易对的24小时行情
            tickers = client.fetch_tickers()
            
            # 筛选USDT交易对并按涨幅排序
            gainers = []
            for symbol, ticker in tickers.items():
                if not symbol.endswith('/USDT'):
                    continue
                    
                if ticker['percentage'] is not None and ticker['percentage'] > 0:
                    gainers.append({
                        'symbol': symbol,
                        'price': ticker['last'],
                        'price_change_24h': ticker['percentage'] / 100,
                        'volume_24h': ticker['quoteVolume'],
                        'volume_change': 0,  # TODO: 需要历史数据
                        'is_pumping': ticker['percentage'] > 10  # 涨幅超过10%认为在爆拉
                    })
                    
            # 按涨幅排序
            gainers.sort(key=lambda x: x['price_change_24h'], reverse=True)
            
            # 获取前N名
            result = gainers[:top]
            
            # 更新缓存
            self.cache[cache_key] = (time.time(), result)
            
            logger.info(f"获取{exchange}涨幅榜成功，前{top}名")
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}涨幅榜失败: {e}")
            return []
            
    def get_losers_ranking(self, exchange: str, top: int = 5) -> List[Dict]:
        """
        获取跌幅榜
        
        Returns:
            [{
                'symbol': 'XXX/USDT',
                'price': 1.234,
                'price_change_24h': -0.356,  # -35.6%跌幅
                'volume_24h': 1234567,
                'is_dumping': True  # 是否在暴跌
            }]
        """
        cache_key = f"losers_{exchange}_{top}"
        
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return data
                
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取所有交易对的24小时行情
            tickers = client.fetch_tickers()
            
            # 筛选USDT交易对并按跌幅排序
            losers = []
            for symbol, ticker in tickers.items():
                if not symbol.endswith('/USDT'):
                    continue
                    
                if ticker['percentage'] is not None and ticker['percentage'] < 0:
                    losers.append({
                        'symbol': symbol,
                        'price': ticker['last'],
                        'price_change_24h': ticker['percentage'] / 100,
                        'volume_24h': ticker['quoteVolume'],
                        'is_dumping': ticker['percentage'] < -10  # 跌幅超过10%认为在暴跌
                    })
                    
            # 按跌幅排序（从大到小）
            losers.sort(key=lambda x: x['price_change_24h'])
            
            # 获取前N名
            result = losers[:top]
            
            # 更新缓存
            self.cache[cache_key] = (time.time(), result)
            
            logger.info(f"获取{exchange}跌幅榜成功，前{top}名")
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}跌幅榜失败: {e}")
            return []
            
    def get_new_listings(self, exchange: str, top: int = 3) -> List[Dict]:
        """
        获取新币榜
        
        Returns:
            [{
                'symbol': 'NEW/USDT',
                'listing_time': '2024-01-01 12:00:00',
                'price': 1.234,
                'price_change_since_listing': 0.85,  # 85%涨幅
                'volume_24h': 1234567,
                'is_explosive': True  # 是否爆发
            }]
        """
        cache_key = f"new_{exchange}_{top}"
        
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return data
                
        try:
            # 这里需要特殊处理，因为CCXT没有直接的新币接口
            # 实际项目中应该调用交易所的专门API
            
            result = []
            
            if exchange == 'binance':
                # Binance有专门的新币接口，这里简化处理
                # 实际应该调用 /api/v3/exchangeInfo 获取上线时间
                logger.warning("新币榜功能需要额外实现")
                
            elif exchange == 'okx':
                # OKX也有类似接口
                logger.warning("新币榜功能需要额外实现")
                
            # 更新缓存
            self.cache[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}新币榜失败: {e}")
            return []
            
    def get_volume_surge(self, threshold: float = 2.0, timeframe: str = '5m') -> List[Dict]:
        """
        获取成交量异动的币种
        
        Args:
            threshold: 成交量放大倍数阈值
            timeframe: 时间周期
            
        Returns:
            成交量异动的币种列表
        """
        try:
            result = []
            
            # 获取两个交易所的数据
            for exchange in ['okx', 'binance']:
                client = self.okx_client if exchange == 'okx' else self.binance_client
                
                # 这里简化处理，实际需要对比历史数据
                tickers = client.fetch_tickers()
                
                for symbol, ticker in tickers.items():
                    if not symbol.endswith('/USDT'):
                        continue
                        
                    # TODO: 需要历史数据计算成交量变化
                    # 这里暂时用模拟数据
                    volume_change = 1.0
                    
                    if volume_change >= threshold:
                        result.append({
                            'symbol': symbol,
                            'exchange': exchange,
                            'volume_24h': ticker['quoteVolume'],
                            'volume_change': volume_change,
                            'price': ticker['last'],
                            'price_change_24h': ticker['percentage'] / 100 if ticker['percentage'] else 0
                        })
                        
            logger.info(f"发现{len(result)}个成交量异动币种")
            return result
            
        except Exception as e:
            logger.error(f"获取成交量异动失败: {e}")
            return []


# 测试代码
if __name__ == "__main__":
    monitor = RankingMonitor()
    
    # 测试获取热门榜
    print("\n=== Binance热门榜 TOP5 ===")
    hot = monitor.get_hot_ranking('binance', 5)
    for coin in hot:
        print(f"{coin['rank']}. {coin['symbol']}: ${coin['price']:.2f}, "
              f"成交量: ${coin['volume_24h']:,.0f}, "
              f"24h涨幅: {coin['price_change_24h']*100:.2f}%")
    
    # 测试获取涨幅榜
    print("\n=== Binance涨幅榜 TOP3 ===")
    gainers = monitor.get_gainers_ranking('binance', 3)
    for coin in gainers:
        print(f"{coin['symbol']}: ${coin['price']:.4f}, "
              f"涨幅: {coin['price_change_24h']*100:.2f}%")
    
    # 测试获取跌幅榜
    print("\n=== Binance跌幅榜 TOP3 ===")
    losers = monitor.get_losers_ranking('binance', 3)
    for coin in losers:
        print(f"{coin['symbol']}: ${coin['price']:.4f}, "
              f"跌幅: {coin['price_change_24h']*100:.2f}%")