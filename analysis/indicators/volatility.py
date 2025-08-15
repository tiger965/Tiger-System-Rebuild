"""
Tiger System - Volatility Indicators Module
Window 4: Technical Analysis Engine
25+ Volatility Indicators Implementation
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional


class VolatilityIndicators:
    """波动率类技术指标实现"""
    
    def __init__(self):
        self.name = "VolatilityIndicators"
    
    # ============= Bollinger Bands Series =============
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """布林带 Bollinger Bands"""
        middle = data.rolling(period).mean()
        std = data.rolling(period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': upper - lower,
            'percent_b': (data - lower) / (upper - lower)
        })
    
    @staticmethod
    def bb_width(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.Series:
        """布林带宽度 Bollinger Band Width"""
        bb = VolatilityIndicators.bollinger_bands(data, period, std_dev)
        return bb['bandwidth'] / bb['middle']
    
    @staticmethod
    def bb_percent_b(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.Series:
        """布林带%B指标 Bollinger Band %B"""
        bb = VolatilityIndicators.bollinger_bands(data, period, std_dev)
        return bb['percent_b']
    
    @staticmethod
    def double_bollinger_bands(data: pd.Series, period: int = 20, 
                              inner_std: float = 1.0, outer_std: float = 2.0) -> pd.DataFrame:
        """双布林带 Double Bollinger Bands"""
        middle = data.rolling(period).mean()
        std = data.rolling(period).std()
        
        return pd.DataFrame({
            'outer_upper': middle + (outer_std * std),
            'inner_upper': middle + (inner_std * std),
            'middle': middle,
            'inner_lower': middle - (inner_std * std),
            'outer_lower': middle - (outer_std * std)
        })
    
    # ============= ATR Series =============
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """真实波幅 Average True Range"""
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        
        true_range = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def natr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """标准化ATR Normalized ATR"""
        atr_value = VolatilityIndicators.atr(high, low, close, period)
        natr = (atr_value / close) * 100
        return natr
    
    @staticmethod
    def atr_bands(high: pd.Series, low: pd.Series, close: pd.Series, 
                  period: int = 14, multiplier: float = 2.0) -> pd.DataFrame:
        """ATR带 ATR Bands"""
        atr_value = VolatilityIndicators.atr(high, low, close, period)
        middle = close.ewm(span=period, adjust=False).mean()
        
        return pd.DataFrame({
            'upper': middle + (multiplier * atr_value),
            'middle': middle,
            'lower': middle - (multiplier * atr_value)
        })
    
    @staticmethod
    def atr_trailing_stop(high: pd.Series, low: pd.Series, close: pd.Series, 
                         period: int = 14, multiplier: float = 3.0) -> pd.Series:
        """ATR跟踪止损 ATR Trailing Stop"""
        atr_value = VolatilityIndicators.atr(high, low, close, period)
        
        trailing_stop = pd.Series(index=close.index, dtype='float64')
        direction = pd.Series(index=close.index, dtype='int')
        
        # 初始化
        trailing_stop.iloc[period] = close.iloc[period] - multiplier * atr_value.iloc[period]
        direction.iloc[period] = 1
        
        for i in range(period + 1, len(close)):
            if direction.iloc[i-1] == 1:  # 多头
                stop = close.iloc[i] - multiplier * atr_value.iloc[i]
                if stop > trailing_stop.iloc[i-1]:
                    trailing_stop.iloc[i] = stop
                else:
                    trailing_stop.iloc[i] = trailing_stop.iloc[i-1]
                
                if close.iloc[i] <= trailing_stop.iloc[i]:
                    direction.iloc[i] = -1
                else:
                    direction.iloc[i] = 1
            else:  # 空头
                stop = close.iloc[i] + multiplier * atr_value.iloc[i]
                if stop < trailing_stop.iloc[i-1]:
                    trailing_stop.iloc[i] = stop
                else:
                    trailing_stop.iloc[i] = trailing_stop.iloc[i-1]
                
                if close.iloc[i] >= trailing_stop.iloc[i]:
                    direction.iloc[i] = 1
                else:
                    direction.iloc[i] = -1
        
        return trailing_stop
    
    # ============= Other Volatility Indicators =============
    
    @staticmethod
    def historical_volatility(close: pd.Series, period: int = 20, annualize: bool = True) -> pd.Series:
        """历史波动率 Historical Volatility"""
        log_returns = np.log(close / close.shift(1))
        volatility = log_returns.rolling(period).std()
        
        if annualize:
            # 假设一年365天交易（加密货币）
            volatility = volatility * np.sqrt(365)
        
        return volatility * 100  # 转换为百分比
    
    @staticmethod
    def chaikin_volatility(high: pd.Series, low: pd.Series, period: int = 10) -> pd.Series:
        """蔡金波动率 Chaikin Volatility"""
        hl_spread = high - low
        ema = hl_spread.ewm(span=period, adjust=False).mean()
        
        chaikin_vol = ((ema - ema.shift(period)) / ema.shift(period)) * 100
        return chaikin_vol
    
    @staticmethod
    def standard_deviation(data: pd.Series, period: int = 20) -> pd.Series:
        """标准差 Standard Deviation"""
        return data.rolling(period).std()
    
    @staticmethod
    def variance(data: pd.Series, period: int = 20) -> pd.Series:
        """方差 Variance"""
        return data.rolling(period).var()
    
    @staticmethod
    def z_score(data: pd.Series, period: int = 20) -> pd.Series:
        """Z分数 Z-Score"""
        mean = data.rolling(period).mean()
        std = data.rolling(period).std()
        z_score = (data - mean) / std
        return z_score
    
    @staticmethod
    def volatility_ratio(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """波动率比率 Volatility Ratio"""
        true_range = pd.DataFrame()
        true_range['h-l'] = high - low
        true_range['h-pc'] = abs(high - close.shift(1))
        true_range['l-pc'] = abs(low - close.shift(1))
        tr = true_range[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        
        atr = tr.ewm(span=period, adjust=False).mean()
        vr = tr / atr
        
        return vr
    
    @staticmethod
    def ulcer_index(close: pd.Series, period: int = 14) -> pd.Series:
        """溃疡指数 Ulcer Index"""
        max_close = close.rolling(period).max()
        drawdown = ((close - max_close) / max_close) * 100
        squared_dd = drawdown ** 2
        ulcer = np.sqrt(squared_dd.rolling(period).mean())
        
        return ulcer
    
    @staticmethod
    def relative_volatility_index(close: pd.Series, period: int = 14) -> pd.Series:
        """相对波动率指数 Relative Volatility Index"""
        std = close.rolling(period).std()
        
        up_std = pd.Series(index=close.index, dtype='float64')
        down_std = pd.Series(index=close.index, dtype='float64')
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                up_std.iloc[i] = std.iloc[i]
                down_std.iloc[i] = 0
            else:
                up_std.iloc[i] = 0
                down_std.iloc[i] = std.iloc[i]
        
        avg_up = up_std.ewm(span=period, adjust=False).mean()
        avg_down = down_std.ewm(span=period, adjust=False).mean()
        
        rvi = 100 * (avg_up / (avg_up + avg_down))
        return rvi
    
    @staticmethod
    def volatility_system(high: pd.Series, low: pd.Series, close: pd.Series, 
                         atr_period: int = 7, constant: float = 3.0) -> pd.DataFrame:
        """波动率系统 Volatility System"""
        atr = VolatilityIndicators.atr(high, low, close, atr_period)
        avg_close = close.rolling(atr_period).mean()
        
        long_stop = avg_close - constant * atr
        short_stop = avg_close + constant * atr
        
        return pd.DataFrame({
            'long_stop': long_stop,
            'short_stop': short_stop,
            'avg_close': avg_close
        })
    
    @staticmethod
    def garch_volatility(returns: pd.Series, p: int = 1, q: int = 1) -> pd.Series:
        """GARCH波动率 (简化版)"""
        # 这是一个简化的GARCH(1,1)实现
        omega = 0.00001
        alpha = 0.1
        beta = 0.85
        
        volatility = pd.Series(index=returns.index, dtype='float64')
        volatility.iloc[0] = returns.std()
        
        for i in range(1, len(returns)):
            volatility.iloc[i] = np.sqrt(
                omega + 
                alpha * returns.iloc[i-1]**2 + 
                beta * volatility.iloc[i-1]**2
            )
        
        return volatility
    
    @staticmethod
    def garman_klass_volatility(open_price: pd.Series, high: pd.Series, 
                               low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Garman-Klass波动率"""
        log_hl = np.log(high / low)
        log_co = np.log(close / open_price)
        
        gk = np.sqrt(
            0.5 * log_hl**2 - 
            (2 * np.log(2) - 1) * log_co**2
        )
        
        return gk.rolling(period).mean() * np.sqrt(365) * 100
    
    @staticmethod
    def parkinson_volatility(high: pd.Series, low: pd.Series, period: int = 20) -> pd.Series:
        """Parkinson波动率"""
        log_hl = np.log(high / low)
        parkinson = log_hl / (2 * np.sqrt(np.log(2)))
        
        return parkinson.rolling(period).mean() * np.sqrt(365) * 100
    
    @staticmethod
    def rogers_satchell_volatility(open_price: pd.Series, high: pd.Series, 
                                  low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Rogers-Satchell波动率"""
        log_ho = np.log(high / open_price)
        log_hc = np.log(high / close)
        log_lo = np.log(low / open_price)
        log_lc = np.log(low / close)
        
        rs = np.sqrt(log_ho * log_hc + log_lo * log_lc)
        
        return rs.rolling(period).mean() * np.sqrt(365) * 100
    
    @staticmethod
    def yang_zhang_volatility(open_price: pd.Series, high: pd.Series, 
                             low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Yang-Zhang波动率"""
        log_ho = np.log(high / open_price)
        log_lo = np.log(low / open_price)
        log_co = np.log(close / open_price)
        
        log_oc = np.log(open_price / close.shift(1))
        log_cc = np.log(close / close.shift(1))
        
        rogers_satchell = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
        
        k = 0.34 / (1.34 + (period + 1) / (period - 1))
        
        overnight = log_oc.rolling(period).var()
        open_close = log_co.rolling(period).var()
        rs = rogers_satchell.rolling(period).mean()
        
        yz = np.sqrt(overnight + k * open_close + (1 - k) * rs) * np.sqrt(365) * 100
        
        return yz


def calculate_all_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有波动率指标"""
    indicators = VolatilityIndicators()
    result = df.copy()
    
    # 布林带系列
    bb = indicators.bollinger_bands(df['close'])
    result['BB_Upper'] = bb['upper']
    result['BB_Middle'] = bb['middle']
    result['BB_Lower'] = bb['lower']
    result['BB_Width'] = indicators.bb_width(df['close'])
    result['BB_PercentB'] = indicators.bb_percent_b(df['close'])
    
    double_bb = indicators.double_bollinger_bands(df['close'])
    result['DBB_Outer_Upper'] = double_bb['outer_upper']
    result['DBB_Inner_Upper'] = double_bb['inner_upper']
    result['DBB_Inner_Lower'] = double_bb['inner_lower']
    result['DBB_Outer_Lower'] = double_bb['outer_lower']
    
    # ATR系列
    result['ATR'] = indicators.atr(df['high'], df['low'], df['close'])
    result['NATR'] = indicators.natr(df['high'], df['low'], df['close'])
    
    atr_bands = indicators.atr_bands(df['high'], df['low'], df['close'])
    result['ATR_Upper'] = atr_bands['upper']
    result['ATR_Lower'] = atr_bands['lower']
    
    result['ATR_Stop'] = indicators.atr_trailing_stop(df['high'], df['low'], df['close'])
    
    # 其他波动率指标
    result['Historical_Vol'] = indicators.historical_volatility(df['close'])
    result['Chaikin_Vol'] = indicators.chaikin_volatility(df['high'], df['low'])
    result['StdDev'] = indicators.standard_deviation(df['close'])
    result['Variance'] = indicators.variance(df['close'])
    result['Z_Score'] = indicators.z_score(df['close'])
    result['Vol_Ratio'] = indicators.volatility_ratio(df['high'], df['low'], df['close'])
    result['Ulcer_Index'] = indicators.ulcer_index(df['close'])
    result['RVI'] = indicators.relative_volatility_index(df['close'])
    
    if 'open' in df.columns:
        result['GK_Vol'] = indicators.garman_klass_volatility(df['open'], df['high'], df['low'], df['close'])
        result['RS_Vol'] = indicators.rogers_satchell_volatility(df['open'], df['high'], df['low'], df['close'])
        result['YZ_Vol'] = indicators.yang_zhang_volatility(df['open'], df['high'], df['low'], df['close'])
    
    result['Parkinson_Vol'] = indicators.parkinson_volatility(df['high'], df['low'])
    
    return result