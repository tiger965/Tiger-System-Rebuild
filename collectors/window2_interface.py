# -*- coding: utf-8 -*-
"""
窗口2接口 - 获取实时交易所数据
专门为窗口3提供实时资金费率和爆仓数据
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class Window2Interface:
    """窗口2数据接口"""
    
    def __init__(self):
        self.session = None
        
        # 币安API配置
        self.binance_config = {
            "api_key": "cKnsfwbBg9nYj1lsPfoK26UtAYf8Oiq7TALPIBQC6UYfJ2p4sMJu5nRRfooVSN4t",
            "secret_key": "iKWUuPcvWrCs3QGMd3it9LuN408TQaRdh7amTpY4mbLQo5K8kvDOVyaQoN7P1NYj",
            "base_url": "https://fapi.binance.com"
        }
        
        # OKX API配置
        self.okx_config = {
            "base_url": "https://www.okx.com"
        }
        
        print("🔗 窗口2接口已初始化")
        print("📡 数据源: Binance + OKX")

    async def initialize(self):
        """初始化异步会话"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Tiger-Trading-System-Window3/1.0'}
        )
        print("✅ 窗口2接口网络会话已初始化")

    async def get_binance_funding_rates(self) -> Dict[str, Any]:
        """获取币安实时资金费率"""
        try:
            url = f"{self.binance_config['base_url']}/fapi/v1/premiumIndex"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 提取主要币种的资金费率
                    funding_rates = {}
                    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
                    
                    for item in data:
                        symbol = item.get('symbol')
                        if symbol in symbols:
                            funding_rates[symbol] = {
                                'symbol': symbol,
                                'funding_rate': float(item.get('lastFundingRate', 0)) * 100,  # 转为百分比
                                'funding_time': item.get('nextFundingTime'),
                                'mark_price': float(item.get('markPrice', 0)),
                                'index_price': float(item.get('indexPrice', 0)),
                                'timestamp': datetime.now().isoformat()
                            }
                    
                    print(f"✅ 币安资金费率获取成功: {len(funding_rates)}个币种")
                    return funding_rates
                    
        except Exception as e:
            print(f"❌ 获取币安资金费率失败: {e}")
            
        return {}

    async def get_okx_funding_rates(self) -> Dict[str, Any]:
        """获取OKX实时资金费率"""
        try:
            url = f"{self.okx_config['base_url']}/api/v5/public/funding-rate"
            params = {'instType': 'SWAP'}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('code') == '0':
                        funding_rates = {}
                        symbols = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP']
                        
                        for item in data.get('data', []):
                            inst_id = item.get('instId')
                            if inst_id in symbols:
                                funding_rates[inst_id] = {
                                    'symbol': inst_id,
                                    'funding_rate': float(item.get('fundingRate', 0)) * 100,
                                    'funding_time': item.get('fundingTime'),
                                    'next_funding_time': item.get('nextFundingTime'),
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        print(f"✅ OKX资金费率获取成功: {len(funding_rates)}个币种")
                        return funding_rates
                        
        except Exception as e:
            print(f"❌ 获取OKX资金费率失败: {e}")
            
        return {}

    async def get_combined_funding_rates(self) -> Dict[str, Any]:
        """获取综合资金费率数据"""
        print("📊 开始获取实时资金费率数据...")
        
        # 并行获取两个交易所的数据
        binance_task = self.get_binance_funding_rates()
        okx_task = self.get_okx_funding_rates()
        
        binance_data, okx_data = await asyncio.gather(binance_task, okx_task)
        
        # 合并数据
        combined_data = {
            'timestamp': datetime.now().isoformat(),
            'binance': binance_data,
            'okx': okx_data,
            'summary': self.calculate_funding_summary(binance_data, okx_data)
        }
        
        return combined_data

    def calculate_funding_summary(self, binance_data: Dict, okx_data: Dict) -> Dict[str, Any]:
        """计算资金费率摘要"""
        summary = {
            'btc_avg_funding': 0,
            'eth_avg_funding': 0,
            'overall_sentiment': 'neutral',
            'positive_funding_ratio': 0,
            'strong_positive_count': 0
        }
        
        try:
            # BTC平均资金费率
            btc_rates = []
            if 'BTCUSDT' in binance_data:
                btc_rates.append(binance_data['BTCUSDT']['funding_rate'])
            if 'BTC-USDT-SWAP' in okx_data:
                btc_rates.append(okx_data['BTC-USDT-SWAP']['funding_rate'])
            
            if btc_rates:
                summary['btc_avg_funding'] = sum(btc_rates) / len(btc_rates)
            
            # ETH平均资金费率
            eth_rates = []
            if 'ETHUSDT' in binance_data:
                eth_rates.append(binance_data['ETHUSDT']['funding_rate'])
            if 'ETH-USDT-SWAP' in okx_data:
                eth_rates.append(okx_data['ETH-USDT-SWAP']['funding_rate'])
            
            if eth_rates:
                summary['eth_avg_funding'] = sum(eth_rates) / len(eth_rates)
            
            # 统计正资金费率比例
            all_rates = []
            for data in binance_data.values():
                all_rates.append(data['funding_rate'])
            for data in okx_data.values():
                all_rates.append(data['funding_rate'])
            
            if all_rates:
                positive_count = sum(1 for rate in all_rates if rate > 0)
                strong_positive_count = sum(1 for rate in all_rates if rate > 0.01)
                
                summary['positive_funding_ratio'] = positive_count / len(all_rates)
                summary['strong_positive_count'] = strong_positive_count
                
                # 判断整体情绪
                if summary['positive_funding_ratio'] > 0.7:
                    summary['overall_sentiment'] = 'very_bullish'
                elif summary['positive_funding_ratio'] > 0.5:
                    summary['overall_sentiment'] = 'bullish'
                elif summary['positive_funding_ratio'] < 0.3:
                    summary['overall_sentiment'] = 'bearish'
                else:
                    summary['overall_sentiment'] = 'neutral'
        
        except Exception as e:
            print(f"❌ 计算资金费率摘要失败: {e}")
        
        return summary

    async def get_liquidation_data(self) -> Dict[str, Any]:
        """获取爆仓数据"""
        try:
            # 币安强平订单
            url = f"{self.binance_config['base_url']}/fapi/v1/forceOrders"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 统计最近的爆仓情况
                    recent_liquidations = {
                        'total_liquidations': len(data),
                        'long_liquidations': sum(1 for item in data if item.get('side') == 'SELL'),
                        'short_liquidations': sum(1 for item in data if item.get('side') == 'BUY'),
                        'total_amount': sum(float(item.get('origQty', 0)) for item in data),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    print(f"✅ 爆仓数据获取成功: {recent_liquidations['total_liquidations']}笔")
                    return recent_liquidations
                    
        except Exception as e:
            print(f"❌ 获取爆仓数据失败: {e}")
            
        return {'total_liquidations': 0, 'timestamp': datetime.now().isoformat()}

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
        print("✅ 窗口2接口已关闭")

async def main():
    """测试窗口2接口"""
    interface = Window2Interface()
    
    try:
        await interface.initialize()
        
        print("🧪 测试窗口2接口...")
        
        # 测试资金费率
        funding_data = await interface.get_combined_funding_rates()
        print("\n" + "="*50)
        print("📊 实时资金费率数据")
        print("="*50)
        print(json.dumps(funding_data, ensure_ascii=False, indent=2))
        
        # 测试爆仓数据
        liquidation_data = await interface.get_liquidation_data()
        print("\n" + "="*50)
        print("💥 爆仓数据")
        print("="*50)
        print(json.dumps(liquidation_data, ensure_ascii=False, indent=2))
        
    finally:
        await interface.close()

if __name__ == "__main__":
    asyncio.run(main())