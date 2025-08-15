"""
Window 3 - 三级监控激活系统 (核心组件)
这是Window 3的大脑，负责监控市场并根据阈值触发不同级别的警报
重要：这是纯数据收集和触发系统，不包含任何分析逻辑
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Window3-Monitor] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringActivationSystem:
    """
    三级监控激活系统 - Window 3的核心
    负责监控市场数据并根据预设阈值触发不同级别的警报
    """
    
    def __init__(self):
        # 触发阈值定义（严格按照文档要求）
        self.thresholds = {
            "price_change": {
                1: 0.003,  # 0.3% - 一级触发
                2: 0.005,  # 0.5% - 二级触发  
                3: 0.010   # 1.0% - 三级触发
            },
            "volume_surge": {
                1: 0.5,    # 50% 增长
                2: 1.0,    # 100% 增长
                3: 2.0     # 200% 增长
            },
            "whale_transfer": {
                1: 50000,      # 5万美元
                2: 100000,     # 10万美元
                3: 1000000     # 100万美元
            },
            "funding_rate_change": {
                1: 0.005,   # 0.5% 变化
                2: 0.010,   # 1.0% 变化
                3: 0.020    # 2.0% 变化
            },
            "exchange_reserve_change": {
                1: 100,     # 100 BTC变化
                2: 500,     # 500 BTC变化
                3: 1000     # 1000 BTC变化
            }
        }
        
        # VIP账号列表（任何动作直接三级触发）
        self.vip_accounts = [
            "@elonmusk",
            "@cz_binance", 
            "@VitalikButerin",
            "@justinsuntron",
            "@SBF_FTX",
            "@brian_armstrong"
        ]
        
        # 监控的主要币种
        self.monitored_symbols = ["BTC", "ETH", "BNB", "SOL", "DOGE", "SHIB"]
        
        # 监控频率配置（秒）
        self.monitor_intervals = {
            "price": 5,          # 价格监控：每5秒
            "volume": 60,        # 成交量监控：每60秒
            "whale": 30,         # 巨鲸监控：每30秒
            "vip": 10,          # VIP账号：每10秒
            "news": 60,         # 新闻监控：每60秒
            "funding": 30,      # 资金费率：每30秒
            "reserve": 120      # 交易所储备：每2分钟
        }
        
        # 价格缓存（用于计算变化）
        self.price_cache = {}
        self.volume_cache = {}
        
        # 触发记录（避免重复触发）
        self.recent_triggers = []
        self.trigger_cooldown = 60  # 同一信号60秒内不重复触发
        
        # 运行状态
        self.is_running = False
        self.monitoring_tasks = []
        
        # API endpoints（使用免费或已付费的）
        self.api_endpoints = {
            "coingecko": "https://api.coingecko.com/api/v3",
            "whale_alert": "https://api.whale-alert.io/v1",
            "cryptopanic": "https://cryptopanic.com/api/v1"
        }
        
        # API Keys（用户付费的）
        self.api_keys = {
            "whale_alert": "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU",
            "cryptopanic": "e79d3bb95497a40871d90a82056e3face2050c53"
        }

    async def start_monitoring(self):
        """启动所有监控任务"""
        self.is_running = True
        logger.info("🚀 三级监控激活系统启动")
        
        # 创建所有监控任务
        self.monitoring_tasks = [
            asyncio.create_task(self.monitor_prices()),
            asyncio.create_task(self.monitor_volumes()),
            asyncio.create_task(self.monitor_whale_transfers()),
            asyncio.create_task(self.monitor_vip_accounts()),
            asyncio.create_task(self.monitor_news()),
            asyncio.create_task(self.monitor_funding_rates()),
            asyncio.create_task(self.monitor_exchange_reserves())
        ]
        
        # 等待所有任务
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

    async def monitor_prices(self):
        """监控价格变化（每5秒）"""
        while self.is_running:
            try:
                for symbol in self.monitored_symbols:
                    price_data = await self.fetch_price_data(symbol)
                    if price_data:
                        self.check_price_trigger(symbol, price_data)
                
                await asyncio.sleep(self.monitor_intervals["price"])
                
            except Exception as e:
                logger.error(f"价格监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["price"])

    async def monitor_volumes(self):
        """监控成交量变化（每60秒）"""
        while self.is_running:
            try:
                for symbol in self.monitored_symbols:
                    volume_data = await self.fetch_volume_data(symbol)
                    if volume_data:
                        self.check_volume_trigger(symbol, volume_data)
                
                await asyncio.sleep(self.monitor_intervals["volume"])
                
            except Exception as e:
                logger.error(f"成交量监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["volume"])

    async def monitor_whale_transfers(self):
        """监控巨鲸转账（每30秒）"""
        while self.is_running:
            try:
                whale_transfers = await self.fetch_whale_transfers()
                for transfer in whale_transfers:
                    self.check_whale_trigger(transfer)
                
                await asyncio.sleep(self.monitor_intervals["whale"])
                
            except Exception as e:
                logger.error(f"巨鲸监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["whale"])

    async def monitor_vip_accounts(self):
        """监控VIP账号动态（每10秒）"""
        while self.is_running:
            try:
                # 这里应该调用Twitter API或其他社交媒体API
                # 由于需要额外配置，暂时用模拟数据
                vip_activities = await self.fetch_vip_activities()
                for activity in vip_activities:
                    self.trigger_vip_alert(activity)
                
                await asyncio.sleep(self.monitor_intervals["vip"])
                
            except Exception as e:
                logger.error(f"VIP监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["vip"])

    async def monitor_news(self):
        """监控重要新闻（每60秒）"""
        while self.is_running:
            try:
                news_data = await self.fetch_news_data()
                for news in news_data:
                    self.check_news_trigger(news)
                
                await asyncio.sleep(self.monitor_intervals["news"])
                
            except Exception as e:
                logger.error(f"新闻监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["news"])

    async def monitor_funding_rates(self):
        """监控资金费率变化（每30秒）"""
        while self.is_running:
            try:
                # 从Window 2接收资金费率数据
                funding_data = await self.receive_window2_funding_data()
                if funding_data:
                    self.check_funding_trigger(funding_data)
                
                await asyncio.sleep(self.monitor_intervals["funding"])
                
            except Exception as e:
                logger.error(f"资金费率监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["funding"])

    async def monitor_exchange_reserves(self):
        """监控交易所储备变化（每2分钟）"""
        while self.is_running:
            try:
                # 从Window 2接收交易所储备数据
                reserve_data = await self.receive_window2_reserve_data()
                if reserve_data:
                    self.check_reserve_trigger(reserve_data)
                
                await asyncio.sleep(self.monitor_intervals["reserve"])
                
            except Exception as e:
                logger.error(f"储备监控错误: {e}")
                await asyncio.sleep(self.monitor_intervals["reserve"])

    async def fetch_price_data(self, symbol: str) -> Optional[Dict]:
        """获取价格数据"""
        try:
            # 使用CoinGecko免费API
            coin_id = self.symbol_to_coingecko_id(symbol)
            url = f"{self.api_endpoints['coingecko']}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if coin_id in data:
                            return {
                                "symbol": symbol,
                                "price": data[coin_id]["usd"],
                                "change_24h": data[coin_id].get("usd_24h_change", 0)
                            }
        except Exception as e:
            logger.error(f"获取{symbol}价格失败: {e}")
        return None

    async def fetch_volume_data(self, symbol: str) -> Optional[Dict]:
        """获取成交量数据"""
        try:
            coin_id = self.symbol_to_coingecko_id(symbol)
            url = f"{self.api_endpoints['coingecko']}/coins/{coin_id}"
            params = {"localization": "false", "tickers": "false", "community_data": "false"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "symbol": symbol,
                            "volume_24h": data["market_data"]["total_volume"]["usd"]
                        }
        except Exception as e:
            logger.error(f"获取{symbol}成交量失败: {e}")
        return None

    async def fetch_whale_transfers(self) -> List[Dict]:
        """获取巨鲸转账数据"""
        transfers = []
        try:
            # 使用WhaleAlert API
            url = f"{self.api_endpoints['whale_alert']}/transactions"
            headers = {"X-WA-API-KEY": self.api_keys["whale_alert"]}
            params = {
                "api_key": self.api_keys["whale_alert"],
                "min_value": 50000,  # 最低5万美元
                "limit": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "transactions" in data:
                            transfers = data["transactions"]
        except Exception as e:
            logger.error(f"获取巨鲸转账失败: {e}")
        return transfers

    async def fetch_vip_activities(self) -> List[Dict]:
        """获取VIP账号活动（需要Twitter API）"""
        # 暂时返回空列表，实际需要接入Twitter API
        return []

    async def fetch_news_data(self) -> List[Dict]:
        """获取新闻数据"""
        news = []
        try:
            # 由于CryptoPanic配额已用完，暂时跳过
            # 实际生产环境需要等配额恢复或使用其他新闻源
            pass
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
        return news

    async def receive_window2_funding_data(self) -> Optional[Dict]:
        """接收Window 2的资金费率数据"""
        # 这里应该从Window 2的API接口获取数据
        # 暂时返回模拟数据
        return None

    async def receive_window2_reserve_data(self) -> Optional[Dict]:
        """接收Window 2的交易所储备数据"""
        # 这里应该从Window 2的API接口获取数据
        # 暂时返回模拟数据
        return None

    def check_price_trigger(self, symbol: str, price_data: Dict):
        """检查价格触发条件"""
        current_price = price_data["price"]
        
        # 获取缓存的上次价格
        if symbol in self.price_cache:
            last_price = self.price_cache[symbol]
            price_change = abs((current_price - last_price) / last_price)
            
            # 检查触发级别
            trigger_level = 0
            for level, threshold in self.thresholds["price_change"].items():
                if price_change >= threshold:
                    trigger_level = level
            
            if trigger_level > 0:
                self.send_trigger(
                    level=trigger_level,
                    type="price_change",
                    symbol=symbol,
                    data={
                        "current_price": current_price,
                        "last_price": last_price,
                        "change_percentage": price_change * 100
                    }
                )
        
        # 更新缓存
        self.price_cache[symbol] = current_price

    def check_volume_trigger(self, symbol: str, volume_data: Dict):
        """检查成交量触发条件"""
        current_volume = volume_data["volume_24h"]
        
        # 获取缓存的上次成交量
        if symbol in self.volume_cache:
            last_volume = self.volume_cache[symbol]
            if last_volume > 0:
                volume_change = (current_volume - last_volume) / last_volume
                
                # 检查触发级别
                trigger_level = 0
                for level, threshold in self.thresholds["volume_surge"].items():
                    if volume_change >= threshold:
                        trigger_level = level
                
                if trigger_level > 0:
                    self.send_trigger(
                        level=trigger_level,
                        type="volume_surge",
                        symbol=symbol,
                        data={
                            "current_volume": current_volume,
                            "last_volume": last_volume,
                            "surge_percentage": volume_change * 100
                        }
                    )
        
        # 更新缓存
        self.volume_cache[symbol] = current_volume

    def check_whale_trigger(self, transfer: Dict):
        """检查巨鲸转账触发条件"""
        amount_usd = transfer.get("amount_usd", 0)
        
        # 检查触发级别
        trigger_level = 0
        for level, threshold in self.thresholds["whale_transfer"].items():
            if amount_usd >= threshold:
                trigger_level = level
        
        if trigger_level > 0:
            self.send_trigger(
                level=trigger_level,
                type="whale_transfer",
                symbol=transfer.get("symbol", "UNKNOWN"),
                data={
                    "amount_usd": amount_usd,
                    "from": transfer.get("from", {}).get("owner", "unknown"),
                    "to": transfer.get("to", {}).get("owner", "unknown"),
                    "transaction_type": transfer.get("transaction_type", "transfer")
                }
            )

    def trigger_vip_alert(self, activity: Dict):
        """VIP账号活动直接三级触发"""
        self.send_trigger(
            level=3,  # VIP直接三级
            type="vip_activity",
            symbol="MULTIPLE",
            data=activity
        )

    def check_news_trigger(self, news: Dict):
        """检查新闻触发条件"""
        # 根据新闻的重要性评分触发
        importance = news.get("importance", 0)
        
        trigger_level = 0
        if importance >= 80:
            trigger_level = 3
        elif importance >= 60:
            trigger_level = 2
        elif importance >= 40:
            trigger_level = 1
        
        if trigger_level > 0:
            self.send_trigger(
                level=trigger_level,
                type="news_alert",
                symbol=news.get("currencies", ["UNKNOWN"])[0] if news.get("currencies") else "UNKNOWN",
                data=news
            )

    def check_funding_trigger(self, funding_data: Dict):
        """检查资金费率触发条件"""
        for symbol, data in funding_data.items():
            rate_change = data.get("rate_change", 0)
            
            # 检查触发级别
            trigger_level = 0
            for level, threshold in self.thresholds["funding_rate_change"].items():
                if abs(rate_change) >= threshold:
                    trigger_level = level
            
            if trigger_level > 0:
                self.send_trigger(
                    level=trigger_level,
                    type="funding_rate_change",
                    symbol=symbol,
                    data=data
                )

    def check_reserve_trigger(self, reserve_data: Dict):
        """检查交易所储备触发条件"""
        btc_change = reserve_data.get("btc_change", 0)
        
        # 检查触发级别
        trigger_level = 0
        for level, threshold in self.thresholds["exchange_reserve_change"].items():
            if abs(btc_change) >= threshold:
                trigger_level = level
        
        if trigger_level > 0:
            self.send_trigger(
                level=trigger_level,
                type="reserve_change",
                symbol="BTC",
                data=reserve_data
            )

    def send_trigger(self, level: int, type: str, symbol: str, data: Dict):
        """发送触发信号给Window 6"""
        # 生成触发ID
        trigger_id = f"{type}_{symbol}_{int(time.time())}"
        
        # 检查是否在冷却期内
        if self.is_in_cooldown(trigger_id):
            return
        
        # 构建触发消息
        trigger_message = {
            "source": "window3",
            "timestamp": datetime.now().isoformat(),
            "trigger_id": trigger_id,
            "level": level,
            "type": type,
            "symbol": symbol,
            "data": data,
            "action_required": self.get_action_for_level(level)
        }
        
        # 记录触发
        self.recent_triggers.append({
            "id": trigger_id,
            "time": time.time()
        })
        
        # 清理过期的触发记录
        self.clean_old_triggers()
        
        # 发送给Window 6
        self.forward_to_window6(trigger_message)
        
        # 记录日志
        level_emoji = ["", "⚡", "🔥", "🚨"][level]
        logger.info(f"{level_emoji} {level}级触发 - {type} - {symbol} - {data}")

    def forward_to_window6(self, trigger_message: Dict):
        """转发触发消息给Window 6"""
        # 这里应该通过消息队列或API发送给Window 6
        # 暂时保存到文件
        filename = f"trigger_{trigger_message['level']}_{int(time.time())}.json"
        filepath = f"/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/triggers/{filename}"
        
        try:
            import os
            os.makedirs("/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/triggers", exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trigger_message, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存触发消息失败: {e}")

    def is_in_cooldown(self, trigger_id: str) -> bool:
        """检查触发是否在冷却期内"""
        current_time = time.time()
        for trigger in self.recent_triggers:
            if trigger["id"].startswith(trigger_id.split("_")[0]):  # 同类型触发
                if current_time - trigger["time"] < self.trigger_cooldown:
                    return True
        return False

    def clean_old_triggers(self):
        """清理过期的触发记录"""
        current_time = time.time()
        self.recent_triggers = [
            t for t in self.recent_triggers 
            if current_time - t["time"] < self.trigger_cooldown * 2
        ]

    def get_action_for_level(self, level: int) -> str:
        """根据级别返回建议的动作"""
        actions = {
            1: "monitor",           # 一级：继续监控
            2: "activate_ai",       # 二级：激活AI分析
            3: "immediate_action"   # 三级：立即行动
        }
        return actions.get(level, "monitor")

    def symbol_to_coingecko_id(self, symbol: str) -> str:
        """将交易符号转换为CoinGecko ID"""
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "DOGE": "dogecoin",
            "SHIB": "shiba-inu"
        }
        return mapping.get(symbol, symbol.lower())

    async def stop_monitoring(self):
        """停止所有监控任务"""
        self.is_running = False
        logger.info("⏹️ 正在停止三级监控激活系统...")
        
        # 等待所有任务完成
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        logger.info("✅ 三级监控激活系统已停止")


# 测试和启动函数
async def main():
    """主函数 - 启动三级监控激活系统"""
    system = MonitoringActivationSystem()
    
    try:
        logger.info("=" * 50)
        logger.info("Window 3 - 三级监控激活系统")
        logger.info("=" * 50)
        
        # 启动监控
        await system.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("\n收到停止信号")
        await system.stop_monitoring()
    except Exception as e:
        logger.error(f"系统错误: {e}")
        await system.stop_monitoring()


if __name__ == "__main__":
    # 运行系统
    asyncio.run(main())