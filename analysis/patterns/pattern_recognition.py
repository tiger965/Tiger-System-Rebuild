"""
Tiger System - Pattern Recognition Module
Window 4: Technical Analysis Engine
K线形态和价格形态识别
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


class PatternRecognition:
    """形态识别系统"""
    
    def __init__(self):
        self.name = "PatternRecognition"
    
    # ============= 反转形态 =============
    
    @staticmethod
    def head_shoulders(high: pd.Series, low: pd.Series, close: pd.Series, 
                       window: int = 20, min_pattern_bars: int = 5) -> pd.DataFrame:
        """头肩顶/头肩底识别"""
        patterns = []
        
        for i in range(window, len(close) - window):
            # 找局部高点和低点
            window_high = high.iloc[i-window:i+window]
            window_low = low.iloc[i-window:i+window]
            
            # 头肩顶检测
            peaks = []
            for j in range(1, len(window_high)-1):
                if window_high.iloc[j] > window_high.iloc[j-1] and window_high.iloc[j] > window_high.iloc[j+1]:
                    peaks.append((j, window_high.iloc[j]))
            
            if len(peaks) >= 3:
                # 检查是否形成头肩顶
                left_shoulder = peaks[0][1]
                head = max(peaks, key=lambda x: x[1])[1]
                right_shoulder = peaks[-1][1]
                
                if head > left_shoulder and head > right_shoulder:
                    if abs(left_shoulder - right_shoulder) / head < 0.05:  # 肩部高度相近
                        patterns.append({
                            'index': i,
                            'type': 'head_shoulders_top',
                            'head_price': head,
                            'neckline': min(window_low.iloc[peaks[0][0]:peaks[-1][0]])
                        })
            
            # 头肩底检测
            troughs = []
            for j in range(1, len(window_low)-1):
                if window_low.iloc[j] < window_low.iloc[j-1] and window_low.iloc[j] < window_low.iloc[j+1]:
                    troughs.append((j, window_low.iloc[j]))
            
            if len(troughs) >= 3:
                # 检查是否形成头肩底
                left_shoulder = troughs[0][1]
                head = min(troughs, key=lambda x: x[1])[1]
                right_shoulder = troughs[-1][1]
                
                if head < left_shoulder and head < right_shoulder:
                    if abs(left_shoulder - right_shoulder) / abs(head) < 0.05:
                        patterns.append({
                            'index': i,
                            'type': 'head_shoulders_bottom',
                            'head_price': head,
                            'neckline': max(window_high.iloc[troughs[0][0]:troughs[-1][0]])
                        })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def double_top_bottom(high: pd.Series, low: pd.Series, close: pd.Series,
                         window: int = 20, tolerance: float = 0.02) -> pd.DataFrame:
        """双顶/双底识别"""
        patterns = []
        
        for i in range(window, len(close) - window):
            window_high = high.iloc[i-window:i+window]
            window_low = low.iloc[i-window:i+window]
            
            # 双顶检测
            peaks = []
            for j in range(2, len(window_high)-2):
                if (window_high.iloc[j] > window_high.iloc[j-1] and 
                    window_high.iloc[j] > window_high.iloc[j+1] and
                    window_high.iloc[j] > window_high.iloc[j-2] and
                    window_high.iloc[j] > window_high.iloc[j+2]):
                    peaks.append((j, window_high.iloc[j]))
            
            if len(peaks) >= 2:
                first_peak = peaks[0][1]
                second_peak = peaks[-1][1]
                
                if abs(first_peak - second_peak) / max(first_peak, second_peak) < tolerance:
                    valley = min(window_low.iloc[peaks[0][0]:peaks[-1][0]])
                    patterns.append({
                        'index': i,
                        'type': 'double_top',
                        'first_peak': first_peak,
                        'second_peak': second_peak,
                        'valley': valley,
                        'target': valley - (max(first_peak, second_peak) - valley)
                    })
            
            # 双底检测
            troughs = []
            for j in range(2, len(window_low)-2):
                if (window_low.iloc[j] < window_low.iloc[j-1] and 
                    window_low.iloc[j] < window_low.iloc[j+1] and
                    window_low.iloc[j] < window_low.iloc[j-2] and
                    window_low.iloc[j] < window_low.iloc[j+2]):
                    troughs.append((j, window_low.iloc[j]))
            
            if len(troughs) >= 2:
                first_trough = troughs[0][1]
                second_trough = troughs[-1][1]
                
                if abs(first_trough - second_trough) / min(first_trough, second_trough) < tolerance:
                    peak = max(window_high.iloc[troughs[0][0]:troughs[-1][0]])
                    patterns.append({
                        'index': i,
                        'type': 'double_bottom',
                        'first_trough': first_trough,
                        'second_trough': second_trough,
                        'peak': peak,
                        'target': peak + (peak - min(first_trough, second_trough))
                    })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def triple_top_bottom(high: pd.Series, low: pd.Series, close: pd.Series,
                         window: int = 30, tolerance: float = 0.03) -> pd.DataFrame:
        """三重顶/三重底识别"""
        patterns = []
        
        for i in range(window, len(close) - window):
            window_high = high.iloc[i-window:i+window]
            window_low = low.iloc[i-window:i+window]
            
            # 三重顶检测
            peaks = []
            for j in range(2, len(window_high)-2):
                if (window_high.iloc[j] > window_high.iloc[j-1] and 
                    window_high.iloc[j] > window_high.iloc[j+1]):
                    peaks.append((j, window_high.iloc[j]))
            
            if len(peaks) >= 3:
                peak_values = [p[1] for p in peaks[-3:]]
                avg_peak = np.mean(peak_values)
                
                if all(abs(p - avg_peak) / avg_peak < tolerance for p in peak_values):
                    support = min(window_low.iloc[peaks[-3][0]:peaks[-1][0]])
                    patterns.append({
                        'index': i,
                        'type': 'triple_top',
                        'peaks': peak_values,
                        'support': support,
                        'target': support - (avg_peak - support)
                    })
            
            # 三重底检测
            troughs = []
            for j in range(2, len(window_low)-2):
                if (window_low.iloc[j] < window_low.iloc[j-1] and 
                    window_low.iloc[j] < window_low.iloc[j+1]):
                    troughs.append((j, window_low.iloc[j]))
            
            if len(troughs) >= 3:
                trough_values = [t[1] for t in troughs[-3:]]
                avg_trough = np.mean(trough_values)
                
                if all(abs(t - avg_trough) / avg_trough < tolerance for t in trough_values):
                    resistance = max(window_high.iloc[troughs[-3][0]:troughs[-1][0]])
                    patterns.append({
                        'index': i,
                        'type': 'triple_bottom',
                        'troughs': trough_values,
                        'resistance': resistance,
                        'target': resistance + (resistance - avg_trough)
                    })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def rounding_patterns(high: pd.Series, low: pd.Series, close: pd.Series,
                         window: int = 30) -> pd.DataFrame:
        """圆弧顶/圆弧底识别"""
        patterns = []
        
        for i in range(window, len(close) - window):
            window_close = close.iloc[i-window:i+window]
            window_high = high.iloc[i-window:i+window]
            window_low = low.iloc[i-window:i+window]
            
            # 计算二阶导数判断曲率
            first_diff = window_close.diff()
            second_diff = first_diff.diff()
            
            # 圆弧顶：先上升后下降，二阶导数为负
            if second_diff.iloc[:window//2].mean() > 0 and second_diff.iloc[window//2:].mean() < 0:
                curvature = abs(second_diff.mean())
                if curvature > second_diff.std() * 0.5:  # 有明显曲率
                    patterns.append({
                        'index': i,
                        'type': 'rounding_top',
                        'peak': window_high.max(),
                        'start': window_close.iloc[0],
                        'end': window_close.iloc[-1],
                        'curvature': curvature
                    })
            
            # 圆弧底：先下降后上升，二阶导数为正
            if second_diff.iloc[:window//2].mean() < 0 and second_diff.iloc[window//2:].mean() > 0:
                curvature = abs(second_diff.mean())
                if curvature > second_diff.std() * 0.5:
                    patterns.append({
                        'index': i,
                        'type': 'rounding_bottom',
                        'trough': window_low.min(),
                        'start': window_close.iloc[0],
                        'end': window_close.iloc[-1],
                        'curvature': curvature
                    })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def v_pattern(high: pd.Series, low: pd.Series, close: pd.Series,
                 window: int = 10, min_move: float = 0.05) -> pd.DataFrame:
        """V型反转识别"""
        patterns = []
        
        for i in range(window, len(close) - window):
            left_window = close.iloc[i-window:i]
            right_window = close.iloc[i:i+window]
            
            # V型底
            if (left_window.iloc[-1] < left_window.iloc[0] * (1 - min_move) and
                right_window.iloc[-1] > right_window.iloc[0] * (1 + min_move)):
                
                angle = abs(left_window.iloc[0] - left_window.iloc[-1]) + \
                       abs(right_window.iloc[-1] - right_window.iloc[0])
                
                patterns.append({
                    'index': i,
                    'type': 'v_bottom',
                    'low_point': low.iloc[i],
                    'left_high': left_window.iloc[0],
                    'right_high': right_window.iloc[-1],
                    'angle': angle / (2 * window)
                })
            
            # V型顶
            if (left_window.iloc[-1] > left_window.iloc[0] * (1 + min_move) and
                right_window.iloc[-1] < right_window.iloc[0] * (1 - min_move)):
                
                angle = abs(left_window.iloc[-1] - left_window.iloc[0]) + \
                       abs(right_window.iloc[0] - right_window.iloc[-1])
                
                patterns.append({
                    'index': i,
                    'type': 'v_top',
                    'high_point': high.iloc[i],
                    'left_low': left_window.iloc[0],
                    'right_low': right_window.iloc[-1],
                    'angle': angle / (2 * window)
                })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    # ============= 持续形态 =============
    
    @staticmethod
    def triangle_patterns(high: pd.Series, low: pd.Series, close: pd.Series,
                         window: int = 20, min_touches: int = 2) -> pd.DataFrame:
        """三角形态识别（上升、下降、对称）"""
        patterns = []
        
        for i in range(window, len(close) - 5):
            window_high = high.iloc[i-window:i]
            window_low = low.iloc[i-window:i]
            
            # 找高点和低点
            highs = []
            lows = []
            
            for j in range(1, len(window_high)-1):
                if window_high.iloc[j] > window_high.iloc[j-1] and window_high.iloc[j] > window_high.iloc[j+1]:
                    highs.append((j, window_high.iloc[j]))
                if window_low.iloc[j] < window_low.iloc[j-1] and window_low.iloc[j] < window_low.iloc[j+1]:
                    lows.append((j, window_low.iloc[j]))
            
            if len(highs) >= min_touches and len(lows) >= min_touches:
                # 计算趋势线斜率
                high_slope = np.polyfit([h[0] for h in highs], [h[1] for h in highs], 1)[0]
                low_slope = np.polyfit([l[0] for l in lows], [l[1] for l in lows], 1)[0]
                
                # 上升三角形：水平阻力，上升支撑
                if abs(high_slope) < 0.001 and low_slope > 0.001:
                    patterns.append({
                        'index': i,
                        'type': 'ascending_triangle',
                        'resistance': np.mean([h[1] for h in highs]),
                        'support_slope': low_slope,
                        'breakout_target': np.mean([h[1] for h in highs]) + \
                                         (highs[0][1] - lows[0][1])
                    })
                
                # 下降三角形：下降阻力，水平支撑
                elif high_slope < -0.001 and abs(low_slope) < 0.001:
                    patterns.append({
                        'index': i,
                        'type': 'descending_triangle',
                        'support': np.mean([l[1] for l in lows]),
                        'resistance_slope': high_slope,
                        'breakdown_target': np.mean([l[1] for l in lows]) - \
                                          (highs[0][1] - lows[0][1])
                    })
                
                # 对称三角形：收敛的高点和低点
                elif high_slope < -0.001 and low_slope > 0.001:
                    patterns.append({
                        'index': i,
                        'type': 'symmetrical_triangle',
                        'high_slope': high_slope,
                        'low_slope': low_slope,
                        'apex': i + int((highs[-1][1] - lows[-1][1]) / (low_slope - high_slope))
                    })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def flag_pennant(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                    pole_window: int = 10, flag_window: int = 10) -> pd.DataFrame:
        """旗形/三角旗形识别"""
        patterns = []
        
        for i in range(pole_window + flag_window, len(close) - 5):
            # 旗杆检测
            pole_start = i - pole_window - flag_window
            pole_end = i - flag_window
            
            pole_move = close.iloc[pole_end] - close.iloc[pole_start]
            pole_range = high.iloc[pole_start:pole_end].max() - low.iloc[pole_start:pole_end].min()
            
            # 需要有明显的旗杆
            if abs(pole_move) > pole_range * 0.7:
                # 旗形部分
                flag_high = high.iloc[pole_end:i]
                flag_low = low.iloc[pole_end:i]
                flag_close = close.iloc[pole_end:i]
                
                # 计算旗形的斜率
                flag_slope = np.polyfit(range(len(flag_close)), flag_close.values, 1)[0]
                
                # 旗形应该与旗杆方向相反
                if pole_move > 0 and flag_slope < 0:
                    # 看涨旗形
                    patterns.append({
                        'index': i,
                        'type': 'bull_flag',
                        'pole_height': pole_move,
                        'flag_slope': flag_slope,
                        'target': close.iloc[i] + pole_move
                    })
                elif pole_move < 0 and flag_slope > 0:
                    # 看跌旗形
                    patterns.append({
                        'index': i,
                        'type': 'bear_flag',
                        'pole_height': pole_move,
                        'flag_slope': flag_slope,
                        'target': close.iloc[i] + pole_move
                    })
                
                # 三角旗形检测（旗形部分呈三角形收敛）
                flag_volatility = flag_high - flag_low
                if flag_volatility.iloc[-1] < flag_volatility.iloc[0] * 0.5:
                    if pole_move > 0:
                        patterns.append({
                            'index': i,
                            'type': 'bull_pennant',
                            'pole_height': pole_move,
                            'convergence': flag_volatility.iloc[-1] / flag_volatility.iloc[0],
                            'target': close.iloc[i] + pole_move
                        })
                    else:
                        patterns.append({
                            'index': i,
                            'type': 'bear_pennant',
                            'pole_height': pole_move,
                            'convergence': flag_volatility.iloc[-1] / flag_volatility.iloc[0],
                            'target': close.iloc[i] + pole_move
                        })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def wedge_patterns(high: pd.Series, low: pd.Series, close: pd.Series,
                      window: int = 20) -> pd.DataFrame:
        """楔形识别（上升楔形、下降楔形）"""
        patterns = []
        
        for i in range(window, len(close) - 5):
            window_high = high.iloc[i-window:i]
            window_low = low.iloc[i-window:i]
            
            # 计算高点和低点的趋势线
            high_slope = np.polyfit(range(len(window_high)), window_high.values, 1)[0]
            low_slope = np.polyfit(range(len(window_low)), window_low.values, 1)[0]
            
            # 计算通道宽度变化
            start_width = window_high.iloc[0] - window_low.iloc[0]
            end_width = window_high.iloc[-1] - window_low.iloc[-1]
            
            # 上升楔形：两条线都上升，但逐渐收敛
            if high_slope > 0 and low_slope > 0 and end_width < start_width * 0.7:
                patterns.append({
                    'index': i,
                    'type': 'rising_wedge',
                    'high_slope': high_slope,
                    'low_slope': low_slope,
                    'convergence': end_width / start_width,
                    'breakdown_target': window_low.iloc[-1] - (window_high.iloc[0] - window_low.iloc[0])
                })
            
            # 下降楔形：两条线都下降，但逐渐收敛
            elif high_slope < 0 and low_slope < 0 and end_width < start_width * 0.7:
                patterns.append({
                    'index': i,
                    'type': 'falling_wedge',
                    'high_slope': high_slope,
                    'low_slope': low_slope,
                    'convergence': end_width / start_width,
                    'breakout_target': window_high.iloc[-1] + (window_high.iloc[0] - window_low.iloc[0])
                })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def rectangle_pattern(high: pd.Series, low: pd.Series, close: pd.Series,
                         window: int = 20, tolerance: float = 0.02) -> pd.DataFrame:
        """矩形整理形态识别"""
        patterns = []
        
        for i in range(window, len(close) - 5):
            window_high = high.iloc[i-window:i]
            window_low = low.iloc[i-window:i]
            
            # 找到支撑和阻力水平
            resistance = window_high.max()
            support = window_low.min()
            
            # 检查高点和低点是否在水平附近
            high_touches = ((window_high > resistance * (1 - tolerance)) & 
                          (window_high <= resistance)).sum()
            low_touches = ((window_low < support * (1 + tolerance)) & 
                         (window_low >= support)).sum()
            
            if high_touches >= 2 and low_touches >= 2:
                # 计算矩形高度
                height = resistance - support
                
                patterns.append({
                    'index': i,
                    'type': 'rectangle',
                    'resistance': resistance,
                    'support': support,
                    'height': height,
                    'high_touches': high_touches,
                    'low_touches': low_touches,
                    'breakout_target': resistance + height,
                    'breakdown_target': support - height
                })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    @staticmethod
    def cup_handle(high: pd.Series, low: pd.Series, close: pd.Series,
                  cup_window: int = 30, handle_window: int = 10) -> pd.DataFrame:
        """杯柄形态识别"""
        patterns = []
        
        for i in range(cup_window + handle_window, len(close) - 5):
            # 杯子部分
            cup_start = i - cup_window - handle_window
            cup_end = i - handle_window
            
            cup_high = high.iloc[cup_start:cup_end]
            cup_low = low.iloc[cup_start:cup_end]
            cup_close = close.iloc[cup_start:cup_end]
            
            # 检查U型
            cup_mid = len(cup_close) // 2
            left_high = cup_high.iloc[:cup_mid].max()
            right_high = cup_high.iloc[cup_mid:].max()
            bottom = cup_low.min()
            
            # 左右高点应该相近
            if abs(left_high - right_high) / max(left_high, right_high) < 0.05:
                # 底部应该明显低于两边
                if bottom < left_high * 0.8:
                    # 柄部分
                    handle_high = high.iloc[cup_end:i]
                    handle_low = low.iloc[cup_end:i]
                    
                    # 柄应该是小幅回调
                    handle_depth = (handle_high.max() - handle_low.min()) / (left_high - bottom)
                    
                    if 0.1 < handle_depth < 0.5:
                        patterns.append({
                            'index': i,
                            'type': 'cup_and_handle',
                            'cup_high': max(left_high, right_high),
                            'cup_low': bottom,
                            'handle_high': handle_high.max(),
                            'handle_low': handle_low.min(),
                            'target': max(left_high, right_high) + (max(left_high, right_high) - bottom)
                        })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    # ============= K线组合形态 =============
    
    @staticmethod
    def candlestick_patterns(open_price: pd.Series, high: pd.Series, 
                           low: pd.Series, close: pd.Series) -> pd.DataFrame:
        """K线组合形态识别"""
        patterns = []
        
        for i in range(2, len(close)):
            # 当前和前几根K线
            o = open_price.iloc[i]
            h = high.iloc[i]
            l = low.iloc[i]
            c = close.iloc[i]
            
            prev_o = open_price.iloc[i-1]
            prev_h = high.iloc[i-1]
            prev_l = low.iloc[i-1]
            prev_c = close.iloc[i-1]
            
            body = abs(c - o)
            prev_body = abs(prev_c - prev_o)
            
            # 锤子线/上吊线
            if body < (h - l) * 0.3:
                if c > o:  # 阳线
                    if l < min(o, c) - body * 2:
                        patterns.append({'index': i, 'type': 'hammer', 'price': c})
                else:  # 阴线
                    if l < min(o, c) - body * 2:
                        patterns.append({'index': i, 'type': 'hanging_man', 'price': c})
            
            # 吞没形态
            if i >= 1:
                if prev_c < prev_o and c > o:  # 看涨吞没
                    if o <= prev_c and c >= prev_o:
                        patterns.append({'index': i, 'type': 'bullish_engulfing', 'price': c})
                elif prev_c > prev_o and c < o:  # 看跌吞没
                    if o >= prev_c and c <= prev_o:
                        patterns.append({'index': i, 'type': 'bearish_engulfing', 'price': c})
            
            # 十字星
            if body < (h - l) * 0.1:
                patterns.append({'index': i, 'type': 'doji', 'price': c})
            
            # 三只乌鸦/三个白兵
            if i >= 2:
                prev2_o = open_price.iloc[i-2]
                prev2_c = close.iloc[i-2]
                
                # 三只乌鸦
                if (prev2_c < prev2_o and prev_c < prev_o and c < o and
                    c < prev_c < prev2_c):
                    patterns.append({'index': i, 'type': 'three_black_crows', 'price': c})
                
                # 三个白兵
                if (prev2_c > prev2_o and prev_c > prev_o and c > o and
                    c > prev_c > prev2_c):
                    patterns.append({'index': i, 'type': 'three_white_soldiers', 'price': c})
            
            # 启明星/黄昏星
            if i >= 2:
                prev2_body = abs(open_price.iloc[i-2] - close.iloc[i-2])
                
                # 启明星
                if (prev2_body > body * 2 and prev_body < body * 0.5 and
                    close.iloc[i-2] < open_price.iloc[i-2] and c > o):
                    patterns.append({'index': i, 'type': 'morning_star', 'price': c})
                
                # 黄昏星
                if (prev2_body > body * 2 and prev_body < body * 0.5 and
                    close.iloc[i-2] > open_price.iloc[i-2] and c < o):
                    patterns.append({'index': i, 'type': 'evening_star', 'price': c})
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()


def detect_all_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """检测所有形态"""
    recognizer = PatternRecognition()
    patterns = {}
    
    # 反转形态
    patterns['head_shoulders'] = recognizer.head_shoulders(df['high'], df['low'], df['close'])
    patterns['double_top_bottom'] = recognizer.double_top_bottom(df['high'], df['low'], df['close'])
    patterns['triple_top_bottom'] = recognizer.triple_top_bottom(df['high'], df['low'], df['close'])
    patterns['rounding'] = recognizer.rounding_patterns(df['high'], df['low'], df['close'])
    patterns['v_pattern'] = recognizer.v_pattern(df['high'], df['low'], df['close'])
    
    # 持续形态
    patterns['triangles'] = recognizer.triangle_patterns(df['high'], df['low'], df['close'])
    patterns['wedges'] = recognizer.wedge_patterns(df['high'], df['low'], df['close'])
    patterns['rectangles'] = recognizer.rectangle_pattern(df['high'], df['low'], df['close'])
    patterns['cup_handle'] = recognizer.cup_handle(df['high'], df['low'], df['close'])
    
    if 'volume' in df.columns:
        patterns['flags_pennants'] = recognizer.flag_pennant(df['high'], df['low'], 
                                                             df['close'], df['volume'])
    
    # K线形态
    if 'open' in df.columns:
        patterns['candlesticks'] = recognizer.candlestick_patterns(df['open'], df['high'], 
                                                                  df['low'], df['close'])
    
    return patterns