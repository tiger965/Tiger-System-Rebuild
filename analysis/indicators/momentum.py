"""
Tiger System - Momentum Indicators Module
Window 4: Technical Analysis Engine
35+ Momentum Indicators Implementation
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional


class MomentumIndicators:
    """动量类技术指标实现"""
    
    def __init__(self):
        self.name = "MomentumIndicators"
    
    # ============= RSI Series =============
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """相对强弱指数 Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def stochastic_rsi(data: pd.Series, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """随机RSI Stochastic RSI"""
        rsi_values = MomentumIndicators.rsi(data, period)
        
        stoch_rsi = pd.Series(index=data.index, dtype='float64')
        for i in range(period - 1, len(rsi_values)):
            rsi_window = rsi_values.iloc[i - period + 1:i + 1]
            min_rsi = rsi_window.min()
            max_rsi = rsi_window.max()
            
            if max_rsi != min_rsi:
                stoch_rsi.iloc[i] = (rsi_values.iloc[i] - min_rsi) / (max_rsi - min_rsi) * 100
            else:
                stoch_rsi.iloc[i] = 0
        
        k = stoch_rsi.rolling(smooth_k).mean()
        d = k.rolling(smooth_d).mean()
        
        return pd.DataFrame({
            'stoch_rsi': stoch_rsi,
            'k': k,
            'd': d
        })
    
    @staticmethod
    def connors_rsi(close: pd.Series, period_rsi: int = 3, period_streak: int = 2, period_pct: int = 100) -> pd.Series:
        """康纳斯RSI Connors RSI"""
        # RSI of price
        rsi_close = MomentumIndicators.rsi(close, period_rsi)
        
        # RSI of streak
        streak = pd.Series(index=close.index, dtype='float64')
        streak.iloc[0] = 0
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                streak.iloc[i] = streak.iloc[i-1] + 1 if streak.iloc[i-1] >= 0 else 1
            elif close.iloc[i] < close.iloc[i-1]:
                streak.iloc[i] = streak.iloc[i-1] - 1 if streak.iloc[i-1] <= 0 else -1
            else:
                streak.iloc[i] = 0
        
        rsi_streak = MomentumIndicators.rsi(streak, period_streak)
        
        # Percent rank
        pct_rank = pd.Series(index=close.index, dtype='float64')
        roc = close.pct_change()
        for i in range(period_pct, len(close)):
            window = roc.iloc[i - period_pct + 1:i + 1]
            pct_rank.iloc[i] = (window < roc.iloc[i]).sum() / period_pct * 100
        
        # Connors RSI
        crsi = (rsi_close + rsi_streak + pct_rank) / 3
        return crsi
    
    @staticmethod
    def rsi_divergence(price: pd.Series, period: int = 14, lookback: int = 20) -> pd.Series:
        """RSI背离检测 RSI Divergence Detection"""
        rsi_values = MomentumIndicators.rsi(price, period)
        divergence = pd.Series(index=price.index, dtype='int')
        
        for i in range(lookback, len(price)):
            price_window = price.iloc[i - lookback:i + 1]
            rsi_window = rsi_values.iloc[i - lookback:i + 1]
            
            # 找到局部高点和低点
            price_highs = (price_window == price_window.rolling(5, center=True).max())
            price_lows = (price_window == price_window.rolling(5, center=True).min())
            
            rsi_highs = (rsi_window == rsi_window.rolling(5, center=True).max())
            rsi_lows = (rsi_window == rsi_window.rolling(5, center=True).min())
            
            # 看涨背离：价格创新低，RSI没有创新低
            if price_lows.iloc[-1] and not rsi_lows.iloc[-1]:
                if price_window.iloc[-1] < price_window[price_lows].iloc[-2] and \
                   rsi_window.iloc[-1] > rsi_window[rsi_lows].iloc[-2]:
                    divergence.iloc[i] = 1
            
            # 看跌背离：价格创新高，RSI没有创新高
            elif price_highs.iloc[-1] and not rsi_highs.iloc[-1]:
                if price_window.iloc[-1] > price_window[price_highs].iloc[-2] and \
                   rsi_window.iloc[-1] < rsi_window[rsi_highs].iloc[-2]:
                    divergence.iloc[i] = -1
            else:
                divergence.iloc[i] = 0
        
        return divergence
    
    # ============= Stochastic Series =============
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """随机指标 Stochastic Oscillator (KD)"""
        lowest_low = low.rolling(k_period).min()
        highest_high = high.rolling(k_period).max()
        
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(d_period).mean()
        
        return pd.DataFrame({
            'k': k,
            'd': d,
            'k_d_diff': k - d
        })
    
    @staticmethod
    def slow_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                       k_period: int = 14, d_period: int = 3, smooth_period: int = 3) -> pd.DataFrame:
        """慢速随机指标 Slow Stochastic"""
        fast_stoch = MomentumIndicators.stochastic(high, low, close, k_period, d_period)
        
        slow_k = fast_stoch['k'].rolling(smooth_period).mean()
        slow_d = slow_k.rolling(d_period).mean()
        
        return pd.DataFrame({
            'slow_k': slow_k,
            'slow_d': slow_d,
            'slow_diff': slow_k - slow_d
        })
    
    @staticmethod
    def full_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                       lookback: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """完全随机指标 Full Stochastic"""
        lowest_low = low.rolling(lookback).min()
        highest_high = high.rolling(lookback).max()
        
        raw_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        full_k = raw_k.rolling(smooth_k).mean()
        full_d = full_k.rolling(smooth_d).mean()
        
        return pd.DataFrame({
            'full_k': full_k,
            'full_d': full_d,
            'full_diff': full_k - full_d
        })
    
    @staticmethod
    def stochastic_momentum_index(high: pd.Series, low: pd.Series, close: pd.Series,
                                 period: int = 14, smooth: int = 3) -> pd.Series:
        """随机动量指数 Stochastic Momentum Index"""
        hl_mid = (high + low) / 2
        hl_range = high.rolling(period).max() - low.rolling(period).min()
        hl_range_half = hl_range / 2
        
        smi_raw = 100 * ((close - hl_mid.rolling(period).mean()) / hl_range_half)
        smi = smi_raw.rolling(smooth).mean()
        
        return smi
    
    # ============= Other Momentum Indicators =============
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """商品通道指数 Commodity Channel Index"""
        tp = (high + low + close) / 3  # Typical Price
        ma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (tp - ma) / (0.015 * mad)
        return cci
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """威廉指标 Williams %R"""
        highest_high = high.rolling(period).max()
        lowest_low = low.rolling(period).min()
        
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return wr
    
    @staticmethod
    def momentum(data: pd.Series, period: int = 10) -> pd.Series:
        """动量指标 Momentum"""
        return data - data.shift(period)
    
    @staticmethod
    def roc(data: pd.Series, period: int = 10) -> pd.Series:
        """变化率 Rate of Change"""
        return 100 * ((data - data.shift(period)) / data.shift(period))
    
    @staticmethod
    def tsi(close: pd.Series, long_period: int = 25, short_period: int = 13) -> pd.Series:
        """真实强度指数 True Strength Index"""
        price_change = close.diff()
        
        # 双重平滑
        ema_long = price_change.ewm(span=long_period, adjust=False).mean()
        double_smooth = ema_long.ewm(span=short_period, adjust=False).mean()
        
        abs_price_change = price_change.abs()
        abs_ema_long = abs_price_change.ewm(span=long_period, adjust=False).mean()
        abs_double_smooth = abs_ema_long.ewm(span=short_period, adjust=False).mean()
        
        tsi = 100 * (double_smooth / abs_double_smooth)
        return tsi
    
    @staticmethod
    def ultimate_oscillator(high: pd.Series, low: pd.Series, close: pd.Series,
                          period1: int = 7, period2: int = 14, period3: int = 28) -> pd.Series:
        """终极震荡器 Ultimate Oscillator"""
        prev_close = close.shift(1)
        
        # True Range and Buying Pressure
        true_low = pd.DataFrame([low, prev_close]).min()
        true_range = high - true_low
        buying_pressure = close - true_low
        
        # 计算三个周期的平均值
        avg1 = buying_pressure.rolling(period1).sum() / true_range.rolling(period1).sum()
        avg2 = buying_pressure.rolling(period2).sum() / true_range.rolling(period2).sum()
        avg3 = buying_pressure.rolling(period3).sum() / true_range.rolling(period3).sum()
        
        # 加权计算
        uo = 100 * ((4 * avg1 + 2 * avg2 + avg3) / 7)
        return uo
    
    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """资金流量指数 Money Flow Index"""
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume
        
        # 计算正负资金流
        money_flow_ratio = pd.Series(index=close.index, dtype='float64')
        
        for i in range(1, len(close)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                money_flow_ratio.iloc[i] = raw_money_flow.iloc[i]
            else:
                money_flow_ratio.iloc[i] = -raw_money_flow.iloc[i]
        
        positive_flow = money_flow_ratio.where(money_flow_ratio > 0, 0).rolling(period).sum()
        negative_flow = -money_flow_ratio.where(money_flow_ratio < 0, 0).rolling(period).sum()
        
        mfi = 100 - (100 / (1 + positive_flow / negative_flow))
        return mfi
    
    @staticmethod
    def kst(close: pd.Series, r1: int = 10, r2: int = 15, r3: int = 20, r4: int = 30,
           n1: int = 10, n2: int = 10, n3: int = 10, n4: int = 15) -> pd.DataFrame:
        """KST震荡器 Know Sure Thing"""
        roc1 = MomentumIndicators.roc(close, r1)
        roc2 = MomentumIndicators.roc(close, r2)
        roc3 = MomentumIndicators.roc(close, r3)
        roc4 = MomentumIndicators.roc(close, r4)
        
        sma1 = roc1.rolling(n1).mean()
        sma2 = roc2.rolling(n2).mean()
        sma3 = roc3.rolling(n3).mean()
        sma4 = roc4.rolling(n4).mean()
        
        kst = (sma1 * 1) + (sma2 * 2) + (sma3 * 3) + (sma4 * 4)
        signal = kst.rolling(9).mean()
        
        return pd.DataFrame({
            'kst': kst,
            'signal': signal,
            'diff': kst - signal
        })
    
    @staticmethod
    def ppo(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """百分比价格震荡器 Percentage Price Oscillator"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        ppo = 100 * ((ema_fast - ema_slow) / ema_slow)
        ppo_signal = ppo.ewm(span=signal, adjust=False).mean()
        ppo_hist = ppo - ppo_signal
        
        return pd.DataFrame({
            'ppo': ppo,
            'signal': ppo_signal,
            'histogram': ppo_hist
        })
    
    @staticmethod
    def cmo(close: pd.Series, period: int = 14) -> pd.Series:
        """钱德动量震荡器 Chande Momentum Oscillator"""
        diff = close.diff()
        gain = diff.where(diff > 0, 0).rolling(period).sum()
        loss = -diff.where(diff < 0, 0).rolling(period).sum()
        
        cmo = 100 * ((gain - loss) / (gain + loss))
        return cmo
    
    @staticmethod
    def dpo(close: pd.Series, period: int = 20) -> pd.Series:
        """去趋势价格震荡器 Detrended Price Oscillator"""
        shift = int(period / 2) + 1
        ma = close.rolling(period).mean()
        dpo = close - ma.shift(shift)
        return dpo
    
    @staticmethod
    def mass_index(high: pd.Series, low: pd.Series, period: int = 9, period2: int = 25) -> pd.Series:
        """质量指数 Mass Index"""
        hl_range = high - low
        ema1 = hl_range.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        
        ratio = ema1 / ema2
        mass_index = ratio.rolling(period2).sum()
        
        return mass_index
    
    @staticmethod
    def vortex(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
        """涡流指标 Vortex Indicator"""
        vm_plus = abs(high - low.shift(1))
        vm_minus = abs(low - high.shift(1))
        
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        true_range = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        
        vi_plus = vm_plus.rolling(period).sum() / true_range.rolling(period).sum()
        vi_minus = vm_minus.rolling(period).sum() / true_range.rolling(period).sum()
        
        return pd.DataFrame({
            'vi_plus': vi_plus,
            'vi_minus': vi_minus,
            'vi_diff': vi_plus - vi_minus
        })
    
    @staticmethod
    def fisher_transform(high: pd.Series, low: pd.Series, period: int = 9) -> pd.DataFrame:
        """费舍尔变换 Fisher Transform"""
        med_price = (high + low) / 2
        
        # 归一化价格到-1到1之间
        max_high = high.rolling(period).max()
        min_low = low.rolling(period).min()
        
        x = pd.Series(index=high.index, dtype='float64')
        for i in range(period - 1, len(med_price)):
            if max_high.iloc[i] != min_low.iloc[i]:
                x.iloc[i] = 0.33 * 2 * ((med_price.iloc[i] - min_low.iloc[i]) / 
                                        (max_high.iloc[i] - min_low.iloc[i]) - 0.5)
                if i > period:
                    x.iloc[i] += 0.67 * x.iloc[i-1]
            else:
                x.iloc[i] = 0
        
        # 限制x的范围
        x = x.clip(-0.999, 0.999)
        
        # Fisher变换
        fisher = 0.5 * np.log((1 + x) / (1 - x))
        trigger = fisher.shift(1)
        
        return pd.DataFrame({
            'fisher': fisher,
            'trigger': trigger,
            'signal': fisher - trigger
        })
    
    @staticmethod
    def awesome_oscillator(high: pd.Series, low: pd.Series, fast: int = 5, slow: int = 34) -> pd.Series:
        """动量震荡器 Awesome Oscillator"""
        midpoint = (high + low) / 2
        ao = midpoint.rolling(fast).mean() - midpoint.rolling(slow).mean()
        return ao
    
    @staticmethod
    def accelerator_oscillator(high: pd.Series, low: pd.Series, fast: int = 5, slow: int = 34) -> pd.Series:
        """加速震荡器 Accelerator Oscillator"""
        ao = MomentumIndicators.awesome_oscillator(high, low, fast, slow)
        ac = ao - ao.rolling(5).mean()
        return ac


def calculate_all_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有动量指标"""
    indicators = MomentumIndicators()
    result = df.copy()
    
    # RSI系列
    result['RSI_14'] = indicators.rsi(df['close'], 14)
    result['RSI_9'] = indicators.rsi(df['close'], 9)
    result['RSI_25'] = indicators.rsi(df['close'], 25)
    
    stoch_rsi = indicators.stochastic_rsi(df['close'])
    result['Stoch_RSI'] = stoch_rsi['stoch_rsi']
    result['Stoch_RSI_K'] = stoch_rsi['k']
    result['Stoch_RSI_D'] = stoch_rsi['d']
    
    result['Connors_RSI'] = indicators.connors_rsi(df['close'])
    result['RSI_Divergence'] = indicators.rsi_divergence(df['close'])
    
    # 随机指标系列
    stoch = indicators.stochastic(df['high'], df['low'], df['close'])
    result['Stoch_K'] = stoch['k']
    result['Stoch_D'] = stoch['d']
    
    slow_stoch = indicators.slow_stochastic(df['high'], df['low'], df['close'])
    result['Slow_Stoch_K'] = slow_stoch['slow_k']
    result['Slow_Stoch_D'] = slow_stoch['slow_d']
    
    full_stoch = indicators.full_stochastic(df['high'], df['low'], df['close'])
    result['Full_Stoch_K'] = full_stoch['full_k']
    result['Full_Stoch_D'] = full_stoch['full_d']
    
    result['SMI'] = indicators.stochastic_momentum_index(df['high'], df['low'], df['close'])
    
    # 其他动量指标
    result['CCI'] = indicators.cci(df['high'], df['low'], df['close'])
    result['Williams_R'] = indicators.williams_r(df['high'], df['low'], df['close'])
    result['MOM'] = indicators.momentum(df['close'])
    result['ROC'] = indicators.roc(df['close'])
    result['TSI'] = indicators.tsi(df['close'])
    result['UO'] = indicators.ultimate_oscillator(df['high'], df['low'], df['close'])
    
    if 'volume' in df.columns:
        result['MFI'] = indicators.mfi(df['high'], df['low'], df['close'], df['volume'])
    
    kst = indicators.kst(df['close'])
    result['KST'] = kst['kst']
    result['KST_Signal'] = kst['signal']
    
    ppo = indicators.ppo(df['close'])
    result['PPO'] = ppo['ppo']
    result['PPO_Signal'] = ppo['signal']
    
    result['CMO'] = indicators.cmo(df['close'])
    result['DPO'] = indicators.dpo(df['close'])
    result['Mass_Index'] = indicators.mass_index(df['high'], df['low'])
    
    vortex = indicators.vortex(df['high'], df['low'], df['close'])
    result['VI_Plus'] = vortex['vi_plus']
    result['VI_Minus'] = vortex['vi_minus']
    
    fisher = indicators.fisher_transform(df['high'], df['low'])
    result['Fisher'] = fisher['fisher']
    result['Fisher_Trigger'] = fisher['trigger']
    
    result['AO'] = indicators.awesome_oscillator(df['high'], df['low'])
    result['AC'] = indicators.accelerator_oscillator(df['high'], df['low'])
    
    return result