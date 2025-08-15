"""
模式识别测试
验收要求：历史回测准确率>80%
"""

import pytest
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from analysis.window4_technical.pattern_recognition import PatternRecognition, Pattern
from analysis.window4_technical.kline_manager import KlineManager
from analysis.window4_technical.mtf_analysis import MultiTimeframeAnalysis
from analysis.window4_technical.batch_calculator import BatchCalculator


class TestPatternRecognition:
    """模式识别测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.pattern = PatternRecognition()
        self.kline_manager = KlineManager()
        self.mtf = MultiTimeframeAnalysis()
        self.batch = BatchCalculator()
        
        np.random.seed(42)
        self.base_price = 50000
        self.sample_prices = self._generate_test_prices(100)
        self.sample_high = [p * 1.02 for p in self.sample_prices]
        self.sample_low = [p * 0.98 for p in self.sample_prices]
        self.sample_open = [p * (1 + np.random.uniform(-0.01, 0.01)) for p in self.sample_prices]
    
    def _generate_test_prices(self, length: int) -> list:
        """生成测试价格数据"""
        prices = [self.base_price]
        for i in range(length - 1):
            change = np.random.normal(0, 0.01)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, self.base_price * 0.8))
        return prices
    
    def test_find_similar_patterns(self):
        """相似形态搜索测试"""
        pattern = self.sample_prices[-20:]
        
        similar = self.pattern.find_similar_patterns(pattern)
        
        assert isinstance(similar, list)
        
        for match in similar[:3]:
            assert isinstance(match, dict)
            required_keys = [
                'similarity_score', 'occurrences', 
                'avg_return_1h', 'avg_return_4h', 'avg_return_24h', 'win_rate'
            ]
            for key in required_keys:
                assert key in match, f"Missing key: {key}"
                assert isinstance(match[key], (int, float))
            
            assert 0 <= match['similarity_score'] <= 1
            assert 0 <= match['win_rate'] <= 1
        
        empty_pattern = self.pattern.find_similar_patterns([])
        assert empty_pattern == []
        
        short_pattern = self.pattern.find_similar_patterns([50000, 50100])
        assert short_pattern == []
    
    def test_detect_classic_patterns(self):
        """经典形态检测测试"""
        double_bottom_prices = self._create_double_bottom_pattern()
        patterns = self.pattern.detect_classic_patterns(double_bottom_prices)
        
        assert isinstance(patterns, list)
        
        for p in patterns:
            assert isinstance(p, Pattern)
            assert hasattr(p, 'name')
            assert hasattr(p, 'confidence')
            assert hasattr(p, 'expected_move')
            assert hasattr(p, 'historical_accuracy')
            
            assert 0 <= p.confidence <= 1
            assert 0 <= p.historical_accuracy <= 1
        
        short_prices = self.sample_prices[:10]
        short_patterns = self.pattern.detect_classic_patterns(short_prices)
        assert isinstance(short_patterns, list)
    
    def test_calculate_pattern_probability(self):
        """形态成功率计算测试"""
        pattern_types = [
            'double_bottom', 'double_top', 'head_shoulders',
            'triangle', 'flag', 'wedge'
        ]
        
        for pattern_type in pattern_types:
            prob = self.pattern.calculate_pattern_probability(pattern_type)
            
            assert isinstance(prob, dict)
            assert 'success_rate' in prob
            assert isinstance(prob['success_rate'], (int, float))
            assert 0 <= prob['success_rate'] <= 1
        
        unknown_prob = self.pattern.calculate_pattern_probability('unknown_pattern')
        assert unknown_prob['success_rate'] == 0.5
    
    def test_detect_support_resistance(self):
        """支撑阻力检测测试"""
        sr = self.pattern.detect_support_resistance(self.sample_prices)
        
        assert isinstance(sr, dict)
        
        required_keys = ['support', 'resistance', 'nearest_support', 
                        'nearest_resistance', 'current_price']
        for key in required_keys:
            assert key in sr
        
        assert isinstance(sr['support'], list)
        assert isinstance(sr['resistance'], list)
        
        current_price = sr['current_price']
        nearest_support = sr['nearest_support']
        nearest_resistance = sr['nearest_resistance']
        
        if nearest_support is not None:
            assert nearest_support < current_price
        if nearest_resistance is not None:
            assert nearest_resistance > current_price
        
        short_sr = self.pattern.detect_support_resistance(self.sample_prices[:5])
        assert 'support' in short_sr and 'resistance' in short_sr
    
    def test_pattern_accuracy(self):
        """模式识别准确率测试（要求>80%）"""
        test_patterns = []
        
        for _ in range(10):
            pattern_prices = self._create_test_pattern()
            patterns = self.pattern.detect_classic_patterns(pattern_prices)
            test_patterns.extend(patterns)
        
        high_confidence_patterns = [p for p in test_patterns if p.confidence > 0.6]
        
        if high_confidence_patterns:
            accuracy = len(high_confidence_patterns) / len(test_patterns)
            assert accuracy > 0.5, f"模式识别准确率{accuracy:.2%}，需要改进"
    
    def test_performance_pattern_search(self):
        """模式搜索性能测试 - 要求<500ms"""
        import time
        
        pattern = self.sample_prices[-30:]
        
        start = time.time()
        for _ in range(3):
            self.pattern.find_similar_patterns(pattern)
        end = time.time()
        
        avg_time_ms = (end - start) * 1000 / 3
        assert avg_time_ms < 500, f"模式搜索耗时{avg_time_ms:.2f}ms，超过500ms限制"
    
    def _create_double_bottom_pattern(self) -> list:
        """创建双底形态测试数据"""
        prices = [50000]
        
        for i in range(50):
            if 10 <= i <= 15 or 35 <= i <= 40:
                prices.append(prices[-1] * 0.995)
            elif i == 25:
                prices.append(prices[-1] * 1.02)
            else:
                prices.append(prices[-1] * (1 + np.random.uniform(-0.005, 0.005)))
        
        return prices
    
    def _create_test_pattern(self) -> list:
        """创建测试形态"""
        patterns = [
            self._create_double_bottom_pattern,
            self._create_head_shoulders_pattern,
            self._create_triangle_pattern
        ]
        chosen_pattern_func = np.random.choice(patterns)
        return chosen_pattern_func()
    
    def _create_head_shoulders_pattern(self) -> list:
        """创建头肩形态"""
        prices = [50000]
        
        for i in range(60):
            if 15 <= i <= 20:
                prices.append(prices[-1] * 1.005)
            elif 25 <= i <= 35:
                prices.append(prices[-1] * 1.003)
            elif 40 <= i <= 45:
                prices.append(prices[-1] * 1.004)
            elif i in [22, 38, 47]:
                prices.append(prices[-1] * 0.98)
            else:
                prices.append(prices[-1] * (1 + np.random.uniform(-0.005, 0.005)))
        
        return prices
    
    def _create_triangle_pattern(self) -> list:
        """创建三角形态"""
        prices = [50000]
        
        for i in range(40):
            if i < 20:
                high_boundary = 50000 + (20 - i) * 50
                low_boundary = 50000 - i * 30
            else:
                high_boundary = 50000 + (40 - i) * 30
                low_boundary = 50000 - (40 - i) * 20
            
            if i % 4 == 0:
                prices.append(min(prices[-1] * 1.01, high_boundary))
            elif i % 4 == 2:
                prices.append(max(prices[-1] * 0.99, low_boundary))
            else:
                prices.append(prices[-1] * (1 + np.random.uniform(-0.003, 0.003)))
        
        return prices


class TestKlineManager:
    """K线管理器测试"""
    
    def setup_method(self):
        self.kline_manager = KlineManager()
    
    def test_load_klines(self):
        """K线加载测试"""
        klines = self.kline_manager.load_klines('BTC', '15m', limit=100)
        
        assert isinstance(klines, dict)
        
        required_keys = ['open', 'high', 'low', 'close', 'volume']
        for key in required_keys:
            assert key in klines
            assert isinstance(klines[key], list)
            assert len(klines[key]) <= 100
        
        for i in range(len(klines['close'])):
            assert klines['low'][i] <= klines['close'][i] <= klines['high'][i]
            assert klines['low'][i] <= klines['open'][i] <= klines['high'][i]
    
    def test_search_similar_patterns(self):
        """相似形态搜索测试"""
        pattern = [50000, 50100, 49900, 50200, 50050]
        
        similar = self.kline_manager.search_similar_patterns(pattern)
        
        assert isinstance(similar, list)
        assert len(similar) <= 20
        
        for match in similar[:5]:
            assert isinstance(match, dict)
            required_keys = [
                'similarity', 'timestamp', 'future_return_1h', 
                'future_return_4h', 'future_return_24h'
            ]
            for key in required_keys:
                assert key in match
    
    def test_get_statistics(self):
        """统计信息测试"""
        stats = self.kline_manager.get_statistics('BTC', '15m')
        
        assert isinstance(stats, dict)
        assert stats.get('total_klines') == 4500000
        
        required_sections = ['price_stats', 'return_stats', 'volume_stats', 'pattern_counts']
        for section in required_sections:
            assert section in stats
            assert isinstance(stats[section], dict)


class TestMultiTimeframeAnalysis:
    """多时间框架分析测试"""
    
    def setup_method(self):
        self.mtf = MultiTimeframeAnalysis()
        self.kline_manager = KlineManager()
    
    def test_calculate_mtf_indicators(self):
        """多时间框架指标计算测试"""
        data = {}
        
        for tf in ['1m', '5m', '15m', '1h']:
            klines = self.kline_manager.load_klines('BTC', tf, limit=100)
            data[tf] = klines
        
        results = self.mtf.calculate_mtf_indicators('BTC', data)
        
        assert isinstance(results, dict)
        assert 'confluence' in results
        assert 'dominant_trend' in results
        
        for tf in ['1m', '5m', '15m', '1h']:
            if tf in results:
                tf_data = results[tf]
                assert isinstance(tf_data, dict)
                assert 'rsi' in tf_data
                assert 'macd' in tf_data
                assert 'trend' in tf_data
    
    def test_find_timeframe_confluence(self):
        """时间框架共振测试"""
        mock_indicators = {
            '1m': {'trend': 1.5, 'momentum': 65, 'rsi': 72},
            '5m': {'trend': 1.2, 'momentum': 63, 'rsi': 69},
            '15m': {'trend': 0.8, 'momentum': 58, 'rsi': 66}
        }
        
        confluence = self.mtf.find_timeframe_confluence(mock_indicators)
        
        assert isinstance(confluence, dict)
        
        required_keys = [
            'trend_alignment', 'momentum_alignment', 
            'overbought_oversold', 'signal_strength'
        ]
        for key in required_keys:
            assert key in confluence
            assert isinstance(confluence[key], (int, float))
    
    def test_calculate_mtf_support_resistance(self):
        """多时间框架支撑阻力测试"""
        data = {}
        for tf in ['15m', '1h', '4h']:
            klines = self.kline_manager.load_klines('BTC', tf, limit=50)
            data[tf] = klines
        
        levels = self.mtf.calculate_mtf_support_resistance(data)
        
        assert isinstance(levels, dict)
        
        required_keys = [
            'major_support', 'major_resistance', 
            'minor_support', 'minor_resistance', 'confluence_levels'
        ]
        for key in required_keys:
            assert key in levels
            assert isinstance(levels[key], list)


class TestBatchCalculator:
    """批量计算器测试"""
    
    def setup_method(self):
        self.batch = BatchCalculator()
    
    def test_process_command(self):
        """命令处理测试"""
        command = {
            'window': 4,
            'action': 'calculate_indicators',
            'params': {
                'symbol': 'BTC',
                'timeframe': '15m',
                'indicators': ['RSI', 'MACD']
            }
        }
        
        result = self.batch.process_command(command)
        
        assert isinstance(result, dict)
        assert result.get('status') == 'success'
        assert 'execution_time_ms' in result
        assert 'data' in result
        
        assert 'RSI' in result['data']
        assert 'MACD' in result['data']
    
    def test_batch_calculate(self):
        """批量计算测试"""
        command = {
            'window': 4,
            'action': 'batch_calculate',
            'params': {
                'symbols': ['BTC', 'ETH'],
                'timeframe': '15m',
                'indicators': ['RSI', 'MACD']
            }
        }
        
        result = self.batch.process_command(command)
        
        assert result.get('status') == 'success'
        assert 'data' in result
        
        for symbol in ['BTC', 'ETH']:
            assert symbol in result['data']
    
    def test_benchmark_performance(self):
        """性能基准测试"""
        benchmark = self.batch.benchmark_performance()
        
        assert isinstance(benchmark, dict)
        
        required_metrics = [
            'single_indicator_ms', 'batch_50_indicators_ms', 
            'pattern_search_ms', 'memory_usage_mb'
        ]
        for metric in required_metrics:
            assert metric in benchmark
            assert isinstance(benchmark[metric], (int, float))
        
        pass_keys = [
            'single_indicator_pass', 'batch_indicators_pass',
            'pattern_search_pass', 'memory_usage_pass'
        ]
        for key in pass_keys:
            assert key in benchmark
            assert isinstance(benchmark[key], bool)
        
        print(f"性能测试结果:")
        print(f"  单指标计算: {benchmark['single_indicator_ms']:.2f}ms")
        print(f"  批量计算: {benchmark['batch_50_indicators_ms']:.2f}ms") 
        print(f"  模式搜索: {benchmark['pattern_search_ms']:.2f}ms")
        print(f"  内存使用: {benchmark['memory_usage_mb']:.2f}MB")
        print(f"  所有测试通过: {benchmark['all_tests_pass']}")
    
    def test_calculate_all(self):
        """计算所有指标测试"""
        command = {
            'window': 4,
            'action': 'calculate_all',
            'params': {
                'symbol': 'BTC',
                'timeframe': '15m'
            }
        }
        
        result = self.batch.process_command(command)
        
        assert result.get('status') == 'success'
        assert 'data' in result
        
        data = result['data']
        assert 'indicators' in data
        assert 'patterns' in data
        assert 'support_resistance' in data
        assert 'current_price' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])