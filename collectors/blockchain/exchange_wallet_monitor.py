"""
交易所钱包监控器
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ExchangeWalletMonitor:
    """交易所钱包监控器"""
    
    # 已知的交易所钱包地址
    EXCHANGE_WALLETS = {
        'Binance': {
            'ETH': [
                '0x28C6c06298d514Db089934071355E5743bf21d60',  # Binance 14
                '0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549',  # Binance 15
                '0xDFd5293D8e347dFe59E90eFd55b2956a1343963d',  # Binance 16
            ],
            'BTC': [
                '34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo',  # Binance Cold
                '3LYJfcfHPXYJreMsASk2jkn69LWEYKzexb',  # Binance Hot
            ]
        },
        'OKX': {
            'ETH': [
                '0x6Fb624B5d129beF02769984B163e021562593E30',  # OKX 1
                '0x461249076b88189f8AC9418De28B365859E46BfB',  # OKX 2
            ],
            'BTC': [
                '1FzWLkAahHooV3kzTgyx6qsswXJ6sCXkSR',  # OKX Cold
            ]
        },
        'Coinbase': {
            'ETH': [
                '0x71660c4005BA85c37ccec55d0C4493E66Fe775d3',  # Coinbase 1
                '0x503828976D22510aad0201ac7EC88293211D23Da',  # Coinbase 2
            ],
            'BTC': [
                '1EgM4BiR68S8iPzqtgG8apPfCx45cNj5qm',  # Coinbase Cold
            ]
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化交易所钱包监控器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.etherscan_api_key = config.get('etherscan_api_key', '')
        self.bscscan_api_key = config.get('bscscan_api_key', '')
        
        # 缓存数据
        self.wallet_balances = {}  # 钱包余额缓存
        self.flow_history = []     # 资金流动历史
        
        # 初始化钱包列表
        self.monitored_wallets = self._init_wallet_list()
    
    def _init_wallet_list(self) -> Dict[str, Dict[str, List[str]]]:
        """初始化监控钱包列表"""
        wallets = {}
        for exchange, chains in self.EXCHANGE_WALLETS.items():
            wallets[exchange] = chains.copy()
        
        # 添加自定义钱包
        if 'custom_wallets' in self.config:
            for exchange, chains in self.config['custom_wallets'].items():
                if exchange not in wallets:
                    wallets[exchange] = {}
                for chain, addresses in chains.items():
                    if chain not in wallets[exchange]:
                        wallets[exchange][chain] = []
                    wallets[exchange][chain].extend(addresses)
        
        return wallets
    
    async def get_exchange_flows(self) -> List[Dict[str, Any]]:
        """
        获取交易所资金流动
        
        Returns:
            资金流动列表
        """
        flows = []
        
        # 并发获取各交易所数据
        tasks = []
        for exchange, chains in self.monitored_wallets.items():
            for chain, addresses in chains.items():
                if chain == 'ETH':
                    tasks.append(self._get_eth_flows(exchange, addresses))
                elif chain == 'BTC':
                    tasks.append(self._get_btc_flows(exchange, addresses))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"获取交易所资金流动失败: {result}")
            else:
                flows.extend(result)
        
        # 分析资金流向
        analyzed_flows = self._analyze_flows(flows)
        
        # 更新历史记录
        self.flow_history.extend(analyzed_flows)
        self.flow_history = self.flow_history[-1000:]  # 保留最近1000条
        
        return analyzed_flows
    
    async def _get_eth_flows(self, exchange: str, addresses: List[str]) -> List[Dict[str, Any]]:
        """获取以太坊资金流动"""
        if not self.etherscan_api_key:
            return []
        
        flows = []
        
        async with aiohttp.ClientSession() as session:
            for address in addresses[:3]:  # 限制查询数量
                try:
                    # 获取地址余额
                    balance_url = "https://api.etherscan.io/api"
                    balance_params = {
                        'module': 'account',
                        'action': 'balance',
                        'address': address,
                        'tag': 'latest',
                        'apikey': self.etherscan_api_key
                    }
                    
                    async with session.get(balance_url, params=balance_params) as response:
                        data = await response.json()
                        if data['status'] == '1':
                            balance = int(data['result']) / 10**18
                            
                            # 检查余额变化
                            prev_balance = self.wallet_balances.get(address, balance)
                            balance_change = balance - prev_balance
                            self.wallet_balances[address] = balance
                            
                            if abs(balance_change) > 100:  # 100 ETH变化
                                flows.append({
                                    'exchange': exchange,
                                    'chain': 'ETH',
                                    'address': address,
                                    'balance': balance,
                                    'change': balance_change,
                                    'change_usd': balance_change * 2500,  # 假设价格
                                    'type': 'inflow' if balance_change > 0 else 'outflow',
                                    'timestamp': datetime.now().isoformat()
                                })
                    
                    # 获取最近交易
                    tx_url = "https://api.etherscan.io/api"
                    tx_params = {
                        'module': 'account',
                        'action': 'txlist',
                        'address': address,
                        'startblock': 0,
                        'endblock': 99999999,
                        'page': 1,
                        'offset': 5,
                        'sort': 'desc',
                        'apikey': self.etherscan_api_key
                    }
                    
                    async with session.get(tx_url, params=tx_params) as response:
                        data = await response.json()
                        if data['status'] == '1' and data['result']:
                            for tx in data['result']:
                                value = int(tx['value']) / 10**18
                                if value > 100:  # 100 ETH以上
                                    flows.append({
                                        'exchange': exchange,
                                        'chain': 'ETH',
                                        'hash': tx['hash'],
                                        'from': tx['from'],
                                        'to': tx['to'],
                                        'value': value,
                                        'value_usd': value * 2500,
                                        'type': 'inflow' if tx['to'].lower() == address.lower() else 'outflow',
                                        'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])).isoformat()
                                    })
                    
                    await asyncio.sleep(0.2)  # 限流
                    
                except Exception as e:
                    logger.error(f"获取{exchange} ETH钱包 {address} 数据失败: {e}")
        
        return flows
    
    async def _get_btc_flows(self, exchange: str, addresses: List[str]) -> List[Dict[str, Any]]:
        """获取比特币资金流动"""
        flows = []
        
        async with aiohttp.ClientSession() as session:
            for address in addresses[:2]:  # 限制查询数量
                try:
                    url = f"https://blockchain.info/rawaddr/{address}"
                    params = {'limit': 5}
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # 获取余额
                            balance = data.get('final_balance', 0) / 10**8
                            
                            # 检查余额变化
                            prev_balance = self.wallet_balances.get(address, balance)
                            balance_change = balance - prev_balance
                            self.wallet_balances[address] = balance
                            
                            if abs(balance_change) > 10:  # 10 BTC变化
                                flows.append({
                                    'exchange': exchange,
                                    'chain': 'BTC',
                                    'address': address,
                                    'balance': balance,
                                    'change': balance_change,
                                    'change_usd': balance_change * 65000,  # 假设价格
                                    'type': 'inflow' if balance_change > 0 else 'outflow',
                                    'timestamp': datetime.now().isoformat()
                                })
                            
                            # 分析最近交易
                            for tx in data.get('txs', [])[:5]:
                                total_out = sum(out.get('value', 0) for out in tx.get('out', [])) / 10**8
                                if total_out > 10:  # 10 BTC以上
                                    flows.append({
                                        'exchange': exchange,
                                        'chain': 'BTC',
                                        'hash': tx.get('hash'),
                                        'value': total_out,
                                        'value_usd': total_out * 65000,
                                        'type': 'transfer',
                                        'timestamp': datetime.fromtimestamp(tx.get('time', 0)).isoformat()
                                    })
                    
                    await asyncio.sleep(0.1)  # 限流
                    
                except Exception as e:
                    logger.error(f"获取{exchange} BTC钱包 {address} 数据失败: {e}")
        
        return flows
    
    def _analyze_flows(self, flows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分析资金流向
        
        Args:
            flows: 原始资金流动数据
            
        Returns:
            分析后的资金流动
        """
        analyzed = []
        
        # 按交易所分组
        exchange_flows = {}
        for flow in flows:
            exchange = flow.get('exchange', 'Unknown')
            if exchange not in exchange_flows:
                exchange_flows[exchange] = {'inflow': 0, 'outflow': 0, 'transactions': []}
            
            if 'type' in flow:
                if flow['type'] == 'inflow':
                    exchange_flows[exchange]['inflow'] += flow.get('value_usd', 0)
                elif flow['type'] == 'outflow':
                    exchange_flows[exchange]['outflow'] += flow.get('value_usd', 0)
                
                exchange_flows[exchange]['transactions'].append(flow)
        
        # 生成分析结果
        for exchange, data in exchange_flows.items():
            net_flow = data['inflow'] - data['outflow']
            
            # 判断资金流向趋势
            if abs(net_flow) > 1000000:  # 100万美元以上
                analyzed.append({
                    'exchange': exchange,
                    'net_flow_usd': net_flow,
                    'inflow_usd': data['inflow'],
                    'outflow_usd': data['outflow'],
                    'type': 'major_flow',
                    'direction': 'inflow' if net_flow > 0 else 'outflow',
                    'timestamp': datetime.now().isoformat(),
                    'transactions': data['transactions'][:10]  # 保留前10笔
                })
        
        # 添加原始大额交易
        for flow in flows:
            if flow.get('value_usd', 0) > 5000000:  # 500万美元以上
                analyzed.append(flow)
        
        return analyzed
    
    def get_exchange_balances(self) -> Dict[str, Dict[str, float]]:
        """
        获取交易所余额汇总
        
        Returns:
            交易所余额字典
        """
        balances = {}
        
        for exchange, chains in self.monitored_wallets.items():
            balances[exchange] = {'total_usd': 0}
            
            for chain, addresses in chains.items():
                chain_balance = 0
                for address in addresses:
                    if address in self.wallet_balances:
                        balance = self.wallet_balances[address]
                        if chain == 'ETH':
                            chain_balance += balance * 2500
                        elif chain == 'BTC':
                            chain_balance += balance * 65000
                
                balances[exchange][chain] = chain_balance
                balances[exchange]['total_usd'] += chain_balance
        
        return balances
    
    def get_flow_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取资金流动统计
        
        Args:
            hours: 统计时间范围（小时）
            
        Returns:
            统计数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        stats = {
            'period_hours': hours,
            'total_inflow_usd': 0,
            'total_outflow_usd': 0,
            'net_flow_usd': 0,
            'by_exchange': {},
            'major_flows': []
        }
        
        for flow in self.flow_history:
            try:
                flow_time = datetime.fromisoformat(flow['timestamp'])
                if flow_time > cutoff_time:
                    exchange = flow.get('exchange', 'Unknown')
                    
                    if exchange not in stats['by_exchange']:
                        stats['by_exchange'][exchange] = {
                            'inflow': 0,
                            'outflow': 0
                        }
                    
                    if flow.get('type') == 'inflow':
                        amount = flow.get('value_usd', 0)
                        stats['total_inflow_usd'] += amount
                        stats['by_exchange'][exchange]['inflow'] += amount
                    elif flow.get('type') == 'outflow':
                        amount = flow.get('value_usd', 0)
                        stats['total_outflow_usd'] += amount
                        stats['by_exchange'][exchange]['outflow'] += amount
                    
                    # 记录大额流动
                    if flow.get('value_usd', 0) > 10000000:  # 1000万美元
                        stats['major_flows'].append(flow)
            
            except Exception as e:
                logger.error(f"处理流动记录失败: {e}")
        
        stats['net_flow_usd'] = stats['total_inflow_usd'] - stats['total_outflow_usd']
        
        return stats