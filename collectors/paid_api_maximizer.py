"""
Window 3 - 付费API最大化利用系统
充分挖掘每个付费API的全部潜力
将35美元的Coinglass和29.95美元的WhaleAlert发挥到极致
"""

import asyncio
import aiohttp
import websockets
import json
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PaidAPIMaximizer:
    """
    付费API最大化利用系统
    目标：榨取每一分钱的价值
    """
    
    def __init__(self):
        # API密钥
        self.coinglass_key = "689079f638414a18bac90b722446f3b3"  # 新的API key
        self.whale_alert_key = "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU"
        
        # Coinglass API基础配置
        self.coinglass_base = "https://open-api-v4.coinglass.com"
        self.coinglass_headers = {
            "coinglassSecret": self.coinglass_key,
            "Content-Type": "application/json"
        }
        
        # WhaleAlert API配置
        self.whale_alert_base = "https://api.whale-alert.io/v1"
        self.whale_alert_ws = "wss://leviathan.whale-alert.io/ws"
        
        # 统计信息
        self.api_usage = {
            "coinglass": {
                "calls_made": 0,
                "data_points": 0,
                "features_used": set()
            },
            "whale_alert": {
                "calls_made": 0,
                "alerts_received": 0,
                "websocket_uptime": 0,
                "features_used": set()
            }
        }
        
        logger.info("=" * 60)
        logger.info("💎 付费API最大化利用系统启动")
        logger.info("📊 Coinglass Hobbyist: $35/月 - 期货/现货/期权/链上/ETF")
        logger.info("🐋 WhaleAlert Personal: $29.95/月 - 实时监控/地址归属/历史数据")
        logger.info("🎯 目标：榨取每一分钱的价值")
        logger.info("=" * 60)

    # ==================== Coinglass深度利用 ====================
    
    async def coinglass_complete_analysis(self, symbol: str = "BTC") -> Dict:
        """
        Coinglass完整分析 - 使用所有可用功能
        """
        logger.info(f"🔥 开始Coinglass深度分析 - {symbol}")
        
        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "futures": {},
            "spot": {},
            "options": {},
            "onchain": {},
            "etf": {},
            "indicators": {},
            "macro": {}
        }
        
        async with aiohttp.ClientSession() as session:
            # 1. 期货数据（最有价值）
            analysis["futures"] = await self.get_futures_comprehensive(session, symbol)
            
            # 2. 现货数据
            analysis["spot"] = await self.get_spot_data(session, symbol)
            
            # 3. 期权数据
            analysis["options"] = await self.get_options_data(session, symbol)
            
            # 4. 链上数据
            analysis["onchain"] = await self.get_onchain_data(session, symbol)
            
            # 5. ETF数据
            analysis["etf"] = await self.get_etf_flows(session)
            
            # 6. 指标数据
            analysis["indicators"] = await self.get_all_indicators(session, symbol)
            
            # 7. 宏观经济日历
            analysis["macro"] = await self.get_economic_calendar(session)
        
        # 生成综合洞察
        analysis["insights"] = self.generate_coinglass_insights(analysis)
        
        logger.info(f"✅ Coinglass分析完成 - 使用了{len(self.api_usage['coinglass']['features_used'])}个功能")
        
        return analysis

    async def get_futures_comprehensive(self, session: aiohttp.ClientSession, symbol: str) -> Dict:
        """获取期货综合数据"""
        futures_data = {}
        
        # 1. 资金费率（核心数据）
        try:
            url = f"{self.coinglass_base}/api/futures/funding-rate"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    futures_data["funding_rates"] = data
                    self.api_usage["coinglass"]["features_used"].add("funding_rates")
                    logger.info(f"  ✓ 资金费率数据获取成功")
        except Exception as e:
            logger.error(f"获取资金费率失败: {e}")
        
        # 2. 未平仓合约（OI）
        try:
            url = f"{self.coinglass_base}/api/futures/openInterest"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    futures_data["open_interest"] = data
                    self.api_usage["coinglass"]["features_used"].add("open_interest")
                    logger.info(f"  ✓ 未平仓合约数据获取成功")
        except Exception as e:
            logger.error(f"获取OI失败: {e}")
        
        # 3. 爆仓数据（重要）
        try:
            url = f"{self.coinglass_base}/api/futures/liquidation"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    futures_data["liquidations"] = data
                    self.api_usage["coinglass"]["features_used"].add("liquidations")
                    logger.info(f"  ✓ 爆仓数据获取成功")
        except Exception as e:
            logger.error(f"获取爆仓数据失败: {e}")
        
        # 4. 多空比（市场情绪）
        try:
            url = f"{self.coinglass_base}/api/futures/longShortRatio"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    futures_data["long_short_ratio"] = data
                    self.api_usage["coinglass"]["features_used"].add("long_short_ratio")
                    logger.info(f"  ✓ 多空比数据获取成功")
        except Exception as e:
            logger.error(f"获取多空比失败: {e}")
        
        # 5. 合约基差
        try:
            url = f"{self.coinglass_base}/api/futures/basis"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    futures_data["basis"] = data
                    self.api_usage["coinglass"]["features_used"].add("basis")
                    logger.info(f"  ✓ 合约基差数据获取成功")
        except Exception as e:
            logger.error(f"获取基差失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 5
        return futures_data

    async def get_spot_data(self, session: aiohttp.ClientSession, symbol: str) -> Dict:
        """获取现货数据"""
        spot_data = {}
        
        # 1. 现货价格K线
        try:
            url = f"{self.coinglass_base}/api/spot/kline"
            params = {"symbol": symbol, "interval": "1h", "limit": 24}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    spot_data["klines"] = data
                    self.api_usage["coinglass"]["features_used"].add("spot_klines")
        except Exception as e:
            logger.error(f"获取现货K线失败: {e}")
        
        # 2. 交易所现货流动性
        try:
            url = f"{self.coinglass_base}/api/spot/liquidity"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    spot_data["liquidity"] = data
                    self.api_usage["coinglass"]["features_used"].add("spot_liquidity")
        except Exception as e:
            logger.error(f"获取流动性失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 2
        return spot_data

    async def get_options_data(self, session: aiohttp.ClientSession, symbol: str) -> Dict:
        """获取期权数据"""
        options_data = {}
        
        # 1. 期权未平仓量
        try:
            url = f"{self.coinglass_base}/api/options/openInterest"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    options_data["open_interest"] = data
                    self.api_usage["coinglass"]["features_used"].add("options_oi")
        except Exception as e:
            logger.error(f"获取期权OI失败: {e}")
        
        # 2. 期权流量
        try:
            url = f"{self.coinglass_base}/api/options/flow"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    options_data["flow"] = data
                    self.api_usage["coinglass"]["features_used"].add("options_flow")
        except Exception as e:
            logger.error(f"获取期权流量失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 2
        return options_data

    async def get_onchain_data(self, session: aiohttp.ClientSession, symbol: str) -> Dict:
        """获取链上数据"""
        onchain_data = {}
        
        # 1. 交易所流入流出
        try:
            url = f"{self.coinglass_base}/api/onchain/exchange-flow"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    onchain_data["exchange_flows"] = data
                    self.api_usage["coinglass"]["features_used"].add("exchange_flows")
                    logger.info(f"  ✓ 交易所流量数据获取成功")
        except Exception as e:
            logger.error(f"获取交易所流量失败: {e}")
        
        # 2. 矿工/验证者数据
        try:
            url = f"{self.coinglass_base}/api/onchain/miners"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    onchain_data["miners"] = data
                    self.api_usage["coinglass"]["features_used"].add("miners_data")
        except Exception as e:
            logger.error(f"获取矿工数据失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 2
        return onchain_data

    async def get_etf_flows(self, session: aiohttp.ClientSession) -> Dict:
        """获取ETF流量数据"""
        etf_data = {}
        
        try:
            url = f"{self.coinglass_base}/api/etf/flow"
            async with session.get(url, headers=self.coinglass_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    etf_data["flows"] = data
                    self.api_usage["coinglass"]["features_used"].add("etf_flows")
                    logger.info(f"  ✓ ETF流量数据获取成功")
        except Exception as e:
            logger.error(f"获取ETF数据失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 1
        return etf_data

    async def get_all_indicators(self, session: aiohttp.ClientSession, symbol: str) -> Dict:
        """获取所有指标"""
        indicators = {}
        
        # 1. 恐慌贪婪指数
        try:
            url = f"{self.coinglass_base}/api/indicators/fear-greed"
            async with session.get(url, headers=self.coinglass_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    indicators["fear_greed"] = data
                    self.api_usage["coinglass"]["features_used"].add("fear_greed")
        except Exception as e:
            logger.error(f"获取恐慌贪婪指数失败: {e}")
        
        # 2. 比特币彩虹图
        try:
            url = f"{self.coinglass_base}/api/indicators/rainbow"
            async with session.get(url, headers=self.coinglass_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    indicators["rainbow"] = data
                    self.api_usage["coinglass"]["features_used"].add("rainbow_chart")
        except Exception as e:
            logger.error(f"获取彩虹图失败: {e}")
        
        # 3. MVRV指标
        try:
            url = f"{self.coinglass_base}/api/indicators/mvrv"
            params = {"symbol": symbol}
            async with session.get(url, headers=self.coinglass_headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    indicators["mvrv"] = data
                    self.api_usage["coinglass"]["features_used"].add("mvrv")
        except Exception as e:
            logger.error(f"获取MVRV失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 3
        return indicators

    async def get_economic_calendar(self, session: aiohttp.ClientSession) -> Dict:
        """获取经济日历"""
        calendar_data = {}
        
        try:
            url = f"{self.coinglass_base}/api/other/economic-calendar"
            async with session.get(url, headers=self.coinglass_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    calendar_data["events"] = data
                    self.api_usage["coinglass"]["features_used"].add("economic_calendar")
                    logger.info(f"  ✓ 经济日历数据获取成功")
        except Exception as e:
            logger.error(f"获取经济日历失败: {e}")
        
        self.api_usage["coinglass"]["calls_made"] += 1
        return calendar_data

    def generate_coinglass_insights(self, data: Dict) -> Dict:
        """生成Coinglass洞察"""
        insights = {
            "market_structure": {},
            "sentiment": {},
            "risk_metrics": {},
            "opportunities": []
        }
        
        # 分析市场结构
        if data.get("futures", {}).get("funding_rates"):
            funding = data["futures"]["funding_rates"]
            insights["market_structure"]["funding_bias"] = "bullish" if funding > 0 else "bearish"
        
        if data.get("futures", {}).get("basis"):
            basis = data["futures"]["basis"]
            insights["market_structure"]["contango"] = basis > 0
        
        # 分析情绪
        if data.get("futures", {}).get("long_short_ratio"):
            ratio = data["futures"]["long_short_ratio"]
            insights["sentiment"]["retail_bias"] = "long" if ratio > 1 else "short"
        
        if data.get("indicators", {}).get("fear_greed"):
            fg = data["indicators"]["fear_greed"]
            insights["sentiment"]["market_emotion"] = fg
        
        # 风险指标
        if data.get("futures", {}).get("liquidations"):
            liquidations = data["futures"]["liquidations"]
            insights["risk_metrics"]["liquidation_risk"] = "high" if liquidations > 1000000000 else "normal"
        
        # 识别机会
        if data.get("etf", {}).get("flows"):
            etf_flow = data["etf"]["flows"]
            if etf_flow > 100000000:  # 1亿美元流入
                insights["opportunities"].append({
                    "type": "etf_inflow",
                    "description": "大量ETF资金流入",
                    "impact": "bullish"
                })
        
        return insights

    # ==================== WhaleAlert深度利用 ====================
    
    async def whale_alert_complete_monitoring(self) -> Dict:
        """
        WhaleAlert完整监控 - 使用所有功能
        """
        logger.info("🐋 开始WhaleAlert深度监控")
        
        monitoring = {
            "timestamp": datetime.now().isoformat(),
            "transactions": {},
            "address_analysis": {},
            "blockchain_status": {},
            "patterns": {}
        }
        
        async with aiohttp.ClientSession() as session:
            # 1. 获取区块链状态
            monitoring["blockchain_status"] = await self.get_blockchain_status(session)
            
            # 2. 获取最新交易（带地址归属）
            monitoring["transactions"] = await self.get_enriched_transactions(session)
            
            # 3. 分析重要地址
            monitoring["address_analysis"] = await self.analyze_key_addresses(session)
            
            # 4. 获取特定区块数据
            monitoring["block_data"] = await self.get_block_transactions(session)
            
            # 5. 识别模式
            monitoring["patterns"] = self.identify_whale_patterns(monitoring)
        
        logger.info(f"✅ WhaleAlert监控完成 - 使用了{len(self.api_usage['whale_alert']['features_used'])}个功能")
        
        return monitoring

    async def get_blockchain_status(self, session: aiohttp.ClientSession) -> Dict:
        """获取所有区块链状态"""
        try:
            url = f"{self.whale_alert_base}/status"
            params = {"api_key": self.whale_alert_key}
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.api_usage["whale_alert"]["features_used"].add("blockchain_status")
                    self.api_usage["whale_alert"]["calls_made"] += 1
                    logger.info(f"  ✓ 区块链状态获取成功")
                    return data
        except Exception as e:
            logger.error(f"获取区块链状态失败: {e}")
        
        return {}

    async def get_enriched_transactions(self, session: aiohttp.ClientSession) -> Dict:
        """获取带地址归属的交易"""
        try:
            url = f"{self.whale_alert_base}/transactions"
            params = {
                "api_key": self.whale_alert_key,
                "min_value": 100000,
                "limit": 100
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # 增强数据：获取地址归属
                    for tx in data.get("transactions", []):
                        # 获取发送地址归属
                        if tx.get("from", {}).get("address"):
                            tx["from"]["attribution"] = await self.get_address_attribution(
                                session, 
                                tx["from"]["address"]
                            )
                        
                        # 获取接收地址归属
                        if tx.get("to", {}).get("address"):
                            tx["to"]["attribution"] = await self.get_address_attribution(
                                session,
                                tx["to"]["address"]
                            )
                    
                    self.api_usage["whale_alert"]["features_used"].add("enriched_transactions")
                    self.api_usage["whale_alert"]["calls_made"] += 1
                    logger.info(f"  ✓ 增强交易数据获取成功")
                    return data
        except Exception as e:
            logger.error(f"获取交易失败: {e}")
        
        return {}

    async def get_address_attribution(self, session: aiohttp.ClientSession, address: str) -> Dict:
        """获取地址归属信息"""
        try:
            url = f"{self.whale_alert_base}/address/{address}/owner_attributions"
            params = {"api_key": self.whale_alert_key}
            
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.api_usage["whale_alert"]["features_used"].add("address_attribution")
                    return data
        except:
            pass
        
        return {}

    async def analyze_key_addresses(self, session: aiohttp.ClientSession) -> Dict:
        """分析关键地址"""
        key_addresses = {
            # 主要交易所热钱包
            "binance_hot": "1JDpDwBAGfPREMqfGe8gD5aFjEUYCdVosp",
            "coinbase_hot": "1P5ZEDWkKTFGxQjZphgWPQUpe554Wd5Jm",
            # 可以添加更多关键地址
        }
        
        analysis = {}
        
        for name, address in key_addresses.items():
            try:
                # 获取地址的最近交易
                url = f"{self.whale_alert_base}/address/{address}/transactions"
                params = {
                    "api_key": self.whale_alert_key,
                    "limit": 10
                }
                
                async with session.get(url, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        analysis[name] = {
                            "address": address,
                            "recent_activity": data
                        }
                        self.api_usage["whale_alert"]["features_used"].add("address_transactions")
            except:
                pass
        
        self.api_usage["whale_alert"]["calls_made"] += len(key_addresses)
        return analysis

    async def get_block_transactions(self, session: aiohttp.ClientSession) -> Dict:
        """获取特定区块的交易"""
        # 获取最新区块的大额交易
        try:
            # 首先获取最新区块高度（从status接口）
            status = await self.get_blockchain_status(session)
            
            block_data = {}
            
            # 获取比特币最新区块
            if "bitcoin" in status:
                btc_height = status["bitcoin"].get("block_height")
                if btc_height:
                    url = f"{self.whale_alert_base}/block/{btc_height}"
                    params = {
                        "api_key": self.whale_alert_key,
                        "blockchain": "bitcoin"
                    }
                    
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            block_data["bitcoin"] = data
                            self.api_usage["whale_alert"]["features_used"].add("block_transactions")
            
            self.api_usage["whale_alert"]["calls_made"] += 1
            return block_data
            
        except Exception as e:
            logger.error(f"获取区块交易失败: {e}")
        
        return {}

    def identify_whale_patterns(self, monitoring_data: Dict) -> Dict:
        """识别巨鲸行为模式"""
        patterns = {
            "accumulation": False,
            "distribution": False,
            "exchange_movements": {},
            "unusual_activity": []
        }
        
        transactions = monitoring_data.get("transactions", {}).get("transactions", [])
        
        # 统计交易所流向
        exchange_inflow = 0
        exchange_outflow = 0
        
        for tx in transactions:
            # 判断是否涉及交易所
            from_owner = tx.get("from", {}).get("owner", "").lower()
            to_owner = tx.get("to", {}).get("owner", "").lower()
            amount_usd = tx.get("amount_usd", 0)
            
            if "exchange" in to_owner:
                exchange_inflow += amount_usd
            if "exchange" in from_owner:
                exchange_outflow += amount_usd
            
            # 识别异常大额交易
            if amount_usd > 50000000:  # 5000万美元
                patterns["unusual_activity"].append({
                    "type": "mega_transaction",
                    "amount": amount_usd,
                    "from": from_owner,
                    "to": to_owner
                })
        
        # 判断积累或分发
        if exchange_outflow > exchange_inflow * 1.5:
            patterns["accumulation"] = True
        elif exchange_inflow > exchange_outflow * 1.5:
            patterns["distribution"] = True
        
        patterns["exchange_movements"] = {
            "inflow": exchange_inflow,
            "outflow": exchange_outflow,
            "net": exchange_outflow - exchange_inflow
        }
        
        return patterns

    async def start_websocket_monitoring(self):
        """
        启动WebSocket实时监控
        Personal计划：每小时最多100个警报
        """
        logger.info("🔌 启动WhaleAlert WebSocket实时监控")
        
        try:
            async with websockets.connect(self.whale_alert_ws) as websocket:
                # 发送认证
                auth_message = {
                    "api_key": self.whale_alert_key,
                    "type": "auth"
                }
                await websocket.send(json.dumps(auth_message))
                
                # 配置过滤器
                filter_message = {
                    "type": "subscribe",
                    "filters": {
                        "min_value": 1000000,  # 100万美元以上
                        "blockchains": ["bitcoin", "ethereum"],
                        "transaction_types": ["transfer", "mint", "burn"]
                    }
                }
                await websocket.send(json.dumps(filter_message))
                
                self.api_usage["whale_alert"]["features_used"].add("websocket_realtime")
                
                # 接收实时警报
                while True:
                    message = await websocket.recv()
                    alert = json.loads(message)
                    
                    # 处理警报
                    await self.process_realtime_alert(alert)
                    
                    self.api_usage["whale_alert"]["alerts_received"] += 1
                    
                    # 注意：每小时最多100个警报
                    if self.api_usage["whale_alert"]["alerts_received"] >= 100:
                        logger.warning("⚠️ 接近每小时100个警报限制")
                        
        except Exception as e:
            logger.error(f"WebSocket连接错误: {e}")

    async def process_realtime_alert(self, alert: Dict):
        """处理实时警报"""
        # 这里可以实现实时警报的处理逻辑
        # 比如：触发交易信号、发送通知等
        
        if alert.get("amount_usd", 0) > 10000000:  # 1000万美元
            logger.warning(f"🚨 巨额交易警报: ${alert['amount_usd']:,.0f}")
            # 可以触发Window 6的紧急分析
        
        if alert.get("transaction_type") == "burn":
            logger.info(f"🔥 代币销毁: {alert['symbol']} - ${alert['amount_usd']:,.0f}")
        
        if alert.get("transaction_type") == "mint":
            logger.info(f"🏭 代币铸造: {alert['symbol']} - ${alert['amount_usd']:,.0f}")

    # ==================== 综合利用 ====================
    
    async def run_complete_paid_analysis(self) -> Dict:
        """
        运行完整的付费API分析
        最大化利用每一分钱
        """
        logger.info("=" * 60)
        logger.info("💎 开始付费API完整分析")
        logger.info("=" * 60)
        
        # 并发运行所有分析
        tasks = [
            self.coinglass_complete_analysis("BTC"),
            self.whale_alert_complete_monitoring()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 整合分析结果
        complete_analysis = {
            "timestamp": datetime.now().isoformat(),
            "coinglass": results[0],
            "whale_alert": results[1],
            "combined_insights": self.generate_combined_insights(results[0], results[1]),
            "api_usage_stats": self.api_usage,
            "value_extracted": self.calculate_value_extracted()
        }
        
        # 显示统计
        logger.info("=" * 60)
        logger.info("📊 付费API使用统计")
        logger.info(f"Coinglass功能使用: {len(self.api_usage['coinglass']['features_used'])}个")
        logger.info(f"Coinglass API调用: {self.api_usage['coinglass']['calls_made']}次")
        logger.info(f"WhaleAlert功能使用: {len(self.api_usage['whale_alert']['features_used'])}个")
        logger.info(f"WhaleAlert API调用: {self.api_usage['whale_alert']['calls_made']}次")
        logger.info(f"价值提取率: {complete_analysis['value_extracted']:.1%}")
        logger.info("=" * 60)
        
        return complete_analysis

    def generate_combined_insights(self, coinglass_data: Dict, whale_data: Dict) -> Dict:
        """生成综合洞察"""
        insights = {
            "market_direction": "neutral",
            "risk_level": "medium",
            "key_signals": [],
            "action_recommendations": []
        }
        
        # 结合Coinglass和WhaleAlert数据
        
        # 1. 判断市场方向
        if coinglass_data.get("insights", {}).get("market_structure", {}).get("funding_bias") == "bullish":
            if whale_data.get("patterns", {}).get("accumulation"):
                insights["market_direction"] = "strongly_bullish"
                insights["key_signals"].append("资金费率和巨鲸都看涨")
        
        # 2. 评估风险
        if coinglass_data.get("insights", {}).get("risk_metrics", {}).get("liquidation_risk") == "high":
            insights["risk_level"] = "high"
            insights["key_signals"].append("爆仓风险升高")
        
        # 3. 生成建议
        if insights["market_direction"] == "strongly_bullish" and insights["risk_level"] != "high":
            insights["action_recommendations"].append({
                "action": "consider_long",
                "confidence": 0.8,
                "reason": "市场结构和链上数据都支持看涨"
            })
        
        return insights

    def calculate_value_extracted(self) -> float:
        """计算价值提取率"""
        # Coinglass可用功能（估计）
        coinglass_total_features = 20
        coinglass_used = len(self.api_usage["coinglass"]["features_used"])
        
        # WhaleAlert可用功能
        whale_total_features = 10
        whale_used = len(self.api_usage["whale_alert"]["features_used"])
        
        # 计算使用率
        coinglass_rate = coinglass_used / coinglass_total_features
        whale_rate = whale_used / whale_total_features
        
        # 加权平均（Coinglass更贵，权重更高）
        total_rate = (coinglass_rate * 35 + whale_rate * 29.95) / (35 + 29.95)
        
        return total_rate


# 测试函数
async def test_paid_apis():
    """测试付费API最大化利用"""
    maximizer = PaidAPIMaximizer()
    
    print("\n" + "=" * 60)
    print("测试付费API最大化利用系统")
    print("=" * 60)
    
    # 运行完整分析
    analysis = await maximizer.run_complete_paid_analysis()
    
    print("\n💎 Coinglass洞察:")
    if analysis["coinglass"].get("insights"):
        insights = analysis["coinglass"]["insights"]
        print(f"  市场结构: {insights.get('market_structure')}")
        print(f"  市场情绪: {insights.get('sentiment')}")
        print(f"  风险指标: {insights.get('risk_metrics')}")
    
    print("\n🐋 WhaleAlert模式:")
    if analysis["whale_alert"].get("patterns"):
        patterns = analysis["whale_alert"]["patterns"]
        print(f"  积累模式: {patterns.get('accumulation')}")
        print(f"  分发模式: {patterns.get('distribution')}")
        print(f"  交易所净流量: ${patterns.get('exchange_movements', {}).get('net', 0):,.0f}")
    
    print("\n🎯 综合洞察:")
    combined = analysis.get("combined_insights", {})
    print(f"  市场方向: {combined.get('market_direction')}")
    print(f"  风险等级: {combined.get('risk_level')}")
    
    if combined.get("action_recommendations"):
        print("\n📋 行动建议:")
        for rec in combined["action_recommendations"]:
            print(f"  - {rec['action']}: {rec['reason']} (置信度: {rec['confidence']:.1%})")
    
    print(f"\n💰 价值提取率: {analysis['value_extracted']:.1%}")
    print("✅ 测试完成！付费API价值已最大化")


if __name__ == "__main__":
    asyncio.run(test_paid_apis())