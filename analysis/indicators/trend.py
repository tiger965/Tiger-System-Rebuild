"""
Tiger System - Trend Indicators Module
Window 4: Technical Analysis Engine
40+ Trend Indicators Implementation
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional


class TrendIndicators:
    """趋势类技术指标实现"""
    
    def __init__(self):
        self.name = "TrendIndicators"
    
    # ============= Moving Averages =============
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """简单移动平均线 Simple Moving Average"""
        return data.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """指数移动平均线 Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def wma(data: pd.Series, period: int) -> pd.Series:
        """加权移动平均线 Weighted Moving Average"""
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    
    @staticmethod
    def dema(data: pd.Series, period: int) -> pd.Series:
        """双指数移动平均线 Double Exponential Moving Average"""
        ema1 = data.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        return 2 * ema1 - ema2
    
    @staticmethod
    def tema(data: pd.Series, period: int) -> pd.Series:
        """三指数移动平均线 Triple Exponential Moving Average"""
        ema1 = data.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        return 3 * ema1 - 3 * ema2 + ema3
    
    @staticmethod
    def kama(data: pd.Series, period: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
        """考夫曼自适应移动平均 Kaufman Adaptive Moving Average"""
        change = abs(data - data.shift(period))
        volatility = abs(data - data.shift(1)).rolling(period).sum()
        
        # 效率比率
        er = change / volatility
        er = er.fillna(0)
        
        # 平滑常数
        fast_sc = 2 / (fast + 1)
        slow_sc = 2 / (slow + 1)
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        
        # KAMA计算
        kama = pd.Series(index=data.index, dtype='float64')
        kama.iloc[0] = data.iloc[0]
        
        for i in range(1, len(data)):
            kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (data.iloc[i] - kama.iloc[i-1])
        
        return kama
    
    @staticmethod
    def hma(data: pd.Series, period: int) -> pd.Series:
        """Hull移动平均线 Hull Moving Average"""
        half_period = int(period / 2)
        sqrt_period = int(np.sqrt(period))
        
        wma_half = TrendIndicators.wma(data, half_period)
        wma_full = TrendIndicators.wma(data, period)
        raw_hma = 2 * wma_half - wma_full
        
        return TrendIndicators.wma(raw_hma, sqrt_period)
    
    @staticmethod
    def zlema(data: pd.Series, period: int) -> pd.Series:
        """零延迟指数移动平均 Zero Lag Exponential Moving Average"""
        lag = int((period - 1) / 2)
        ema_data = data + (data - data.shift(lag))
        return ema_data.ewm(span=period, adjust=False).mean()
    
    # ============= MACD Series =============
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD指标 Moving Average Convergence Divergence"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    @staticmethod
    def macd_cross_signals(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """MACD交叉信号"""
        macd_df = TrendIndicators.macd(data, fast, slow, signal)
        
        signals = pd.Series(index=data.index, dtype='int')
        signals[0] = 0
        
        for i in range(1, len(macd_df)):
            if macd_df['macd'].iloc[i] > macd_df['signal'].iloc[i] and \
               macd_df['macd'].iloc[i-1] <= macd_df['signal'].iloc[i-1]:
                signals.iloc[i] = 1  # 金叉买入信号
            elif macd_df['macd'].iloc[i] < macd_df['signal'].iloc[i] and \
                 macd_df['macd'].iloc[i-1] >= macd_df['signal'].iloc[i-1]:
                signals.iloc[i] = -1  # 死叉卖出信号
            else:
                signals.iloc[i] = 0
        
        return signals
    
    # ============= Trend Strength =============
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
        """平均方向指数 Average Directional Index"""
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        tr['tr'] = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        
        # 方向移动
        dm_plus = pd.Series(index=high.index, dtype='float64')
        dm_minus = pd.Series(index=high.index, dtype='float64')
        
        for i in range(1, len(high)):
            up = high.iloc[i] - high.iloc[i-1]
            down = low.iloc[i-1] - low.iloc[i]
            
            dm_plus.iloc[i] = up if up > down and up > 0 else 0
            dm_minus.iloc[i] = down if down > up and down > 0 else 0
        
        # 平滑
        atr = tr['tr'].ewm(span=period, adjust=False).mean()
        di_plus = 100 * (dm_plus.ewm(span=period, adjust=False).mean() / atr)
        di_minus = 100 * (dm_minus.ewm(span=period, adjust=False).mean() / atr)
        
        # ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.ewm(span=period, adjust=False).mean()
        
        return pd.DataFrame({
            'adx': adx,
            'di_plus': di_plus,
            'di_minus': di_minus
        })
    
    @staticmethod
    def aroon(high: pd.Series, low: pd.Series, period: int = 25) -> pd.DataFrame:
        """阿隆指标 Aroon Indicator"""
        aroon_up = 100 * high.rolling(period + 1).apply(
            lambda x: x.argmax() / period, raw=False
        )
        aroon_down = 100 * low.rolling(period + 1).apply(
            lambda x: x.argmin() / period, raw=False
        )
        
        return pd.DataFrame({
            'aroon_up': aroon_up,
            'aroon_down': aroon_down,
            'aroon_oscillator': aroon_up - aroon_down
        })
    
    @staticmethod
    def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, 
                   period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """超级趋势指标 Supertrend"""
        # ATR计算
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        atr = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1).rolling(period).mean()
        
        # 基础带
        hl_avg = (high + low) / 2
        upper_band = hl_avg + multiplier * atr
        lower_band = hl_avg - multiplier * atr
        
        # Supertrend
        supertrend = pd.Series(index=close.index, dtype='float64')
        trend = pd.Series(index=close.index, dtype='int')
        
        for i in range(period, len(close)):
            if close.iloc[i] <= upper_band.iloc[i]:
                supertrend.iloc[i] = upper_band.iloc[i]
                trend.iloc[i] = -1
            else:
                supertrend.iloc[i] = lower_band.iloc[i]
                trend.iloc[i] = 1
            
            # 趋势延续
            if i > period:
                if trend.iloc[i] == 1:
                    if supertrend.iloc[i] < supertrend.iloc[i-1]:
                        supertrend.iloc[i] = supertrend.iloc[i-1]
                else:
                    if supertrend.iloc[i] > supertrend.iloc[i-1]:
                        supertrend.iloc[i] = supertrend.iloc[i-1]
        
        return pd.DataFrame({
            'supertrend': supertrend,
            'trend': trend
        })
    
    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, 
                      acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """抛物线SAR Parabolic Stop and Reverse"""
        sar = pd.Series(index=high.index, dtype='float64')
        ep = pd.Series(index=high.index, dtype='float64')  # 极值点
        af = pd.Series(index=high.index, dtype='float64')  # 加速因子
        trend = pd.Series(index=high.index, dtype='int')  # 1=上涨, -1=下跌
        
        # 初始化
        sar.iloc[0] = low.iloc[0]
        ep.iloc[0] = high.iloc[0]
        af.iloc[0] = acceleration
        trend.iloc[0] = 1
        
        for i in range(1, len(high)):
            if trend.iloc[i-1] == 1:  # 上升趋势
                sar.iloc[i] = sar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - sar.iloc[i-1])
                
                if low.iloc[i] < sar.iloc[i]:  # 趋势反转
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = acceleration
                else:
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep.iloc[i-1]:
                        ep.iloc[i] = high.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
            else:  # 下降趋势
                sar.iloc[i] = sar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - sar.iloc[i-1])
                
                if high.iloc[i] > sar.iloc[i]:  # 趋势反转
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = acceleration
                else:
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep.iloc[i-1]:
                        ep.iloc[i] = low.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
        
        return sar
    
    # ============= Channel Indicators =============
    
    @staticmethod
    def donchian_channel(high: pd.Series, low: pd.Series, period: int = 20) -> pd.DataFrame:
        """唐奇安通道 Donchian Channel"""
        upper = high.rolling(period).max()
        lower = low.rolling(period).min()
        middle = (upper + lower) / 2
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower
        })
    
    @staticmethod
    def keltner_channel(high: pd.Series, low: pd.Series, close: pd.Series,
                       period: int = 20, multiplier: float = 2.0) -> pd.DataFrame:
        """肯特纳通道 Keltner Channel"""
        # 计算ATR
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        atr = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1).ewm(span=period, adjust=False).mean()
        
        # 中线使用EMA
        middle = close.ewm(span=period, adjust=False).mean()
        upper = middle + multiplier * atr
        lower = middle - multiplier * atr
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower
        })
    
    @staticmethod
    def price_channel(high: pd.Series, low: pd.Series, period: int = 20) -> pd.DataFrame:
        """价格通道 Price Channel"""
        upper = high.shift(1).rolling(period).max()
        lower = low.shift(1).rolling(period).min()
        middle = (upper + lower) / 2
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower
        })
    
    # ============= Ichimoku Cloud =============
    
    @staticmethod
    def ichimoku_cloud(high: pd.Series, low: pd.Series, close: pd.Series,
                      conversion: int = 9, base: int = 26, 
                      span_b: int = 52, displacement: int = 26) -> pd.DataFrame:
        """一目均衡表 Ichimoku Cloud"""
        # 转换线
        conversion_line = (high.rolling(conversion).max() + 
                          low.rolling(conversion).min()) / 2
        
        # 基准线
        base_line = (high.rolling(base).max() + 
                    low.rolling(base).min()) / 2
        
        # 先行スパンA
        span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # 先行スパンB
        span_b_calc = ((high.rolling(span_b).max() + 
                       low.rolling(span_b).min()) / 2).shift(displacement)
        
        # 遅行スパン
        lagging_span = close.shift(-displacement)
        
        return pd.DataFrame({
            'conversion_line': conversion_line,
            'base_line': base_line,
            'span_a': span_a,
            'span_b': span_b_calc,
            'lagging_span': lagging_span
        })
    
    # ============= Linear Regression =============
    
    @staticmethod
    def linear_regression(data: pd.Series, period: int) -> pd.DataFrame:
        """线性回归 Linear Regression"""
        def lr_calc(values):
            if len(values) < 2:
                return np.nan, np.nan, np.nan
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            slope = coeffs[0]
            intercept = coeffs[1]
            regression_line = slope * (len(values) - 1) + intercept
            return regression_line, slope, intercept
        
        result = data.rolling(period).apply(
            lambda x: lr_calc(x)[0] if len(x) >= 2 else np.nan, raw=False
        )
        
        slope = data.rolling(period).apply(
            lambda x: lr_calc(x)[1] if len(x) >= 2 else np.nan, raw=False
        )
        
        return pd.DataFrame({
            'regression': result,
            'slope': slope
        })
    
    # ============= Pivots =============
    
    @staticmethod
    def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        """枢轴点 Pivot Points"""
        pivot = (high + low + close) / 3
        
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return pd.DataFrame({
            'pivot': pivot,
            'r1': r1, 's1': s1,
            'r2': r2, 's2': s2,
            'r3': r3, 's3': s3
        })
    
    @staticmethod
    def fibonacci_retracement(high_point: float, low_point: float) -> dict:
        """斐波那契回撤 Fibonacci Retracement"""
        diff = high_point - low_point
        
        return {
            '0.0%': high_point,
            '23.6%': high_point - diff * 0.236,
            '38.2%': high_point - diff * 0.382,
            '50.0%': high_point - diff * 0.5,
            '61.8%': high_point - diff * 0.618,
            '78.6%': high_point - diff * 0.786,
            '100.0%': low_point
        }
    
    # ============= Trend Detection =============
    
    @staticmethod
    def trend_detection(data: pd.Series, short_period: int = 20, 
                       long_period: int = 50) -> pd.Series:
        """趋势检测"""
        sma_short = TrendIndicators.sma(data, short_period)
        sma_long = TrendIndicators.sma(data, long_period)
        
        trend = pd.Series(index=data.index, dtype='int')
        trend[sma_short > sma_long] = 1  # 上升趋势
        trend[sma_short < sma_long] = -1  # 下降趋势
        trend[sma_short == sma_long] = 0  # 无趋势
        
        return trend
    
    @staticmethod
    def moving_average_ribbon(data: pd.Series, periods: list = None) -> pd.DataFrame:
        """移动平均线带 Moving Average Ribbon"""
        if periods is None:
            periods = [5, 10, 20, 30, 40, 50, 60]
        
        ribbon = pd.DataFrame(index=data.index)
        for period in periods:
            ribbon[f'MA_{period}'] = TrendIndicators.sma(data, period)
        
        return ribbon


def calculate_all_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有趋势指标"""
    indicators = TrendIndicators()
    result = df.copy()
    
    # 基础移动平均
    for period in [5, 10, 20, 30, 60, 120, 200]:
        result[f'SMA_{period}'] = indicators.sma(df['close'], period)
    
    for period in [9, 12, 26, 50, 100, 200]:
        result[f'EMA_{period}'] = indicators.ema(df['close'], period)
    
    # 高级移动平均
    result['WMA_20'] = indicators.wma(df['close'], 20)
    result['DEMA_20'] = indicators.dema(df['close'], 20)
    result['TEMA_20'] = indicators.tema(df['close'], 20)
    result['KAMA_10'] = indicators.kama(df['close'], 10)
    result['HMA_20'] = indicators.hma(df['close'], 20)
    result['ZLEMA_20'] = indicators.zlema(df['close'], 20)
    
    # MACD
    macd_standard = indicators.macd(df['close'], 12, 26, 9)
    result['MACD'] = macd_standard['macd']
    result['MACD_Signal'] = macd_standard['signal']
    result['MACD_Histogram'] = macd_standard['histogram']
    result['MACD_Cross'] = indicators.macd_cross_signals(df['close'])
    
    # 趋势强度
    adx = indicators.adx(df['high'], df['low'], df['close'])
    result['ADX'] = adx['adx']
    result['DI_Plus'] = adx['di_plus']
    result['DI_Minus'] = adx['di_minus']
    
    aroon = indicators.aroon(df['high'], df['low'])
    result['Aroon_Up'] = aroon['aroon_up']
    result['Aroon_Down'] = aroon['aroon_down']
    result['Aroon_Oscillator'] = aroon['aroon_oscillator']
    
    supertrend = indicators.supertrend(df['high'], df['low'], df['close'])
    result['Supertrend'] = supertrend['supertrend']
    result['Supertrend_Direction'] = supertrend['trend']
    
    result['SAR'] = indicators.parabolic_sar(df['high'], df['low'])
    
    # 通道指标
    donchian = indicators.donchian_channel(df['high'], df['low'])
    result['Donchian_Upper'] = donchian['upper']
    result['Donchian_Middle'] = donchian['middle']
    result['Donchian_Lower'] = donchian['lower']
    
    keltner = indicators.keltner_channel(df['high'], df['low'], df['close'])
    result['Keltner_Upper'] = keltner['upper']
    result['Keltner_Middle'] = keltner['middle']
    result['Keltner_Lower'] = keltner['lower']
    
    # 趋势检测
    result['Trend'] = indicators.trend_detection(df['close'])
    
    return result