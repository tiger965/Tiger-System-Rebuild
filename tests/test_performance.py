#!/usr/bin/env python3
"""Performance tests for Tiger System database infrastructure"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
import statistics
from datetime import datetime, timedelta
import concurrent.futures
from typing import List, Dict, Any
import random
import string

from core.dal import get_dal
from core.interfaces import MarketData, Signal, SignalType, TimeHorizon
from core.redis_manager import RedisManager

class PerformanceTester:
    """Performance testing for database operations"""
    
    def __init__(self):
        self.dal = get_dal()
        self.redis = RedisManager()
        self.results = {}
    
    def generate_random_symbol(self) -> str:
        """Generate random trading symbol"""
        bases = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC']
        quotes = ['USDT', 'USDC', 'BUSD']
        return f"{random.choice(bases)}/{random.choice(quotes)}"
    
    def generate_market_data(self, count: int) -> List[MarketData]:
        """Generate test market data"""
        data_list = []
        base_time = datetime.now()
        
        for i in range(count):
            data = MarketData(
                symbol=self.generate_random_symbol(),
                price=random.uniform(1, 50000),
                volume=random.uniform(100, 10000),
                source="performance_test",
                exchange=random.choice(['binance', 'coinbase', 'okx']),
                timestamp=base_time - timedelta(seconds=i),
                high_24h=random.uniform(1, 55000),
                low_24h=random.uniform(1, 45000),
                bid_price=random.uniform(1, 49000),
                ask_price=random.uniform(1, 51000)
            )
            data_list.append(data)
        
        return data_list
    
    def test_single_insert_performance(self, iterations: int = 1000):
        """Test single insert performance"""
        print(f"\n Testing single insert performance ({iterations} iterations)...")
        
        data_list = self.generate_market_data(iterations)
        times = []
        
        for data in data_list:
            start_time = time.perf_counter()
            self.dal.insert_market_data(data)
            elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantile(times, 0.95)
        p99_time = statistics.quantile(times, 0.99)
        
        self.results['single_insert'] = {
            'iterations': iterations,
            'avg_ms': round(avg_time, 2),
            'median_ms': round(median_time, 2),
            'p95_ms': round(p95_time, 2),
            'p99_ms': round(p99_time, 2),
            'throughput_per_sec': round(1000 / avg_time, 2)
        }
        
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median: {median_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        print(f"  P99: {p99_time:.2f}ms")
        print(f"  Throughput: {1000/avg_time:.2f} ops/sec")
        
        # Check if meets requirements
        if avg_time < 10:
            print("  ✓ Meets requirement: < 10ms average")
        else:
            print("  ✗ Does not meet requirement: < 10ms average")
    
    async def test_batch_insert_performance(self, batch_size: int = 1000, batches: int = 10):
        """Test batch insert performance"""
        print(f"\n Testing batch insert performance ({batches} batches of {batch_size})...")
        
        times = []
        
        for _ in range(batches):
            data_list = self.generate_market_data(batch_size)
            
            start_time = time.perf_counter()
            inserted = await self.dal.insert_market_data_batch(data_list)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        total_records = batch_size * batches
        throughput = (total_records / sum(times)) * 1000
        
        self.results['batch_insert'] = {
            'batch_size': batch_size,
            'batches': batches,
            'total_records': total_records,
            'avg_batch_ms': round(avg_time, 2),
            'throughput_per_sec': round(throughput, 2)
        }
        
        print(f"  Average batch time: {avg_time:.2f}ms")
        print(f"  Records per second: {throughput:.2f}")
        
        # Check if meets requirements
        if throughput > 10000:
            print("  ✓ Meets requirement: > 10,000 records/sec")
        else:
            print("  ✗ Does not meet requirement: > 10,000 records/sec")
    
    def test_query_performance(self, iterations: int = 100):
        """Test query performance"""
        print(f"\n Testing query performance ({iterations} iterations)...")
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        times = []
        
        for _ in range(iterations):
            symbol = random.choice(symbols)
            
            start_time = time.perf_counter()
            results = self.dal.get_latest_market_data(symbol, limit=100)
            elapsed = (time.perf_counter() - start_time) * 1000
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = statistics.quantile(times, 0.95)
        
        self.results['query'] = {
            'iterations': iterations,
            'avg_ms': round(avg_time, 2),
            'median_ms': round(median_time, 2),
            'p95_ms': round(p95_time, 2)
        }
        
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Median: {median_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")
        
        # Check if meets requirements
        if avg_time < 100:
            print("  ✓ Meets requirement: < 100ms average")
        else:
            print("  ✗ Does not meet requirement: < 100ms average")
    
    def test_concurrent_operations(self, workers: int = 20, operations: int = 100):
        """Test concurrent database operations"""
        print(f"\n Testing concurrent operations ({workers} workers, {operations} ops each)...")
        
        def worker_task(worker_id):
            times = []
            for _ in range(operations):
                data = MarketData(
                    symbol=self.generate_random_symbol(),
                    price=random.uniform(1, 50000),
                    volume=random.uniform(100, 10000),
                    source=f"worker_{worker_id}",
                    exchange="test",
                    timestamp=datetime.now()
                )
                
                start_time = time.perf_counter()
                self.dal.insert_market_data(data)
                elapsed = (time.perf_counter() - start_time) * 1000
                times.append(elapsed)
            
            return times
        
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(workers)]
            all_times = []
            for future in concurrent.futures.as_completed(futures):
                all_times.extend(future.result())
        
        total_time = time.perf_counter() - start_time
        total_operations = workers * operations
        throughput = total_operations / total_time
        
        avg_time = statistics.mean(all_times)
        p95_time = statistics.quantile(all_times, 0.95)
        
        self.results['concurrent'] = {
            'workers': workers,
            'operations_per_worker': operations,
            'total_operations': total_operations,
            'total_time_sec': round(total_time, 2),
            'throughput_per_sec': round(throughput, 2),
            'avg_operation_ms': round(avg_time, 2),
            'p95_operation_ms': round(p95_time, 2)
        }
        
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} ops/sec")
        print(f"  Average operation: {avg_time:.2f}ms")
        print(f"  P95 operation: {p95_time:.2f}ms")
    
    def test_redis_performance(self, iterations: int = 1000):
        """Test Redis cache performance"""
        print(f"\n Testing Redis performance ({iterations} iterations)...")
        
        # Test set operations
        set_times = []
        for i in range(iterations):
            key = f"perf_test_{i}"
            value = {"data": f"value_{i}", "timestamp": datetime.now().isoformat()}
            
            start_time = time.perf_counter()
            self.redis.set_cache(key, value, ttl=60)
            elapsed = (time.perf_counter() - start_time) * 1000
            set_times.append(elapsed)
        
        # Test get operations
        get_times = []
        for i in range(iterations):
            key = f"perf_test_{i}"
            
            start_time = time.perf_counter()
            self.redis.get_cache(key)
            elapsed = (time.perf_counter() - start_time) * 1000
            get_times.append(elapsed)
        
        # Clean up
        self.redis.delete_cache("perf_test_*")
        
        avg_set = statistics.mean(set_times)
        avg_get = statistics.mean(get_times)
        
        self.results['redis'] = {
            'iterations': iterations,
            'avg_set_ms': round(avg_set, 2),
            'avg_get_ms': round(avg_get, 2),
            'set_throughput_per_sec': round(1000 / avg_set, 2),
            'get_throughput_per_sec': round(1000 / avg_get, 2)
        }
        
        print(f"  Average SET: {avg_set:.2f}ms")
        print(f"  Average GET: {avg_get:.2f}ms")
        print(f"  SET throughput: {1000/avg_set:.2f} ops/sec")
        print(f"  GET throughput: {1000/avg_get:.2f} ops/sec")
        
        # Check if meets requirements
        if avg_set < 1 and avg_get < 1:
            print("  ✓ Meets requirement: < 1ms average")
        else:
            print("  ✗ Does not meet requirement: < 1ms average")
    
    def test_memory_usage(self):
        """Test memory usage"""
        print("\n Testing memory usage...")
        
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate and insert large dataset
        large_data = self.generate_market_data(10000)
        
        for data in large_data[:1000]:  # Insert subset
            self.dal.insert_market_data(data)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        self.results['memory'] = {
            'initial_mb': round(initial_memory, 2),
            'final_mb': round(final_memory, 2),
            'increase_mb': round(memory_increase, 2)
        }
        
        print(f"  Initial memory: {initial_memory:.2f} MB")
        print(f"  Final memory: {final_memory:.2f} MB")
        print(f"  Memory increase: {memory_increase:.2f} MB")
        
        if memory_increase < 100:
            print("  ✓ Memory usage acceptable (< 100MB increase)")
        else:
            print("  ⚠ High memory usage detected")
    
    def generate_report(self):
        """Generate performance test report"""
        print("\n" + "="*60)
        print("PERFORMANCE TEST REPORT")
        print("="*60)
        
        print("\n📊 Test Results Summary:")
        print("-" * 40)
        
        for test_name, results in self.results.items():
            print(f"\n{test_name.upper()}:")
            for key, value in results.items():
                print(f"  {key}: {value}")
        
        print("\n" + "="*60)
        print("PERFORMANCE REQUIREMENTS CHECK")
        print("="*60)
        
        checks = [
            ("Database write latency < 10ms", 
             self.results.get('single_insert', {}).get('avg_ms', float('inf')) < 10),
            ("Query response time < 100ms",
             self.results.get('query', {}).get('avg_ms', float('inf')) < 100),
            ("Redis operation latency < 1ms",
             self.results.get('redis', {}).get('avg_get_ms', float('inf')) < 1),
            ("Support 10,000+ writes/sec",
             self.results.get('batch_insert', {}).get('throughput_per_sec', 0) > 10000),
        ]
        
        for requirement, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {requirement}")
        
        all_passed = all(check[1] for check in checks)
        
        print("\n" + "="*60)
        if all_passed:
            print("✓ ALL PERFORMANCE REQUIREMENTS MET")
        else:
            print("⚠ SOME PERFORMANCE REQUIREMENTS NOT MET")
        print("="*60)
        
        return all_passed

async def main():
    """Run all performance tests"""
    tester = PerformanceTester()
    
    print("="*60)
    print("TIGER SYSTEM PERFORMANCE TESTING")
    print("="*60)
    
    # Run tests
    tester.test_single_insert_performance(iterations=100)
    await tester.test_batch_insert_performance(batch_size=1000, batches=5)
    tester.test_query_performance(iterations=50)
    tester.test_concurrent_operations(workers=10, operations=50)
    tester.test_redis_performance(iterations=500)
    tester.test_memory_usage()
    
    # Generate report
    all_passed = tester.generate_report()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n Test interrupted by user")
        sys.exit(1)