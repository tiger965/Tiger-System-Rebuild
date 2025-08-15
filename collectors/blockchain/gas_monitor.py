"""
Gas费监控器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class GasMonitor:
    """Gas费监控器"""
    
    # Gas费级别定义
    GAS_LEVELS = {
        'low': {'percentile': 25, 'desc': '慢速'},
        'medium': {'percentile': 50, 'desc': '标准'},
        'high': {'percentile': 75, 'desc': '快速'},
        'instant': {'percentile': 90, 'desc': '极速'}
    }
    
    # 异常检测阈值
    SPIKE_THRESHOLDS = {
        'multiplier': 3,      # 3倍于平均值视为异常
        'absolute_gwei': 200,  # 绝对值超过200 Gwei视为异常
        'rapid_change': 50     # 5分钟内变化50%视为快速变化
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Gas监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.etherscan_api_key = config.get('etherscan_api_key', '')
        self.blocknative_api_key = config.get('blocknative_api_key', '')
        
        # 历史数据缓存
        self.gas_history = []  # 历史Gas价格
        self.spike_events = []  # Gas异常事件
        self.base_fee_history = []  # EIP-1559 base fee历史
        
        # 统计数据
        self.stats = {
            'avg_24h': 0,
            'median_24h': 0,
            'max_24h': 0,
            'min_24h': 0
        }
    
    async def get_gas_metrics(self) -> Dict[str, Any]:
        """
        获取Gas费指标
        
        Returns:
            Gas费指标字典
        """
        metrics = {}
        
        # 获取当前Gas价格
        current_gas = await self._get_current_gas_price()
        if current_gas:
            metrics.update(current_gas)
            
            # 添加到历史记录
            self.gas_history.append({
                'timestamp': datetime.now().isoformat(),
                'gwei': current_gas['current_gwei'],
                'base_fee': current_gas.get('base_fee', 0)
            })
            
            # 保留24小时数据
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.gas_history = [
                g for g in self.gas_history 
                if datetime.fromisoformat(g['timestamp']) > cutoff_time
            ]
        
        # 计算统计数据
        self._update_statistics()
        metrics['statistics'] = self.stats.copy()
        
        # 检测异常
        spike_detected = self._detect_spike(metrics.get('current_gwei', 0))
        metrics['spike_detected'] = spike_detected
        
        if spike_detected:
            spike_info = {
                'timestamp': datetime.now().isoformat(),
                'current_gwei': metrics.get('current_gwei', 0),
                'avg_24h': self.stats['avg_24h'],
                'spike_multiplier': metrics.get('current_gwei', 0) / self.stats['avg_24h'] if self.stats['avg_24h'] > 0 else 0
            }
            metrics['spike_info'] = spike_info
            self.spike_events.append(spike_info)
        
        # 获取Gas预测
        predictions = await self._get_gas_predictions()
        if predictions:
            metrics['predictions'] = predictions
        
        # 获取网络拥堵状态
        congestion = self._analyze_congestion(metrics.get('current_gwei', 0))
        metrics['congestion_level'] = congestion
        
        return metrics
    
    async def _get_current_gas_price(self) -> Optional[Dict[str, Any]]:
        """获取当前Gas价格"""
        if not self.etherscan_api_key:
            return None
        
        gas_data = {}
        
        async with aiohttp.ClientSession() as session:
            try:
                # 从Etherscan获取Gas价格
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'gastracker',
                    'action': 'gasoracle',
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data['status'] == '1' and data['result']:
                        result = data['result']
                        gas_data = {
                            'current_gwei': float(result.get('ProposeGasPrice', 0)),
                            'safe_gwei': float(result.get('SafeGasPrice', 0)),
                            'fast_gwei': float(result.get('FastGasPrice', 0)),
                            'base_fee': float(result.get('suggestBaseFee', 0)),
                            'last_block': result.get('LastBlock', ''),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # 计算优先费建议
                        if gas_data['base_fee'] > 0:
                            gas_data['priority_fee'] = {
                                'low': 1,
                                'medium': 2,
                                'high': 3
                            }
                            gas_data['estimated_total'] = {
                                'low': gas_data['base_fee'] + 1,
                                'medium': gas_data['base_fee'] + 2,
                                'high': gas_data['base_fee'] + 3
                            }
            
            except Exception as e:
                logger.error(f"获取Gas价格失败: {e}")
                return None
        
        return gas_data
    
    async def _get_gas_predictions(self) -> Optional[Dict[str, Any]]:
        """获取Gas价格预测"""
        predictions = {}
        
        if len(self.gas_history) < 10:
            return None
        
        try:
            # 简单的移动平均预测
            recent_prices = [g['gwei'] for g in self.gas_history[-10:]]
            
            # 计算趋势
            trend = 'stable'
            if len(recent_prices) >= 2:
                change = recent_prices[-1] - recent_prices[-5] if len(recent_prices) >= 5 else recent_prices[-1] - recent_prices[0]
                change_percent = (change / recent_prices[0]) * 100 if recent_prices[0] > 0 else 0
                
                if change_percent > 20:
                    trend = 'rising'
                elif change_percent < -20:
                    trend = 'falling'
            
            predictions = {
                'trend': trend,
                'next_5min': sum(recent_prices[-3:]) / 3,  # 最近3个数据点的平均
                'next_15min': sum(recent_prices[-5:]) / 5,  # 最近5个数据点的平均
                'next_30min': sum(recent_prices) / len(recent_prices),  # 所有数据点的平均
                'confidence': 'medium' if len(self.gas_history) > 50 else 'low'
            }
            
        except Exception as e:
            logger.error(f"计算Gas预测失败: {e}")
            return None
        
        return predictions
    
    def _detect_spike(self, current_gwei: float) -> bool:
        """
        检测Gas费异常
        
        Args:
            current_gwei: 当前Gas价格（Gwei）
            
        Returns:
            是否检测到异常
        """
        if current_gwei <= 0:
            return False
        
        # 绝对值检测
        if current_gwei > self.SPIKE_THRESHOLDS['absolute_gwei']:
            return True
        
        # 相对值检测
        if self.stats['avg_24h'] > 0:
            multiplier = current_gwei / self.stats['avg_24h']
            if multiplier > self.SPIKE_THRESHOLDS['multiplier']:
                return True
        
        # 快速变化检测
        if len(self.gas_history) >= 5:
            recent_5min = [g['gwei'] for g in self.gas_history[-5:]]
            if recent_5min[0] > 0:
                change_percent = abs((current_gwei - recent_5min[0]) / recent_5min[0] * 100)
                if change_percent > self.SPIKE_THRESHOLDS['rapid_change']:
                    return True
        
        return False
    
    def _analyze_congestion(self, current_gwei: float) -> str:
        """
        分析网络拥堵程度
        
        Args:
            current_gwei: 当前Gas价格
            
        Returns:
            拥堵级别: 'low', 'medium', 'high', 'severe'
        """
        if current_gwei < 20:
            return 'low'
        elif current_gwei < 50:
            return 'medium'
        elif current_gwei < 100:
            return 'high'
        else:
            return 'severe'
    
    def _update_statistics(self):
        """更新统计数据"""
        if len(self.gas_history) == 0:
            return
        
        gas_prices = [g['gwei'] for g in self.gas_history]
        
        self.stats = {
            'avg_24h': statistics.mean(gas_prices),
            'median_24h': statistics.median(gas_prices),
            'max_24h': max(gas_prices),
            'min_24h': min(gas_prices),
            'std_dev': statistics.stdev(gas_prices) if len(gas_prices) > 1 else 0
        }
    
    async def get_gas_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取历史Gas价格
        
        Args:
            hours: 历史时间范围（小时）
            
        Returns:
            历史Gas价格列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = [
            g for g in self.gas_history
            if datetime.fromisoformat(g['timestamp']) > cutoff_time
        ]
        
        return history
    
    async def get_spike_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取Gas异常事件
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            异常事件列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        events = [
            e for e in self.spike_events
            if datetime.fromisoformat(e['timestamp']) > cutoff_time
        ]
        
        return events
    
    def get_recommendations(self, current_gwei: float) -> Dict[str, Any]:
        """
        获取Gas费建议
        
        Args:
            current_gwei: 当前Gas价格
            
        Returns:
            使用建议
        """
        recommendations = {
            'current_gwei': current_gwei,
            'congestion': self._analyze_congestion(current_gwei),
            'actions': []
        }
        
        if current_gwei < 30:
            recommendations['actions'] = [
                '当前Gas费较低，适合执行交易',
                '可以进行大额转账或复杂合约交互'
            ]
            recommendations['urgency'] = 'high'
        elif current_gwei < 50:
            recommendations['actions'] = [
                'Gas费适中，可以正常交易',
                '非紧急交易可以再等待'
            ]
            recommendations['urgency'] = 'medium'
        elif current_gwei < 100:
            recommendations['actions'] = [
                'Gas费较高，建议推迟非紧急交易',
                '只执行必要的交易'
            ]
            recommendations['urgency'] = 'low'
        else:
            recommendations['actions'] = [
                'Gas费异常高，强烈建议暂停交易',
                '等待Gas费回落后再操作',
                '检查是否有网络异常事件'
            ]
            recommendations['urgency'] = 'none'
        
        # 基于趋势的建议
        if len(self.gas_history) >= 10:
            recent = [g['gwei'] for g in self.gas_history[-10:]]
            if recent[-1] < recent[0]:
                recommendations['trend_advice'] = 'Gas费正在下降，可以稍等'
            elif recent[-1] > recent[0] * 1.5:
                recommendations['trend_advice'] = 'Gas费快速上涨，尽快执行紧急交易'
        
        return recommendations