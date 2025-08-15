"""
链上数据主监控器
"""
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
import json
from decimal import Decimal

from .whale_tracker import WhaleTracker
from .exchange_wallet_monitor import ExchangeWalletMonitor
from .defi_monitor import DeFiMonitor
from .gas_monitor import GasMonitor

logger = logging.getLogger(__name__)

class ChainMonitor:
    """区块链数据监控主类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化链上监控器
        
        Args:
            config: 配置字典，包含API密钥、监控参数等
        """
        self.config = config
        self.is_running = False
        
        # 初始化各个子监控器
        self.whale_tracker = WhaleTracker(config.get('whale_config', {}))
        self.exchange_monitor = ExchangeWalletMonitor(config.get('exchange_config', {}))
        self.defi_monitor = DeFiMonitor(config.get('defi_config', {}))
        self.gas_monitor = GasMonitor(config.get('gas_config', {}))
        
        # 监控数据缓存
        self.latest_data = {
            'whale_activities': [],
            'exchange_flows': [],
            'defi_events': [],
            'gas_metrics': {}
        }
        
        # 警报阈值
        self.alert_thresholds = {
            'large_transfer_usd': 1000000,  # 100万美元
            'gas_spike_multiplier': 3,      # Gas费异常倍数
            'exchange_outflow_usd': 10000000,  # 1000万美元
            'defi_liquidation_usd': 500000     # 50万美元清算
        }
    
    async def start(self):
        """启动监控"""
        self.is_running = True
        logger.info("链上监控器启动")
        
        # 并发运行所有监控任务
        tasks = [
            self._monitor_whales(),
            self._monitor_exchanges(),
            self._monitor_defi(),
            self._monitor_gas()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """停止监控"""
        self.is_running = False
        logger.info("链上监控器停止")
    
    async def _monitor_whales(self):
        """监控巨鲸活动"""
        while self.is_running:
            try:
                # 获取巨鲸活动数据
                whale_data = await self.whale_tracker.get_whale_activities()
                
                # 更新缓存
                self.latest_data['whale_activities'] = whale_data
                
                # 检查是否需要报警
                for activity in whale_data:
                    if activity.get('value_usd', 0) > self.alert_thresholds['large_transfer_usd']:
                        await self._send_alert('WHALE_ALERT', activity)
                
                # 间隔30秒
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"巨鲸监控错误: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_exchanges(self):
        """监控交易所钱包"""
        while self.is_running:
            try:
                # 获取交易所资金流动
                exchange_flows = await self.exchange_monitor.get_exchange_flows()
                
                # 更新缓存
                self.latest_data['exchange_flows'] = exchange_flows
                
                # 检查大额流出
                for flow in exchange_flows:
                    if flow.get('type') == 'outflow' and flow.get('value_usd', 0) > self.alert_thresholds['exchange_outflow_usd']:
                        await self._send_alert('EXCHANGE_OUTFLOW', flow)
                
                # 间隔60秒
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"交易所监控错误: {e}")
                await asyncio.sleep(120)
    
    async def _monitor_defi(self):
        """监控DeFi协议"""
        while self.is_running:
            try:
                # 获取DeFi事件
                defi_events = await self.defi_monitor.get_defi_events()
                
                # 更新缓存
                self.latest_data['defi_events'] = defi_events
                
                # 检查大额清算
                for event in defi_events:
                    if event.get('type') == 'liquidation' and event.get('value_usd', 0) > self.alert_thresholds['defi_liquidation_usd']:
                        await self._send_alert('DEFI_LIQUIDATION', event)
                
                # 间隔45秒
                await asyncio.sleep(45)
                
            except Exception as e:
                logger.error(f"DeFi监控错误: {e}")
                await asyncio.sleep(90)
    
    async def _monitor_gas(self):
        """监控Gas费"""
        while self.is_running:
            try:
                # 获取Gas费数据
                gas_metrics = await self.gas_monitor.get_gas_metrics()
                
                # 更新缓存
                self.latest_data['gas_metrics'] = gas_metrics
                
                # 检查Gas费异常
                if gas_metrics.get('spike_detected'):
                    await self._send_alert('GAS_SPIKE', gas_metrics)
                
                # 间隔15秒（Gas费变化较快）
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"Gas监控错误: {e}")
                await asyncio.sleep(30)
    
    async def _send_alert(self, alert_type: str, data: Dict[str, Any]):
        """
        发送警报
        
        Args:
            alert_type: 警报类型
            data: 警报数据
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'severity': self._get_severity(alert_type, data),
            'data': data
        }
        
        logger.warning(f"[{alert_type}] {json.dumps(alert, indent=2, default=str)}")
        
        # TODO: 发送到通知系统（8号窗口）
        
    def _get_severity(self, alert_type: str, data: Dict[str, Any]) -> str:
        """
        判断警报严重程度
        
        Args:
            alert_type: 警报类型
            data: 警报数据
            
        Returns:
            严重程度: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
        """
        if alert_type == 'WHALE_ALERT':
            value = data.get('value_usd', 0)
            if value > 10000000:  # 1000万美元
                return 'CRITICAL'
            elif value > 5000000:  # 500万美元
                return 'HIGH'
            else:
                return 'MEDIUM'
        
        elif alert_type == 'EXCHANGE_OUTFLOW':
            value = data.get('value_usd', 0)
            if value > 50000000:  # 5000万美元
                return 'CRITICAL'
            elif value > 20000000:  # 2000万美元
                return 'HIGH'
            else:
                return 'MEDIUM'
        
        elif alert_type == 'DEFI_LIQUIDATION':
            return 'HIGH'  # 清算都是高优先级
        
        elif alert_type == 'GAS_SPIKE':
            multiplier = data.get('spike_multiplier', 1)
            if multiplier > 5:
                return 'CRITICAL'
            elif multiplier > 3:
                return 'HIGH'
            else:
                return 'MEDIUM'
        
        return 'LOW'
    
    def get_latest_data(self) -> Dict[str, Any]:
        """获取最新监控数据"""
        return self.latest_data.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        return {
            'timestamp': datetime.now().isoformat(),
            'whale_activities_count': len(self.latest_data['whale_activities']),
            'exchange_flows_count': len(self.latest_data['exchange_flows']),
            'defi_events_count': len(self.latest_data['defi_events']),
            'current_gas': self.latest_data['gas_metrics'].get('current_gwei', 0),
            'is_running': self.is_running
        }