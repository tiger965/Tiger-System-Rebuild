"""
Tiger System - Multi-Timeframe Analysis Module
Window 4: Technical Analysis Engine
多时间框架同步分析系统
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import concurrent.futures
from indicators.trend import TrendIndicators
from indicators.momentum import MomentumIndicators
from indicators.volatility import VolatilityIndicators
from indicators.volume import VolumeIndicators
from indicators.custom import CustomIndicators


class MultiTimeframeAnalysis:
    """多时间框架分析系统"""
    
    def __init__(self):
        self.timeframes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        self.trend_indicators = TrendIndicators()
        self.momentum_indicators = MomentumIndicators()
        self.volatility_indicators = VolatilityIndicators()
        self.volume_indicators = VolumeIndicators()
        self.custom_indicators = CustomIndicators()
    
    def resample_data(self, df: pd.DataFrame, source_tf: str, target_tf: str) -> pd.DataFrame:
        """数据重采样到不同时间框架"""
        source_minutes = self.timeframes[source_tf]
        target_minutes = self.timeframes[target_tf]
        
        if target_minutes <= source_minutes:
            return df
        
        # 计算重采样比率
        resample_ratio = target_minutes // source_minutes
        
        # 重采样OHLCV数据
        resampled = pd.DataFrame()
        resampled['open'] = df['open'].iloc[::resample_ratio] if 'open' in df.columns else df['close'].iloc[::resample_ratio]
        resampled['high'] = df['high'].rolling(resample_ratio).max().iloc[::resample_ratio]
        resampled['low'] = df['low'].rolling(resample_ratio).min().iloc[::resample_ratio]
        resampled['close'] = df['close'].iloc[::resample_ratio]
        
        if 'volume' in df.columns:
            resampled['volume'] = df['volume'].rolling(resample_ratio).sum().iloc[::resample_ratio]
        
        return resampled.dropna()
    
    def calculate_tf_indicators(self, df: pd.DataFrame, tf_name: str) -> Dict:
        """计算单个时间框架的所有指标"""
        results = {
            'timeframe': tf_name,
            'data': df.copy()
        }
        
        # 趋势指标
        results['sma_20'] = self.trend_indicators.sma(df['close'], 20)
        results['ema_20'] = self.trend_indicators.ema(df['close'], 20)
        macd = self.trend_indicators.macd(df['close'])
        results['macd'] = macd['macd']
        results['macd_signal'] = macd['signal']
        results['macd_histogram'] = macd['histogram']
        
        # 动量指标
        results['rsi'] = self.momentum_indicators.rsi(df['close'])
        stoch = self.momentum_indicators.stochastic(df['high'], df['low'], df['close'])
        results['stoch_k'] = stoch['k']
        results['stoch_d'] = stoch['d']
        
        # 波动率指标
        bb = self.volatility_indicators.bollinger_bands(df['close'])
        results['bb_upper'] = bb['upper']
        results['bb_middle'] = bb['middle']
        results['bb_lower'] = bb['lower']
        results['atr'] = self.volatility_indicators.atr(df['high'], df['low'], df['close'])
        
        # 成交量指标（如果有）
        if 'volume' in df.columns:
            results['obv'] = self.volume_indicators.obv(df['close'], df['volume'])
            results['mfi'] = self.volume_indicators.mfi(df['high'], df['low'], df['close'], df['volume'])
        
        # 趋势方向
        results['trend'] = self.detect_trend(df['close'])
        
        # 信号强度
        results['signal_strength'] = self.calculate_signal_strength(results)
        
        return results
    
    def detect_trend(self, close: pd.Series, short_period: int = 20, long_period: int = 50) -> pd.Series:
        """检测趋势方向"""
        sma_short = close.rolling(short_period).mean()
        sma_long = close.rolling(long_period).mean()
        
        trend = pd.Series(index=close.index, dtype='int')
        trend[sma_short > sma_long] = 1  # 上升趋势
        trend[sma_short < sma_long] = -1  # 下降趋势
        trend[(sma_short == sma_long) | trend.isna()] = 0  # 无趋势
        
        return trend
    
    def calculate_signal_strength(self, indicators: Dict) -> float:
        """计算信号强度（0-100）"""
        strength = 0
        count = 0
        
        # RSI信号
        if 'rsi' in indicators:
            rsi_val = indicators['rsi'].iloc[-1] if len(indicators['rsi']) > 0 else 50
            if rsi_val < 30:
                strength += 100
            elif rsi_val < 40:
                strength += 70
            elif rsi_val > 70:
                strength += 0
            elif rsi_val > 60:
                strength += 30
            else:
                strength += 50
            count += 1
        
        # MACD信号
        if 'macd' in indicators and 'macd_signal' in indicators:
            if len(indicators['macd']) > 0:
                if indicators['macd'].iloc[-1] > indicators['macd_signal'].iloc[-1]:
                    strength += 70
                else:
                    strength += 30
                count += 1
        
        # 布林带位置
        if all(k in indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
            if len(indicators['data']) > 0:
                close_val = indicators['data']['close'].iloc[-1]
                bb_position = (close_val - indicators['bb_lower'].iloc[-1]) / \
                            (indicators['bb_upper'].iloc[-1] - indicators['bb_lower'].iloc[-1])
                strength += (1 - bb_position) * 100  # 越接近下轨越强
                count += 1
        
        # 趋势一致性
        if 'trend' in indicators:
            if len(indicators['trend']) > 0:
                trend_val = indicators['trend'].iloc[-1]
                if trend_val == 1:
                    strength += 70
                elif trend_val == -1:
                    strength += 30
                else:
                    strength += 50
                count += 1
        
        return strength / count if count > 0 else 50
    
    def analyze_all_timeframes(self, base_df: pd.DataFrame, base_tf: str = '1m') -> Dict:
        """分析所有时间框架"""
        mtf_results = {}
        
        # 并行计算各时间框架
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for tf_name, tf_minutes in self.timeframes.items():
                if tf_minutes >= self.timeframes[base_tf]:
                    # 重采样数据
                    resampled_df = self.resample_data(base_df, base_tf, tf_name)
                    
                    # 提交计算任务
                    future = executor.submit(self.calculate_tf_indicators, resampled_df, tf_name)
                    futures[tf_name] = future
            
            # 收集结果
            for tf_name, future in futures.items():
                mtf_results[tf_name] = future.result()
        
        # 计算综合信号
        mtf_results['combined_signal'] = self.calculate_combined_signal(mtf_results)
        
        # 检测共振
        mtf_results['resonance'] = self.detect_resonance(mtf_results)
        
        return mtf_results
    
    def calculate_combined_signal(self, mtf_results: Dict) -> Dict:
        """计算多时间框架综合信号"""
        weights = {
            '1m': 0.05,
            '5m': 0.10,
            '15m': 0.15,
            '30m': 0.15,
            '1h': 0.25,
            '4h': 0.20,
            '1d': 0.10
        }
        
        total_signal = 0
        total_weight = 0
        trend_votes = []
        
        for tf_name, result in mtf_results.items():
            if tf_name in weights and isinstance(result, dict):
                weight = weights[tf_name]
                
                # 信号强度加权
                if 'signal_strength' in result:
                    total_signal += result['signal_strength'] * weight
                    total_weight += weight
                
                # 趋势投票
                if 'trend' in result and len(result['trend']) > 0:
                    trend_votes.append(result['trend'].iloc[-1])
        
        # 计算趋势一致性
        if trend_votes:
            trend_consensus = np.mean(trend_votes)
        else:
            trend_consensus = 0
        
        # 综合信号
        combined_strength = total_signal / total_weight if total_weight > 0 else 50
        
        # 生成交易建议
        if combined_strength > 70 and trend_consensus > 0.5:
            recommendation = 'STRONG_BUY'
        elif combined_strength > 60 and trend_consensus > 0:
            recommendation = 'BUY'
        elif combined_strength < 30 and trend_consensus < -0.5:
            recommendation = 'STRONG_SELL'
        elif combined_strength < 40 and trend_consensus < 0:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'
        
        return {
            'strength': combined_strength,
            'trend_consensus': trend_consensus,
            'recommendation': recommendation,
            'confidence': abs(trend_consensus) * (abs(combined_strength - 50) / 50)
        }
    
    def detect_resonance(self, mtf_results: Dict) -> Dict:
        """检测多时间框架共振"""
        resonance_indicators = {
            'trend': [],
            'momentum': [],
            'volatility': []
        }
        
        for tf_name, result in mtf_results.items():
            if isinstance(result, dict):
                # 趋势共振
                if 'trend' in result and len(result['trend']) > 0:
                    resonance_indicators['trend'].append(result['trend'].iloc[-1])
                
                # 动量共振（RSI）
                if 'rsi' in result and len(result['rsi']) > 0:
                    rsi_val = result['rsi'].iloc[-1]
                    if rsi_val < 30:
                        resonance_indicators['momentum'].append(1)  # 超卖
                    elif rsi_val > 70:
                        resonance_indicators['momentum'].append(-1)  # 超买
                    else:
                        resonance_indicators['momentum'].append(0)
                
                # 波动率状态
                if 'atr' in result and len(result['atr']) > 0:
                    atr_val = result['atr'].iloc[-1]
                    atr_ma = result['atr'].rolling(20).mean().iloc[-1]
                    if pd.notna(atr_ma):
                        if atr_val > atr_ma * 1.5:
                            resonance_indicators['volatility'].append(1)  # 高波动
                        elif atr_val < atr_ma * 0.5:
                            resonance_indicators['volatility'].append(-1)  # 低波动
                        else:
                            resonance_indicators['volatility'].append(0)
        
        # 计算共振强度
        trend_resonance = np.mean(resonance_indicators['trend']) if resonance_indicators['trend'] else 0
        momentum_resonance = np.mean(resonance_indicators['momentum']) if resonance_indicators['momentum'] else 0
        volatility_state = np.mean(resonance_indicators['volatility']) if resonance_indicators['volatility'] else 0
        
        # 共振类型判断
        if abs(trend_resonance) > 0.7 and abs(momentum_resonance) > 0.5:
            if trend_resonance > 0 and momentum_resonance > 0:
                resonance_type = 'BULLISH_RESONANCE'
            elif trend_resonance < 0 and momentum_resonance < 0:
                resonance_type = 'BEARISH_RESONANCE'
            else:
                resonance_type = 'MIXED'
        else:
            resonance_type = 'NO_RESONANCE'
        
        return {
            'type': resonance_type,
            'trend_strength': abs(trend_resonance),
            'momentum_strength': abs(momentum_resonance),
            'volatility_state': volatility_state,
            'overall_strength': (abs(trend_resonance) + abs(momentum_resonance)) / 2
        }
    
    def get_dominant_timeframe(self, mtf_results: Dict) -> str:
        """获取主导时间框架"""
        max_strength = 0
        dominant_tf = None
        
        for tf_name, result in mtf_results.items():
            if isinstance(result, dict) and 'signal_strength' in result:
                strength = abs(result['signal_strength'] - 50)
                if strength > max_strength:
                    max_strength = strength
                    dominant_tf = tf_name
        
        return dominant_tf or '1h'
    
    def generate_mtf_report(self, mtf_results: Dict) -> str:
        """生成多时间框架分析报告"""
        report = []
        report.append("=" * 50)
        report.append("多时间框架分析报告")
        report.append("=" * 50)
        
        # 各时间框架状态
        report.append("\n时间框架分析：")
        for tf_name in ['1m', '5m', '15m', '30m', '1h', '4h', '1d']:
            if tf_name in mtf_results and isinstance(mtf_results[tf_name], dict):
                result = mtf_results[tf_name]
                if 'trend' in result and len(result['trend']) > 0:
                    trend_dir = result['trend'].iloc[-1]
                    trend_str = "↑上升" if trend_dir > 0 else "↓下降" if trend_dir < 0 else "→横盘"
                    strength = result.get('signal_strength', 50)
                    report.append(f"  {tf_name:5s}: {trend_str} | 强度: {strength:.1f}%")
        
        # 综合信号
        if 'combined_signal' in mtf_results:
            signal = mtf_results['combined_signal']
            report.append(f"\n综合分析：")
            report.append(f"  建议: {signal['recommendation']}")
            report.append(f"  信号强度: {signal['strength']:.1f}%")
            report.append(f"  置信度: {signal['confidence']*100:.1f}%")
        
        # 共振检测
        if 'resonance' in mtf_results:
            resonance = mtf_results['resonance']
            report.append(f"\n共振状态：")
            report.append(f"  类型: {resonance['type']}")
            report.append(f"  强度: {resonance['overall_strength']*100:.1f}%")
        
        # 主导时间框架
        dominant = self.get_dominant_timeframe(mtf_results)
        report.append(f"\n主导时间框架: {dominant}")
        
        report.append("=" * 50)
        
        return "\n".join(report)