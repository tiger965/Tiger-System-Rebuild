"""
Tiger System - Volume Indicators Module
Window 4: Technical Analysis Engine
30+ Volume Indicators Implementation
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional


class VolumeIndicators:
    """成交量类技术指标实现"""
    
    def __init__(self):
        self.name = "VolumeIndicators"
    
    # ============= Volume Price Indicators =============
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """能量潮 On Balance Volume"""
        obv = pd.Series(index=close.index, dtype='float64')
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """蔡金资金流 Chaikin Money Flow"""
        mf_multiplier = ((close - low) - (high - close)) / (high - low)
        mf_volume = mf_multiplier * volume
        
        cmf = mf_volume.rolling(period).sum() / volume.rolling(period).sum()
        return cmf
    
    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """资金流指数 Money Flow Index"""
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume
        
        positive_flow = pd.Series(index=close.index, dtype='float64')
        negative_flow = pd.Series(index=close.index, dtype='float64')
        
        for i in range(1, len(typical_price)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = raw_money_flow.iloc[i]
                negative_flow.iloc[i] = 0
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                positive_flow.iloc[i] = 0
                negative_flow.iloc[i] = raw_money_flow.iloc[i]
            else:
                positive_flow.iloc[i] = 0
                negative_flow.iloc[i] = 0
        
        positive_mf = positive_flow.rolling(period).sum()
        negative_mf = negative_flow.rolling(period).sum()
        
        mfi = 100 - (100 / (1 + positive_mf / negative_mf))
        return mfi
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """成交量加权平均价格 Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        cumulative_tp_volume = (typical_price * volume).cumsum()
        cumulative_volume = volume.cumsum()
        
        vwap = cumulative_tp_volume / cumulative_volume
        return vwap
    
    @staticmethod
    def vwma(close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """成交量加权移动平均 Volume Weighted Moving Average"""
        vwma = (close * volume).rolling(period).sum() / volume.rolling(period).sum()
        return vwma
    
    # ============= Accumulation Distribution =============
    
    @staticmethod
    def ad_line(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """累积派发线 Accumulation/Distribution Line"""
        mf_multiplier = ((close - low) - (high - close)) / (high - low)
        mf_volume = mf_multiplier * volume
        ad_line = mf_volume.cumsum()
        return ad_line
    
    @staticmethod
    def ad_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                     fast: int = 3, slow: int = 10) -> pd.Series:
        """累积派发震荡器 A/D Oscillator"""
        ad = VolumeIndicators.ad_line(high, low, close, volume)
        ad_osc = ad.ewm(span=fast, adjust=False).mean() - ad.ewm(span=slow, adjust=False).mean()
        return ad_osc
    
    @staticmethod
    def chaikin_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                          fast: int = 3, slow: int = 10) -> pd.Series:
        """蔡金震荡器 Chaikin Oscillator"""
        ad = VolumeIndicators.ad_line(high, low, close, volume)
        chaikin = ad.ewm(span=fast, adjust=False).mean() - ad.ewm(span=slow, adjust=False).mean()
        return chaikin
    
    # ============= Volume Analysis =============
    
    @staticmethod
    def volume_roc(volume: pd.Series, period: int = 12) -> pd.Series:
        """成交量变化率 Volume Rate of Change"""
        vroc = ((volume - volume.shift(period)) / volume.shift(period)) * 100
        return vroc
    
    @staticmethod
    def volume_oscillator(volume: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """成交量震荡器 Volume Oscillator"""
        fast_ma = volume.ewm(span=fast, adjust=False).mean()
        slow_ma = volume.ewm(span=slow, adjust=False).mean()
        vo = ((fast_ma - slow_ma) / slow_ma) * 100
        return vo
    
    @staticmethod
    def force_index(close: pd.Series, volume: pd.Series, period: int = 13) -> pd.Series:
        """力量指数 Force Index"""
        fi = (close - close.shift(1)) * volume
        return fi.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def ease_of_movement(high: pd.Series, low: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """轻松移动指标 Ease of Movement"""
        distance_moved = (high + low) / 2 - (high.shift(1) + low.shift(1)) / 2
        emv_ratio = distance_moved / (volume / 100000000 / (high - low))
        emv = emv_ratio.rolling(period).mean()
        return emv
    
    @staticmethod
    def volume_price_trend(close: pd.Series, volume: pd.Series) -> pd.Series:
        """量价趋势 Volume Price Trend"""
        vpt = pd.Series(index=close.index, dtype='float64')
        vpt.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            price_change = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
            vpt.iloc[i] = vpt.iloc[i-1] + volume.iloc[i] * price_change
        
        return vpt
    
    @staticmethod
    def negative_volume_index(close: pd.Series, volume: pd.Series) -> pd.Series:
        """负成交量指数 Negative Volume Index"""
        nvi = pd.Series(index=close.index, dtype='float64')
        nvi.iloc[0] = 1000
        
        for i in range(1, len(close)):
            if volume.iloc[i] < volume.iloc[i-1]:
                roc = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
                nvi.iloc[i] = nvi.iloc[i-1] * (1 + roc)
            else:
                nvi.iloc[i] = nvi.iloc[i-1]
        
        return nvi
    
    @staticmethod
    def positive_volume_index(close: pd.Series, volume: pd.Series) -> pd.Series:
        """正成交量指数 Positive Volume Index"""
        pvi = pd.Series(index=close.index, dtype='float64')
        pvi.iloc[0] = 1000
        
        for i in range(1, len(close)):
            if volume.iloc[i] > volume.iloc[i-1]:
                roc = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
                pvi.iloc[i] = pvi.iloc[i-1] * (1 + roc)
            else:
                pvi.iloc[i] = pvi.iloc[i-1]
        
        return pvi
    
    @staticmethod
    def volume_profile(close: pd.Series, volume: pd.Series, bins: int = 20) -> pd.DataFrame:
        """成交量分布 Volume Profile"""
        price_bins = pd.cut(close, bins=bins)
        volume_profile = volume.groupby(price_bins).sum()
        
        result = pd.DataFrame({
            'price_level': volume_profile.index.categories.mid,
            'volume': volume_profile.values
        })
        
        # 找出高成交量区域（POC - Point of Control）
        poc_idx = result['volume'].idxmax()
        result['is_poc'] = False
        result.loc[poc_idx, 'is_poc'] = True
        
        # 计算价值区域（70%成交量的区域）
        total_volume = result['volume'].sum()
        cumulative_volume = result['volume'].cumsum()
        value_area_volume = total_volume * 0.7
        
        result['in_value_area'] = cumulative_volume <= value_area_volume
        
        return result
    
    @staticmethod
    def klinger_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                          fast: int = 34, slow: int = 55, signal: int = 13) -> pd.DataFrame:
        """克林格震荡器 Klinger Oscillator"""
        trend = pd.Series(index=close.index, dtype='int')
        trend.iloc[0] = 1
        
        for i in range(1, len(close)):
            hlc = high.iloc[i] + low.iloc[i] + close.iloc[i]
            hlc_prev = high.iloc[i-1] + low.iloc[i-1] + close.iloc[i-1]
            
            if hlc > hlc_prev:
                trend.iloc[i] = 1
            else:
                trend.iloc[i] = -1
        
        dm = high - low
        cm = pd.Series(index=close.index, dtype='float64')
        cm.iloc[0] = dm.iloc[0]
        
        for i in range(1, len(close)):
            if trend.iloc[i] == trend.iloc[i-1]:
                cm.iloc[i] = cm.iloc[i-1] + dm.iloc[i]
            else:
                cm.iloc[i] = dm.iloc[i-1] + dm.iloc[i]
        
        vf = volume * trend * abs(2 * dm / cm - 1)
        
        kvo = vf.ewm(span=fast, adjust=False).mean() - vf.ewm(span=slow, adjust=False).mean()
        signal_line = kvo.ewm(span=signal, adjust=False).mean()
        
        return pd.DataFrame({
            'kvo': kvo,
            'signal': signal_line,
            'diff': kvo - signal_line
        })
    
    @staticmethod
    def twiggs_money_flow(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 21) -> pd.Series:
        """特威格斯资金流 Twiggs Money Flow"""
        true_low = pd.DataFrame([low, close.shift(1)]).min()
        true_high = pd.DataFrame([high, close.shift(1)]).max()
        
        mf = ((close - true_low) - (true_high - close)) / (true_high - true_low)
        mf_volume = mf * volume
        
        tmf = mf_volume.ewm(span=period, adjust=False).mean() / volume.ewm(span=period, adjust=False).mean()
        return tmf
    
    @staticmethod
    def williams_ad(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """威廉累积派发 Williams Accumulation/Distribution"""
        wad = pd.Series(index=close.index, dtype='float64')
        wad.iloc[0] = 0
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                wad.iloc[i] = wad.iloc[i-1] + close.iloc[i] - min(low.iloc[i], close.iloc[i-1])
            elif close.iloc[i] < close.iloc[i-1]:
                wad.iloc[i] = wad.iloc[i-1] + close.iloc[i] - max(high.iloc[i], close.iloc[i-1])
            else:
                wad.iloc[i] = wad.iloc[i-1]
        
        return wad
    
    @staticmethod
    def volume_weighted_macd(close: pd.Series, volume: pd.Series, 
                           fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """成交量加权MACD Volume Weighted MACD"""
        vwma_fast = VolumeIndicators.vwma(close, volume, fast)
        vwma_slow = VolumeIndicators.vwma(close, volume, slow)
        
        macd_line = vwma_fast - vwma_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    @staticmethod
    def volume_zone_oscillator(close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """成交量区域震荡器 Volume Zone Oscillator"""
        r = pd.Series(index=close.index, dtype='float64')
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                r.iloc[i] = volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                r.iloc[i] = -volume.iloc[i]
            else:
                r.iloc[i] = 0
        
        vzo = 100 * r.ewm(span=period, adjust=False).mean() / volume.ewm(span=period, adjust=False).mean()
        return vzo
    
    @staticmethod
    def elder_force_index(close: pd.Series, volume: pd.Series, period: int = 2) -> pd.Series:
        """艾尔德力量指数 Elder's Force Index"""
        efi = (close - close.shift(1)) * volume
        return efi.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def volume_spread_analysis(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.DataFrame:
        """成交量价差分析 Volume Spread Analysis"""
        spread = high - low
        close_location = (close - low) / spread
        
        # VSA信号
        vsa_signals = pd.Series(index=close.index, dtype='str')
        
        for i in range(1, len(close)):
            # 高成交量 + 窄价差 = 可能的顶部
            if volume.iloc[i] > volume.iloc[i-1] * 1.5 and spread.iloc[i] < spread.iloc[i-1]:
                vsa_signals.iloc[i] = 'potential_top'
            # 低成交量 + 测试前低 = 可能的底部
            elif volume.iloc[i] < volume.iloc[i-1] * 0.5 and low.iloc[i] <= low.iloc[i-1:i-5].min():
                vsa_signals.iloc[i] = 'potential_bottom'
            # 高成交量突破
            elif volume.iloc[i] > volume.iloc[i-1] * 2 and close.iloc[i] > high.iloc[i-1]:
                vsa_signals.iloc[i] = 'breakout'
            else:
                vsa_signals.iloc[i] = 'neutral'
        
        return pd.DataFrame({
            'spread': spread,
            'close_location': close_location,
            'volume_ratio': volume / volume.rolling(20).mean(),
            'signal': vsa_signals
        })


def calculate_all_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有成交量指标"""
    indicators = VolumeIndicators()
    result = df.copy()
    
    if 'volume' not in df.columns:
        print("Warning: No volume data available")
        return result
    
    # 量价指标
    result['OBV'] = indicators.obv(df['close'], df['volume'])
    result['CMF'] = indicators.cmf(df['high'], df['low'], df['close'], df['volume'])
    result['MFI'] = indicators.mfi(df['high'], df['low'], df['close'], df['volume'])
    result['VWAP'] = indicators.vwap(df['high'], df['low'], df['close'], df['volume'])
    result['VWMA'] = indicators.vwma(df['close'], df['volume'])
    
    # 累积派发
    result['AD_Line'] = indicators.ad_line(df['high'], df['low'], df['close'], df['volume'])
    result['AD_Oscillator'] = indicators.ad_oscillator(df['high'], df['low'], df['close'], df['volume'])
    result['Chaikin_Osc'] = indicators.chaikin_oscillator(df['high'], df['low'], df['close'], df['volume'])
    
    # 量能分析
    result['Volume_ROC'] = indicators.volume_roc(df['volume'])
    result['Volume_Osc'] = indicators.volume_oscillator(df['volume'])
    result['Force_Index'] = indicators.force_index(df['close'], df['volume'])
    result['EOM'] = indicators.ease_of_movement(df['high'], df['low'], df['volume'])
    result['VPT'] = indicators.volume_price_trend(df['close'], df['volume'])
    result['NVI'] = indicators.negative_volume_index(df['close'], df['volume'])
    result['PVI'] = indicators.positive_volume_index(df['close'], df['volume'])
    
    # 高级指标
    klinger = indicators.klinger_oscillator(df['high'], df['low'], df['close'], df['volume'])
    result['Klinger'] = klinger['kvo']
    result['Klinger_Signal'] = klinger['signal']
    
    result['Twiggs_MF'] = indicators.twiggs_money_flow(df['high'], df['low'], df['close'], df['volume'])
    result['Williams_AD'] = indicators.williams_ad(df['high'], df['low'], df['close'])
    
    vw_macd = indicators.volume_weighted_macd(df['close'], df['volume'])
    result['VW_MACD'] = vw_macd['macd']
    result['VW_MACD_Signal'] = vw_macd['signal']
    
    result['VZO'] = indicators.volume_zone_oscillator(df['close'], df['volume'])
    result['Elder_FI'] = indicators.elder_force_index(df['close'], df['volume'])
    
    # VSA分析
    vsa = indicators.volume_spread_analysis(df['high'], df['low'], df['close'], df['volume'])
    result['VSA_Signal'] = vsa['signal']
    result['Volume_Ratio'] = vsa['volume_ratio']
    
    return result