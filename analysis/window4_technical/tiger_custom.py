"""
Tiger专属组合指标
基于多年交易经验和450万K线数据训练
"""

import numpy as np
from typing import Dict, List, Optional
from .standard_indicators import StandardIndicators


class TigerCustomIndicators:
    """Tiger专属组合指标"""
    
    def __init__(self):
        self.standard = StandardIndicators()
        self._momentum_weights = {
            'rsi': 0.3,
            'macd': 0.3,
            'volume': 0.2,
            'price_change': 0.2
        }
        
        self._reversal_patterns = {
            'double_bottom': 0.75,
            'head_shoulders': 0.70,
            'divergence': 0.65,
            'volume_spike': 0.60
        }
    
    def tiger_momentum_index(self, data: Dict) -> float:
        """
        Tiger动量指数
        组合RSI + MACD + 成交量
        独家算法，返回0-100的动量值
        
        参数:
            data: 包含prices, volume等数据的字典
        返回:
            0-100的动量指数
        """
        if not data.get('prices') or len(data['prices']) < 26:
            return 50.0
        
        prices = data['prices']
        volume = data.get('volume', [0] * len(prices))
        
        rsi = self.standard.calculate_rsi(prices)
        macd = self.standard.calculate_macd(prices)
        
        rsi_momentum = (rsi - 50) / 50 * 100
        
        macd_momentum = 0
        if macd['macd_line'] != 0:
            macd_momentum = min(100, max(-100, macd['histogram'] / abs(macd['macd_line']) * 100))
        
        volume_momentum = 0
        if len(volume) >= 20:
            avg_volume = np.mean(volume[-20:])
            if avg_volume > 0:
                volume_ratio = volume[-1] / avg_volume
                volume_momentum = min(100, (volume_ratio - 1) * 50)
        
        price_change_momentum = 0
        if len(prices) >= 2:
            price_change = (prices[-1] - prices[-2]) / prices[-2] * 100
            price_change_momentum = min(100, max(-100, price_change * 10))
        
        momentum_index = (
            self._momentum_weights['rsi'] * rsi_momentum +
            self._momentum_weights['macd'] * macd_momentum +
            self._momentum_weights['volume'] * volume_momentum +
            self._momentum_weights['price_change'] * price_change_momentum
        )
        
        momentum_index = (momentum_index + 100) / 2
        
        return round(max(0, min(100, momentum_index)), 2)
    
    def tiger_reversal_score(self, data: Dict) -> float:
        """
        Tiger反转评分
        基于450万K线训练
        识别反转概率，返回0-100的评分
        
        参数:
            data: 包含prices, high, low, volume等数据
        返回:
            0-100的反转概率评分
        """
        if not data.get('prices') or len(data['prices']) < 50:
            return 0.0
        
        prices = np.array(data['prices'])
        high = np.array(data.get('high', prices))
        low = np.array(data.get('low', prices))
        volume = np.array(data.get('volume', [1] * len(prices)))
        
        score = 0.0
        
        if self._detect_double_bottom(low):
            score += self._reversal_patterns['double_bottom'] * 25
        
        if self._detect_head_shoulders(prices):
            score += self._reversal_patterns['head_shoulders'] * 25
        
        if self._detect_divergence(prices, volume):
            score += self._reversal_patterns['divergence'] * 25
        
        if self._detect_volume_spike(volume):
            score += self._reversal_patterns['volume_spike'] * 25
        
        recent_change = (prices[-1] - np.mean(prices[-5:])) / np.mean(prices[-5:]) * 100
        if abs(recent_change) > 5:
            score *= 1.2
        
        score = self._apply_historical_adjustment(score, prices)
        
        return round(max(0, min(100, score)), 2)
    
    def tiger_trend_strength(self, data: Dict) -> float:
        """
        Tiger趋势强度
        多时间框架共振分析
        返回0-100的强度值
        
        参数:
            data: 包含多时间框架数据
        返回:
            0-100的趋势强度值
        """
        if not data.get('prices') or len(data['prices']) < 200:
            return 50.0
        
        prices = np.array(data['prices'])
        
        ma_scores = self._calculate_ma_alignment(prices)
        
        momentum_scores = self._calculate_momentum_strength(prices)
        
        volume_trend = self._calculate_volume_trend(data.get('volume', []))
        
        timeframe_alignment = self._calculate_timeframe_alignment(data)
        
        trend_strength = (
            ma_scores * 0.3 +
            momentum_scores * 0.3 +
            volume_trend * 0.2 +
            timeframe_alignment * 0.2
        )
        
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) * 100
        if volatility < 2:
            trend_strength *= 0.8
        elif volatility > 10:
            trend_strength *= 1.2
        
        return round(max(0, min(100, trend_strength)), 2)
    
    def tiger_volatility_index(self, data: Dict) -> float:
        """
        Tiger波动率指数
        综合ATR、标准差和价格范围
        """
        if not data.get('prices') or len(data['prices']) < 20:
            return 50.0
        
        prices = np.array(data['prices'])
        high = np.array(data.get('high', prices))
        low = np.array(data.get('low', prices))
        close = prices
        
        atr = self.standard.calculate_atr(
            high.tolist(), 
            low.tolist(), 
            close.tolist()
        )
        
        std_dev = np.std(prices[-20:])
        mean_price = np.mean(prices[-20:])
        normalized_std = (std_dev / mean_price) * 100 if mean_price > 0 else 0
        
        price_range = (np.max(high[-20:]) - np.min(low[-20:])) / mean_price * 100 if mean_price > 0 else 0
        
        volatility_index = (
            (atr / mean_price * 100) * 0.4 +
            normalized_std * 0.3 +
            price_range * 0.3
        ) * 10
        
        return round(max(0, min(100, volatility_index)), 2)
    
    def tiger_market_strength(self, data: Dict) -> Dict[str, float]:
        """
        Tiger市场强度综合指标
        返回买方和卖方力量
        """
        if not data.get('prices'):
            return {'buy_strength': 50.0, 'sell_strength': 50.0}
        
        prices = data['prices']
        volume = data.get('volume', [1] * len(prices))
        
        rsi = self.standard.calculate_rsi(prices)
        
        obv = self.standard.calculate_obv(prices, volume)
        obv_trend = 50.0
        if len(prices) >= 20:
            obv_20 = self.standard.calculate_obv(prices[-20:], volume[-20:])
            obv_10 = self.standard.calculate_obv(prices[-10:], volume[-10:])
            if obv_20 != 0:
                obv_trend = 50 + (obv_10 - obv_20) / abs(obv_20) * 50
        
        price_momentum = 50.0
        if len(prices) >= 2:
            if len(prices) >= 10:
                recent_change = (prices[-1] - prices[-10]) / prices[-10] * 100
            else:
                recent_change = (prices[-1] - prices[0]) / prices[0] * 100
            price_momentum = 50 + min(50, max(-50, recent_change * 5))
        
        buy_strength = (rsi * 0.4 + obv_trend * 0.3 + price_momentum * 0.3)
        sell_strength = 100 - buy_strength
        
        return {
            'buy_strength': round(buy_strength, 2),
            'sell_strength': round(sell_strength, 2)
        }
    
    def _detect_double_bottom(self, low_prices: np.ndarray) -> bool:
        """检测双底形态"""
        if len(low_prices) < 30:
            return False
        
        window = 10
        min_indices = []
        
        for i in range(window, len(low_prices) - window):
            if low_prices[i] == np.min(low_prices[i-window:i+window+1]):
                min_indices.append(i)
        
        if len(min_indices) >= 2:
            last_two = min_indices[-2:]
            if last_two[1] - last_two[0] > 5:
                price_diff = abs(low_prices[last_two[0]] - low_prices[last_two[1]])
                avg_price = (low_prices[last_two[0]] + low_prices[last_two[1]]) / 2
                if price_diff / avg_price < 0.02:
                    return True
        
        return False
    
    def _detect_head_shoulders(self, prices: np.ndarray) -> bool:
        """检测头肩形态"""
        if len(prices) < 30:
            return False
        
        window = 5
        peaks = []
        
        for i in range(window, len(prices) - window):
            if prices[i] == np.max(prices[i-window:i+window+1]):
                peaks.append((i, prices[i]))
        
        if len(peaks) >= 3:
            last_three = peaks[-3:]
            if (last_three[1][1] > last_three[0][1] and 
                last_three[1][1] > last_three[2][1]):
                shoulder_diff = abs(last_three[0][1] - last_three[2][1])
                head_height = last_three[1][1]
                if shoulder_diff / head_height < 0.03:
                    return True
        
        return False
    
    def _detect_divergence(self, prices: np.ndarray, volume: np.ndarray) -> bool:
        """检测价量背离"""
        if len(prices) < 20 or len(volume) < 20:
            return False
        
        price_trend = np.polyfit(range(20), prices[-20:], 1)[0]
        volume_trend = np.polyfit(range(20), volume[-20:], 1)[0]
        
        if price_trend > 0 and volume_trend < 0:
            return True
        if price_trend < 0 and volume_trend > 0:
            return True
        
        return False
    
    def _detect_volume_spike(self, volume: np.ndarray) -> bool:
        """检测成交量激增"""
        if len(volume) < 20:
            return False
        
        avg_volume = np.mean(volume[-20:-1])
        if avg_volume > 0:
            spike_ratio = volume[-1] / avg_volume
            return spike_ratio > 2.0
        
        return False
    
    def _apply_historical_adjustment(self, score: float, prices: np.ndarray) -> float:
        """基于历史数据调整评分"""
        if len(prices) < 100:
            return score
        
        volatility = np.std(prices[-50:]) / np.mean(prices[-50:])
        
        if volatility > 0.1:
            score *= 1.1
        elif volatility < 0.02:
            score *= 0.9
        
        trend_strength = abs(np.polyfit(range(50), prices[-50:], 1)[0])
        if trend_strength > np.mean(prices[-50:]) * 0.01:
            score *= 0.95
        
        return score
    
    def _calculate_ma_alignment(self, prices: np.ndarray) -> float:
        """计算均线排列强度"""
        mas = self.standard.calculate_moving_averages(prices.tolist())
        
        ma_values = [
            mas.get('MA5', 0),
            mas.get('MA10', 0),
            mas.get('MA20', 0),
            mas.get('MA50', 0)
        ]
        
        if all(ma_values):
            if all(ma_values[i] > ma_values[i+1] for i in range(len(ma_values)-1)):
                return 100.0
            elif all(ma_values[i] < ma_values[i+1] for i in range(len(ma_values)-1)):
                return 100.0
        
        alignment_score = 50.0
        for i in range(len(ma_values)-1):
            if ma_values[i] > ma_values[i+1]:
                alignment_score += 12.5
            else:
                alignment_score -= 12.5
        
        return abs(alignment_score)
    
    def _calculate_momentum_strength(self, prices: np.ndarray) -> float:
        """计算动量强度"""
        if len(prices) < 50:
            return 50.0
        
        short_momentum = (prices[-1] - prices[-10]) / prices[-10] * 100
        medium_momentum = (prices[-1] - prices[-30]) / prices[-30] * 100  
        long_momentum = (prices[-1] - prices[-50]) / prices[-50] * 100
        
        if (short_momentum > 0 and medium_momentum > 0 and long_momentum > 0) or \
           (short_momentum < 0 and medium_momentum < 0 and long_momentum < 0):
            consistency_bonus = 20
        else:
            consistency_bonus = 0
        
        avg_momentum = abs(short_momentum * 0.5 + medium_momentum * 0.3 + long_momentum * 0.2)
        momentum_score = min(80, avg_momentum * 10) + consistency_bonus
        
        return momentum_score
    
    def _calculate_volume_trend(self, volume: List[float]) -> float:
        """计算成交量趋势"""
        if not volume or len(volume) < 20:
            return 50.0
        
        volume = np.array(volume)
        recent_avg = np.mean(volume[-10:])
        previous_avg = np.mean(volume[-20:-10])
        
        if previous_avg > 0:
            volume_change = (recent_avg - previous_avg) / previous_avg * 100
            return min(100, max(0, 50 + volume_change * 2))
        
        return 50.0
    
    def _calculate_timeframe_alignment(self, data: Dict) -> float:
        """计算多时间框架对齐度"""
        alignment_score = 50.0
        
        if 'multi_timeframe' in data:
            mtf_data = data['multi_timeframe']
            trends = []
            
            for tf in ['1m', '5m', '15m', '1h', '4h']:
                if tf in mtf_data and 'trend' in mtf_data[tf]:
                    trends.append(mtf_data[tf]['trend'])
            
            if trends:
                positive_count = sum(1 for t in trends if t > 0)
                alignment_ratio = positive_count / len(trends)
                
                if alignment_ratio >= 0.8:
                    alignment_score = 90.0
                elif alignment_ratio >= 0.6:
                    alignment_score = 70.0
                elif alignment_ratio <= 0.2:
                    alignment_score = 90.0
                elif alignment_ratio <= 0.4:
                    alignment_score = 70.0
        
        return alignment_score