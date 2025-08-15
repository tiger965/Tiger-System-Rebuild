"""
Window 2 - 账户管理器
负责查询账户余额、持仓、订单等信息
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
import ccxt
from loguru import logger


class AccountManager:
    """账户管理器"""
    
    def __init__(self):
        """初始化账户管理器"""
        self.okx_client = None
        self.binance_client = None
        self._init_exchanges()
        self.account_cache = {}
        self.cache_ttl = 30  # 账户信息缓存30秒
        
    def _init_exchanges(self):
        """初始化交易所客户端"""
        try:
            # OKX配置
            self.okx_client = ccxt.okx({
                'apiKey': '79d7b5b4-2e9b-4a31-be9c-95527d618739',
                'secret': '070B16A29AF22C13A67D9CB807B5693D',
                'password': 'Yzh198796&',
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            # Binance配置（通过代理）
            self.binance_client = ccxt.binance({
                'apiKey': 'cKnsfwbBg9nYj1lsPfoK26UtAYf8Oiq7TALPIBQC6UYfJ2p4sMJu5nRRfooVSN4t',
                'secret': 'iKWUuPcvWrCs3QGMd3it9LuN408TQaRdh7amTpY4mbLQo5K8kvDOVyaQoN7P1NYj',
                'enableRateLimit': True,
                'proxies': {
                    'http': 'http://127.0.0.1:1080',
                    'https': 'http://127.0.0.1:1080'
                },
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            logger.info("账户管理器初始化成功")
            
        except Exception as e:
            logger.error(f"初始化交易所失败: {e}")
            
    def get_okx_account(self) -> Dict:
        """
        获取OKX账户信息
        使用配置的API密钥
        
        Returns:
            {
                'exchange': 'okx',
                'total_balance': 10000.00,
                'available_balance': 8500.00,
                'used_balance': 1500.00,
                'balances': {
                    'USDT': {'free': 5000.00, 'used': 1000.00, 'total': 6000.00},
                    'BTC': {'free': 0.1, 'used': 0.05, 'total': 0.15}
                },
                'positions': [...],
                'timestamp': 1234567890
            }
        """
        cache_key = 'okx_account'
        
        # 检查缓存
        if cache_key in self.account_cache:
            cache_time, data = self.account_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return data
                
        try:
            # 获取账户余额
            balance = self.okx_client.fetch_balance()
            
            # 计算总余额（以USDT计）
            total_balance = balance['USDT']['total'] if 'USDT' in balance else 0
            available_balance = balance['USDT']['free'] if 'USDT' in balance else 0
            used_balance = balance['USDT']['used'] if 'USDT' in balance else 0
            
            # 处理其他币种余额（简化处理，实际应该转换为USDT价值）
            balances = {}
            for currency, bal in balance.items():
                if currency not in ['free', 'used', 'total', 'info'] and bal['total'] > 0:
                    balances[currency] = {
                        'free': bal['free'],
                        'used': bal['used'],
                        'total': bal['total']
                    }
            
            result = {
                'exchange': 'okx',
                'total_balance': total_balance,
                'available_balance': available_balance,
                'used_balance': used_balance,
                'balances': balances,
                'positions': [],  # TODO: 获取持仓信息
                'timestamp': int(time.time() * 1000)
            }
            
            # 更新缓存
            self.account_cache[cache_key] = (time.time(), result)
            
            logger.info(f"获取OKX账户信息成功，总余额: ${total_balance:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"获取OKX账户信息失败: {e}")
            return {}
            
    def get_binance_account(self) -> Dict:
        """
        获取Binance账户信息
        通过VPN代理访问
        
        Returns:
            类似OKX的格式
        """
        cache_key = 'binance_account'
        
        # 检查缓存
        if cache_key in self.account_cache:
            cache_time, data = self.account_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return data
                
        try:
            # 获取账户余额
            balance = self.binance_client.fetch_balance()
            
            # 计算总余额
            total_balance = balance['USDT']['total'] if 'USDT' in balance else 0
            available_balance = balance['USDT']['free'] if 'USDT' in balance else 0
            used_balance = balance['USDT']['used'] if 'USDT' in balance else 0
            
            # 处理其他币种余额
            balances = {}
            for currency, bal in balance.items():
                if currency not in ['free', 'used', 'total', 'info'] and bal['total'] > 0:
                    balances[currency] = {
                        'free': bal['free'],
                        'used': bal['used'],
                        'total': bal['total']
                    }
            
            result = {
                'exchange': 'binance',
                'total_balance': total_balance,
                'available_balance': available_balance,
                'used_balance': used_balance,
                'balances': balances,
                'positions': [],
                'timestamp': int(time.time() * 1000)
            }
            
            # 更新缓存
            self.account_cache[cache_key] = (time.time(), result)
            
            logger.info(f"获取Binance账户信息成功，总余额: ${total_balance:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"获取Binance账户信息失败: {e}")
            return {}
            
    def get_positions(self, exchange: str) -> List[Dict]:
        """
        获取当前持仓
        
        Args:
            exchange: 交易所名称
            
        Returns:
            [{
                'symbol': 'BTC/USDT',
                'side': 'long',  # long/short
                'size': 0.5,
                'entry_price': 67000.00,
                'current_price': 67500.00,
                'pnl': 250.00,
                'pnl_percentage': 0.0075,  # 0.75%
                'margin': 1000.00,
                'leverage': 2.0
            }]
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取持仓信息
            positions = client.fetch_positions()
            
            result = []
            for pos in positions:
                if pos['size'] > 0:  # 只返回有持仓的
                    result.append({
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'size': pos['size'],
                        'entry_price': pos['entryPrice'],
                        'current_price': pos['markPrice'],
                        'pnl': pos['unrealizedPnl'],
                        'pnl_percentage': pos['percentage'],
                        'margin': pos['initialMargin'],
                        'leverage': pos['leverage']
                    })
                    
            logger.info(f"获取{exchange}持仓成功，共{len(result)}个")
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}持仓失败: {e}")
            return []
            
    def get_open_orders(self, exchange: str, symbol: str = None) -> List[Dict]:
        """
        获取未成交订单
        
        Args:
            exchange: 交易所名称
            symbol: 交易对，为None时获取所有
            
        Returns:
            [{
                'id': '123456789',
                'symbol': 'BTC/USDT',
                'type': 'limit',
                'side': 'buy',
                'amount': 0.1,
                'price': 67000.00,
                'filled': 0.05,
                'remaining': 0.05,
                'status': 'open',
                'timestamp': 1234567890
            }]
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            if symbol:
                orders = client.fetch_open_orders(symbol)
            else:
                orders = client.fetch_open_orders()
                
            result = []
            for order in orders:
                result.append({
                    'id': order['id'],
                    'symbol': order['symbol'],
                    'type': order['type'],
                    'side': order['side'],
                    'amount': order['amount'],
                    'price': order['price'],
                    'filled': order['filled'],
                    'remaining': order['remaining'],
                    'status': order['status'],
                    'timestamp': order['timestamp']
                })
                
            logger.info(f"获取{exchange}未成交订单成功，共{len(result)}个")
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}未成交订单失败: {e}")
            return []
            
    def get_trading_fees(self, exchange: str) -> Dict:
        """
        获取交易手续费
        
        Returns:
            {
                'maker': 0.001,  # 0.1%
                'taker': 0.001,  # 0.1%
                'tier': 'VIP1'
            }
        """
        try:
            client = self.okx_client if exchange == 'okx' else self.binance_client
            
            # 获取交易费率
            fees = client.fetch_trading_fees()
            
            result = {
                'maker': fees.get('maker', 0.001),
                'taker': fees.get('taker', 0.001),
                'tier': 'Regular'  # 简化处理
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}交易费率失败: {e}")
            return {'maker': 0.001, 'taker': 0.001, 'tier': 'Unknown'}
            
    def get_account_summary(self, exchange: str) -> Dict:
        """
        获取账户概要信息
        整合余额、持仓、订单等信息
        
        Returns:
            {
                'exchange': 'okx',
                'account_info': {...},
                'positions': [...],
                'open_orders': [...],
                'trading_fees': {...},
                'risk_level': 0.3,  # 风险度
                'available_margin': 5000.00
            }
        """
        try:
            # 获取各种信息
            if exchange == 'okx':
                account_info = self.get_okx_account()
            else:
                account_info = self.get_binance_account()
                
            positions = self.get_positions(exchange)
            open_orders = self.get_open_orders(exchange)
            trading_fees = self.get_trading_fees(exchange)
            
            # 计算风险度
            total_pnl = sum([pos['pnl'] for pos in positions if pos['pnl']])
            risk_level = abs(total_pnl) / account_info.get('total_balance', 1) if account_info.get('total_balance', 0) > 0 else 0
            
            result = {
                'exchange': exchange,
                'account_info': account_info,
                'positions': positions,
                'open_orders': open_orders,
                'trading_fees': trading_fees,
                'risk_level': min(risk_level, 1.0),  # 最大1.0
                'available_margin': account_info.get('available_balance', 0),
                'timestamp': int(time.time() * 1000)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取{exchange}账户概要失败: {e}")
            return {}


# 测试代码
if __name__ == "__main__":
    manager = AccountManager()
    
    print("\n=== 测试账户管理器 ===")
    
    # 测试OKX账户（如果有API权限的话）
    print("\n--- OKX账户信息 ---")
    try:
        okx_account = manager.get_okx_account()
        if okx_account:
            print(f"总余额: ${okx_account['total_balance']:.2f}")
            print(f"可用余额: ${okx_account['available_balance']:.2f}")
            print(f"币种数量: {len(okx_account['balances'])}")
        else:
            print("无法获取OKX账户信息（可能需要API权限）")
    except Exception as e:
        print(f"OKX账户测试失败: {e}")
    
    # 测试Binance账户
    print("\n--- Binance账户信息 ---")
    try:
        binance_account = manager.get_binance_account()
        if binance_account:
            print(f"总余额: ${binance_account['total_balance']:.2f}")
            print(f"可用余额: ${binance_account['available_balance']:.2f}")
            print(f"币种数量: {len(binance_account['balances'])}")
        else:
            print("无法获取Binance账户信息（可能需要代理或API权限）")
    except Exception as e:
        print(f"Binance账户测试失败: {e}")
    
    # 测试交易费率
    print("\n--- 交易费率 ---")
    for exchange in ['okx', 'binance']:
        try:
            fees = manager.get_trading_fees(exchange)
            print(f"{exchange}: Maker {fees['maker']:.4f}%, Taker {fees['taker']:.4f}%")
        except Exception as e:
            print(f"{exchange}费率获取失败: {e}")