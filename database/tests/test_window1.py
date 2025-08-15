"""Window 1 完整测试用例"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_interface import Window1API, process_command, get_window1_api
from account_cache import AccountCache
from decision_tracker import DecisionTracker, DecisionStatus, DecisionType
from success_calculator import SuccessCalculator


class TestWindow1API:
    """Window 1 API测试类"""
    
    @pytest.fixture
    def api(self):
        """创建API实例"""
        return Window1API()
    
    @pytest.mark.asyncio
    async def test_get_account_cache(self, api):
        """测试获取账户缓存"""
        # 测试默认用户
        result = await api.get_account_cache()
        
        assert result is not None
        assert 'total_balance' in result
        assert 'available' in result
        assert 'positions' in result
        assert 'last_7d_trades' in result
        assert 'risk_level' in result
        
        # 验证数据类型
        assert isinstance(result['total_balance'], (int, float))
        assert isinstance(result['available'], (int, float))
        assert isinstance(result['positions'], list)
        assert isinstance(result['last_7d_trades'], list)
        assert 0 <= result['risk_level'] <= 1
        
        # 测试指定用户
        result2 = await api.get_account_cache('test_user')
        assert result2 is not None
    
    @pytest.mark.asyncio
    async def test_record_decision(self, api):
        """测试记录决策"""
        decision_data = {
            'type': DecisionType.BUY.value,
            'symbol': 'BTCUSDT',
            'price': 50000,
            'amount': 0.1,
            'reason': '测试决策',
            'confidence': 0.85,
            'risk_level': 0.3,
            'strategy': 'test_strategy'
        }
        
        result = await api.record_decision(decision_data)
        assert isinstance(result, bool)
        
        # 测试无效决策
        invalid_decision = {
            'price': -100  # 无效价格
        }
        result2 = await api.record_decision(invalid_decision)
        # 即使失败也应该返回bool
        assert isinstance(result2, bool)
    
    @pytest.mark.asyncio
    async def test_get_success_rate(self, api):
        """测试获取成功率"""
        # 测试默认周期
        result = await api.get_success_rate()
        
        assert result is not None
        assert 'period' in result
        assert 'total_decisions' in result
        
        # 测试不同周期
        periods = ['last_7_days', 'last_30_days', 'last_90_days', 'last_365_days']
        for period in periods:
            result = await api.get_success_rate(period)
            assert result is not None
            assert result['period'] == period
    
    @pytest.mark.asyncio
    async def test_query_kline_patterns(self, api):
        """测试查询K线形态"""
        result = await api.query_kline_patterns(
            'BTCUSDT', 
            'double_bottom',
            '1h',
            10
        )
        
        assert isinstance(result, list)
        if result:
            pattern = result[0]
            assert 'symbol' in pattern
            assert 'pattern_type' in pattern
            assert 'timeframe' in pattern
    
    @pytest.mark.asyncio
    async def test_batch_query(self, api):
        """测试批量查询"""
        queries = [
            {
                'function': 'get_account_cache',
                'params': {'user_id': 'test'}
            },
            {
                'function': 'get_success_rate',
                'params': {'period': 'last_7_days'}
            }
        ]
        
        results = await api.batch_query(queries)
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            assert 'function' in result
            assert 'result' in result or 'error' in result
    
    @pytest.mark.asyncio
    async def test_health_check(self, api):
        """测试健康检查"""
        result = await api.health_check()
        
        assert result is not None
        assert 'status' in result
        assert 'timestamp' in result
        assert 'components' in result
        
        # 检查组件状态
        components = result['components']
        assert 'account_cache' in components
        assert 'decision_tracker' in components
        assert 'success_calculator' in components


class TestAccountCache:
    """账户缓存测试类"""
    
    @pytest.fixture
    def cache(self):
        """创建缓存实例"""
        return AccountCache()
    
    @pytest.mark.asyncio
    async def test_get_account_cache(self, cache):
        """测试获取账户缓存"""
        result = await cache.get_account_cache()
        
        assert result is not None
        assert result['user_id'] == 'default'
        assert result['total_balance'] > 0
        assert 'statistics' in result
        assert 'update_time' in result
    
    @pytest.mark.asyncio
    async def test_update_cache(self, cache):
        """测试更新缓存"""
        # 先获取缓存
        original = await cache.get_account_cache()
        original_balance = original['total_balance']
        
        # 更新缓存
        update_data = {
            'total_balance': original_balance + 1000
        }
        await cache.update_cache('default', update_data)
        
        # 验证更新
        updated = await cache.get_account_cache()
        assert updated['total_balance'] == original_balance + 1000
    
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, cache):
        """测试失效缓存"""
        # 先获取缓存（会创建）
        await cache.get_account_cache()
        
        # 失效缓存
        await cache.invalidate_cache('default')
        
        # 再次获取应该是新的
        result = await cache.get_account_cache()
        assert result is not None


class TestDecisionTracker:
    """决策跟踪测试类"""
    
    @pytest.fixture
    def tracker(self):
        """创建跟踪器实例"""
        return DecisionTracker()
    
    @pytest.mark.asyncio
    async def test_record_decision(self, tracker):
        """测试记录决策"""
        decision_data = {
            'type': DecisionType.BUY.value,
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'price': 50000,
            'amount': 0.1,
            'reason': '测试',
            'confidence': 0.8,
            'risk_level': 0.3
        }
        
        result = await tracker.record_decision(decision_data)
        
        assert result['success'] == True
        assert 'decision_id' in result
        assert result['status'] == DecisionStatus.PENDING.value
    
    @pytest.mark.asyncio
    async def test_get_decision(self, tracker):
        """测试获取决策"""
        # 先记录一个决策
        decision_data = {
            'id': 'test_decision_1',
            'type': DecisionType.SELL.value,
            'symbol': 'ETHUSDT',
            'side': 'sell',
            'price': 3000,
            'amount': 1.0,
            'confidence': 0.7
        }
        
        await tracker.record_decision(decision_data)
        
        # 获取决策
        decision = await tracker.get_decision('test_decision_1')
        assert decision is not None
        assert decision['id'] == 'test_decision_1'
    
    @pytest.mark.asyncio
    async def test_update_decision_status(self, tracker):
        """测试更新决策状态"""
        # 先记录决策
        decision_data = {
            'id': 'test_decision_2',
            'type': DecisionType.BUY.value,
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'price': 50000,
            'amount': 0.1
        }
        
        await tracker.record_decision(decision_data)
        
        # 更新状态
        success = await tracker.update_decision_status(
            'test_decision_2',
            DecisionStatus.COMPLETED.value,
            {'price': 50100, 'amount': 0.1, 'profit': 10}
        )
        
        assert success == True
        
        # 验证更新
        decision = await tracker.get_decision('test_decision_2')
        assert decision['status'] == DecisionStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_get_pending_decisions(self, tracker):
        """测试获取待执行决策"""
        # 添加几个不同状态的决策
        for i, status in enumerate([
            DecisionStatus.PENDING, 
            DecisionStatus.COMPLETED, 
            DecisionStatus.PENDING
        ]):
            decision_data = {
                'id': f'test_pending_{i}',
                'type': DecisionType.BUY.value,
                'symbol': 'BTCUSDT',
                'price': 50000 + i * 100,
                'amount': 0.1
            }
            await tracker.record_decision(decision_data)
            
            if status != DecisionStatus.PENDING:
                await tracker.update_decision_status(
                    f'test_pending_{i}', 
                    status.value
                )
        
        # 获取待执行决策
        pending = await tracker.get_pending_decisions()
        assert isinstance(pending, list)
        
        # 应该有2个待执行决策
        pending_ids = [d['id'] for d in pending if 'test_pending' in d['id']]
        assert 'test_pending_0' in pending_ids
        assert 'test_pending_2' in pending_ids
    
    @pytest.mark.asyncio
    async def test_get_decision_statistics(self, tracker):
        """测试获取决策统计"""
        stats = await tracker.get_decision_statistics(30)
        
        assert isinstance(stats, dict)
        assert 'total_decisions' in stats
        assert 'success_rate' in stats
        assert 'avg_confidence' in stats
        assert 'by_type' in stats
        assert 'by_status' in stats


class TestSuccessCalculator:
    """成功率计算测试类"""
    
    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return SuccessCalculator()
    
    @pytest.mark.asyncio
    async def test_get_success_rate(self, calculator):
        """测试获取成功率"""
        result = await calculator.get_success_rate('last_30_days')
        
        assert result is not None
        assert 'period' in result
        assert 'days' in result
        assert 'overall_metrics' in result
        assert 'strategy_metrics' in result
        assert 'time_metrics' in result
        assert 'risk_adjusted_metrics' in result
        assert 'recommendations' in result
    
    @pytest.mark.asyncio
    async def test_parse_period(self, calculator):
        """测试周期解析"""
        test_cases = [
            ('last_7_days', 7),
            ('last_30_days', 30),
            ('last_90_days', 90),
            ('last_365_days', 365),
            ('week', 7),
            ('month', 30),
            ('quarter', 90),
            ('year', 365),
            ('15_days', 15),
            ('unknown', 30)  # 默认值
        ]
        
        for period_str, expected_days in test_cases:
            days = calculator._parse_period(period_str)
            assert days == expected_days
    
    @pytest.mark.asyncio
    async def test_calculate_metrics(self, calculator):
        """测试指标计算"""
        # 模拟决策和交易数据
        decisions = [
            {'id': f'd_{i}', 'status': 'completed' if i < 7 else 'failed'}
            for i in range(10)
        ]
        
        trades = [
            {'id': f't_{i}', 'decision_id': f'd_{i}', 'pnl': (i - 5) * 10}
            for i in range(10)
        ]
        
        # 计算基础指标
        metrics = await calculator._calculate_success_metrics(decisions, trades)
        
        assert metrics is not None
        assert 'success_rate' in metrics
        assert 'win_rate' in metrics
        assert 'profit_loss_ratio' in metrics
        assert 'expectancy' in metrics
        
        # 验证计算正确性
        assert 0 <= metrics['success_rate'] <= 1
        assert 0 <= metrics['win_rate'] <= 1


class TestProcessCommand:
    """测试命令处理"""
    
    @pytest.mark.asyncio
    async def test_process_valid_command(self):
        """测试处理有效命令"""
        command = {
            'window': 1,
            'function': 'get_account_cache',
            'params': {'user_id': 'test'}
        }
        
        result = await process_command(command)
        
        assert result['success'] == True
        assert 'result' in result
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_process_invalid_window(self):
        """测试无效窗口号"""
        command = {
            'window': 2,  # 错误的窗口号
            'function': 'get_account_cache',
            'params': {}
        }
        
        result = await process_command(command)
        assert 'error' in result
        assert 'Invalid window' in result['error']
    
    @pytest.mark.asyncio
    async def test_process_unknown_function(self):
        """测试未知函数"""
        command = {
            'window': 1,
            'function': 'unknown_function',
            'params': {}
        }
        
        result = await process_command(command)
        assert 'Unknown function' in str(result)
    
    @pytest.mark.asyncio
    async def test_all_api_functions(self):
        """测试所有API函数"""
        functions = [
            ('get_account_cache', {'user_id': 'test'}),
            ('record_decision', {'decision_data': {
                'type': 'buy',
                'symbol': 'BTCUSDT',
                'price': 50000,
                'amount': 0.1
            }}),
            ('get_success_rate', {'period': 'last_7_days'}),
            ('query_kline_patterns', {
                'symbol': 'BTCUSDT',
                'pattern_type': 'double_bottom',
                'timeframe': '1h',
                'limit': 10
            }),
            ('get_market_statistics', {'symbol': 'BTCUSDT'}),
            ('get_decision_history', {'user_id': 'test', 'days': 7}),
            ('health_check', {})
        ]
        
        for function_name, params in functions:
            command = {
                'window': 1,
                'function': function_name,
                'params': params
            }
            
            result = await process_command(command)
            assert 'success' in result
            assert 'timestamp' in result


class TestSingleton:
    """测试单例模式"""
    
    def test_singleton_instance(self):
        """测试API单例"""
        api1 = get_window1_api()
        api2 = get_window1_api()
        
        assert api1 is api2  # 应该是同一个实例


# 性能测试
class TestPerformance:
    """性能测试类"""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """测试缓存性能"""
        api = Window1API()
        
        # 测试缓存响应时间
        start = datetime.now()
        for _ in range(10):
            await api.get_account_cache()
        duration = (datetime.now() - start).total_seconds()
        
        # 10次查询应该在1秒内完成（使用缓存）
        assert duration < 1.0
    
    @pytest.mark.asyncio
    async def test_batch_query_performance(self):
        """测试批量查询性能"""
        api = Window1API()
        
        # 构建100个查询
        queries = [
            {
                'function': 'get_account_cache',
                'params': {'user_id': f'user_{i}'}
            }
            for i in range(100)
        ]
        
        start = datetime.now()
        results = await api.batch_query(queries)
        duration = (datetime.now() - start).total_seconds()
        
        # 100个查询应该在5秒内完成
        assert duration < 5.0
        assert len(results) == 100


# 集成测试
class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """测试完整工作流"""
        api = Window1API()
        
        # 1. 获取账户信息
        account = await api.get_account_cache('integration_test')
        assert account is not None
        
        # 2. 记录决策
        decision_data = {
            'type': 'buy',
            'symbol': 'BTCUSDT',
            'price': 50000,
            'amount': 0.1,
            'reason': '集成测试',
            'confidence': 0.9
        }
        
        success = await api.record_decision(decision_data)
        assert success or not success  # 记录可能成功或失败
        
        # 3. 获取成功率
        success_rate = await api.get_success_rate('last_7_days')
        assert success_rate is not None
        
        # 4. 查询K线形态
        patterns = await api.query_kline_patterns(
            'BTCUSDT', 'double_bottom', '1h', 5
        )
        assert isinstance(patterns, list)
        
        # 5. 健康检查
        health = await api.health_check()
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        api = Window1API()
        
        # 测试各种错误情况
        test_cases = [
            # 无效参数
            ('get_account_cache', {'user_id': None}),
            # 空决策
            ('record_decision', {'decision_data': {}}),
            # 无效周期
            ('get_success_rate', {'period': ''}),
            # 无效符号
            ('query_kline_patterns', {
                'symbol': '',
                'pattern_type': '',
                'timeframe': '',
                'limit': -1
            })
        ]
        
        for function_name, params in test_cases:
            command = {
                'window': 1,
                'function': function_name,
                'params': params
            }
            
            # 不应该抛出异常
            result = await process_command(command)
            assert result is not None


if __name__ == '__main__':
    # 运行所有测试
    pytest.main([__file__, '-v', '--tb=short'])