"""
巨鲸地址追踪器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

class WhaleTracker:
    """巨鲸地址追踪器"""
    
    # 知名巨鲸地址（示例）
    KNOWN_WHALES = {
        'ETH': [
            '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH Contract
            '0x00000000219ab540356cBB839Cbe05303d7705Fa',  # ETH 2.0 Deposit
            '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',  # Binance 7
        ],
        'BTC': [
            '1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ',  # Binance Cold Wallet
            '34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo',  # Binance Cold Wallet 2
            'bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97',  # Bitfinex Cold
        ]
    }
    
    # 阈值设置
    THRESHOLDS = {
        'BTC': 100,      # 100 BTC
        'ETH': 1000,     # 1000 ETH
        'USDT': 1000000, # 100万 USDT
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化巨鲸追踪器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.etherscan_api_key = config.get('etherscan_api_key', '')
        self.bscscan_api_key = config.get('bscscan_api_key', '')
        self.blockchain_info_api = 'https://blockchain.info'
        
        # API限流控制
        self.rate_limits = {
            'etherscan': 5,  # 5次/秒
            'bscscan': 5,    # 5次/秒
            'blockchain': 10  # 10次/秒
        }
        
        # 缓存最近的交易
        self.recent_transactions = []
        self.monitored_addresses = self._load_monitored_addresses()
    
    def _load_monitored_addresses(self) -> Dict[str, List[str]]:
        """加载监控地址列表"""
        addresses = {
            'ETH': self.KNOWN_WHALES['ETH'].copy(),
            'BTC': self.KNOWN_WHALES['BTC'].copy(),
            'BSC': []
        }
        
        # 从配置中加载额外的地址
        if 'custom_addresses' in self.config:
            for chain, addrs in self.config['custom_addresses'].items():
                if chain in addresses:
                    addresses[chain].extend(addrs)
        
        return addresses
    
    async def get_whale_activities(self) -> List[Dict[str, Any]]:
        """
        获取巨鲸活动
        
        Returns:
            巨鲸活动列表
        """
        activities = []
        
        # 并发获取各链数据
        tasks = [
            self._get_eth_whale_activities(),
            self._get_bsc_whale_activities(),
            self._get_btc_whale_activities()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"获取巨鲸活动失败: {result}")
            else:
                activities.extend(result)
        
        # 按时间排序
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 缓存最近的交易
        self.recent_transactions = activities[:100]
        
        return activities
    
    async def _get_eth_whale_activities(self) -> List[Dict[str, Any]]:
        """获取以太坊巨鲸活动"""
        if not self.etherscan_api_key:
            logger.warning("未配置Etherscan API密钥")
            return []
        
        activities = []
        
        async with aiohttp.ClientSession() as session:
            for address in self.monitored_addresses['ETH'][:10]:  # 限制查询数量
                try:
                    # 获取地址最近的交易
                    url = f"https://api.etherscan.io/api"
                    params = {
                        'module': 'account',
                        'action': 'txlist',
                        'address': address,
                        'startblock': 0,
                        'endblock': 99999999,
                        'page': 1,
                        'offset': 10,
                        'sort': 'desc',
                        'apikey': self.etherscan_api_key
                    }
                    
                    async with session.get(url, params=params) as response:
                        data = await response.json()
                        
                        if data['status'] == '1' and data['result']:
                            for tx in data['result']:
                                # 转换Wei到ETH
                                value_eth = int(tx['value']) / 10**18
                                
                                # 检查是否达到阈值
                                if value_eth >= self.THRESHOLDS['ETH']:
                                    activities.append({
                                        'chain': 'ETH',
                                        'hash': tx['hash'],
                                        'from': tx['from'],
                                        'to': tx['to'],
                                        'value': value_eth,
                                        'value_usd': value_eth * 2500,  # 假设ETH价格
                                        'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])).isoformat(),
                                        'block': tx['blockNumber'],
                                        'type': 'whale_transfer'
                                    })
                    
                    # 限流
                    await asyncio.sleep(1 / self.rate_limits['etherscan'])
                    
                except Exception as e:
                    logger.error(f"获取ETH地址 {address} 数据失败: {e}")
        
        return activities
    
    async def _get_bsc_whale_activities(self) -> List[Dict[str, Any]]:
        """获取BSC巨鲸活动"""
        if not self.bscscan_api_key:
            logger.warning("未配置BSCscan API密钥")
            return []
        
        activities = []
        
        # BSC实现逻辑类似ETH
        # 这里简化处理
        
        return activities
    
    async def _get_btc_whale_activities(self) -> List[Dict[str, Any]]:
        """获取比特币巨鲸活动"""
        activities = []
        
        async with aiohttp.ClientSession() as session:
            for address in self.monitored_addresses['BTC'][:5]:  # 限制查询数量
                try:
                    # 使用blockchain.info API
                    url = f"{self.blockchain_info_api}/rawaddr/{address}"
                    params = {'limit': 10}
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'txs' in data:
                                for tx in data['txs'][:10]:
                                    # 计算交易总额
                                    total_out = sum(out.get('value', 0) for out in tx.get('out', [])) / 10**8
                                    
                                    if total_out >= self.THRESHOLDS['BTC']:
                                        activities.append({
                                            'chain': 'BTC',
                                            'hash': tx.get('hash'),
                                            'value': total_out,
                                            'value_usd': total_out * 65000,  # 假设BTC价格
                                            'timestamp': datetime.fromtimestamp(tx.get('time', 0)).isoformat(),
                                            'type': 'whale_transfer'
                                        })
                    
                    # 限流
                    await asyncio.sleep(1 / self.rate_limits['blockchain'])
                    
                except Exception as e:
                    logger.error(f"获取BTC地址 {address} 数据失败: {e}")
        
        return activities
    
    async def add_monitored_address(self, chain: str, address: str) -> bool:
        """
        添加监控地址
        
        Args:
            chain: 链类型 (ETH, BSC, BTC)
            address: 地址
            
        Returns:
            是否添加成功
        """
        if chain not in self.monitored_addresses:
            return False
        
        if address not in self.monitored_addresses[chain]:
            self.monitored_addresses[chain].append(address)
            logger.info(f"添加监控地址: {chain} - {address}")
            return True
        
        return False
    
    async def remove_monitored_address(self, chain: str, address: str) -> bool:
        """
        移除监控地址
        
        Args:
            chain: 链类型
            address: 地址
            
        Returns:
            是否移除成功
        """
        if chain in self.monitored_addresses and address in self.monitored_addresses[chain]:
            self.monitored_addresses[chain].remove(address)
            logger.info(f"移除监控地址: {chain} - {address}")
            return True
        
        return False
    
    def get_monitored_addresses(self) -> Dict[str, List[str]]:
        """获取当前监控的地址列表"""
        return self.monitored_addresses.copy()
    
    def get_recent_transactions(self) -> List[Dict[str, Any]]:
        """获取最近的交易记录"""
        return self.recent_transactions.copy()