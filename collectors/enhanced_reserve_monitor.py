# -*- coding: utf-8 -*-
"""
增强交易所储备监控系统
解决窗口2无法获取高质量稳定数据的问题

基于测试结果：
- WhaleAlert可用但覆盖不足
- Coinglass API路径有问题
- 需要自建多源数据聚合系统
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ExchangeReserveData:
    """交易所储备数据结构"""
    exchange: str
    timestamp: datetime
    btc_reserve: float
    eth_reserve: float
    usdt_reserve: float
    inflow_24h: float
    outflow_24h: float
    net_flow_24h: float
    reserve_change_7d: float
    data_source: str
    confidence_level: str

class EnhancedReserveMonitor:
    """增强交易所储备监控系统"""
    
    def __init__(self):
        # API配置
        self.whale_alert_key = "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU"
        self.coinglass_key = "3897e5abd6bf41e1ab2fb61a45f9372d"
        
        self.session = None
        
        # 支持的交易所
        self.exchanges = ['Binance', 'OKX', 'Coinbase', 'Kraken', 'Bitfinex', 'Huobi']
        
        # 数据缓存
        self.reserve_cache = {}
        self.flow_data = []
        
        print("🏦 增强交易所储备监控系统已初始化")
        print("📊 多源数据聚合：WhaleAlert + 自建计算 + 备用源")
        print("🎯 解决窗口2数据质量问题")

    async def initialize(self):
        """初始化"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Tiger-Trading-System-Enhanced/1.0'}
        )
        print("✅ 增强储备监控系统初始化完成")

    async def get_whale_alert_flows(self, hours: int = 24) -> List[Dict]:
        """从WhaleAlert获取流量数据"""
        try:
            url = "https://api.whale-alert.io/v1/transactions"
            params = {
                'api_key': self.whale_alert_key,
                'min_value': 500000,  # 50万美元以上
                'limit': 100,
                'start': int((datetime.now() - timedelta(hours=hours)).timestamp()),
                'end': int(datetime.now().timestamp())
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    transactions = data.get('transactions', [])
                    
                    # 过滤交易所相关交易
                    exchange_flows = []
                    for tx in transactions:
                        flow_data = self.analyze_transaction_flow(tx)
                        if flow_data:
                            exchange_flows.append(flow_data)
                    
                    print(f"✅ WhaleAlert获取到{len(exchange_flows)}笔交易所流量")
                    return exchange_flows
                    
        except Exception as e:
            print(f"❌ WhaleAlert流量获取失败: {e}")
        
        return []

    def analyze_transaction_flow(self, tx: Dict) -> Optional[Dict]:
        """分析交易流向"""
        from_info = tx.get('from', {})
        to_info = tx.get('to', {})
        
        from_owner = from_info.get('owner', '').lower()
        to_owner = to_info.get('owner', '').lower()
        from_type = from_info.get('owner_type', '')
        to_type = to_info.get('owner_type', '')
        
        amount = tx.get('amount', 0)
        amount_usd = tx.get('amount_usd', 0)
        symbol = tx.get('symbol', '').upper()
        timestamp = datetime.fromtimestamp(tx.get('timestamp', 0))
        
        # 识别交易所
        exchange = None
        direction = None
        
        for exchange_name in self.exchanges:
            if exchange_name.lower() in from_owner:
                exchange = exchange_name
                direction = 'outflow'
                break
            elif exchange_name.lower() in to_owner:
                exchange = exchange_name
                direction = 'inflow'
                break
        
        if exchange and direction:
            return {
                'exchange': exchange,
                'direction': direction,
                'amount': amount,
                'amount_usd': amount_usd,
                'symbol': symbol,
                'timestamp': timestamp,
                'from_type': from_type,
                'to_type': to_type,
                'hash': tx.get('hash', '')
            }
        
        return None

    async def calculate_reserve_estimates(self, flows: List[Dict]) -> Dict[str, ExchangeReserveData]:
        """基于流量数据计算储备估算"""
        reserve_estimates = {}
        
        for exchange in self.exchanges:
            # 筛选该交易所的流量
            exchange_flows = [f for f in flows if f['exchange'] == exchange]
            
            if not exchange_flows:
                continue
            
            # 计算24小时流量
            inflow_24h = sum(f['amount_usd'] for f in exchange_flows if f['direction'] == 'inflow')
            outflow_24h = sum(f['amount_usd'] for f in exchange_flows if f['direction'] == 'outflow')
            net_flow_24h = inflow_24h - outflow_24h
            
            # 分币种统计
            btc_flows = [f for f in exchange_flows if f['symbol'] == 'BTC']
            eth_flows = [f for f in exchange_flows if f['symbol'] == 'ETH']
            usdt_flows = [f for f in exchange_flows if f['symbol'] in ['USDT', 'USDC']]
            
            # 基础储备估算（这里使用简化方法，实际需要更复杂的模型）
            btc_net = sum(f['amount'] * (1 if f['direction'] == 'inflow' else -1) for f in btc_flows)
            eth_net = sum(f['amount'] * (1 if f['direction'] == 'inflow' else -1) for f in eth_flows)
            usdt_net = sum(f['amount'] * (1 if f['direction'] == 'inflow' else -1) for f in usdt_flows)
            
            # 置信度评估
            confidence = self.calculate_confidence(exchange_flows)
            
            reserve_data = ExchangeReserveData(
                exchange=exchange,
                timestamp=datetime.now(),
                btc_reserve=abs(btc_net),  # 简化估算
                eth_reserve=abs(eth_net),
                usdt_reserve=abs(usdt_net),
                inflow_24h=inflow_24h,
                outflow_24h=outflow_24h,
                net_flow_24h=net_flow_24h,
                reserve_change_7d=0,  # 需要7天数据计算
                data_source="WhaleAlert+计算",
                confidence_level=confidence
            )
            
            reserve_estimates[exchange] = reserve_data
        
        return reserve_estimates

    def calculate_confidence(self, flows: List[Dict]) -> str:
        """计算数据置信度"""
        if not flows:
            return "极低"
        
        # 基于交易数量和金额评估
        total_volume = sum(f['amount_usd'] for f in flows)
        transaction_count = len(flows)
        
        if transaction_count >= 10 and total_volume >= 10000000:  # 1000万美元
            return "高"
        elif transaction_count >= 5 and total_volume >= 5000000:   # 500万美元
            return "中等"
        elif transaction_count >= 2:
            return "低"
        else:
            return "极低"

    async def get_backup_data_sources(self) -> Dict[str, Any]:
        """获取备用数据源"""
        backup_data = {}
        
        # 1. 免费的区块链浏览器数据
        try:
            # Bitcoin网络数据
            btc_data = await self.get_blockchain_info_data()
            if btc_data:
                backup_data['bitcoin_network'] = btc_data
        except Exception as e:
            print(f"❌ Bitcoin网络数据获取失败: {e}")
        
        # 2. DeFi TVL数据作为参考
        try:
            defi_data = await self.get_defi_llama_data()
            if defi_data:
                backup_data['defi_tvl'] = defi_data
        except Exception as e:
            print(f"❌ DeFi TVL数据获取失败: {e}")
        
        # 3. CoinGecko交易量数据
        try:
            volume_data = await self.get_coingecko_volume_data()
            if volume_data:
                backup_data['exchange_volumes'] = volume_data
        except Exception as e:
            print(f"❌ 交易量数据获取失败: {e}")
        
        return backup_data

    async def get_blockchain_info_data(self) -> Dict[str, Any]:
        """获取区块链基础数据"""
        try:
            url = "https://blockchain.info/q/totalbc"
            async with self.session.get(url) as response:
                if response.status == 200:
                    total_btc = float(await response.text()) / 100000000  # 转换为BTC
                    return {
                        'total_btc_supply': total_btc,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"❌ 区块链信息获取失败: {e}")
        return {}

    async def get_defi_llama_data(self) -> Dict[str, Any]:
        """获取DeFi TVL数据"""
        try:
            url = "https://api.llama.fi/protocols"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    total_tvl = sum(protocol.get('tvl', 0) for protocol in data[:50])  # 前50个协议
                    return {
                        'total_defi_tvl': total_tvl,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"❌ DeFi数据获取失败: {e}")
        return {}

    async def get_coingecko_volume_data(self) -> Dict[str, Any]:
        """获取CoinGecko交易量数据"""
        try:
            url = "https://api.coingecko.com/api/v3/exchanges"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    exchange_volumes = {}
                    
                    for exchange in data[:20]:  # 前20个交易所
                        name = exchange.get('name', '')
                        volume = exchange.get('trade_volume_24h_btc', 0)
                        if name and volume:
                            exchange_volumes[name] = volume
                    
                    return {
                        'exchange_volumes_24h': exchange_volumes,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"❌ 交易量数据获取失败: {e}")
        return {}

    async def generate_comprehensive_reserve_report(self) -> Dict[str, Any]:
        """生成综合储备报告"""
        print("🚀 开始生成综合储备报告...")
        
        # 获取WhaleAlert流量数据
        flows_24h = await self.get_whale_alert_flows(24)
        
        # 计算储备估算
        reserve_estimates = await self.calculate_reserve_estimates(flows_24h)
        
        # 获取备用数据
        backup_data = await self.get_backup_data_sources()
        
        # 生成市场分析
        market_analysis = self.analyze_market_implications(reserve_estimates, flows_24h)
        
        # 构建完整报告
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "data_quality": {
                "primary_source": "WhaleAlert",
                "transaction_count": len(flows_24h),
                "exchanges_covered": len(reserve_estimates),
                "overall_confidence": self.calculate_overall_confidence(reserve_estimates)
            },
            "exchange_reserves": {
                exchange: asdict(data) for exchange, data in reserve_estimates.items()
            },
            "flow_analysis": {
                "total_inflow_24h": sum(f['amount_usd'] for f in flows_24h if f['direction'] == 'inflow'),
                "total_outflow_24h": sum(f['amount_usd'] for f in flows_24h if f['direction'] == 'outflow'),
                "net_flow_24h": sum(f['amount_usd'] * (1 if f['direction'] == 'inflow' else -1) for f in flows_24h),
                "largest_inflow": max([f for f in flows_24h if f['direction'] == 'inflow'], 
                                    key=lambda x: x['amount_usd'], default={}),
                "largest_outflow": max([f for f in flows_24h if f['direction'] == 'outflow'], 
                                     key=lambda x: x['amount_usd'], default={})
            },
            "market_analysis": market_analysis,
            "backup_data": backup_data,
            "for_window6": self.format_for_window6(reserve_estimates, flows_24h, market_analysis)
        }
        
        print(f"✅ 储备报告生成完成")
        print(f"📊 覆盖{len(reserve_estimates)}个交易所")
        print(f"💰 24H总流量: ${report['flow_analysis']['total_inflow_24h'] + report['flow_analysis']['total_outflow_24h']:,.0f}")
        
        return report

    def analyze_market_implications(self, reserves: Dict[str, ExchangeReserveData], 
                                  flows: List[Dict]) -> Dict[str, Any]:
        """分析市场影响"""
        
        # 计算总体流向
        total_inflow = sum(f['amount_usd'] for f in flows if f['direction'] == 'inflow')
        total_outflow = sum(f['amount_usd'] for f in flows if f['direction'] == 'outflow')
        net_flow = total_inflow - total_outflow
        
        # 判断市场情绪
        if net_flow > 10000000:  # 净流入超过1000万
            sentiment = "强烈看空"
            explanation = "大量资金流入交易所，可能准备抛售"
        elif net_flow > 5000000:
            sentiment = "看空"
            explanation = "资金流入交易所，抛售压力增加"
        elif net_flow < -10000000:  # 净流出超过1000万
            sentiment = "强烈看多"
            explanation = "大量资金流出交易所，减少抛售压力"
        elif net_flow < -5000000:
            sentiment = "看多"
            explanation = "资金流出交易所，HODLing增加"
        else:
            sentiment = "中性"
            explanation = "流入流出基本平衡"
        
        # 风险评估
        risk_level = "高" if abs(net_flow) > 20000000 else "中" if abs(net_flow) > 10000000 else "低"
        
        return {
            "market_sentiment": sentiment,
            "explanation": explanation,
            "risk_level": risk_level,
            "net_flow_24h": net_flow,
            "flow_ratio": total_outflow / total_inflow if total_inflow > 0 else 0,
            "key_exchanges": self.identify_key_exchanges(reserves)
        }

    def identify_key_exchanges(self, reserves: Dict[str, ExchangeReserveData]) -> List[str]:
        """识别关键交易所"""
        if not reserves:
            return []
        
        # 按净流量排序
        sorted_exchanges = sorted(
            reserves.values(),
            key=lambda x: abs(x.net_flow_24h),
            reverse=True
        )
        
        return [exchange.exchange for exchange in sorted_exchanges[:3]]

    def calculate_overall_confidence(self, reserves: Dict[str, ExchangeReserveData]) -> str:
        """计算整体置信度"""
        if not reserves:
            return "极低"
        
        confidence_scores = {'极低': 0, '低': 1, '中等': 2, '高': 3}
        avg_score = sum(confidence_scores.get(r.confidence_level, 0) for r in reserves.values()) / len(reserves)
        
        if avg_score >= 2.5:
            return "高"
        elif avg_score >= 1.5:
            return "中等"
        elif avg_score >= 0.5:
            return "低"
        else:
            return "极低"

    def format_for_window6(self, reserves: Dict[str, ExchangeReserveData], 
                          flows: List[Dict], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """为窗口6格式化数据"""
        return {
            "data_source": "window3_enhanced_reserves",
            "timestamp": datetime.now().isoformat(),
            "reserve_summary": {
                "total_exchanges_monitored": len(reserves),
                "market_sentiment": analysis["market_sentiment"],
                "risk_level": analysis["risk_level"],
                "net_flow_indicator": "流入" if analysis["net_flow_24h"] > 0 else "流出",
                "flow_magnitude": abs(analysis["net_flow_24h"])
            },
            "key_alerts": self.generate_key_alerts(reserves, flows, analysis),
            "trading_implications": {
                "short_term_pressure": "抛售压力" if analysis["net_flow_24h"] > 5000000 else "买入机会",
                "recommended_action": self.get_recommended_action(analysis),
                "confidence": self.calculate_overall_confidence(reserves)
            },
            "detailed_reserves": {
                exchange: {
                    "net_flow_24h": data.net_flow_24h,
                    "confidence": data.confidence_level,
                    "flow_direction": "流入" if data.net_flow_24h > 0 else "流出"
                } for exchange, data in reserves.items()
            }
        }

    def generate_key_alerts(self, reserves: Dict[str, ExchangeReserveData], 
                           flows: List[Dict], analysis: Dict[str, Any]) -> List[str]:
        """生成关键警报"""
        alerts = []
        
        # 大额流量警报
        if analysis["net_flow_24h"] > 20000000:
            alerts.append(f"🚨 大量资金流入交易所：${analysis['net_flow_24h']:,.0f}")
        elif analysis["net_flow_24h"] < -20000000:
            alerts.append(f"💎 大量资金流出交易所：${abs(analysis['net_flow_24h']):,.0f}")
        
        # 单笔大额交易警报
        large_flows = [f for f in flows if f['amount_usd'] > 5000000]
        if large_flows:
            alerts.append(f"⚡ 检测到{len(large_flows)}笔超500万美元大额交易")
        
        # 数据质量警报
        low_confidence_exchanges = [e for e, r in reserves.items() if r.confidence_level in ['低', '极低']]
        if len(low_confidence_exchanges) > len(reserves) / 2:
            alerts.append("⚠️ 数据质量偏低，建议谨慎使用")
        
        return alerts

    def get_recommended_action(self, analysis: Dict[str, Any]) -> str:
        """获取推荐行动"""
        sentiment = analysis["market_sentiment"]
        risk = analysis["risk_level"]
        
        if sentiment == "强烈看空" and risk == "高":
            return "建议减仓，准备抄底"
        elif sentiment == "强烈看多" and risk == "高":
            return "建议加仓，HODLing增加"
        elif sentiment == "看空":
            return "谨慎观望，准备买入"
        elif sentiment == "看多":
            return "适度加仓"
        else:
            return "保持现有仓位"

    async def close(self):
        """关闭资源"""
        if self.session:
            await self.session.close()
        print("✅ 增强储备监控系统已关闭")

async def main():
    """测试增强储备监控系统"""
    monitor = EnhancedReserveMonitor()
    
    try:
        await monitor.initialize()
        
        # 生成综合报告
        report = await monitor.generate_comprehensive_reserve_report()
        
        # 显示关键信息
        print("\n" + "="*60)
        print("📊 储备监控报告摘要")
        print("="*60)
        
        data_quality = report["data_quality"]
        print(f"📈 数据质量: {data_quality['overall_confidence']}")
        print(f"💱 覆盖交易所: {data_quality['exchanges_covered']}个")
        print(f"📝 交易记录: {data_quality['transaction_count']}笔")
        
        flow_analysis = report["flow_analysis"]
        print(f"💰 24H净流量: ${flow_analysis['net_flow_24h']:,.0f}")
        
        window6_data = report["for_window6"]
        print(f"🎯 市场情绪: {window6_data['reserve_summary']['market_sentiment']}")
        print(f"⚠️ 风险等级: {window6_data['reserve_summary']['risk_level']}")
        print(f"💡 推荐行动: {window6_data['trading_implications']['recommended_action']}")
        
        if window6_data['key_alerts']:
            print(f"\n🚨 关键警报:")
            for alert in window6_data['key_alerts']:
                print(f"  {alert}")
        
        # 保存报告
        with open('/tmp/enhanced_reserve_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 完整报告已保存到: /tmp/enhanced_reserve_report.json")
        
    finally:
        await monitor.close()

if __name__ == "__main__":
    asyncio.run(main())