"""
Window 2 - WebSocket数据流推送器
负责实时推送价格、深度、成交等数据
"""

import asyncio
import json
import time
import websockets
from typing import Dict, List, Callable, Optional
from datetime import datetime
import ccxt.pro as ccxtpro
from loguru import logger
import threading
from queue import Queue
import signal
import sys


class WebSocketStreamer:
    """WebSocket数据流推送器"""
    
    def __init__(self):
        """初始化WebSocket推送器"""
        self.okx_client = None
        self.binance_client = None
        self.subscribers = {}  # 订阅者回调函数
        self.running = False
        self.tasks = []
        self.message_queue = Queue()
        self._init_exchanges()
        
    def _init_exchanges(self):
        """初始化交易所客户端"""
        try:
            # OKX WebSocket配置
            self.okx_client = ccxtpro.okx({
                'apiKey': '79d7b5b4-2e9b-4a31-be9c-95527d618739',
                'secret': '070B16A29AF22C13A67D9CB807B5693D',
                'password': 'Yzh198796&',
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            # Binance WebSocket配置（通过代理）
            self.binance_client = ccxtpro.binance({
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
            
            logger.info("WebSocket推送器初始化成功")
            
        except Exception as e:
            logger.error(f"初始化WebSocket失败: {e}")
            
    async def subscribe_price_stream(self, symbols: List[str], exchange: str = 'binance', callback: Callable = None):
        """
        订阅价格推送
        毫秒级更新
        
        Args:
            symbols: 交易对列表 ['BTC/USDT', 'ETH/USDT']
            exchange: 交易所名称
            callback: 回调函数，接收数据 callback(data)
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            logger.info(f"开始订阅{exchange}价格流: {symbols}")
            
            while self.running:
                try:
                    for symbol in symbols:
                        ticker = await client.watch_ticker(symbol)
                        
                        data = {
                            'type': 'ticker',
                            'exchange': exchange,
                            'symbol': symbol,
                            'price': ticker['last'],
                            'bid': ticker['bid'],
                            'ask': ticker['ask'],
                            'volume': ticker['baseVolume'],
                            'change': ticker['percentage'],
                            'timestamp': ticker['timestamp']
                        }
                        
                        # 发送到回调函数
                        if callback:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data)
                                else:
                                    callback(data)
                            except Exception as e:
                                logger.error(f"价格回调函数错误: {e}")
                        
                        # 添加到消息队列
                        self.message_queue.put(data)
                        
                except Exception as e:
                    logger.error(f"价格订阅错误: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"价格流订阅失败: {e}")
            
    async def subscribe_trade_stream(self, symbols: List[str], exchange: str = 'binance', callback: Callable = None):
        """
        订阅成交推送
        实时成交数据
        
        Args:
            symbols: 交易对列表
            exchange: 交易所名称  
            callback: 回调函数
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            logger.info(f"开始订阅{exchange}成交流: {symbols}")
            
            while self.running:
                try:
                    for symbol in symbols:
                        trades = await client.watch_trades(symbol)
                        
                        for trade in trades:
                            data = {
                                'type': 'trade',
                                'exchange': exchange,
                                'symbol': symbol,
                                'price': trade['price'],
                                'amount': trade['amount'],
                                'side': trade['side'],
                                'timestamp': trade['timestamp'],
                                'id': trade['id']
                            }
                            
                            # 发送到回调函数
                            if callback:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(data)
                                    else:
                                        callback(data)
                                except Exception as e:
                                    logger.error(f"成交回调函数错误: {e}")
                            
                            # 添加到消息队列
                            self.message_queue.put(data)
                            
                except Exception as e:
                    logger.error(f"成交订阅错误: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"成交流订阅失败: {e}")
            
    async def subscribe_orderbook_stream(self, symbols: List[str], exchange: str = 'binance', callback: Callable = None):
        """
        订阅订单簿推送
        订单簿变化
        
        Args:
            symbols: 交易对列表
            exchange: 交易所名称
            callback: 回调函数
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            logger.info(f"开始订阅{exchange}订单簿流: {symbols}")
            
            while self.running:
                try:
                    for symbol in symbols:
                        orderbook = await client.watch_order_book(symbol)
                        
                        data = {
                            'type': 'orderbook',
                            'exchange': exchange,
                            'symbol': symbol,
                            'bids': orderbook['bids'][:10],  # 前10档
                            'asks': orderbook['asks'][:10],
                            'timestamp': orderbook['timestamp']
                        }
                        
                        # 发送到回调函数
                        if callback:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data)
                                else:
                                    callback(data)
                            except Exception as e:
                                logger.error(f"订单簿回调函数错误: {e}")
                        
                        # 添加到消息队列
                        self.message_queue.put(data)
                        
                except Exception as e:
                    logger.error(f"订单簿订阅错误: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"订单簿流订阅失败: {e}")
            
    async def start_streaming(self, config: Dict):
        """
        开始流式传输
        
        Args:
            config: 配置字典
            {
                'price_symbols': ['BTC/USDT', 'ETH/USDT'],
                'trade_symbols': ['BTC/USDT'],
                'orderbook_symbols': ['BTC/USDT'],
                'exchanges': ['binance', 'okx'],
                'callbacks': {
                    'price': price_callback,
                    'trade': trade_callback,
                    'orderbook': orderbook_callback
                }
            }
        """
        self.running = True
        
        try:
            # 创建所有订阅任务
            for exchange in config.get('exchanges', ['binance']):
                
                # 价格流订阅
                if config.get('price_symbols'):
                    task = asyncio.create_task(
                        self.subscribe_price_stream(
                            config['price_symbols'],
                            exchange,
                            config.get('callbacks', {}).get('price')
                        )
                    )
                    self.tasks.append(task)
                
                # 成交流订阅
                if config.get('trade_symbols'):
                    task = asyncio.create_task(
                        self.subscribe_trade_stream(
                            config['trade_symbols'],
                            exchange,
                            config.get('callbacks', {}).get('trade')
                        )
                    )
                    self.tasks.append(task)
                
                # 订单簿流订阅
                if config.get('orderbook_symbols'):
                    task = asyncio.create_task(
                        self.subscribe_orderbook_stream(
                            config['orderbook_symbols'],
                            exchange,
                            config.get('callbacks', {}).get('orderbook')
                        )
                    )
                    self.tasks.append(task)
            
            logger.info(f"启动{len(self.tasks)}个WebSocket流")
            
            # 等待所有任务完成
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"WebSocket流启动失败: {e}")
            
    def stop_streaming(self):
        """停止流式传输"""
        self.running = False
        
        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        # 关闭连接
        try:
            if self.okx_client:
                asyncio.create_task(self.okx_client.close())
            if self.binance_client:
                asyncio.create_task(self.binance_client.close())
        except Exception as e:
            logger.error(f"关闭WebSocket连接失败: {e}")
            
        logger.info("WebSocket流已停止")
        
    def get_message_queue(self) -> Queue:
        """获取消息队列"""
        return self.message_queue
        
    def clear_message_queue(self):
        """清空消息队列"""
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except:
                break


# 示例回调函数
async def price_callback(data):
    """价格数据回调"""
    print(f"💰 {data['symbol']}: ${data['price']:.2f} ({data['exchange']})")

def trade_callback(data):
    """成交数据回调"""
    side_emoji = "🟢" if data['side'] == 'buy' else "🔴"
    print(f"{side_emoji} {data['symbol']}: {data['amount']:.4f} @ ${data['price']:.2f}")

def orderbook_callback(data):
    """订单簿数据回调"""
    best_bid = data['bids'][0][0] if data['bids'] else 0
    best_ask = data['asks'][0][0] if data['asks'] else 0
    print(f"📊 {data['symbol']}: Bid ${best_bid:.2f} | Ask ${best_ask:.2f}")


# 测试代码
if __name__ == "__main__":
    async def test_websocket():
        """测试WebSocket功能"""
        print("=== WebSocket流测试 ===")
        
        streamer = WebSocketStreamer()
        
        # 配置订阅
        config = {
            'price_symbols': ['BTC/USDT', 'ETH/USDT'],
            'trade_symbols': ['BTC/USDT'],
            'orderbook_symbols': ['BTC/USDT'],
            'exchanges': ['binance'],
            'callbacks': {
                'price': price_callback,
                'trade': trade_callback,
                'orderbook': orderbook_callback
            }
        }
        
        # 设置信号处理
        def signal_handler(sig, frame):
            print("\\n正在停止WebSocket流...")
            streamer.stop_streaming()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            print("开始WebSocket流，按Ctrl+C停止...")
            await streamer.start_streaming(config)
        except KeyboardInterrupt:
            print("\\n收到停止信号")
        finally:
            streamer.stop_streaming()
    
    # 运行测试（仅在直接运行时）
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("测试已停止")