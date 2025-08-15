"""
交易所数据采集器单元测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import asyncio
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from collectors.exchange.okx_collector import OKXCollector, OKXConfig
from collectors.exchange.binance_collector import BinanceCollector, BinanceConfig
from collectors.exchange.normalizer import DataNormalizer
from collectors.exchange.detector import AnomalyDetector
from collectors.exchange.validator import DataValidator


class TestOKXCollector(unittest.TestCase):
    """测试OKX采集器"""
    
    def setUp(self):
        self.config = OKXConfig(demo_mode=True)
        self.collector = OKXCollector(self.config)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.collector)
        self.assertTrue(self.collector.config.demo_mode)
        self.assertEqual(self.collector.config.rest_url, "https://www.okx.com")
    
    async def async_test_get_ticker(self):
        """测试获取行情"""
        await self.collector.initialize()
        ticker = await self.collector.get_ticker("BTC-USDT")
        
        self.assertIsNotNone(ticker)
        self.assertIn("instId", ticker)
        self.assertIn("last", ticker)
        
        await self.collector.close()
    
    def test_get_ticker(self):
        """同步测试获取行情"""
        asyncio.run(self.async_test_get_ticker())
    
    async def async_test_get_order_book(self):
        """测试获取深度"""
        await self.collector.initialize()
        depth = await self.collector.get_order_book("BTC-USDT")
        
        self.assertIsNotNone(depth)
        self.assertIn("asks", depth)
        self.assertIn("bids", depth)
        
        await self.collector.close()
    
    def test_get_order_book(self):
        """同步测试获取深度"""
        asyncio.run(self.async_test_get_order_book())


class TestBinanceCollector(unittest.TestCase):
    """测试Binance采集器"""
    
    def setUp(self):
        self.config = BinanceConfig(demo_mode=True)
        self.collector = BinanceCollector(self.config)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.collector)
        self.assertTrue(self.collector.config.demo_mode)
        self.assertEqual(self.collector.config.rest_url, "https://api.binance.com")
    
    async def async_test_get_ticker_24hr(self):
        """测试获取24小时行情"""
        await self.collector.initialize()
        ticker = await self.collector.get_ticker_24hr("BTCUSDT")
        
        self.assertIsNotNone(ticker)
        self.assertIn("symbol", ticker)
        self.assertIn("lastPrice", ticker)
        
        await self.collector.close()
    
    def test_get_ticker_24hr(self):
        """同步测试获取24小时行情"""
        asyncio.run(self.async_test_get_ticker_24hr())
    
    async def async_test_get_order_book(self):
        """测试获取深度"""
        await self.collector.initialize()
        depth = await self.collector.get_order_book("BTCUSDT", 10)
        
        self.assertIsNotNone(depth)
        self.assertIn("bids", depth)
        self.assertIn("asks", depth)
        
        await self.collector.close()
    
    def test_get_order_book(self):
        """同步测试获取深度"""
        asyncio.run(self.async_test_get_order_book())


class TestDataNormalizer(unittest.TestCase):
    """测试数据标准化"""
    
    def setUp(self):
        self.normalizer = DataNormalizer()
    
    def test_normalize_okx_ticker(self):
        """测试标准化OKX行情"""
        okx_data = {
            "instId": "BTC-USDT",
            "last": "67500.5",
            "bidPx": "67500.0",
            "bidSz": "2.0",
            "askPx": "67501.0",
            "askSz": "1.5",
            "open24h": "67000.0",
            "high24h": "68000.0",
            "low24h": "66500.0",
            "vol24h": "5432.1",
            "ts": "1704067200000"
        }
        
        normalized = self.normalizer.normalize_ticker(okx_data, "OKX")
        
        self.assertEqual(normalized["symbol"], "BTCUSDT")
        self.assertEqual(normalized["last_price"], 67500.5)
        self.assertEqual(normalized["source"], "OKX")
    
    def test_normalize_binance_ticker(self):
        """测试标准化Binance行情"""
        binance_data = {
            "symbol": "BTCUSDT",
            "lastPrice": "67500.50",
            "bidPrice": "67500.00",
            "bidQty": "2.00",
            "askPrice": "67501.00",
            "askQty": "1.50",
            "openPrice": "67000.00",
            "highPrice": "68000.00",
            "lowPrice": "66500.00",
            "volume": "5432.10",
            "closeTime": 1704067200000
        }
        
        normalized = self.normalizer.normalize_ticker(binance_data, "Binance")
        
        self.assertEqual(normalized["symbol"], "BTCUSDT")
        self.assertEqual(normalized["last_price"], 67500.5)
        self.assertEqual(normalized["source"], "Binance")
    
    def test_convert_symbol(self):
        """测试符号转换"""
        # OKX to Binance
        result = self.normalizer.convert_symbol("BTC-USDT", "OKX", "Binance")
        self.assertEqual(result, "BTCUSDT")
        
        # Binance to OKX
        result = self.normalizer.convert_symbol("BTCUSDT", "Binance", "OKX")
        self.assertEqual(result, "BTC-USDT")


class TestAnomalyDetector(unittest.TestCase):
    """测试异常检测"""
    
    def setUp(self):
        self.detector = AnomalyDetector()
    
    async def async_test_price_anomaly(self):
        """测试价格异常检测"""
        symbol = "BTCUSDT"
        
        # 添加正常价格历史（带时间戳）
        base_time = datetime.now(timezone.utc) - timedelta(seconds=70)
        for i in range(15):
            timestamp = base_time + timedelta(seconds=i * 4)
            await self.detector.detect_price_anomaly(symbol, 67000 + i * 10, timestamp)
        
        # 检测价格暴涨（当前时间）
        anomaly = await self.detector.detect_price_anomaly(symbol, 70000, datetime.now(timezone.utc))
        
        self.assertIsNotNone(anomaly)
        self.assertEqual(anomaly["type"], "price_anomaly")
        self.assertEqual(anomaly["direction"], "surge")
    
    def test_price_anomaly(self):
        """同步测试价格异常"""
        asyncio.run(self.async_test_price_anomaly())
    
    async def async_test_volume_anomaly(self):
        """测试成交量异常检测"""
        symbol = "BTCUSDT"
        
        # 添加正常成交量历史
        for i in range(10):
            await self.detector.detect_volume_anomaly(symbol, 100 + i * 5)
        
        # 检测成交量激增
        anomaly = await self.detector.detect_volume_anomaly(symbol, 1000)
        
        self.assertIsNotNone(anomaly)
        self.assertEqual(anomaly["type"], "volume_anomaly")
    
    def test_volume_anomaly(self):
        """同步测试成交量异常"""
        asyncio.run(self.async_test_volume_anomaly())
    
    async def async_test_large_trade(self):
        """测试大单检测"""
        trade = {
            "price": 67000,
            "size": 20,
            "side": "buy"
        }
        
        anomaly = await self.detector.detect_large_trade("BTCUSDT", trade)
        
        self.assertIsNotNone(anomaly)
        self.assertEqual(anomaly["type"], "large_trade")
        self.assertEqual(anomaly["value"], 1340000)
    
    def test_large_trade(self):
        """同步测试大单检测"""
        asyncio.run(self.async_test_large_trade())


class TestDataValidator(unittest.TestCase):
    """测试数据验证"""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_validate_ticker(self):
        """测试行情数据验证"""
        # 有效数据
        valid_ticker = {
            "symbol": "BTCUSDT",
            "last_price": 67500.5,
            "bid_price": 67500.0,
            "ask_price": 67501.0,
            "volume_24h": 5432.1,
            "timestamp": datetime.now(timezone.utc)
        }
        
        valid, error = self.validator.validate_ticker(valid_ticker)
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # 无效数据（买价高于卖价）
        invalid_ticker = valid_ticker.copy()
        invalid_ticker["bid_price"] = 68000
        
        valid, error = self.validator.validate_ticker(invalid_ticker)
        self.assertFalse(valid)
        self.assertIn("买价", error)
    
    def test_validate_depth(self):
        """测试深度数据验证"""
        depth = {
            "symbol": "BTCUSDT",
            "bids": [
                {"price": 67500.0, "size": 2.0},
                {"price": 67499.0, "size": 1.8}
            ],
            "asks": [
                {"price": 67501.0, "size": 1.5},
                {"price": 67502.0, "size": 2.0}
            ],
            "timestamp": datetime.now(timezone.utc)
        }
        
        valid, error = self.validator.validate_depth(depth)
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_validate_trade(self):
        """测试成交数据验证"""
        trade = {
            "symbol": "BTCUSDT",
            "price": 67500.5,
            "size": 0.5,
            "side": "buy",
            "timestamp": datetime.now(timezone.utc)
        }
        
        valid, error = self.validator.validate_trade(trade)
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_cross_validation(self):
        """测试交叉验证"""
        okx_data = {
            "last_price": 67500.0,
            "timestamp": datetime.now(timezone.utc)
        }
        binance_data = {
            "last_price": 67510.0,
            "timestamp": datetime.now(timezone.utc)
        }
        
        valid, error = self.validator.validate_cross_exchange(okx_data, binance_data)
        self.assertTrue(valid)
        self.assertIsNone(error)


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)