"""
DeFi协议监控器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DeFiMonitor:
    """DeFi协议监控器"""
    
    # 主要DeFi协议合约地址
    DEFI_CONTRACTS = {
        'Uniswap': {
            'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
        },
        'AAVE': {
            'lending_pool': '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9',
            'price_oracle': '0xA50ba011c48153De246E5192C8f9258A2ba79Ca9',
        },
        'Compound': {
            'comptroller': '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B',
            'cETH': '0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5',
        },
        'MakerDAO': {
            'dai': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
            'vat': '0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B',
        }
    }
    
    # 监控阈值
    THRESHOLDS = {
        'large_swap_usd': 1000000,        # 100万美元大额交换
        'liquidation_usd': 500000,        # 50万美元清算
        'supply_change_percent': 10,      # 供应量变化10%
        'tvl_change_percent': 5,          # TVL变化5%
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DeFi监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.etherscan_api_key = config.get('etherscan_api_key', '')
        self.infura_project_id = config.get('infura_project_id', '')
        
        # 缓存数据
        self.protocol_tvl = {}  # 协议TVL
        self.recent_events = []  # 最近事件
        self.liquidations = []  # 清算记录
    
    async def get_defi_events(self) -> List[Dict[str, Any]]:
        """
        获取DeFi事件
        
        Returns:
            DeFi事件列表
        """
        events = []
        
        # 并发获取各协议数据
        tasks = [
            self._monitor_uniswap(),
            self._monitor_aave(),
            self._monitor_compound(),
            self._monitor_makerdao()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"获取DeFi事件失败: {result}")
            else:
                events.extend(result)
        
        # 按时间排序
        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 更新缓存
        self.recent_events = events[:100]
        
        return events
    
    async def _monitor_uniswap(self) -> List[Dict[str, Any]]:
        """监控Uniswap"""
        events = []
        
        if not self.etherscan_api_key:
            return events
        
        async with aiohttp.ClientSession() as session:
            try:
                # 获取Uniswap Router的最近交易
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': self.DEFI_CONTRACTS['Uniswap']['router'],
                    'startblock': 0,
                    'endblock': 99999999,
                    'page': 1,
                    'offset': 20,
                    'sort': 'desc',
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data['status'] == '1' and data['result']:
                        for tx in data['result']:
                            # 分析大额交易
                            value = int(tx.get('value', 0)) / 10**18
                            
                            if value > 100:  # 100 ETH以上
                                events.append({
                                    'protocol': 'Uniswap',
                                    'type': 'large_swap',
                                    'hash': tx['hash'],
                                    'value_eth': value,
                                    'value_usd': value * 2500,  # 假设价格
                                    'from': tx['from'],
                                    'to': tx['to'],
                                    'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])).isoformat(),
                                    'block': tx['blockNumber']
                                })
                
            except Exception as e:
                logger.error(f"监控Uniswap失败: {e}")
        
        return events
    
    async def _monitor_aave(self) -> List[Dict[str, Any]]:
        """监控AAVE"""
        events = []
        
        if not self.etherscan_api_key:
            return events
        
        async with aiohttp.ClientSession() as session:
            try:
                # 获取AAVE Lending Pool的事件日志
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'logs',
                    'action': 'getLogs',
                    'address': self.DEFI_CONTRACTS['AAVE']['lending_pool'],
                    'fromBlock': 'latest',
                    'toBlock': 'latest',
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data['status'] == '1' and data['result']:
                        for log in data['result'][:10]:
                            # 检测清算事件
                            # LiquidationCall事件的topic
                            if log['topics'][0] == '0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286':
                                events.append({
                                    'protocol': 'AAVE',
                                    'type': 'liquidation',
                                    'hash': log['transactionHash'],
                                    'timestamp': datetime.now().isoformat(),
                                    'block': int(log['blockNumber'], 16),
                                    'severity': 'HIGH'
                                })
                                
                                # 添加到清算记录
                                self.liquidations.append({
                                    'protocol': 'AAVE',
                                    'hash': log['transactionHash'],
                                    'timestamp': datetime.now().isoformat()
                                })
                
            except Exception as e:
                logger.error(f"监控AAVE失败: {e}")
        
        return events
    
    async def _monitor_compound(self) -> List[Dict[str, Any]]:
        """监控Compound"""
        events = []
        
        if not self.etherscan_api_key:
            return events
        
        async with aiohttp.ClientSession() as session:
            try:
                # 获取cETH合约的供应量
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'stats',
                    'action': 'tokensupply',
                    'contractaddress': self.DEFI_CONTRACTS['Compound']['cETH'],
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data['status'] == '1':
                        current_supply = int(data['result']) / 10**8  # cETH has 8 decimals
                        
                        # 检查供应量变化
                        prev_supply = self.protocol_tvl.get('compound_ceth_supply', current_supply)
                        supply_change = ((current_supply - prev_supply) / prev_supply * 100) if prev_supply > 0 else 0
                        
                        self.protocol_tvl['compound_ceth_supply'] = current_supply
                        
                        if abs(supply_change) > self.THRESHOLDS['supply_change_percent']:
                            events.append({
                                'protocol': 'Compound',
                                'type': 'supply_change',
                                'metric': 'cETH_supply',
                                'current_value': current_supply,
                                'change_percent': supply_change,
                                'timestamp': datetime.now().isoformat(),
                                'severity': 'MEDIUM' if abs(supply_change) < 20 else 'HIGH'
                            })
                
            except Exception as e:
                logger.error(f"监控Compound失败: {e}")
        
        return events
    
    async def _monitor_makerdao(self) -> List[Dict[str, Any]]:
        """监控MakerDAO"""
        events = []
        
        if not self.etherscan_api_key:
            return events
        
        async with aiohttp.ClientSession() as session:
            try:
                # 获取DAI供应量
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'stats',
                    'action': 'tokensupply',
                    'contractaddress': self.DEFI_CONTRACTS['MakerDAO']['dai'],
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data['status'] == '1':
                        current_supply = int(data['result']) / 10**18
                        
                        # 检查DAI供应量变化
                        prev_supply = self.protocol_tvl.get('dai_supply', current_supply)
                        supply_change = ((current_supply - prev_supply) / prev_supply * 100) if prev_supply > 0 else 0
                        
                        self.protocol_tvl['dai_supply'] = current_supply
                        
                        if abs(supply_change) > 5:  # DAI供应量变化5%以上
                            events.append({
                                'protocol': 'MakerDAO',
                                'type': 'dai_supply_change',
                                'current_supply': current_supply,
                                'change_percent': supply_change,
                                'timestamp': datetime.now().isoformat(),
                                'severity': 'MEDIUM'
                            })
                
            except Exception as e:
                logger.error(f"监控MakerDAO失败: {e}")
        
        return events
    
    async def get_protocol_tvl(self) -> Dict[str, float]:
        """
        获取各协议TVL
        
        Returns:
            协议TVL字典
        """
        tvl_data = {}
        
        # 这里简化处理，实际应该从DeFi Llama等数据源获取
        tvl_data['Uniswap'] = 5000000000  # 50亿美元
        tvl_data['AAVE'] = 12000000000    # 120亿美元
        tvl_data['Compound'] = 8000000000  # 80亿美元
        tvl_data['MakerDAO'] = 7000000000  # 70亿美元
        
        return tvl_data
    
    async def get_liquidation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取清算统计
        
        Args:
            hours: 统计时间范围
            
        Returns:
            清算统计数据
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        stats = {
            'period_hours': hours,
            'total_liquidations': 0,
            'by_protocol': {},
            'recent_liquidations': []
        }
        
        for liquidation in self.liquidations:
            try:
                liq_time = datetime.fromisoformat(liquidation['timestamp']).timestamp()
                if liq_time > cutoff_time:
                    protocol = liquidation['protocol']
                    
                    if protocol not in stats['by_protocol']:
                        stats['by_protocol'][protocol] = 0
                    
                    stats['by_protocol'][protocol] += 1
                    stats['total_liquidations'] += 1
                    
                    if len(stats['recent_liquidations']) < 10:
                        stats['recent_liquidations'].append(liquidation)
            
            except Exception as e:
                logger.error(f"处理清算记录失败: {e}")
        
        return stats
    
    def get_recent_events(self) -> List[Dict[str, Any]]:
        """获取最近的DeFi事件"""
        return self.recent_events.copy()