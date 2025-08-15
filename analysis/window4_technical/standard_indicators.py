"""
标准技术指标计算
纯计算，不做任何判断
"""

import numpy as np
from typing import List, Dict, Optional, Union


class StandardIndicators:
    """标准技术指标 - Window 6常用"""
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        计算RSI（相对强弱指标）
        Window 6命令：'计算BTC 15分钟线RSI'
        返回：具体数值，不判断超买超卖
        """
        if len(prices) < period + 1:
            return 50.0
        
        prices = np.array(prices)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0 and avg_gain == 0:
            return 50.0
        elif avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(float(rsi), 2)
    
    def calculate_macd(self, prices: List[float], fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """
        计算MACD
        返回：
        - macd_line: MACD线
        - signal_line: 信号线  
        - histogram: 柱状图
        """
        if len(prices) < slow:
            return {
                'macd_line': 0.0,
                'signal_line': 0.0,
                'histogram': 0.0
            }
        
        prices = np.array(prices)
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line[-1] - signal_line[-1]
        
        return {
            'macd_line': round(float(macd_line[-1]), 4),
            'signal_line': round(float(signal_line[-1]), 4),
            'histogram': round(float(histogram), 4)
        }
    
    def calculate_bollinger_bands(self, prices: List[float], 
                                 period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """
        计算布林带
        返回：
        - upper: 上轨
        - middle: 中轨
        - lower: 下轨
        - bandwidth: 带宽
        """
        if len(prices) < period:
            current_price = prices[-1] if prices else 0
            return {
                'upper': current_price * 1.02,
                'middle': current_price,
                'lower': current_price * 0.98,
                'bandwidth': 0.04
            }
        
        prices = np.array(prices)
        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        bandwidth = (upper - lower) / middle if middle != 0 else 0
        
        return {
            'upper': round(float(upper), 2),
            'middle': round(float(middle), 2),
            'lower': round(float(lower), 2),
            'bandwidth': round(float(bandwidth), 4)
        }
    
    def calculate_moving_averages(self, prices: List[float]) -> Dict[str, float]:
        """
        计算多种均线
        返回：
        - MA5, MA10, MA20, MA50, MA200
        - EMA9, EMA21, EMA55
        """
        result = {}
        prices = np.array(prices)
        
        ma_periods = [5, 10, 20, 50, 200]
        for period in ma_periods:
            if len(prices) >= period:
                result[f'MA{period}'] = round(float(np.mean(prices[-period:])), 2)
            else:
                result[f'MA{period}'] = round(float(prices[-1] if prices.size > 0 else 0), 2)
        
        ema_periods = [9, 21, 55]
        for period in ema_periods:
            if len(prices) >= period:
                ema = self._calculate_ema(prices, period)
                result[f'EMA{period}'] = round(float(ema[-1]), 2)
            else:
                result[f'EMA{period}'] = round(float(prices[-1] if prices.size > 0 else 0), 2)
        
        return result
    
    def calculate_stochastic(self, high: List[float], low: List[float], 
                           close: List[float], period: int = 14, 
                           smooth_k: int = 3, smooth_d: int = 3) -> Dict[str, float]:
        """
        计算随机指标(KDJ)
        返回：K线和D线的值
        """
        if len(close) < period:
            return {'K': 50.0, 'D': 50.0, 'J': 50.0}
        
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        
        lowest_low = np.min(low[-period:])
        highest_high = np.max(high[-period:])
        
        if highest_high == lowest_low:
            k = 50.0
        else:
            k = 100 * (close[-1] - lowest_low) / (highest_high - lowest_low)
        
        k_smooth = self._simple_moving_average([k], smooth_k)
        d = self._simple_moving_average([k_smooth], smooth_d)
        j = 3 * k_smooth - 2 * d
        
        return {
            'K': round(float(k_smooth), 2),
            'D': round(float(d), 2),
            'J': round(float(j), 2)
        }
    
    def calculate_atr(self, high: List[float], low: List[float], 
                     close: List[float], period: int = 14) -> float:
        """
        计算平均真实波幅(ATR)
        """
        if len(close) < 2:
            return 0.0
        
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        
        tr_list = []
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr = max(hl, hc, lc)
            tr_list.append(tr)
        
        if len(tr_list) < period:
            return np.mean(tr_list) if tr_list else 0.0
        
        atr = np.mean(tr_list[-period:])
        return round(float(atr), 4)
    
    def calculate_cci(self, high: List[float], low: List[float], 
                     close: List[float], period: int = 20) -> float:
        """
        计算商品通道指数(CCI)
        """
        if len(close) < period:
            return 0.0
        
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        
        typical_price = (high + low + close) / 3
        sma = np.mean(typical_price[-period:])
        mean_deviation = np.mean(np.abs(typical_price[-period:] - sma))
        
        if mean_deviation == 0:
            return 0.0
        
        cci = (typical_price[-1] - sma) / (0.015 * mean_deviation)
        return round(float(cci), 2)
    
    def calculate_obv(self, close: List[float], volume: List[float]) -> float:
        """
        计算能量潮(OBV)
        """
        if len(close) < 2 or len(volume) < 2:
            return 0.0
        
        close = np.array(close)
        volume = np.array(volume)
        
        obv = 0.0
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv += volume[i]
            elif close[i] < close[i-1]:
                obv -= volume[i]
        
        return round(float(obv), 0)
    
    def calculate_williams_r(self, high: List[float], low: List[float], 
                            close: List[float], period: int = 14) -> float:
        """
        计算威廉指标(%R)
        """
        if len(close) < period:
            return -50.0
        
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        
        highest_high = np.max(high[-period:])
        lowest_low = np.min(low[-period:])
        
        if highest_high == lowest_low:
            return -50.0
        
        williams_r = -100 * (highest_high - close[-1]) / (highest_high - lowest_low)
        return round(float(williams_r), 2)
    
    def calculate_mfi(self, high: List[float], low: List[float], 
                     close: List[float], volume: List[float], period: int = 14) -> float:
        """
        计算资金流量指标(MFI)
        """
        if len(close) < period + 1:
            return 50.0
        
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        volume = np.array(volume)
        
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        positive_flow = 0.0
        negative_flow = 0.0
        
        for i in range(1, period + 1):
            if typical_price[-i] > typical_price[-i-1]:
                positive_flow += money_flow[-i]
            else:
                negative_flow += money_flow[-i]
        
        if negative_flow == 0:
            return 100.0
        
        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))
        
        return round(float(mfi), 2)
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """计算指数移动平均"""
        if len(data) < period:
            return data
        
        ema = np.zeros_like(data)
        ema[:period] = data[:period]
        ema[period-1] = np.mean(data[:period])
        
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def _simple_moving_average(self, data: List[float], period: int) -> float:
        """计算简单移动平均"""
        if len(data) < period:
            return np.mean(data) if data else 0.0
        return float(np.mean(data[-period:]))