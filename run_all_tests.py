#!/usr/bin/env python3
"""
Complete system test and validation for Window 1 - Database Infrastructure
This script verifies all components are working correctly
"""

import sys
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test modules
from tests.test_database import TestDatabaseConnection, TestRedisOperations
from tests.test_performance import PerformanceTester
from database.init_database import DatabaseInitializer
from core.dal import get_dal
from core.redis_manager import RedisManager
from core.interfaces import MarketData, Signal, SignalType, TimeHorizon

class SystemValidator:
    """Complete system validation"""
    
    def __init__(self):
        self.results = {}
        self.dal = None
        self.redis = None
        self.errors = []
        self.warnings = []
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_status(self, component: str, status: bool, message: str = ""):
        """Print component status"""
        icon = "✓" if status else "✗"
        status_text = "PASS" if status else "FAIL"
        print(f"  [{icon}] {component}: {status_text} {message}")
    
    def validate_prerequisites(self) -> bool:
        """Validate system prerequisites"""
        self.print_header("VALIDATING PREREQUISITES")
        
        all_pass = True
        
        # Check Python version
        import sys
        python_version = sys.version_info
        python_ok = python_version.major == 3 and python_version.minor >= 10
        self.print_status("Python 3.10+", python_ok, f"(Found {python_version.major}.{python_version.minor})")
        all_pass &= python_ok
        
        # Check PostgreSQL
        try:
            import psycopg2
            self.print_status("PostgreSQL driver", True, "(psycopg2 installed)")
        except ImportError:
            self.print_status("PostgreSQL driver", False, "(psycopg2 not found)")
            all_pass = False
        
        # Check Redis
        try:
            import redis
            self.print_status("Redis driver", True, "(redis-py installed)")
        except ImportError:
            self.print_status("Redis driver", False, "(redis-py not found)")
            all_pass = False
        
        # Check required packages
        required_packages = ['sqlalchemy', 'asyncpg', 'pyyaml', 'pydantic']
        for package in required_packages:
            try:
                __import__(package)
                self.print_status(f"Package {package}", True)
            except ImportError:
                self.print_status(f"Package {package}", False)
                all_pass = False
        
        self.results['prerequisites'] = all_pass
        return all_pass
    
    def validate_database(self) -> bool:
        """Validate database setup"""
        self.print_header("VALIDATING DATABASE")
        
        all_pass = True
        
        try:
            # Initialize database
            initializer = DatabaseInitializer()
            
            # Check database exists
            db_exists = initializer.create_database()
            self.print_status("Database exists", db_exists)
            all_pass &= db_exists
            
            # Verify tables
            tables_ok = initializer.verify_tables()
            self.print_status("All tables created", tables_ok)
            all_pass &= tables_ok
            
            # Test connection
            conn_ok = initializer.test_connection()
            self.print_status("Database connection", conn_ok)
            all_pass &= conn_ok
            
        except Exception as e:
            self.print_status("Database validation", False, f"Error: {e}")
            self.errors.append(f"Database error: {e}")
            all_pass = False
        
        self.results['database'] = all_pass
        return all_pass
    
    def validate_redis(self) -> bool:
        """Validate Redis setup"""
        self.print_header("VALIDATING REDIS")
        
        all_pass = True
        
        try:
            self.redis = RedisManager()
            
            # Check health
            health = self.redis.health_check()
            redis_healthy = health.get('status') == 'healthy'
            self.print_status("Redis connection", redis_healthy)
            all_pass &= redis_healthy
            
            # Test cache operations
            test_key = "validation_test"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Set
            set_ok = self.redis.set_cache(test_key, test_value, ttl=10)
            self.print_status("Cache SET operation", set_ok)
            all_pass &= set_ok
            
            # Get
            retrieved = self.redis.get_cache(test_key)
            get_ok = retrieved is not None
            self.print_status("Cache GET operation", get_ok)
            all_pass &= get_ok
            
            # Pub/Sub
            pub_ok = self.redis.publish('test_channel', {"test": "message"})
            self.print_status("Pub/Sub operation", pub_ok)
            all_pass &= pub_ok
            
            # Clean up
            self.redis.delete_cache(test_key)
            
        except Exception as e:
            self.print_status("Redis validation", False, f"Error: {e}")
            self.errors.append(f"Redis error: {e}")
            all_pass = False
        
        self.results['redis'] = all_pass
        return all_pass
    
    def validate_dal(self) -> bool:
        """Validate Data Access Layer"""
        self.print_header("VALIDATING DATA ACCESS LAYER")
        
        all_pass = True
        
        try:
            self.dal = get_dal()
            
            # Test market data operations
            test_data = MarketData(
                symbol="TEST/USDT",
                price=100.0,
                volume=1000.0,
                source="validation",
                exchange="test"
            )
            
            insert_ok = self.dal.insert_market_data(test_data)
            self.print_status("DAL insert operation", insert_ok)
            all_pass &= insert_ok
            
            # Test query
            results = self.dal.get_latest_market_data("TEST/USDT", limit=1)
            query_ok = len(results) > 0
            self.print_status("DAL query operation", query_ok)
            all_pass &= query_ok
            
            # Test signal operations
            test_signal = Signal(
                signal_type=SignalType.BUY,
                symbol="TEST/USDT",
                confidence=0.95,
                trigger_reason="Validation test",
                source="validator"
            )
            
            signal_id = self.dal.insert_signal(test_signal)
            signal_ok = signal_id is not None
            self.print_status("Signal operations", signal_ok)
            all_pass &= signal_ok
            
            # Test logging
            self.dal.log(1, "info", "validator", "System validation test")
            self.print_status("System logging", True)
            
        except Exception as e:
            self.print_status("DAL validation", False, f"Error: {e}")
            self.errors.append(f"DAL error: {e}")
            all_pass = False
        
        self.results['dal'] = all_pass
        return all_pass
    
    async def validate_performance(self) -> bool:
        """Validate performance requirements"""
        self.print_header("VALIDATING PERFORMANCE")
        
        all_pass = True
        
        try:
            tester = PerformanceTester()
            
            # Quick performance tests
            print("  Running performance tests (this may take a moment)...")
            
            # Test write latency
            tester.test_single_insert_performance(iterations=50)
            write_latency = tester.results.get('single_insert', {}).get('avg_ms', float('inf'))
            write_ok = write_latency < 10
            self.print_status("Write latency < 10ms", write_ok, f"({write_latency:.2f}ms)")
            all_pass &= write_ok
            
            # Test query latency
            tester.test_query_performance(iterations=20)
            query_latency = tester.results.get('query', {}).get('avg_ms', float('inf'))
            query_ok = query_latency < 100
            self.print_status("Query latency < 100ms", query_ok, f"({query_latency:.2f}ms)")
            all_pass &= query_ok
            
            # Test Redis latency
            tester.test_redis_performance(iterations=100)
            redis_latency = tester.results.get('redis', {}).get('avg_get_ms', float('inf'))
            redis_ok = redis_latency < 1
            self.print_status("Redis latency < 1ms", redis_ok, f"({redis_latency:.2f}ms)")
            all_pass &= redis_ok
            
            # Test throughput
            await tester.test_batch_insert_performance(batch_size=1000, batches=2)
            throughput = tester.results.get('batch_insert', {}).get('throughput_per_sec', 0)
            throughput_ok = throughput > 10000
            self.print_status("Throughput > 10,000/sec", throughput_ok, f"({throughput:.0f}/sec)")
            all_pass &= throughput_ok
            
        except Exception as e:
            self.print_status("Performance validation", False, f"Error: {e}")
            self.errors.append(f"Performance error: {e}")
            all_pass = False
        
        self.results['performance'] = all_pass
        return all_pass
    
    def validate_configuration(self) -> bool:
        """Validate configuration files"""
        self.print_header("VALIDATING CONFIGURATION")
        
        all_pass = True
        config_files = [
            'config/database.yaml',
            'config/redis.yaml',
            'config/system.yaml'
        ]
        
        for config_file in config_files:
            exists = os.path.exists(config_file)
            self.print_status(f"Config {config_file}", exists)
            all_pass &= exists
        
        self.results['configuration'] = all_pass
        return all_pass
    
    def generate_report(self):
        """Generate final validation report"""
        self.print_header("VALIDATION REPORT")
        
        # Summary
        total_tests = len(self.results)
        passed_tests = sum(1 for v in self.results.values() if v)
        
        print(f"\n  Total Components: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {total_tests - passed_tests}")
        
        # Component status
        print("\n  Component Status:")
        for component, status in self.results.items():
            icon = "✓" if status else "✗"
            print(f"    [{icon}] {component.title()}")
        
        # Errors
        if self.errors:
            print("\n  ⚠ Errors Encountered:")
            for error in self.errors:
                print(f"    - {error}")
        
        # Warnings
        if self.warnings:
            print("\n  ⚠ Warnings:")
            for warning in self.warnings:
                print(f"    - {warning}")
        
        # Final status
        all_passed = all(self.results.values())
        
        self.print_header("FINAL STATUS")
        if all_passed:
            print("  ✓ ALL VALIDATIONS PASSED")
            print("  System is ready for use by other windows")
        else:
            print("  ✗ SOME VALIDATIONS FAILED")
            print("  Please fix the issues before proceeding")
        
        return all_passed

async def main():
    """Main validation entry point"""
    print("="*60)
    print(" TIGER SYSTEM - WINDOW 1 VALIDATION")
    print(" Database Infrastructure Complete Test")
    print("="*60)
    print(f" Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    validator = SystemValidator()
    
    # Run validations
    validator.validate_prerequisites()
    validator.validate_database()
    validator.validate_redis()
    validator.validate_dal()
    await validator.validate_performance()
    validator.validate_configuration()
    
    # Generate report
    all_passed = validator.generate_report()
    
    # Completion message
    print("\n" + "="*60)
    print(" WINDOW 1 COMPLETION REPORT")
    print("="*60)
    print(f" Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(" Developer: Window-1 Database Infrastructure")
    print()
    
    if all_passed:
        print(" ✓ Database Infrastructure is FULLY OPERATIONAL")
        print(" ✓ Ready to support all other windows")
        print(" ✓ Performance requirements MET")
        print(" ✓ No critical issues found")
        print()
        print(" STATUS: READY FOR PRODUCTION")
    else:
        print(" ✗ Some components need attention")
        print(" Please review the errors above")
    
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n Critical error: {e}")
        sys.exit(1)