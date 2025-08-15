"""
Tiger System - Market Structure Indicators Module  
Window 4: Technical Analysis Engine
20+ Market Structure Indicators Implementation
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional, List


class StructureIndicators:
    """市场结构类技术指标实现"""
    
    def __init__(self):
        self.name = "StructureIndicators"
    
    # ============= Support & Resistance =============
    
    @staticmethod
    def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series, 
                    method: str = 'standard') -> pd.DataFrame:
        """枢轴点 Pivot Points"""
        if method == 'standard':
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
            
        elif method == 'fibonacci':
            pivot = (high + low + close) / 3
            range_hl = high - low
            r1 = pivot + 0.382 * range_hl
            s1 = pivot - 0.382 * range_hl
            r2 = pivot + 0.618 * range_hl
            s2 = pivot - 0.618 * range_hl
            r3 = pivot + 1.000 * range_hl
            s3 = pivot - 1.000 * range_hl
            
        elif method == 'camarilla':
            pivot = (high + low + close) / 3
            range_hl = high - low
            r1 = close + range_hl * 1.1 / 12
            s1 = close - range_hl * 1.1 / 12
            r2 = close + range_hl * 1.1 / 6
            s2 = close - range_hl * 1.1 / 6
            r3 = close + range_hl * 1.1 / 4
            s3 = close - range_hl * 1.1 / 4
            
        elif method == 'woodie':
            pivot = (high + low + 2 * close) / 4
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + high - low
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
        
        else:  # DeMark
            x = pd.Series(index=high.index, dtype='float64')
            for i in range(len(close)):
                if i == 0:
                    x.iloc[i] = (high.iloc[i] + low.iloc[i] + close.iloc[i]) / 3
                else:
                    if close.iloc[i-1] < open.iloc[i-1] if 'open' in locals() else close.iloc[i-1]:
                        x.iloc[i] = high.iloc[i] + 2 * low.iloc[i] + close.iloc[i]
                    elif close.iloc[i-1] > open.iloc[i-1] if 'open' in locals() else close.iloc[i-1]:
                        x.iloc[i] = 2 * high.iloc[i] + low.iloc[i] + close.iloc[i]
                    else:
                        x.iloc[i] = high.iloc[i] + low.iloc[i] + 2 * close.iloc[i]
            
            pivot = x / 4
            r1 = x / 2 - low
            s1 = x / 2 - high
            r2 = pivot + (r1 - s1)
            s2 = pivot - (r1 - s1)
            r3 = r1 + (high - low)
            s3 = s1 - (high - low)
        
        return pd.DataFrame({
            'pivot': pivot,
            'r1': r1, 's1': s1,
            'r2': r2, 's2': s2,
            'r3': r3, 's3': s3
        })
    
    @staticmethod
    def support_resistance_levels(high: pd.Series, low: pd.Series, close: pd.Series,
                                 lookback: int = 50, min_touches: int = 2) -> pd.DataFrame:
        """支撑阻力位 Support/Resistance Levels"""
        levels = []
        
        for i in range(lookback, len(close)):
            window_high = high.iloc[i-lookback:i]
            window_low = low.iloc[i-lookback:i]
            window_close = close.iloc[i-lookback:i]
            
            # 找局部高点作为阻力
            for j in range(1, len(window_high)-1):
                if window_high.iloc[j] > window_high.iloc[j-1] and window_high.iloc[j] > window_high.iloc[j+1]:
                    level = window_high.iloc[j]
                    touches = ((abs(window_high - level) < level * 0.002) | 
                              (abs(window_close - level) < level * 0.002)).sum()
                    if touches >= min_touches:
                        levels.append({
                            'index': i,
                            'level': level,
                            'type': 'resistance',
                            'touches': touches,
                            'strength': touches / lookback
                        })
            
            # 找局部低点作为支撑
            for j in range(1, len(window_low)-1):
                if window_low.iloc[j] < window_low.iloc[j-1] and window_low.iloc[j] < window_low.iloc[j+1]:
                    level = window_low.iloc[j]
                    touches = ((abs(window_low - level) < level * 0.002) | 
                              (abs(window_close - level) < level * 0.002)).sum()
                    if touches >= min_touches:
                        levels.append({
                            'index': i,
                            'level': level,
                            'type': 'support',
                            'touches': touches,
                            'strength': touches / lookback
                        })
        
        return pd.DataFrame(levels) if levels else pd.DataFrame()
    
    @staticmethod
    def dynamic_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series,
                                  period: int = 20) -> pd.DataFrame:
        """动态支撑阻力 Dynamic Support/Resistance"""
        # 使用移动平均作为动态支撑/阻力
        sma = close.rolling(period).mean()
        ema = close.ewm(span=period, adjust=False).mean()
        
        # 动态通道
        std = close.rolling(period).std()
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        
        # ATR动态支撑/阻力
        tr = pd.DataFrame()
        tr['h-l'] = high - low
        tr['h-pc'] = abs(high - close.shift(1))
        tr['l-pc'] = abs(low - close.shift(1))
        atr = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1).rolling(period).mean()
        
        dynamic_resistance = close.rolling(period).max() - 0.5 * atr
        dynamic_support = close.rolling(period).min() + 0.5 * atr
        
        return pd.DataFrame({
            'sma_level': sma,
            'ema_level': ema,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'dynamic_resistance': dynamic_resistance,
            'dynamic_support': dynamic_support
        })
    
    # ============= Market Depth =============
    
    @staticmethod
    def market_profile(high: pd.Series, low: pd.Series, close: pd.Series, 
                      volume: pd.Series, bins: int = 30) -> pd.DataFrame:
        """市场轮廓 Market Profile"""
        # 计算TPO (Time Price Opportunity)
        price_range = pd.Series(index=close.index, dtype='float64')
        tpo_count = {}
        
        for i in range(len(close)):
            day_range = np.linspace(low.iloc[i], high.iloc[i], bins)
            for price in day_range:
                if price not in tpo_count:
                    tpo_count[price] = 0
                tpo_count[price] += 1
        
        # 价值区域计算
        tpo_df = pd.DataFrame(list(tpo_count.items()), columns=['price', 'tpo'])
        tpo_df = tpo_df.sort_values('tpo', ascending=False)
        
        total_tpo = tpo_df['tpo'].sum()
        value_area_tpo = total_tpo * 0.7
        
        cumulative_tpo = 0
        value_area_prices = []
        
        for _, row in tpo_df.iterrows():
            cumulative_tpo += row['tpo']
            value_area_prices.append(row['price'])
            if cumulative_tpo >= value_area_tpo:
                break
        
        poc = tpo_df.iloc[0]['price']  # Point of Control
        vah = max(value_area_prices)  # Value Area High
        val = min(value_area_prices)  # Value Area Low
        
        return pd.DataFrame({
            'poc': [poc],
            'vah': [vah],
            'val': [val],
            'value_area_volume': [value_area_tpo],
            'total_volume': [total_tpo]
        })
    
    @staticmethod
    def order_flow_imbalance(bid_volume: pd.Series, ask_volume: pd.Series, 
                            period: int = 20) -> pd.Series:
        """订单流失衡 Order Flow Imbalance"""
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        smoothed_imbalance = imbalance.rolling(period).mean()
        return smoothed_imbalance
    
    @staticmethod
    def cumulative_delta(bid_volume: pd.Series, ask_volume: pd.Series) -> pd.Series:
        """累积Delta Cumulative Delta"""
        delta = bid_volume - ask_volume
        cumulative_delta = delta.cumsum()
        return cumulative_delta
    
    # ============= Microstructure =============
    
    @staticmethod
    def bid_ask_spread(bid: pd.Series, ask: pd.Series, mid_price: Optional[pd.Series] = None) -> pd.DataFrame:
        """买卖价差 Bid-Ask Spread"""
        spread = ask - bid
        
        if mid_price is None:
            mid_price = (bid + ask) / 2
        
        spread_percentage = (spread / mid_price) * 100
        
        return pd.DataFrame({
            'spread': spread,
            'spread_pct': spread_percentage,
            'mid_price': mid_price
        })
    
    @staticmethod
    def order_book_imbalance(bid_sizes: List[float], ask_sizes: List[float], 
                           levels: int = 5) -> float:
        """订单簿失衡 Order Book Imbalance"""
        bid_volume = sum(bid_sizes[:levels])
        ask_volume = sum(ask_sizes[:levels])
        
        if bid_volume + ask_volume == 0:
            return 0
        
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        return imbalance
    
    @staticmethod
    def trade_size_distribution(trade_sizes: pd.Series, bins: int = 10) -> pd.DataFrame:
        """交易规模分布 Trade Size Distribution"""
        size_bins = pd.qcut(trade_sizes, q=bins, duplicates='drop')
        distribution = trade_sizes.groupby(size_bins).agg(['count', 'sum', 'mean'])
        
        distribution['percentage'] = distribution['count'] / distribution['count'].sum() * 100
        distribution['volume_percentage'] = distribution['sum'] / distribution['sum'].sum() * 100
        
        return distribution
    
    # ============= Market Breadth =============
    
    @staticmethod
    def advance_decline_line(advances: pd.Series, declines: pd.Series) -> pd.Series:
        """涨跌线 Advance/Decline Line"""
        net_advances = advances - declines
        adl = net_advances.cumsum()
        return adl
    
    @staticmethod
    def mcclellan_oscillator(advances: pd.Series, declines: pd.Series,
                           fast: int = 19, slow: int = 39) -> pd.DataFrame:
        """麦克莱伦振荡器 McClellan Oscillator"""
        net_advances = advances - declines
        ratio = net_advances / (advances + declines)
        
        ema_fast = ratio.ewm(span=fast, adjust=False).mean()
        ema_slow = ratio.ewm(span=slow, adjust=False).mean()
        
        oscillator = (ema_fast - ema_slow) * 1000
        summation = oscillator.cumsum()
        
        return pd.DataFrame({
            'oscillator': oscillator,
            'summation': summation
        })
    
    @staticmethod
    def arms_index(advancing_volume: pd.Series, declining_volume: pd.Series,
                  advancing_issues: pd.Series, declining_issues: pd.Series) -> pd.Series:
        """阿姆斯指数 Arms Index (TRIN)"""
        ad_ratio = advancing_issues / declining_issues
        volume_ratio = advancing_volume / declining_volume
        
        trin = ad_ratio / volume_ratio
        return trin
    
    # ============= Market Sentiment =============
    
    @staticmethod
    def put_call_ratio(put_volume: pd.Series, call_volume: pd.Series, 
                      period: int = 20) -> pd.DataFrame:
        """看跌看涨比率 Put/Call Ratio"""
        pcr = put_volume / call_volume
        pcr_ma = pcr.rolling(period).mean()
        
        # 极端值信号
        pcr_std = pcr.rolling(period).std()
        upper_extreme = pcr_ma + 2 * pcr_std
        lower_extreme = pcr_ma - 2 * pcr_std
        
        return pd.DataFrame({
            'pcr': pcr,
            'pcr_ma': pcr_ma,
            'upper_extreme': upper_extreme,
            'lower_extreme': lower_extreme
        })
    
    @staticmethod
    def vix_calculation(option_prices: pd.DataFrame, strike_prices: List[float],
                       risk_free_rate: float = 0.02, time_to_expiry: float = 30/365) -> float:
        """VIX计算（简化版）"""
        # 这是一个简化的VIX计算
        # 实际VIX计算更复杂，需要期权链数据
        
        implied_volatilities = []
        
        for strike in strike_prices:
            if strike in option_prices.columns:
                # 使用Black-Scholes反推隐含波动率（简化）
                iv = option_prices[strike].std() * np.sqrt(252)
                implied_volatilities.append(iv)
        
        if implied_volatilities:
            vix = np.mean(implied_volatilities) * 100
        else:
            vix = 0
        
        return vix
    
    # ============= Liquidity Indicators =============
    
    @staticmethod
    def amihud_illiquidity(returns: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """Amihud非流动性指标"""
        abs_returns = returns.abs()
        illiquidity = (abs_returns / volume).rolling(period).mean() * 1e6
        return illiquidity
    
    @staticmethod
    def roll_spread(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Roll价差估计"""
        price_change = close.diff()
        cov = price_change.rolling(20).cov(price_change.shift(1))
        
        roll_spread = 2 * np.sqrt(-cov)
        roll_spread[cov >= 0] = 0  # 协方差为正时无法计算
        
        return roll_spread
    
    @staticmethod
    def kyle_lambda(price_change: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """Kyle's Lambda（价格影响系数）"""
        # 使用滚动回归计算价格影响
        lambda_values = pd.Series(index=price_change.index, dtype='float64')
        
        for i in range(period, len(price_change)):
            window_price = price_change.iloc[i-period:i]
            window_volume = volume.iloc[i-period:i]
            
            if window_volume.std() > 0:
                coef = np.cov(window_price, window_volume)[0, 1] / np.var(window_volume)
                lambda_values.iloc[i] = abs(coef)
        
        return lambda_values


def calculate_all_structure_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有市场结构指标"""
    indicators = StructureIndicators()
    result = df.copy()
    
    # 枢轴点
    for method in ['standard', 'fibonacci', 'camarilla', 'woodie']:
        pivots = indicators.pivot_points(df['high'], df['low'], df['close'], method)
        for col in pivots.columns:
            result[f'{method}_{col}'] = pivots[col]
    
    # 支撑阻力
    sr_levels = indicators.support_resistance_levels(df['high'], df['low'], df['close'])
    if not sr_levels.empty:
        result['support_count'] = sr_levels[sr_levels['type'] == 'support'].groupby('index')['level'].count()
        result['resistance_count'] = sr_levels[sr_levels['type'] == 'resistance'].groupby('index')['level'].count()
    
    dynamic_sr = indicators.dynamic_support_resistance(df['high'], df['low'], df['close'])
    for col in dynamic_sr.columns:
        result[f'dynamic_{col}'] = dynamic_sr[col]
    
    # 市场深度（如果有成交量数据）
    if 'volume' in df.columns:
        market_prof = indicators.market_profile(df['high'], df['low'], df['close'], df['volume'])
        if not market_prof.empty:
            result['market_poc'] = market_prof['poc'].iloc[0]
            result['market_vah'] = market_prof['vah'].iloc[0]
            result['market_val'] = market_prof['val'].iloc[0]
    
    # 流动性指标
    if 'volume' in df.columns:
        returns = df['close'].pct_change()
        result['amihud_illiquidity'] = indicators.amihud_illiquidity(returns, df['volume'])
        result['roll_spread'] = indicators.roll_spread(df['high'], df['low'], df['close'])
        result['kyle_lambda'] = indicators.kyle_lambda(df['close'].diff(), df['volume'])
    
    return result