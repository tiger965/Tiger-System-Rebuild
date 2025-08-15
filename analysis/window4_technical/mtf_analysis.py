"""
多时间框架分析
同时分析多个时间周期，寻找共振信号
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from .standard_indicators import StandardIndicators
from .tiger_custom import TigerCustomIndicators


class MultiTimeframeAnalysis:
    """多时间周期分析"""
    
    def __init__(self):
        self.standard = StandardIndicators()
        self.tiger = TigerCustomIndicators()
        
        self.timeframes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080
        }
        
        self.timeframe_weights = {
            '1m': 0.05,
            '5m': 0.10,
            '15m': 0.15,
            '30m': 0.15,
            '1h': 0.20,
            '4h': 0.20,
            '1d': 0.10,
            '1w': 0.05
        }
    
    def calculate_mtf_indicators(self, symbol: str, data: Dict) -> Dict:
        """
        计算多时间框架指标
        同时计算：
        - 1分钟、5分钟、15分钟
        - 1小时、4小时
        - 日线、周线
        
        参数:
            symbol: 交易对
            data: 包含各时间框架数据的字典
        返回:
            各时间框架的指标值
        """
        mtf_results = {}
        
        for timeframe in self.timeframes.keys():
            if timeframe not in data:
                continue
            
            tf_data = data[timeframe]
            if not tf_data:
                continue
            
            if 'prices' in tf_data:
                prices = tf_data['prices']
            elif 'close' in tf_data:
                prices = tf_data['close']
            else:
                continue
            if len(prices) < 20:
                continue
            
            indicators = {}
            
            indicators['rsi'] = self.standard.calculate_rsi(prices)
            
            indicators['macd'] = self.standard.calculate_macd(prices)
            
            indicators['bollinger'] = self.standard.calculate_bollinger_bands(prices)
            
            indicators['moving_averages'] = self.standard.calculate_moving_averages(prices)
            
            indicators['trend'] = self._calculate_trend(prices)
            
            indicators['momentum'] = self.tiger.tiger_momentum_index({
                'prices': prices,
                'volume': tf_data.get('volume', [])
            })
            
            indicators['strength'] = self._calculate_strength(prices)
            
            mtf_results[timeframe] = indicators
        
        mtf_results['confluence'] = self.find_timeframe_confluence(mtf_results)
        mtf_results['dominant_trend'] = self._find_dominant_trend(mtf_results)
        mtf_results['divergences'] = self._find_divergences(mtf_results)
        
        return mtf_results
    
    def find_timeframe_confluence(self, indicators: Dict) -> Dict:
        """
        寻找时间框架共振
        多个时间框架信号一致时更可靠
        
        参数:
            indicators: 各时间框架的指标
        返回:
            共振分析结果
        """
        confluence = {
            'trend_alignment': 0.0,
            'momentum_alignment': 0.0,
            'overbought_oversold': 0.0,
            'signal_strength': 0.0,
            'timeframes_aligned': []
        }
        
        if not indicators:
            return confluence
        
        trend_scores = []
        momentum_scores = []
        rsi_values = []
        
        for timeframe, data in indicators.items():
            if timeframe == 'confluence' or timeframe == 'dominant_trend':
                continue
            
            weight = self.timeframe_weights.get(timeframe, 0.1)
            
            if 'trend' in data:
                trend_scores.append((data['trend'], weight))
            
            if 'momentum' in data:
                momentum_scores.append((data['momentum'], weight))
            
            if 'rsi' in data:
                rsi_values.append((data['rsi'], weight))
        
        if trend_scores:
            positive_trends = sum(w for t, w in trend_scores if t > 0)
            negative_trends = sum(w for t, w in trend_scores if t < 0)
            total_weight = sum(w for _, w in trend_scores)
            
            if total_weight > 0:
                if positive_trends > negative_trends:
                    confluence['trend_alignment'] = (positive_trends / total_weight) * 100
                else:
                    confluence['trend_alignment'] = -(negative_trends / total_weight) * 100
        
        if momentum_scores:
            weighted_momentum = sum(m * w for m, w in momentum_scores)
            total_weight = sum(w for _, w in momentum_scores)
            if total_weight > 0:
                confluence['momentum_alignment'] = weighted_momentum / total_weight
        
        if rsi_values:
            weighted_rsi = sum(r * w for r, w in rsi_values)
            total_weight = sum(w for _, w in rsi_values)
            if total_weight > 0:
                avg_rsi = weighted_rsi / total_weight
                if avg_rsi > 70:
                    confluence['overbought_oversold'] = min(100, (avg_rsi - 70) * 3.33)
                elif avg_rsi < 30:
                    confluence['overbought_oversold'] = max(-100, (avg_rsi - 30) * 3.33)
                else:
                    confluence['overbought_oversold'] = 0
        
        aligned_count = 0
        for timeframe, data in indicators.items():
            if timeframe in ['confluence', 'dominant_trend', 'divergences']:
                continue
            
            if 'trend' in data and 'momentum' in data:
                if (data['trend'] > 0 and data['momentum'] > 50) or \
                   (data['trend'] < 0 and data['momentum'] < 50):
                    aligned_count += 1
                    confluence['timeframes_aligned'].append(timeframe)
        
        total_timeframes = len([k for k in indicators.keys() 
                               if k not in ['confluence', 'dominant_trend', 'divergences']])
        
        if total_timeframes > 0:
            confluence['signal_strength'] = (aligned_count / total_timeframes) * 100
        
        return confluence
    
    def analyze_timeframe_divergence(self, data: Dict) -> Dict:
        """
        分析时间框架背离
        短期和长期趋势不一致时的分析
        """
        divergences = {
            'has_divergence': False,
            'type': None,
            'strength': 0.0,
            'description': '',
            'timeframes': []
        }
        
        short_term = ['1m', '5m', '15m']
        medium_term = ['30m', '1h']
        long_term = ['4h', '1d', '1w']
        
        short_trend = self._get_timeframe_group_trend(data, short_term)
        medium_trend = self._get_timeframe_group_trend(data, medium_term)
        long_trend = self._get_timeframe_group_trend(data, long_term)
        
        if short_trend is not None and long_trend is not None:
            if short_trend > 0 and long_trend < 0:
                divergences['has_divergence'] = True
                divergences['type'] = 'bearish_divergence'
                divergences['strength'] = abs(short_trend - long_trend)
                divergences['description'] = '短期上涨但长期下跌，可能见顶'
                divergences['timeframes'] = ['short_bullish', 'long_bearish']
                
            elif short_trend < 0 and long_trend > 0:
                divergences['has_divergence'] = True
                divergences['type'] = 'bullish_divergence'
                divergences['strength'] = abs(short_trend - long_trend)
                divergences['description'] = '短期下跌但长期上涨，可能见底'
                divergences['timeframes'] = ['short_bearish', 'long_bullish']
        
        if medium_trend is not None:
            if short_trend is not None and long_trend is not None:
                if (short_trend > 0 and medium_trend < 0 and long_trend > 0) or \
                   (short_trend < 0 and medium_trend > 0 and long_trend < 0):
                    divergences['has_divergence'] = True
                    divergences['type'] = 'complex_divergence'
                    divergences['strength'] = 50.0
                    divergences['description'] = '多时间框架复杂背离，市场不确定性高'
        
        return divergences
    
    def calculate_mtf_support_resistance(self, data: Dict) -> Dict:
        """
        计算多时间框架支撑阻力
        """
        levels = {
            'major_support': [],
            'major_resistance': [],
            'minor_support': [],
            'minor_resistance': [],
            'confluence_levels': []
        }
        
        all_supports = []
        all_resistances = []
        
        major_timeframes = ['1d', '1w', '4h']
        minor_timeframes = ['1h', '30m', '15m']
        
        for timeframe in major_timeframes:
            if timeframe in data and 'prices' in data[timeframe]:
                prices = data[timeframe]['prices']
                sr_levels = self._calculate_sr_levels(prices)
                
                for level in sr_levels['support']:
                    all_supports.append((level, timeframe, 'major'))
                    levels['major_support'].append({
                        'level': level,
                        'timeframe': timeframe
                    })
                
                for level in sr_levels['resistance']:
                    all_resistances.append((level, timeframe, 'major'))
                    levels['major_resistance'].append({
                        'level': level,
                        'timeframe': timeframe
                    })
        
        for timeframe in minor_timeframes:
            if timeframe in data and 'prices' in data[timeframe]:
                prices = data[timeframe]['prices']
                sr_levels = self._calculate_sr_levels(prices)
                
                for level in sr_levels['support'][:3]:
                    all_supports.append((level, timeframe, 'minor'))
                    levels['minor_support'].append({
                        'level': level,
                        'timeframe': timeframe
                    })
                
                for level in sr_levels['resistance'][:3]:
                    all_resistances.append((level, timeframe, 'minor'))
                    levels['minor_resistance'].append({
                        'level': level,
                        'timeframe': timeframe
                    })
        
        confluence_levels = self._find_confluence_levels(
            all_supports + all_resistances
        )
        levels['confluence_levels'] = confluence_levels
        
        return levels
    
    def calculate_mtf_momentum(self, data: Dict) -> Dict:
        """
        计算多时间框架动量
        """
        momentum = {
            'overall': 50.0,
            'short_term': 50.0,
            'medium_term': 50.0,
            'long_term': 50.0,
            'acceleration': 0.0
        }
        
        short_term = ['1m', '5m', '15m']
        medium_term = ['30m', '1h', '4h']
        long_term = ['1d', '1w']
        
        short_momentum = []
        medium_momentum = []
        long_momentum = []
        
        for timeframe, tf_data in data.items():
            if timeframe in short_term and 'momentum' in tf_data:
                short_momentum.append(tf_data['momentum'])
            elif timeframe in medium_term and 'momentum' in tf_data:
                medium_momentum.append(tf_data['momentum'])
            elif timeframe in long_term and 'momentum' in tf_data:
                long_momentum.append(tf_data['momentum'])
        
        if short_momentum:
            momentum['short_term'] = np.mean(short_momentum)
        
        if medium_momentum:
            momentum['medium_term'] = np.mean(medium_momentum)
        
        if long_momentum:
            momentum['long_term'] = np.mean(long_momentum)
        
        all_momentum = short_momentum + medium_momentum + long_momentum
        if all_momentum:
            momentum['overall'] = np.mean(all_momentum)
        
        if momentum['short_term'] > momentum['medium_term'] > momentum['long_term']:
            momentum['acceleration'] = 20.0
        elif momentum['short_term'] < momentum['medium_term'] < momentum['long_term']:
            momentum['acceleration'] = -20.0
        else:
            momentum['acceleration'] = 0.0
        
        return momentum
    
    def _calculate_trend(self, prices: List[float]) -> float:
        """计算趋势方向和强度"""
        if len(prices) < 20:
            return 0.0
        
        prices = np.array(prices)
        
        short_ma = np.mean(prices[-10:])
        long_ma = np.mean(prices[-20:])
        
        if short_ma > long_ma:
            trend = (short_ma - long_ma) / long_ma * 100
        else:
            trend = -(long_ma - short_ma) / long_ma * 100
        
        slope = np.polyfit(range(20), prices[-20:], 1)[0]
        normalized_slope = slope / np.mean(prices[-20:]) * 100
        
        combined_trend = (trend + normalized_slope) / 2
        
        return round(max(-100, min(100, combined_trend)), 2)
    
    def _calculate_strength(self, prices: List[float]) -> float:
        """计算趋势强度"""
        if len(prices) < 20:
            return 50.0
        
        prices = np.array(prices)
        
        returns = np.diff(prices) / prices[:-1]
        
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        if len(positive_returns) == 0:
            return 0.0
        if len(negative_returns) == 0:
            return 100.0
        
        avg_positive = np.mean(positive_returns)
        avg_negative = np.mean(np.abs(negative_returns))
        
        if avg_negative == 0:
            return 100.0
        
        strength = 100 / (1 + avg_negative / avg_positive)
        
        directional_movement = len(positive_returns) / len(returns) * 100
        
        combined_strength = (strength + directional_movement) / 2
        
        return round(max(0, min(100, combined_strength)), 2)
    
    def _find_dominant_trend(self, mtf_results: Dict) -> Dict:
        """找出主导趋势"""
        dominant = {
            'direction': 'neutral',
            'strength': 0.0,
            'leading_timeframe': None,
            'confirmation_count': 0
        }
        
        bullish_count = 0
        bearish_count = 0
        total_strength = 0.0
        
        for timeframe, data in mtf_results.items():
            if timeframe in ['confluence', 'dominant_trend', 'divergences']:
                continue
            
            if 'trend' in data:
                weight = self.timeframe_weights.get(timeframe, 0.1)
                
                if data['trend'] > 0:
                    bullish_count += 1
                    total_strength += data['trend'] * weight
                elif data['trend'] < 0:
                    bearish_count += 1
                    total_strength += abs(data['trend']) * weight
        
        if bullish_count > bearish_count:
            dominant['direction'] = 'bullish'
            dominant['confirmation_count'] = bullish_count
        elif bearish_count > bullish_count:
            dominant['direction'] = 'bearish'
            dominant['confirmation_count'] = bearish_count
        
        dominant['strength'] = abs(total_strength)
        
        max_trend = 0
        for timeframe, data in mtf_results.items():
            if timeframe in ['confluence', 'dominant_trend', 'divergences']:
                continue
            
            if 'trend' in data and abs(data['trend']) > abs(max_trend):
                max_trend = data['trend']
                dominant['leading_timeframe'] = timeframe
        
        return dominant
    
    def _find_divergences(self, mtf_results: Dict) -> List[Dict]:
        """查找时间框架间的背离"""
        divergences = []
        
        timeframe_list = sorted([tf for tf in mtf_results.keys() 
                                if tf not in ['confluence', 'dominant_trend', 'divergences']],
                               key=lambda x: self.timeframes.get(x, 0))
        
        for i in range(len(timeframe_list) - 1):
            tf1 = timeframe_list[i]
            tf2 = timeframe_list[i + 1]
            
            if tf1 in mtf_results and tf2 in mtf_results:
                data1 = mtf_results[tf1]
                data2 = mtf_results[tf2]
                
                if 'trend' in data1 and 'trend' in data2:
                    if data1['trend'] * data2['trend'] < 0:
                        divergences.append({
                            'type': 'trend_divergence',
                            'timeframe1': tf1,
                            'timeframe2': tf2,
                            'value1': data1['trend'],
                            'value2': data2['trend']
                        })
                
                if 'momentum' in data1 and 'momentum' in data2:
                    if abs(data1['momentum'] - data2['momentum']) > 30:
                        divergences.append({
                            'type': 'momentum_divergence',
                            'timeframe1': tf1,
                            'timeframe2': tf2,
                            'value1': data1['momentum'],
                            'value2': data2['momentum']
                        })
        
        return divergences
    
    def _get_timeframe_group_trend(self, data: Dict, 
                                  timeframes: List[str]) -> Optional[float]:
        """获取时间框架组的趋势"""
        trends = []
        
        for tf in timeframes:
            if tf in data and 'trend' in data[tf]:
                trends.append(data[tf]['trend'])
        
        if trends:
            return np.mean(trends)
        
        return None
    
    def _calculate_sr_levels(self, prices: List[float]) -> Dict:
        """计算支撑阻力位"""
        if len(prices) < 20:
            return {'support': [], 'resistance': []}
        
        prices = np.array(prices)
        
        window = 10
        supports = []
        resistances = []
        
        for i in range(window, len(prices) - window):
            if prices[i] == np.min(prices[i-window:i+window+1]):
                supports.append(prices[i])
            
            if prices[i] == np.max(prices[i-window:i+window+1]):
                resistances.append(prices[i])
        
        supports = list(set(supports))
        resistances = list(set(resistances))
        
        return {
            'support': sorted(supports, reverse=True)[:5],
            'resistance': sorted(resistances)[:5]
        }
    
    def _find_confluence_levels(self, levels: List[Tuple]) -> List[Dict]:
        """找出共振价格水平"""
        confluence = []
        processed = set()
        
        for i, (level1, tf1, type1) in enumerate(levels):
            if i in processed:
                continue
            
            cluster = [(level1, tf1, type1)]
            processed.add(i)
            
            for j, (level2, tf2, type2) in enumerate(levels[i+1:], i+1):
                if j in processed:
                    continue
                
                if abs(level1 - level2) / level1 < 0.005:
                    cluster.append((level2, tf2, type2))
                    processed.add(j)
            
            if len(cluster) >= 2:
                avg_level = np.mean([l for l, _, _ in cluster])
                timeframes = list(set([tf for _, tf, _ in cluster]))
                importance = len([1 for _, _, t in cluster if t == 'major'])
                
                confluence.append({
                    'level': round(avg_level, 2),
                    'timeframes': timeframes,
                    'count': len(cluster),
                    'importance': importance
                })
        
        confluence.sort(key=lambda x: x['count'], reverse=True)
        
        return confluence[:10]