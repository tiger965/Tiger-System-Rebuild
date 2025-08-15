"""
Window 2 - 实时数据采集器
负责获取实时价格、深度、成交等数据
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import ccxt
import pandas as pd
from loguru import logger


class RealtimeDataCollector:
    """实时数据采集器"""
    
    def __init__(self):
        """初始化数据采集器"""
        self.okx_client = None
        self.binance_client = None
        self._init_exchanges()
        self.price_cache = {}
        self.cache_ttl = 5  # 缓存5秒
        
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
            
            # Binance配置（通过代理）
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
            
            logger.info("实时数据采集器初始化成功")
            
        except Exception as e:
            logger.error(f"初始化交易所失败: {e}")
            
    def get_realtime_price(self, symbol: str, exchange: str) -> Dict:
        """
        获取实时价格
        Window 6命令格式：获取BTC/USDT实时价格、买一价、卖一价、深度前10档
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            exchange: 交易所 'okx' 或 'binance'
            
        Returns:
            {
                'symbol': 'BTC/USDT',
                'exchange': 'binance',
                'price': 67500.00,
                'bid': 67499.00,
                'ask': 67501.00,
                'spread': 2.00,
                'spread_percentage': 0.003,
                'volume_24h': 1234567890,
                'timestamp': 1234567890
            }
        """
        cache_key = f"{exchange}_{symbol}_price"
        
        # 检查缓存
        if cache_key in self.price_cache:
            cache_time, data = self.price_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return data
                
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取ticker信息
            ticker = client.fetch_ticker(symbol)
            
            result = {
                'symbol': symbol,
                'exchange': exchange,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread': ticker['ask'] - ticker['bid'],
                'spread_percentage': (ticker['ask'] - ticker['bid']) / ticker['last'] * 100,
                'volume_24h': ticker['quoteVolume'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'change_24h': ticker['percentage'],
                'timestamp': int(time.time() * 1000)
            }
            
            # 更新缓存
            self.price_cache[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange} {symbol}实时价格失败: {e}")
            return {}
            
    def get_orderbook_depth(self, symbol: str, exchange: str, depth: int = 10) -> Dict:
        """
        获取订单簿深度
        
        Args:
            symbol: 交易对
            exchange: 交易所
            depth: 深度档位数
            
        Returns:
            {
                'symbol': 'BTC/USDT',
                'exchange': 'binance',
                'bids': [[67499, 0.5], [67498, 1.2], ...],  # [价格, 数量]
                'asks': [[67501, 0.3], [67502, 0.8], ...],
                'bid_total': 10.5,  # 买单总量
                'ask_total': 8.3,   # 卖单总量
                'imbalance': 0.26,  # 买卖不平衡度
                'timestamp': 1234567890
            }
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取订单簿
            orderbook = client.fetch_order_book(symbol, depth)
            
            # 计算买卖单总量
            bid_total = sum([bid[1] for bid in orderbook['bids']])
            ask_total = sum([ask[1] for ask in orderbook['asks']])
            
            # 计算不平衡度 (正数表示买盘强，负数表示卖盘强)
            imbalance = (bid_total - ask_total) / (bid_total + ask_total) if (bid_total + ask_total) > 0 else 0
            
            result = {
                'symbol': symbol,
                'exchange': exchange,
                'bids': orderbook['bids'][:depth],
                'asks': orderbook['asks'][:depth],
                'bid_total': bid_total,
                'ask_total': ask_total,
                'imbalance': imbalance,
                'spread': orderbook['asks'][0][0] - orderbook['bids'][0][0] if orderbook['bids'] and orderbook['asks'] else 0,
                'mid_price': (orderbook['asks'][0][0] + orderbook['bids'][0][0]) / 2 if orderbook['bids'] and orderbook['asks'] else 0,
                'timestamp': orderbook['timestamp']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange} {symbol}订单簿失败: {e}")
            return {}
            
    def get_recent_trades(self, symbol: str, exchange: str, limit: int = 100) -> List[Dict]:
        """
        获取最近成交记录
        用于判断是否有大单成交
        
        Args:
            symbol: 交易对
            exchange: 交易所
            limit: 获取数量
            
        Returns:
            [{
                'id': '123456',
                'price': 67500.00,
                'amount': 0.5,
                'value': 33750.00,
                'side': 'buy',
                'timestamp': 1234567890,
                'is_large': True  # 是否大单
            }]
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取最近成交
            trades = client.fetch_trades(symbol, limit=limit)
            
            # 计算平均成交额，用于判断大单
            values = [trade['amount'] * trade['price'] for trade in trades]
            avg_value = sum(values) / len(values) if values else 0
            
            result = []
            for trade in trades:
                value = trade['amount'] * trade['price']
                result.append({
                    'id': trade['id'],
                    'price': trade['price'],
                    'amount': trade['amount'],
                    'value': value,
                    'side': trade['side'],
                    'timestamp': trade['timestamp'],
                    'is_large': value > avg_value * 3  # 超过平均值3倍认为是大单
                })
                
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange} {symbol}最近成交失败: {e}")
            return []
            
    def get_volume_change(self, symbol: str, exchange: str, minutes: int = 5) -> Dict:
        """
        获取成交量变化
        返回最近N分钟vs前N分钟的变化率
        
        Args:
            symbol: 交易对
            exchange: 交易所
            minutes: 时间窗口（分钟）
            
        Returns:
            {
                'symbol': 'BTC/USDT',
                'current_volume': 1234.56,
                'previous_volume': 1000.00,
                'change_rate': 0.2346,  # 23.46%增长
                'is_surge': True  # 是否放量
            }
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取K线数据
            timeframe = '1m'
            limit = minutes * 2
            ohlcv = client.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if len(ohlcv) < limit:
                logger.warning(f"数据不足，只有{len(ohlcv)}条")
                return {}
                
            # 转换为DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 计算最近N分钟和前N分钟的成交量
            current_volume = df.tail(minutes)['volume'].sum()
            previous_volume = df.head(minutes)['volume'].sum()
            
            # 计算变化率
            change_rate = (current_volume - previous_volume) / previous_volume if previous_volume > 0 else 0
            
            result = {
                'symbol': symbol,
                'exchange': exchange,
                'current_volume': current_volume,
                'previous_volume': previous_volume,
                'change_rate': change_rate,
                'is_surge': change_rate > 0.5,  # 增长50%以上认为放量
                'timeframe': f'{minutes}m'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange} {symbol}成交量变化失败: {e}")
            return {}
            
    def get_multiple_prices(self, symbols: List[str], exchange: str) -> Dict[str, Dict]:
        """
        批量获取多个币种的价格
        
        Args:
            symbols: 交易对列表
            exchange: 交易所
            
        Returns:
            {
                'BTC/USDT': {...},
                'ETH/USDT': {...},
                ...
            }
        """
        result = {}
        
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 批量获取ticker
            tickers = client.fetch_tickers(symbols)
            
            for symbol in symbols:
                if symbol in tickers:
                    ticker = tickers[symbol]
                    result[symbol] = {
                        'price': ticker['last'],
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'volume_24h': ticker['quoteVolume'],
                        'change_24h': ticker['percentage']
                    }
                    
            return result
            
        except Exception as e:
            logger.error(f"批量获取{exchange}价格失败: {e}")
            # 降级为逐个获取
            for symbol in symbols:
                price_data = self.get_realtime_price(symbol, exchange)
                if price_data:
                    result[symbol] = price_data
                    
            return result


# 测试代码
if __name__ == "__main__":
    collector = RealtimeDataCollector()
    
    # 测试获取实时价格
    print("\n=== BTC/USDT实时价格 ===")
    price = collector.get_realtime_price('BTC/USDT', 'binance')
    if price:
        print(f"价格: ${price['price']:.2f}")
        print(f"买一: ${price['bid']:.2f}")
        print(f"卖一: ${price['ask']:.2f}")
        print(f"价差: ${price['spread']:.2f} ({price['spread_percentage']:.3f}%)")
        print(f"24h成交量: ${price['volume_24h']:,.0f}")
    
    # 测试获取订单簿
    print("\n=== BTC/USDT订单簿深度 ===")
    depth = collector.get_orderbook_depth('BTC/USDT', 'binance', 5)
    if depth:
        print(f"买单前5档:")
        for bid in depth['bids'][:5]:
            print(f"  ${bid[0]:.2f}: {bid[1]:.4f} BTC")
        print(f"卖单前5档:")
        for ask in depth['asks'][:5]:
            print(f"  ${ask[0]:.2f}: {ask[1]:.4f} BTC")
        print(f"买卖不平衡度: {depth['imbalance']:.2%}")
    
    # 测试成交量变化
    print("\n=== BTC/USDT成交量变化 ===")
    volume = collector.get_volume_change('BTC/USDT', 'binance', 5)
    if volume:
        print(f"最近5分钟成交量: {volume['current_volume']:.2f}")
        print(f"前5分钟成交量: {volume['previous_volume']:.2f}")
        print(f"变化率: {volume['change_rate']:.2%}")
        print(f"是否放量: {'是' if volume['is_surge'] else '否'}")