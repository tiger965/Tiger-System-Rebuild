"""
批量计算器
高效处理Window 6的批量计算请求
"""

import numpy as np
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from .standard_indicators import StandardIndicators
from .tiger_custom import TigerCustomIndicators
from .pattern_recognition import PatternRecognition
from .mtf_analysis import MultiTimeframeAnalysis
from .kline_manager import KlineManager


class BatchCalculator:
    """批量计算器 - 为Window 6提供高效计算服务"""
    
    def __init__(self):
        self.standard = StandardIndicators()
        self.tiger = TigerCustomIndicators()
        self.pattern = PatternRecognition()
        self.mtf = MultiTimeframeAnalysis()
        self.kline_manager = KlineManager()
        
        self.max_workers = 4
        
        self.performance_requirements = {
            'single_indicator': 10,
            'batch_indicators': 100,
            'pattern_search': 500,
            'memory_usage': 500
        }
    
    def process_command(self, command: Dict) -> Dict:
        """
        处理Window 6的命令
        
        参数:
            command: Window 6发来的计算命令
        
        返回:
            计算结果（只有数值，没有判断）
        """
        start_time = time.time()
        
        if command.get('window') != 4:
            return {
                'status': 'error',
                'message': 'Wrong window number'
            }
        
        action = command.get('action')
        params = command.get('params', {})
        
        try:
            if action == 'calculate_indicators':
                result = self._calculate_indicators(params)
            elif action == 'batch_calculate':
                result = self._batch_calculate(params)
            elif action == 'find_patterns':
                result = self._find_patterns(params)
            elif action == 'mtf_analysis':
                result = self._mtf_analysis(params)
            elif action == 'search_similar':
                result = self._search_similar(params)
            elif action == 'calculate_all':
                result = self._calculate_all(params)
            else:
                result = {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
            
            execution_time = (time.time() - start_time) * 1000
            
            if 'status' not in result:
                result['status'] = 'success'
            result['execution_time_ms'] = round(execution_time, 2)
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'execution_time_ms': (time.time() - start_time) * 1000
            }
    
    def _calculate_indicators(self, params: Dict) -> Dict:
        """计算指定指标"""
        symbol = params.get('symbol', 'BTC')
        timeframe = params.get('timeframe', '15m')
        indicators = params.get('indicators', [])
        prices = params.get('prices', [])
        
        if not prices:
            klines = self.kline_manager.load_klines(symbol, timeframe)
            prices = klines.get('close', [])
            high = klines.get('high', prices)
            low = klines.get('low', prices)
            volume = klines.get('volume', [])
        else:
            high = params.get('high', prices)
            low = params.get('low', prices)
            volume = params.get('volume', [])
        
        result = {'data': {}}
        
        for indicator in indicators:
            indicator_upper = indicator.upper()
            
            if indicator_upper == 'RSI':
                result['data']['RSI'] = self.standard.calculate_rsi(prices)
                
            elif indicator_upper == 'MACD':
                result['data']['MACD'] = self.standard.calculate_macd(prices)
                
            elif indicator_upper in ['BB', 'BOLLINGER']:
                result['data']['BB'] = self.standard.calculate_bollinger_bands(prices)
                
            elif indicator_upper in ['MA', 'EMA']:
                result['data']['MA'] = self.standard.calculate_moving_averages(prices)
                
            elif indicator_upper in ['STOCH', 'KDJ']:
                result['data']['STOCH'] = self.standard.calculate_stochastic(
                    high, low, prices
                )
                
            elif indicator_upper == 'ATR':
                result['data']['ATR'] = self.standard.calculate_atr(
                    high, low, prices
                )
                
            elif indicator_upper == 'CCI':
                result['data']['CCI'] = self.standard.calculate_cci(
                    high, low, prices
                )
                
            elif indicator_upper == 'OBV':
                result['data']['OBV'] = self.standard.calculate_obv(
                    prices, volume
                )
                
            elif indicator_upper == 'WILLIAMS':
                result['data']['WILLIAMS'] = self.standard.calculate_williams_r(
                    high, low, prices
                )
                
            elif indicator_upper == 'MFI':
                result['data']['MFI'] = self.standard.calculate_mfi(
                    high, low, prices, volume
                )
                
            elif indicator_upper == 'TIGER_MOMENTUM':
                result['data']['TIGER_MOMENTUM'] = self.tiger.tiger_momentum_index({
                    'prices': prices,
                    'volume': volume
                })
                
            elif indicator_upper == 'TIGER_REVERSAL':
                result['data']['TIGER_REVERSAL'] = self.tiger.tiger_reversal_score({
                    'prices': prices,
                    'high': high,
                    'low': low,
                    'volume': volume
                })
                
            elif indicator_upper == 'TIGER_TREND':
                result['data']['TIGER_TREND'] = self.tiger.tiger_trend_strength({
                    'prices': prices,
                    'volume': volume
                })
                
            elif indicator_upper == 'TIGER_VOLATILITY':
                result['data']['TIGER_VOLATILITY'] = self.tiger.tiger_volatility_index({
                    'prices': prices,
                    'high': high,
                    'low': low
                })
                
            elif indicator_upper == 'TIGER_STRENGTH':
                result['data']['TIGER_STRENGTH'] = self.tiger.tiger_market_strength({
                    'prices': prices,
                    'volume': volume
                })
        
        return result
    
    def _batch_calculate(self, params: Dict) -> Dict:
        """批量计算多个交易对的指标"""
        symbols = params.get('symbols', ['BTC'])
        timeframe = params.get('timeframe', '15m')
        indicators = params.get('indicators', ['RSI', 'MACD'])
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for symbol in symbols:
                future = executor.submit(
                    self._calculate_indicators,
                    {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'indicators': indicators
                    }
                )
                futures[future] = symbol
            
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result(timeout=5)
                    results[symbol] = result['data']
                except Exception as e:
                    results[symbol] = {'error': str(e)}
        
        return {'data': results}
    
    def _find_patterns(self, params: Dict) -> Dict:
        """查找K线形态"""
        symbol = params.get('symbol', 'BTC')
        timeframe = params.get('timeframe', '15m')
        prices = params.get('prices', [])
        
        if not prices:
            klines = self.kline_manager.load_klines(symbol, timeframe)
            prices = klines.get('close', [])
            high = klines.get('high', prices)
            low = klines.get('low', prices)
            open_prices = klines.get('open', prices)
        else:
            high = params.get('high', prices)
            low = params.get('low', prices)
            open_prices = params.get('open', prices)
        
        patterns = self.pattern.detect_classic_patterns(
            prices, high, low, open_prices
        )
        
        support_resistance = self.pattern.detect_support_resistance(prices)
        
        pattern_list = []
        for p in patterns:
            pattern_list.append({
                'name': p.name,
                'confidence': p.confidence,
                'expected_move': p.expected_move,
                'historical_accuracy': p.historical_accuracy
            })
        
        return {
            'data': {
                'patterns': pattern_list,
                'support_resistance': support_resistance
            }
        }
    
    def _mtf_analysis(self, params: Dict) -> Dict:
        """多时间框架分析"""
        symbol = params.get('symbol', 'BTC')
        data = params.get('data', {})
        
        if not data:
            data = {}
            for tf in ['1m', '5m', '15m', '1h', '4h', '1d']:
                klines = self.kline_manager.load_klines(symbol, tf, limit=200)
                data[tf] = klines
        
        mtf_results = self.mtf.calculate_mtf_indicators(symbol, data)
        
        return {'data': mtf_results}
    
    def _search_similar(self, params: Dict) -> Dict:
        """搜索相似K线形态"""
        pattern = params.get('pattern', [])
        symbol = params.get('symbol', 'BTC')
        timeframe = params.get('timeframe', '15m')
        
        if not pattern:
            return {'data': {'similar_patterns': []}}
        
        similar = self.kline_manager.search_similar_patterns(
            pattern, symbol, timeframe
        )
        
        statistics = []
        if similar:
            avg_1h = np.mean([s['future_return_1h'] for s in similar])
            avg_4h = np.mean([s['future_return_4h'] for s in similar])
            avg_24h = np.mean([s['future_return_24h'] for s in similar])
            
            statistics = {
                'avg_return_1h': round(avg_1h, 2),
                'avg_return_4h': round(avg_4h, 2),
                'avg_return_24h': round(avg_24h, 2),
                'pattern_count': len(similar),
                'avg_similarity': round(np.mean([s['similarity'] for s in similar]), 3)
            }
        
        return {
            'data': {
                'similar_patterns': similar[:10],
                'statistics': statistics
            }
        }
    
    def _calculate_all(self, params: Dict) -> Dict:
        """计算所有可用指标"""
        symbol = params.get('symbol', 'BTC')
        timeframe = params.get('timeframe', '15m')
        
        klines = self.kline_manager.load_klines(symbol, timeframe)
        prices = klines.get('close', [])
        high = klines.get('high', prices)
        low = klines.get('low', prices)
        volume = klines.get('volume', [])
        open_prices = klines.get('open', prices)
        
        all_indicators = [
            'RSI', 'MACD', 'BB', 'MA', 'STOCH', 'ATR', 'CCI', 
            'OBV', 'WILLIAMS', 'MFI', 'TIGER_MOMENTUM', 
            'TIGER_REVERSAL', 'TIGER_TREND', 'TIGER_VOLATILITY',
            'TIGER_STRENGTH'
        ]
        
        indicators_result = self._calculate_indicators({
            'symbol': symbol,
            'timeframe': timeframe,
            'indicators': all_indicators,
            'prices': prices,
            'high': high,
            'low': low,
            'volume': volume
        })
        
        patterns = self.pattern.detect_classic_patterns(
            prices, high, low, open_prices
        )
        
        pattern_list = []
        for p in patterns:
            pattern_list.append({
                'name': p.name,
                'confidence': p.confidence,
                'expected_move': p.expected_move
            })
        
        support_resistance = self.pattern.detect_support_resistance(prices)
        
        return {
            'data': {
                'indicators': indicators_result['data'],
                'patterns': pattern_list,
                'support_resistance': support_resistance,
                'current_price': prices[-1] if prices else 0
            }
        }
    
    def benchmark_performance(self) -> Dict:
        """性能基准测试"""
        results = {}
        
        test_prices = list(np.random.random(1000) * 100 + 50000)
        
        start = time.time()
        self.standard.calculate_rsi(test_prices)
        single_time = (time.time() - start) * 1000
        results['single_indicator_ms'] = round(single_time, 2)
        results['single_indicator_pass'] = single_time < self.performance_requirements['single_indicator']
        
        start = time.time()
        for _ in range(50):
            self.standard.calculate_rsi(test_prices[:100])
        batch_time = (time.time() - start) * 1000
        results['batch_50_indicators_ms'] = round(batch_time, 2)
        results['batch_indicators_pass'] = batch_time < self.performance_requirements['batch_indicators']
        
        start = time.time()
        self.pattern.find_similar_patterns(test_prices[:50])
        pattern_time = (time.time() - start) * 1000
        results['pattern_search_ms'] = round(pattern_time, 2)
        results['pattern_search_pass'] = pattern_time < self.performance_requirements['pattern_search']
        
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        results['memory_usage_mb'] = round(memory_mb, 2)
        results['memory_usage_pass'] = memory_mb < self.performance_requirements['memory_usage']
        
        results['all_tests_pass'] = all([
            results['single_indicator_pass'],
            results['batch_indicators_pass'],
            results['pattern_search_pass'],
            results['memory_usage_pass']
        ])
        
        return results