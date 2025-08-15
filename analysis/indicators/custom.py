"""
Tiger System - Custom Indicators Module
Window 4: Technical Analysis Engine
50+ Custom Combination Indicators (Tiger专属)
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional, Dict, List


class CustomIndicators:
    """自定义组合指标 - Tiger系统专属"""
    
    def __init__(self):
        self.name = "CustomIndicators"
    
    # ============= Tiger专属核心指标 =============
    
    @staticmethod
    def tiger_momentum_index(close: pd.Series, volume: pd.Series, 
                            rsi_period: int = 14, macd_fast: int = 12, 
                            macd_slow: int = 26) -> pd.Series:
        """Tiger动量指数 TMI - 综合RSI、MACD和成交量"""
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = -delta.where(delta < 0, 0).rolling(rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_fast = close.ewm(span=macd_fast, adjust=False).mean()
        ema_slow = close.ewm(span=macd_slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_normalized = macd / close * 100
        
        # 成交量动量
        volume_ma = volume.rolling(20).mean()
        volume_ratio = volume / volume_ma
        
        # TMI综合计算
        tmi = (rsi / 100 * 0.4 + 
               (macd_normalized + 50) / 100 * 0.4 + 
               volume_ratio.clip(0, 2) / 2 * 0.2) * 100
        
        return tmi
    
    @staticmethod 
    def tiger_trend_score(high: pd.Series, low: pd.Series, close: pd.Series, 
                         period: int = 20) -> pd.Series:
        """Tiger趋势评分 TTS - 多维度趋势强度评估"""
        # 价格位置
        highest = high.rolling(period).max()
        lowest = low.rolling(period).min()
        price_position = (close - lowest) / (highest - lowest) * 100
        
        # 移动平均趋势
        sma_short = close.rolling(int(period/2)).mean()
        sma_long = close.rolling(period).mean()
        ma_trend = ((sma_short - sma_long) / sma_long) * 100
        
        # ATR趋势强度
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        atr = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1).rolling(period).mean()
        atr_ratio = atr / close * 100
        
        # 趋势连续性
        up_days = (close > close.shift(1)).rolling(period).sum()
        trend_consistency = (up_days / period - 0.5) * 200
        
        # TTS综合评分
        tts = (price_position * 0.3 + 
               ma_trend.clip(-50, 50) + 50) * 0.3 + \
              (100 - atr_ratio.clip(0, 100)) * 0.2 + \
              trend_consistency * 0.2
        
        return tts
    
    @staticmethod
    def tiger_volatility_ratio(high: pd.Series, low: pd.Series, close: pd.Series,
                              short_period: int = 7, long_period: int = 30) -> pd.Series:
        """Tiger波动率比率 TVR - 短期vs长期波动率"""
        # 历史波动率
        returns = np.log(close / close.shift(1))
        vol_short = returns.rolling(short_period).std() * np.sqrt(365)
        vol_long = returns.rolling(long_period).std() * np.sqrt(365)
        
        # Parkinson波动率
        log_hl = np.log(high / low)
        park_vol_short = log_hl.rolling(short_period).mean() * np.sqrt(365/1.67)
        park_vol_long = log_hl.rolling(long_period).mean() * np.sqrt(365/1.67)
        
        # 综合波动率比率
        tvr = ((vol_short / vol_long) * 0.5 + 
               (park_vol_short / park_vol_long) * 0.5) * 100
        
        return tvr
    
    @staticmethod
    def tiger_money_flow(high: pd.Series, low: pd.Series, close: pd.Series, 
                        volume: pd.Series, period: int = 20) -> pd.Series:
        """Tiger资金流 TMF - 智能资金流向分析"""
        # 智能资金指标
        typical_price = (high + low + close) / 3
        
        # 计算资金流强度
        mf_raw = ((close - low) - (high - close)) / (high - low)
        mf_volume = mf_raw * volume * typical_price
        
        # 分离大单小单
        volume_ma = volume.rolling(period).mean()
        large_volume = volume > volume_ma * 1.5
        
        # 大单资金流
        large_mf = mf_volume.where(large_volume, 0)
        small_mf = mf_volume.where(~large_volume, 0)
        
        # TMF计算
        tmf = (large_mf.rolling(period).sum() - small_mf.rolling(period).sum()) / \
              (volume.rolling(period).sum() * typical_price.rolling(period).mean())
        
        return tmf * 100
    
    # ============= 多指标组合信号 =============
    
    @staticmethod
    def rsi_macd_combo(close: pd.Series, rsi_period: int = 14,
                      macd_fast: int = 12, macd_slow: int = 26, 
                      macd_signal: int = 9) -> pd.DataFrame:
        """RSI + MACD组合信号"""
        # RSI计算
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = -delta.where(delta < 0, 0).rolling(rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD计算
        ema_fast = close.ewm(span=macd_fast, adjust=False).mean()
        ema_slow = close.ewm(span=macd_slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=macd_signal, adjust=False).mean()
        
        # 组合信号
        combo_signal = pd.Series(index=close.index, dtype='int')
        
        # 强买入：RSI超卖 + MACD金叉
        combo_signal[(rsi < 30) & (macd > signal) & (macd.shift(1) <= signal.shift(1))] = 2
        
        # 买入：RSI < 50 + MACD上升
        combo_signal[(rsi < 50) & (macd > macd.shift(1))] = 1
        
        # 强卖出：RSI超买 + MACD死叉
        combo_signal[(rsi > 70) & (macd < signal) & (macd.shift(1) >= signal.shift(1))] = -2
        
        # 卖出：RSI > 50 + MACD下降
        combo_signal[(rsi > 50) & (macd < macd.shift(1))] = -1
        
        return pd.DataFrame({
            'rsi': rsi,
            'macd': macd,
            'signal': signal,
            'combo_signal': combo_signal
        })
    
    @staticmethod
    def bb_rsi_squeeze(close: pd.Series, bb_period: int = 20, bb_std: float = 2.0,
                      rsi_period: int = 14, kc_period: int = 20, kc_mult: float = 1.5) -> pd.DataFrame:
        """布林带 + RSI挤压信号"""
        # 布林带
        bb_middle = close.rolling(bb_period).mean()
        bb_std_val = close.rolling(bb_period).std()
        bb_upper = bb_middle + bb_std * bb_std_val
        bb_lower = bb_middle - bb_std * bb_std_val
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = -delta.where(delta < 0, 0).rolling(rsi_period).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        
        # 肯特纳通道（用于挤压检测）
        tr = pd.Series(index=close.index, dtype='float64')
        for i in range(1, len(close)):
            tr.iloc[i] = max(close.iloc[i] - close.iloc[i-1], 
                            abs(close.iloc[i] - close.iloc[i-1]))
        atr = tr.rolling(kc_period).mean()
        kc_upper = bb_middle + kc_mult * atr
        kc_lower = bb_middle - kc_mult * atr
        
        # 挤压检测
        squeeze = (bb_upper < kc_upper) & (bb_lower > kc_lower)
        
        # 信号生成
        signal = pd.Series(index=close.index, dtype='int')
        signal[squeeze & (rsi < 30)] = 1  # 挤压 + 超卖 = 买入
        signal[squeeze & (rsi > 70)] = -1  # 挤压 + 超买 = 卖出
        signal[~squeeze & (close > bb_upper)] = -1  # 突破上轨 = 卖出
        signal[~squeeze & (close < bb_lower)] = 1  # 突破下轨 = 买入
        
        return pd.DataFrame({
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'rsi': rsi,
            'squeeze': squeeze.astype(int),
            'signal': signal
        })
    
    @staticmethod
    def volume_price_momentum(close: pd.Series, volume: pd.Series, 
                            price_period: int = 20, volume_period: int = 20) -> pd.Series:
        """量价动量信号"""
        # 价格动量
        price_roc = (close - close.shift(price_period)) / close.shift(price_period) * 100
        
        # 成交量动量
        volume_ma = volume.rolling(volume_period).mean()
        volume_ratio = volume / volume_ma
        
        # OBV动量
        obv = pd.Series(index=close.index, dtype='float64')
        obv.iloc[0] = volume.iloc[0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        obv_ma = obv.rolling(volume_period).mean()
        obv_momentum = (obv - obv_ma) / obv_ma * 100
        
        # 综合量价动量
        vp_momentum = (price_roc * 0.5 + 
                      (volume_ratio - 1) * 100 * 0.25 + 
                      obv_momentum * 0.25)
        
        return vp_momentum
    
    @staticmethod
    def multi_timeframe_resonance(close_1m: pd.Series, close_5m: pd.Series,
                                 close_15m: pd.Series, close_1h: pd.Series) -> pd.DataFrame:
        """多时间框架共振信号"""
        results = {}
        
        for tf_name, tf_data in [('1m', close_1m), ('5m', close_5m), 
                                ('15m', close_15m), ('1h', close_1h)]:
            # 计算各时间框架的趋势
            sma_short = tf_data.rolling(20).mean()
            sma_long = tf_data.rolling(50).mean()
            
            trend = pd.Series(index=tf_data.index, dtype='int')
            trend[sma_short > sma_long] = 1
            trend[sma_short < sma_long] = -1
            
            results[f'{tf_name}_trend'] = trend
        
        # 计算共振强度
        resonance = pd.DataFrame(results)
        resonance['total'] = resonance.sum(axis=1)
        resonance['signal'] = 0
        resonance.loc[resonance['total'] >= 3, 'signal'] = 1  # 强买入
        resonance.loc[resonance['total'] <= -3, 'signal'] = -1  # 强卖出
        
        return resonance
    
    # ============= 市场情绪指标 =============
    
    @staticmethod
    def fear_greed_index(close: pd.Series, volume: pd.Series, high: pd.Series, 
                        low: pd.Series, period: int = 20) -> pd.Series:
        """恐惧贪婪指数"""
        components = []
        
        # 1. 价格动量
        momentum = (close - close.shift(period)) / close.shift(period)
        components.append((momentum + 0.5).clip(0, 1))
        
        # 2. 市场波动率（反向）
        returns = close.pct_change()
        volatility = returns.rolling(period).std()
        vol_percentile = volatility.rolling(100).rank(pct=True)
        components.append(1 - vol_percentile)
        
        # 3. 市场宽度（成交量）
        volume_ma = volume.rolling(period).mean()
        volume_ratio = volume / volume_ma
        components.append(volume_ratio.rolling(period).mean().clip(0, 2) / 2)
        
        # 4. 高低点距离
        high_low_ratio = (close - low.rolling(period).min()) / \
                        (high.rolling(period).max() - low.rolling(period).min())
        components.append(high_low_ratio)
        
        # 5. Put/Call比率模拟（使用波动率偏斜）
        up_moves = returns.where(returns > 0, 0).rolling(period).std()
        down_moves = -returns.where(returns < 0, 0).rolling(period).std()
        skew = up_moves / down_moves
        components.append(skew.clip(0.5, 1.5) / 1.5)
        
        # 综合计算
        fgi = pd.concat(components, axis=1).mean(axis=1) * 100
        
        return fgi
    
    @staticmethod
    def market_sentiment_score(close: pd.Series, volume: pd.Series, 
                             period: int = 20) -> pd.Series:
        """市场情绪评分"""
        # 价格强度
        price_strength = (close - close.rolling(period).min()) / \
                        (close.rolling(period).max() - close.rolling(period).min())
        
        # 成交量强度
        volume_strength = volume / volume.rolling(period * 2).mean()
        
        # 趋势强度
        sma = close.rolling(period).mean()
        trend_strength = (close - sma) / sma
        
        # 动量强度
        momentum = close.pct_change(period)
        
        # 综合情绪分数
        sentiment = (price_strength * 0.3 + 
                    volume_strength.clip(0, 2) / 2 * 0.2 + 
                    (trend_strength + 0.1).clip(-0.2, 0.2) / 0.4 + 0.5) * 0.25 + \
                   (momentum + 0.5).clip(0, 1) * 0.25
        
        return sentiment * 100
    
    @staticmethod
    def whale_activity_index(volume: pd.Series, close: pd.Series, 
                           threshold_multiplier: float = 2.5) -> pd.Series:
        """鲸鱼活动指数"""
        volume_ma = volume.rolling(100).mean()
        volume_std = volume.rolling(100).std()
        
        # 识别异常大单
        whale_threshold = volume_ma + threshold_multiplier * volume_std
        whale_volume = volume.where(volume > whale_threshold, 0)
        
        # 计算鲸鱼活动强度
        whale_ratio = whale_volume / volume.rolling(20).sum()
        
        # 价格影响
        price_change = close.pct_change()
        whale_impact = pd.Series(index=close.index, dtype='float64')
        
        for i in range(1, len(close)):
            if whale_volume.iloc[i] > 0:
                whale_impact.iloc[i] = abs(price_change.iloc[i]) * whale_ratio.iloc[i]
            else:
                whale_impact.iloc[i] = 0
        
        # 鲸鱼活动指数
        wai = whale_impact.rolling(20).sum() * 1000
        
        return wai
    
    @staticmethod
    def retail_fomo_index(close: pd.Series, volume: pd.Series, 
                         period: int = 10) -> pd.Series:
        """散户FOMO指数"""
        # 价格加速度
        returns = close.pct_change()
        acceleration = returns - returns.shift(1)
        
        # 成交量激增
        volume_surge = volume / volume.rolling(period * 2).mean()
        
        # 价格偏离
        sma = close.rolling(period * 2).mean()
        price_deviation = (close - sma) / sma
        
        # 连续上涨天数
        up_days = pd.Series(index=close.index, dtype='int')
        up_days.iloc[0] = 0
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                up_days.iloc[i] = up_days.iloc[i-1] + 1
            else:
                up_days.iloc[i] = 0
        
        # FOMO指数计算
        fomo = (acceleration * 100 * 0.3 + 
               (volume_surge - 1).clip(0, 2) * 0.3 + 
               price_deviation.clip(0, 0.2) * 5 * 0.2 + 
               (up_days / period).clip(0, 1) * 0.2) * 100
        
        return fomo
    
    # ============= 高级组合指标 =============
    
    @staticmethod
    def smart_money_flow(high: pd.Series, low: pd.Series, close: pd.Series, 
                        volume: pd.Series, period: int = 20) -> pd.Series:
        """智能资金流"""
        # 开盘30分钟和收盘30分钟的识别（简化版）
        # 实际应用需要真实的时间戳数据
        
        typical_price = (high + low + close) / 3
        
        # 计算资金流
        mf = typical_price * volume
        
        # 识别智能资金（大单）
        volume_percentile = volume.rolling(period * 5).rank(pct=True)
        smart_money = mf.where(volume_percentile > 0.8, 0)
        dumb_money = mf.where(volume_percentile <= 0.8, 0)
        
        # 智能资金流指标
        smf = (smart_money.rolling(period).sum() - dumb_money.rolling(period).sum()) / \
              mf.rolling(period).sum()
        
        return smf * 100
    
    @staticmethod
    def composite_momentum_oscillator(close: pd.Series, volume: pd.Series, 
                                    periods: List[int] = [5, 10, 20, 40]) -> pd.Series:
        """复合动量振荡器"""
        momentums = []
        
        for period in periods:
            # 价格动量
            price_mom = (close - close.shift(period)) / close.shift(period)
            
            # 成交量动量
            vol_mom = (volume.rolling(period).mean() - volume.rolling(period * 2).mean()) / \
                     volume.rolling(period * 2).mean()
            
            # 加权动量
            weighted_mom = price_mom * 0.7 + vol_mom * 0.3
            momentums.append(weighted_mom)
        
        # 综合所有周期的动量
        composite = pd.concat(momentums, axis=1).mean(axis=1) * 100
        
        return composite
    
    @staticmethod
    def adaptive_bands(close: pd.Series, period: int = 20, 
                      volatility_period: int = 100) -> pd.DataFrame:
        """自适应通道"""
        # 计算中线
        middle = close.ewm(span=period, adjust=False).mean()
        
        # 计算自适应标准差
        returns = close.pct_change()
        volatility = returns.rolling(period).std()
        
        # 计算波动率百分位
        vol_percentile = volatility.rolling(volatility_period).rank(pct=True)
        
        # 自适应乘数（波动率高时扩大，低时收窄）
        multiplier = 1 + vol_percentile * 2  # 1到3之间
        
        # 计算上下轨
        atr = pd.Series(index=close.index, dtype='float64')
        for i in range(1, len(close)):
            atr.iloc[i] = abs(close.iloc[i] - close.iloc[i-1])
        
        atr_ma = atr.rolling(period).mean()
        
        upper = middle + multiplier * atr_ma
        lower = middle - multiplier * atr_ma
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': upper - lower,
            'multiplier': multiplier
        })
    
    @staticmethod
    def regime_detection(close: pd.Series, lookback: int = 100) -> pd.Series:
        """市场状态检测"""
        returns = close.pct_change()
        
        # 计算各种市场特征
        volatility = returns.rolling(20).std()
        trend = close.rolling(50).mean() - close.rolling(200).mean()
        momentum = close.pct_change(20)
        
        # 定义市场状态
        regime = pd.Series(index=close.index, dtype='str')
        
        for i in range(lookback, len(close)):
            vol_percentile = volatility.iloc[i] > volatility.iloc[i-lookback:i].quantile(0.75)
            trend_up = trend.iloc[i] > 0
            trend_down = trend.iloc[i] < 0
            high_momentum = abs(momentum.iloc[i]) > momentum.iloc[i-lookback:i].std() * 2
            
            if trend_up and not vol_percentile:
                regime.iloc[i] = 'bull_quiet'  # 平静牛市
            elif trend_up and vol_percentile:
                regime.iloc[i] = 'bull_volatile'  # 波动牛市
            elif trend_down and not vol_percentile:
                regime.iloc[i] = 'bear_quiet'  # 平静熊市
            elif trend_down and vol_percentile:
                regime.iloc[i] = 'bear_volatile'  # 波动熊市
            elif high_momentum:
                regime.iloc[i] = 'breakout'  # 突破
            else:
                regime.iloc[i] = 'ranging'  # 震荡
        
        return regime


def calculate_all_custom_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有自定义指标"""
    indicators = CustomIndicators()
    result = df.copy()
    
    # Tiger专属指标
    if 'volume' in df.columns:
        result['TMI'] = indicators.tiger_momentum_index(df['close'], df['volume'])
        result['TMF'] = indicators.tiger_money_flow(df['high'], df['low'], df['close'], df['volume'])
    
    result['TTS'] = indicators.tiger_trend_score(df['high'], df['low'], df['close'])
    result['TVR'] = indicators.tiger_volatility_ratio(df['high'], df['low'], df['close'])
    
    # 组合信号
    rsi_macd = indicators.rsi_macd_combo(df['close'])
    result['RSI_MACD_Signal'] = rsi_macd['combo_signal']
    
    bb_rsi = indicators.bb_rsi_squeeze(df['close'])
    result['BB_RSI_Squeeze'] = bb_rsi['squeeze']
    result['BB_RSI_Signal'] = bb_rsi['signal']
    
    if 'volume' in df.columns:
        result['VP_Momentum'] = indicators.volume_price_momentum(df['close'], df['volume'])
    
    # 市场情绪
    if 'volume' in df.columns:
        result['Fear_Greed'] = indicators.fear_greed_index(df['close'], df['volume'], 
                                                          df['high'], df['low'])
        result['Sentiment'] = indicators.market_sentiment_score(df['close'], df['volume'])
        result['Whale_Activity'] = indicators.whale_activity_index(df['volume'], df['close'])
        result['FOMO'] = indicators.retail_fomo_index(df['close'], df['volume'])
    
    # 高级指标
    if 'volume' in df.columns:
        result['Smart_Money'] = indicators.smart_money_flow(df['high'], df['low'], 
                                                           df['close'], df['volume'])
        result['Composite_Momentum'] = indicators.composite_momentum_oscillator(df['close'], df['volume'])
    
    adaptive = indicators.adaptive_bands(df['close'])
    result['Adaptive_Upper'] = adaptive['upper']
    result['Adaptive_Lower'] = adaptive['lower']
    result['Adaptive_Bandwidth'] = adaptive['bandwidth']
    
    result['Market_Regime'] = indicators.regime_detection(df['close'])
    
    return result