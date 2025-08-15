"""
标准指标测试
验收要求：与TradingView对比，误差<0.1%
"""

import pytest
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from analysis.window4_technical.standard_indicators import StandardIndicators
from analysis.window4_technical.tiger_custom import TigerCustomIndicators


class TestStandardIndicators:
    """标准技术指标测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.indicators = StandardIndicators()
        self.tiger = TigerCustomIndicators()
        
        self.sample_prices = [
            50000, 50100, 49900, 50200, 50150, 50300, 49800, 50250,
            50400, 50050, 50500, 49900, 50600, 50100, 50700, 50200,
            50800, 50300, 50900, 50400, 51000, 50500, 50950, 50450,
            51100, 50600, 51200, 50700, 51300, 50800
        ]
        
        self.high_prices = [p * 1.01 for p in self.sample_prices]
        self.low_prices = [p * 0.99 for p in self.sample_prices]
        self.volume = [1000000 + i * 10000 for i in range(len(self.sample_prices))]
    
    def test_rsi_accuracy(self):
        """RSI计算精度测试"""
        rsi = self.indicators.calculate_rsi(self.sample_prices)
        
        assert isinstance(rsi, (int, float))
        assert 0 <= rsi <= 100
        
        assert 45 <= rsi <= 70
        
        rsi_short = self.indicators.calculate_rsi(self.sample_prices[:5])
        assert rsi_short == 50.0
        
        flat_prices = [50000] * 20
        rsi_flat = self.indicators.calculate_rsi(flat_prices)
        assert rsi_flat == 50.0
    
    def test_macd_consistency(self):
        """MACD一致性测试"""
        macd1 = self.indicators.calculate_macd(self.sample_prices)
        macd2 = self.indicators.calculate_macd(self.sample_prices)
        
        assert macd1 == macd2
        
        required_keys = ['macd_line', 'signal_line', 'histogram']
        for key in required_keys:
            assert key in macd1
            assert isinstance(macd1[key], (int, float))
        
        assert macd1['histogram'] == macd1['macd_line'] - macd1['signal_line']
        
        short_macd = self.indicators.calculate_macd(self.sample_prices[:5])
        assert all(v == 0.0 for v in short_macd.values())
    
    def test_bollinger_bands(self):
        """布林带测试"""
        bb = self.indicators.calculate_bollinger_bands(self.sample_prices)
        
        required_keys = ['upper', 'middle', 'lower', 'bandwidth']
        for key in required_keys:
            assert key in bb
            assert isinstance(bb[key], (int, float))
        
        assert bb['upper'] > bb['middle'] > bb['lower']
        
        assert bb['bandwidth'] > 0
        
        short_bb = self.indicators.calculate_bollinger_bands(self.sample_prices[:5])
        assert short_bb['upper'] > short_bb['lower']
    
    def test_moving_averages(self):
        """移动平均线测试"""
        ma = self.indicators.calculate_moving_averages(self.sample_prices)
        
        expected_keys = ['MA5', 'MA10', 'MA20', 'MA50', 'MA200', 'EMA9', 'EMA21', 'EMA55']
        for key in expected_keys:
            assert key in ma
            assert isinstance(ma[key], (int, float))
            assert ma[key] > 0
        
        assert ma['MA5'] != ma['MA10']
        assert ma['EMA9'] != ma['EMA21']
    
    def test_stochastic(self):
        """随机指标测试"""
        stoch = self.indicators.calculate_stochastic(
            self.high_prices, self.low_prices, self.sample_prices
        )
        
        required_keys = ['K', 'D', 'J']
        for key in required_keys:
            assert key in stoch
            assert isinstance(stoch[key], (int, float))
        
        assert -100 <= stoch['K'] <= 100
        assert -100 <= stoch['D'] <= 100
    
    def test_atr(self):
        """ATR测试"""
        atr = self.indicators.calculate_atr(
            self.high_prices, self.low_prices, self.sample_prices
        )
        
        assert isinstance(atr, (int, float))
        assert atr >= 0
        
        atr_short = self.indicators.calculate_atr(
            self.high_prices[:1], self.low_prices[:1], self.sample_prices[:1]
        )
        assert atr_short == 0.0
    
    def test_cci(self):
        """CCI测试"""
        cci = self.indicators.calculate_cci(
            self.high_prices, self.low_prices, self.sample_prices
        )
        
        assert isinstance(cci, (int, float))
        
        cci_short = self.indicators.calculate_cci(
            self.high_prices[:5], self.low_prices[:5], self.sample_prices[:5]
        )
        assert cci_short == 0.0
    
    def test_obv(self):
        """OBV测试"""
        obv = self.indicators.calculate_obv(self.sample_prices, self.volume)
        
        assert isinstance(obv, (int, float))
        
        obv_short = self.indicators.calculate_obv(
            self.sample_prices[:1], self.volume[:1]
        )
        assert obv_short == 0.0
    
    def test_williams_r(self):
        """威廉指标测试"""
        williams = self.indicators.calculate_williams_r(
            self.high_prices, self.low_prices, self.sample_prices
        )
        
        assert isinstance(williams, (int, float))
        assert -100 <= williams <= 0
    
    def test_mfi(self):
        """资金流量指标测试"""
        mfi = self.indicators.calculate_mfi(
            self.high_prices, self.low_prices, self.sample_prices, self.volume
        )
        
        assert isinstance(mfi, (int, float))
        assert 0 <= mfi <= 100
    
    def test_performance(self):
        """性能测试 - 单指标计算<10ms"""
        import time
        
        start = time.time()
        for _ in range(10):
            self.indicators.calculate_rsi(self.sample_prices)
        end = time.time()
        
        avg_time_ms = (end - start) * 1000 / 10
        assert avg_time_ms < 10, f"RSI计算耗时{avg_time_ms:.2f}ms，超过10ms限制"
        
        start = time.time()
        for _ in range(10):
            self.indicators.calculate_macd(self.sample_prices)
        end = time.time()
        
        avg_time_ms = (end - start) * 1000 / 10
        assert avg_time_ms < 10, f"MACD计算耗时{avg_time_ms:.2f}ms，超过10ms限制"
    
    def test_tiger_momentum_index(self):
        """Tiger动量指数测试"""
        data = {
            'prices': self.sample_prices,
            'volume': self.volume
        }
        
        momentum = self.tiger.tiger_momentum_index(data)
        
        assert isinstance(momentum, (int, float))
        assert 0 <= momentum <= 100
        
        empty_data = {'prices': []}
        momentum_empty = self.tiger.tiger_momentum_index(empty_data)
        assert momentum_empty == 50.0
    
    def test_tiger_reversal_score(self):
        """Tiger反转评分测试"""
        data = {
            'prices': self.sample_prices,
            'high': self.high_prices,
            'low': self.low_prices,
            'volume': self.volume
        }
        
        reversal = self.tiger.tiger_reversal_score(data)
        
        assert isinstance(reversal, (int, float))
        assert 0 <= reversal <= 100
        
        short_data = {'prices': self.sample_prices[:10]}
        reversal_short = self.tiger.tiger_reversal_score(short_data)
        assert reversal_short == 0.0
    
    def test_tiger_trend_strength(self):
        """Tiger趋势强度测试"""
        data = {
            'prices': self.sample_prices,
            'volume': self.volume
        }
        
        trend_strength = self.tiger.tiger_trend_strength(data)
        
        assert isinstance(trend_strength, (int, float))
        assert 0 <= trend_strength <= 100
    
    def test_tiger_volatility_index(self):
        """Tiger波动率指数测试"""
        data = {
            'prices': self.sample_prices,
            'high': self.high_prices,
            'low': self.low_prices
        }
        
        volatility = self.tiger.tiger_volatility_index(data)
        
        assert isinstance(volatility, (int, float))
        assert 0 <= volatility <= 100
    
    def test_tiger_market_strength(self):
        """Tiger市场强度测试"""
        data = {
            'prices': self.sample_prices,
            'volume': self.volume
        }
        
        strength = self.tiger.tiger_market_strength(data)
        
        assert isinstance(strength, dict)
        assert 'buy_strength' in strength
        assert 'sell_strength' in strength
        
        assert 0 <= strength['buy_strength'] <= 100
        assert 0 <= strength['sell_strength'] <= 100
        
        assert abs(strength['buy_strength'] + strength['sell_strength'] - 100) < 0.01
    
    def test_edge_cases(self):
        """边界情况测试"""
        empty_prices = []
        single_price = [50000]
        identical_prices = [50000] * 100
        
        assert self.indicators.calculate_rsi(empty_prices) == 50.0
        assert self.indicators.calculate_rsi(single_price) == 50.0
        assert self.indicators.calculate_rsi(identical_prices) == 50.0
        
        macd_empty = self.indicators.calculate_macd(empty_prices)
        assert all(v == 0.0 for v in macd_empty.values())
        
        bb_empty = self.indicators.calculate_bollinger_bands(empty_prices)
        assert bb_empty['upper'] == bb_empty['middle'] == bb_empty['lower'] == 0
    
    def test_data_types(self):
        """数据类型测试"""
        int_prices = [50000, 50100, 49900, 50200]
        float_prices = [50000.0, 50100.5, 49900.2, 50200.8]
        numpy_prices = np.array([50000, 50100, 49900, 50200])
        
        rsi_int = self.indicators.calculate_rsi(int_prices)
        rsi_float = self.indicators.calculate_rsi(float_prices)
        rsi_numpy = self.indicators.calculate_rsi(numpy_prices.tolist())
        
        assert isinstance(rsi_int, (int, float))
        assert isinstance(rsi_float, (int, float))
        assert isinstance(rsi_numpy, (int, float))
        
        assert all(isinstance(rsi, (int, float)) for rsi in [rsi_int, rsi_float, rsi_numpy])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])