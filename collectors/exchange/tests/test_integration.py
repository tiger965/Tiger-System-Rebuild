"""
交易所数据采集器集成测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import asyncio
import unittest
from datetime import datetime, timezone
import logging

from collectors.exchange.main_collector import ExchangeDataCollector

logging.basicConfig(level=logging.INFO)

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    async def async_test_main_collector(self):
        """测试主采集器"""
        collector = ExchangeDataCollector()
        
        try:
            # 初始化
            await collector.initialize()
            
            # 启动采集
            await collector.start()
            
            # 运行5秒
            await asyncio.sleep(5)
            
            # 检查是否有数据
            latest_data = collector.get_latest_data()
            self.assertIsNotNone(latest_data)
            
            # 检查BTC数据
            btc_data = collector.get_latest_data("ticker", "BTC-USDT")
            if btc_data:
                self.assertIn("last_price", btc_data)
                self.assertGreater(btc_data["last_price"], 0)
                print(f"BTC-USDT价格: {btc_data['last_price']}")
            
            # 检查统计信息
            detector_stats = collector.detector.get_statistics()
            validator_stats = collector.validator.get_stats()
            
            print(f"检测器统计: {detector_stats}")
            print(f"验证器统计: {validator_stats}")
            
        finally:
            # 停止采集
            await collector.stop()
    
    def test_main_collector(self):
        """同步测试主采集器"""
        asyncio.run(self.async_test_main_collector())
    
    async def async_test_data_flow(self):
        """测试数据流"""
        collector = ExchangeDataCollector()
        
        try:
            await collector.initialize()
            
            # 模拟数据流
            # 1. 采集原始数据
            okx_ticker = await collector.okx_collector.get_ticker("BTC-USDT")
            self.assertIsNotNone(okx_ticker)
            
            # 2. 标准化数据
            normalized = collector.normalizer.normalize_ticker(okx_ticker, "OKX")
            self.assertIsNotNone(normalized)
            self.assertEqual(normalized["symbol"], "BTCUSDT")
            
            # 3. 验证数据
            valid, error = collector.validator.validate_ticker(normalized)
            self.assertTrue(valid, f"验证失败: {error}")
            
            # 4. 检测异常
            anomaly = await collector.detector.detect_price_anomaly(
                normalized["symbol"], 
                normalized["last_price"]
            )
            # 第一次检测通常不会有异常（需要历史数据）
            
            print("数据流测试通过")
            
        finally:
            await collector.okx_collector.close()
            await collector.binance_collector.close()
    
    def test_data_flow(self):
        """同步测试数据流"""
        asyncio.run(self.async_test_data_flow())
    
    async def async_test_websocket_connection(self):
        """测试WebSocket连接"""
        collector = ExchangeDataCollector()
        
        try:
            await collector.initialize()
            
            # 连接WebSocket
            await collector.okx_collector.connect_public_ws()
            self.assertIsNotNone(collector.okx_collector.ws_public_conn)
            
            # 订阅数据
            await collector.okx_collector.subscribe_ticker(["BTC-USDT"])
            
            # 等待数据
            await asyncio.sleep(3)
            
            print("WebSocket连接测试通过")
            
        finally:
            await collector.okx_collector.close()
            await collector.binance_collector.close()
    
    def test_websocket_connection(self):
        """同步测试WebSocket连接"""
        asyncio.run(self.async_test_websocket_connection())


if __name__ == "__main__":
    # 运行集成测试
    unittest.main(verbosity=2)