#!/usr/bin/env python3
"""Database connection and operation tests"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import psycopg2
from datetime import datetime
import time
from database.init_database import DatabaseInitializer
from core.dal import DataAccessLayer, get_dal
from core.interfaces import (
    MarketData, Signal, SignalType, TimeHorizon,
    SystemLog, LogLevel, SocialSentiment
)

class TestDatabaseConnection(unittest.TestCase):
    """Test database connections"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        cls.initializer = DatabaseInitializer()
        cls.dal = get_dal()
    
    def test_01_database_exists(self):
        """Test if database exists"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='tiger_system',
                user='postgres',
                password='postgres'
            )
            conn.close()
            self.assertTrue(True, "Database connection successful")
        except psycopg2.Error as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_02_tables_exist(self):
        """Test if all required tables exist"""
        result = self.initializer.verify_tables()
        self.assertTrue(result, "All required tables should exist")
    
    def test_03_insert_market_data(self):
        """Test inserting market data"""
        market_data = MarketData(
            symbol="BTC/USDT",
            price=50000.0,
            volume=1000.0,
            source="test",
            exchange="binance",
            timestamp=datetime.now()
        )
        
        result = self.dal.insert_market_data(market_data)
        self.assertTrue(result, "Market data should be inserted successfully")
    
    def test_04_retrieve_market_data(self):
        """Test retrieving market data"""
        # First insert some data
        market_data = MarketData(
            symbol="ETH/USDT",
            price=3000.0,
            volume=500.0,
            source="test",
            exchange="binance",
            timestamp=datetime.now()
        )
        self.dal.insert_market_data(market_data)
        
        # Retrieve the data
        results = self.dal.get_latest_market_data("ETH/USDT", limit=10)
        self.assertIsNotNone(results, "Should retrieve market data")
        self.assertGreater(len(results), 0, "Should have at least one record")
    
    def test_05_insert_signal(self):
        """Test inserting trading signal"""
        signal = Signal(
            signal_type=SignalType.BUY,
            symbol="BTC/USDT",
            confidence=0.85,
            trigger_reason="Technical indicators bullish",
            source="technical_analysis",
            target_price=55000.0,
            stop_loss=48000.0,
            time_horizon=TimeHorizon.MEDIUM
        )
        
        signal_id = self.dal.insert_signal(signal)
        self.assertIsNotNone(signal_id, "Signal should be inserted with ID")
    
    def test_06_get_active_signals(self):
        """Test retrieving active signals"""
        signals = self.dal.get_active_signals()
        self.assertIsInstance(signals, list, "Should return list of signals")
    
    def test_07_system_logging(self):
        """Test system logging"""
        self.dal.log(
            window_id=1,
            level="info",
            component="test",
            message="Test log message"
        )
        # If no exception, test passes
        self.assertTrue(True, "Log should be written successfully")
    
    def test_08_sentiment_operations(self):
        """Test social sentiment operations"""
        sentiment = SocialSentiment(
            source="twitter",
            content="Bitcoin to the moon!",
            sentiment_score=0.8,
            symbol="BTC",
            author="test_user"
        )
        
        result = self.dal.insert_social_sentiment(sentiment)
        self.assertTrue(result, "Sentiment should be inserted")
        
        # Get sentiment summary
        summary = self.dal.get_sentiment_summary("BTC", hours=24)
        self.assertIsNotNone(summary, "Should get sentiment summary")
    
    def test_09_batch_insert_performance(self):
        """Test batch insert performance"""
        import asyncio
        
        # Create batch of market data
        batch_data = []
        base_time = datetime.now()
        for i in range(100):
            data = MarketData(
                symbol="TEST/USDT",
                price=100.0 + i,
                volume=1000.0 + i,
                source="test",
                exchange="test_exchange",
                timestamp=base_time
            )
            batch_data.append(data)
        
        # Test batch insert
        start_time = time.time()
        
        async def insert_batch():
            return await self.dal.insert_market_data_batch(batch_data)
        
        inserted = asyncio.run(insert_batch())
        
        elapsed_time = time.time() - start_time
        
        self.assertEqual(inserted, 100, "Should insert 100 records")
        self.assertLess(elapsed_time, 5, "Batch insert should complete within 5 seconds")
        print(f"Batch insert of 100 records took {elapsed_time:.2f} seconds")
    
    def test_10_connection_pool(self):
        """Test connection pool functionality"""
        # Test multiple concurrent connections
        import concurrent.futures
        
        def query_test(i):
            results = self.dal.execute_query(
                "SELECT COUNT(*) as count FROM market_data"
            )
            return results[0]['count'] if results else 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_test, i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        self.assertEqual(len(results), 20, "All concurrent queries should complete")
    
    def test_11_system_health(self):
        """Test system health monitoring"""
        health = self.dal.get_system_health()
        self.assertIsInstance(health, list, "Should return health data")
    
    def test_12_performance_stats(self):
        """Test performance statistics"""
        stats = self.dal.get_performance_stats()
        self.assertIn('database', stats, "Should have database stats")
        self.assertIn('redis', stats, "Should have redis stats")

class TestRedisOperations(unittest.TestCase):
    """Test Redis operations"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Redis connection"""
        from core.redis_manager import RedisManager
        cls.redis = RedisManager()
    
    def test_01_redis_connection(self):
        """Test Redis connection"""
        health = self.redis.health_check()
        self.assertEqual(health['status'], 'healthy', "Redis should be healthy")
    
    def test_02_cache_operations(self):
        """Test cache operations"""
        # Set cache
        result = self.redis.set_cache("test_key", {"data": "test_value"}, ttl=60)
        self.assertTrue(result, "Should set cache successfully")
        
        # Get cache
        value = self.redis.get_cache("test_key")
        self.assertIsNotNone(value, "Should retrieve cached value")
        self.assertEqual(value['data'], "test_value", "Cache value should match")
        
        # Delete cache
        deleted = self.redis.delete_cache("test_key")
        self.assertGreater(deleted, 0, "Should delete cache key")
    
    def test_03_market_data_cache(self):
        """Test market data caching"""
        market_data = {
            'symbol': 'BTC/USDT',
            'price': 50000,
            'volume': 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        result = self.redis.set_market_data('BTC/USDT', market_data)
        self.assertTrue(result, "Should cache market data")
        
        cached = self.redis.get_market_data('BTC/USDT')
        self.assertIsNotNone(cached, "Should retrieve cached market data")
    
    def test_04_message_queue(self):
        """Test message queue operations"""
        message = {'type': 'test', 'data': 'test_message'}
        
        # Push message
        result = self.redis.push_message('test_queue', message)
        self.assertTrue(result, "Should push message to queue")
        
        # Check queue length
        length = self.redis.get_queue_length('test_queue')
        self.assertGreater(length, 0, "Queue should have messages")
        
        # Pop message
        popped = self.redis.pop_message('test_queue', timeout=1)
        self.assertIsNotNone(popped, "Should pop message from queue")
        self.assertEqual(popped['type'], 'test', "Message type should match")
    
    def test_05_pub_sub(self):
        """Test pub/sub functionality"""
        import threading
        import time
        
        received_messages = []
        
        def callback(channel, message):
            received_messages.append({'channel': channel, 'message': message})
        
        # Subscribe to channel
        self.redis.subscribe(['test_channel'], callback)
        
        # Give subscription time to set up
        time.sleep(0.5)
        
        # Publish message
        result = self.redis.publish('test_channel', {'test': 'pub_sub_message'})
        self.assertTrue(result, "Should publish message")
        
        # Wait for message to be received
        time.sleep(0.5)
        
        self.assertGreater(len(received_messages), 0, "Should receive published message")
    
    def test_06_stream_operations(self):
        """Test Redis stream operations"""
        # Add to stream
        stream_data = {'event': 'test', 'value': 123}
        message_id = self.redis.add_to_stream('test_stream', stream_data)
        self.assertIsNotNone(message_id, "Should add message to stream")
        
        # Read from stream
        messages = self.redis.read_from_stream('test_stream', last_id='0', count=10)
        self.assertGreater(len(messages), 0, "Should read messages from stream")
        self.assertEqual(messages[0]['event'], 'test', "Stream message should match")
    
    def test_07_signal_management(self):
        """Test signal management in Redis"""
        signal_data = {
            'symbol': 'BTC/USDT',
            'type': 'buy',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        }
        
        # Set signal
        result = self.redis.set_signal('test_signal_123', signal_data)
        self.assertTrue(result, "Should store signal in Redis")
        
        # Get active signals
        signals = self.redis.get_active_signals(limit=10)
        self.assertIsInstance(signals, list, "Should return list of signals")

def run_all_tests():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestRedisOperations))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed successfully!")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())