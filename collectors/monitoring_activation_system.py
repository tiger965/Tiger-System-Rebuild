"""
三级监控激活系统 - Window 3核心组件
实现实时监控和触发机制
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import aiohttp
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TriggerLevel(Enum):
    """触发级别枚举"""
    LEVEL_1 = 1  # 一级触发 - 低风险
    LEVEL_2 = 2  # 二级触发 - 中风险
    LEVEL_3 = 3  # 三级触发 - 高风险


class MonitorType(Enum):
    """监控类型枚举"""
    PRICE_CHANGE = "price_change"
    VOLUME_SURGE = "volume_surge"
    WHALE_TRANSFER = "whale_transfer"
    VIP_ACCOUNT = "vip_account"
    NEWS_ALERT = "news_alert"
    SOCIAL_SENTIMENT = "social_sentiment"


@dataclass
class TriggerSignal:
    """触发信号数据类"""
    source: str = "window3"
    level: int = 1
    type: str = ""
    symbol: str = ""
    value: float = 0.0
    action_required: str = "monitor"
    timestamp: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}


class MonitoringActivationSystem:
    """三级监控激活系统 - Window 3的核心"""
    
    def __init__(self):
        # 触发阈值定义
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
            "social_sentiment": {
                1: 0.6,    # 60% 正面情绪
                2: 0.7,    # 70% 正面情绪
                3: 0.8     # 80% 正面情绪
            }
        }
        
        # VIP账号列表（直接三级触发）
        self.vip_accounts = [
            "@elonmusk", 
            "@cz_binance", 
            "@VitalikButerin",
            "@SBF_FTX",
            "@CathieDWood",
            "@michael_saylor"
        ]
        
        # 监控的主要币种
        self.monitored_symbols = [
            "BTC", "ETH", "BNB", "SOL", "ADA", 
            "XRP", "DOT", "AVAX", "LUNA", "MATIC"
        ]
        
        # 价格缓存（用于计算变化率）
        self.price_cache = {}
        self.volume_cache = {}
        
        # 触发历史记录
        self.trigger_history = []
        
        # 监控任务列表
        self.monitoring_tasks = []
        
        # Window 6的API接口
        self.window6_endpoint = "http://localhost:8000/api/window6/trigger"
        
        # 监控统计
        self.stats = {
            "total_triggers": 0,
            "level_1_triggers": 0,
            "level_2_triggers": 0,
            "level_3_triggers": 0,
            "last_trigger_time": None
        }
    
    async def initialize(self):
        """初始化监控系统"""
        logger.info("正在初始化三级监控激活系统...")
        
        # 初始化价格缓存
        await self._initialize_price_cache()
        
        # 启动所有监控任务
        await self.start_all_monitors()
        
        logger.info("三级监控激活系统初始化完成")
    
    async def _initialize_price_cache(self):
        """初始化价格缓存"""
        # 这里应该从交易所API获取初始价格
        # 暂时使用模拟数据
        self.price_cache = {
            "BTC": 45000.0,
            "ETH": 3000.0,
            "BNB": 400.0,
            "SOL": 100.0,
            "ADA": 0.5
        }
        
        self.volume_cache = {
            "BTC": 1000000000,
            "ETH": 500000000,
            "BNB": 200000000,
            "SOL": 100000000,
            "ADA": 50000000
        }
    
    async def start_all_monitors(self):
        """启动所有监控任务"""
        self.monitoring_tasks = [
            asyncio.create_task(self.monitor_price_changes()),
            asyncio.create_task(self.monitor_volume_surge()),
            asyncio.create_task(self.monitor_whale_transfers()),
            asyncio.create_task(self.monitor_vip_accounts()),
            asyncio.create_task(self.monitor_news_alerts())
        ]
        logger.info(f"已启动 {len(self.monitoring_tasks)} 个监控任务")
    
    async def monitor_price_changes(self):
        """监控价格变化 - 每5秒检查一次"""
        logger.info("启动价格监控任务")
        
        while True:
            try:
                for symbol in self.monitored_symbols:
                    # 获取当前价格（这里应该从交易所API获取）
                    current_price = await self._get_current_price(symbol)
                    
                    if symbol in self.price_cache:
                        old_price = self.price_cache[symbol]
                        if old_price > 0:
                            # 计算价格变化率
                            change_rate = abs((current_price - old_price) / old_price)
                            
                            # 检查触发级别
                            trigger_level = self._check_trigger_level(
                                change_rate, 
                                MonitorType.PRICE_CHANGE
                            )
                            
                            if trigger_level:
                                await self._send_trigger_signal(
                                    level=trigger_level,
                                    monitor_type=MonitorType.PRICE_CHANGE,
                                    symbol=symbol,
                                    value=change_rate,
                                    details={
                                        "old_price": old_price,
                                        "new_price": current_price,
                                        "change_percent": round(change_rate * 100, 2)
                                    }
                                )
                    
                    # 更新缓存
                    self.price_cache[symbol] = current_price
                
                await asyncio.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"价格监控出错: {e}")
                await asyncio.sleep(5)
    
    async def monitor_volume_surge(self):
        """监控成交量激增 - 每60秒检查一次"""
        logger.info("启动成交量监控任务")
        
        while True:
            try:
                for symbol in self.monitored_symbols:
                    # 获取当前成交量（这里应该从交易所API获取）
                    current_volume = await self._get_current_volume(symbol)
                    
                    if symbol in self.volume_cache:
                        old_volume = self.volume_cache[symbol]
                        if old_volume > 0:
                            # 计算成交量变化率
                            volume_change = (current_volume - old_volume) / old_volume
                            
                            # 检查触发级别
                            trigger_level = self._check_trigger_level(
                                volume_change,
                                MonitorType.VOLUME_SURGE
                            )
                            
                            if trigger_level:
                                await self._send_trigger_signal(
                                    level=trigger_level,
                                    monitor_type=MonitorType.VOLUME_SURGE,
                                    symbol=symbol,
                                    value=volume_change,
                                    details={
                                        "old_volume": old_volume,
                                        "new_volume": current_volume,
                                        "surge_percent": round(volume_change * 100, 2)
                                    }
                                )
                    
                    # 更新缓存
                    self.volume_cache[symbol] = current_volume
                
                await asyncio.sleep(60)  # 每60秒检查一次
                
            except Exception as e:
                logger.error(f"成交量监控出错: {e}")
                await asyncio.sleep(60)
    
    async def monitor_whale_transfers(self):
        """监控巨鲸转账 - 每30秒检查一次"""
        logger.info("启动巨鲸监控任务")
        
        while True:
            try:
                # 获取最新的巨鲸转账（这里应该从WhaleAlert API获取）
                whale_transfers = await self._get_whale_transfers()
                
                for transfer in whale_transfers:
                    amount_usd = transfer.get("amount_usd", 0)
                    
                    # 检查触发级别
                    trigger_level = self._check_trigger_level(
                        amount_usd,
                        MonitorType.WHALE_TRANSFER
                    )
                    
                    if trigger_level:
                        await self._send_trigger_signal(
                            level=trigger_level,
                            monitor_type=MonitorType.WHALE_TRANSFER,
                            symbol=transfer.get("symbol", "UNKNOWN"),
                            value=amount_usd,
                            details={
                                "from": transfer.get("from", ""),
                                "to": transfer.get("to", ""),
                                "amount": transfer.get("amount", 0),
                                "transaction_type": transfer.get("transaction_type", "")
                            }
                        )
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"巨鲸监控出错: {e}")
                await asyncio.sleep(30)
    
    async def monitor_vip_accounts(self):
        """监控VIP账号 - 每10秒检查一次"""
        logger.info("启动VIP账号监控任务")
        
        while True:
            try:
                # 检查VIP账号的新动态（这里应该从Twitter API获取）
                for account in self.vip_accounts:
                    new_activity = await self._check_vip_activity(account)
                    
                    if new_activity:
                        # VIP账号活动直接触发三级
                        await self._send_trigger_signal(
                            level=3,
                            monitor_type=MonitorType.VIP_ACCOUNT,
                            symbol="MULTIPLE",
                            value=1.0,
                            details={
                                "account": account,
                                "activity_type": new_activity.get("type", ""),
                                "content": new_activity.get("content", ""),
                                "timestamp": new_activity.get("timestamp", "")
                            }
                        )
                
                await asyncio.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                logger.error(f"VIP账号监控出错: {e}")
                await asyncio.sleep(10)
    
    async def monitor_news_alerts(self):
        """监控新闻警报 - 每60秒检查一次"""
        logger.info("启动新闻监控任务")
        
        while True:
            try:
                # 获取最新新闻（这里应该从新闻API获取）
                news_alerts = await self._get_news_alerts()
                
                for news in news_alerts:
                    importance = news.get("importance", 0)
                    
                    # 根据新闻重要性决定触发级别
                    if importance >= 8:
                        trigger_level = 3
                    elif importance >= 6:
                        trigger_level = 2
                    elif importance >= 4:
                        trigger_level = 1
                    else:
                        trigger_level = None
                    
                    if trigger_level:
                        await self._send_trigger_signal(
                            level=trigger_level,
                            monitor_type=MonitorType.NEWS_ALERT,
                            symbol=news.get("related_symbols", ["MARKET"])[0],
                            value=importance,
                            details={
                                "title": news.get("title", ""),
                                "summary": news.get("summary", ""),
                                "source": news.get("source", ""),
                                "url": news.get("url", "")
                            }
                        )
                
                await asyncio.sleep(60)  # 每60秒检查一次
                
            except Exception as e:
                logger.error(f"新闻监控出错: {e}")
                await asyncio.sleep(60)
    
    def _check_trigger_level(self, value: float, monitor_type: MonitorType) -> Optional[int]:
        """检查触发级别"""
        thresholds = self.thresholds.get(monitor_type.value, {})
        
        # 从高到低检查触发级别
        for level in [3, 2, 1]:
            if level in thresholds and value >= thresholds[level]:
                return level
        
        return None
    
    async def _send_trigger_signal(self, level: int, monitor_type: MonitorType, 
                                  symbol: str, value: float, details: Dict[str, Any]):
        """发送触发信号给Window 6"""
        
        # 创建触发信号
        signal = TriggerSignal(
            source="window3",
            level=level,
            type=monitor_type.value,
            symbol=symbol,
            value=value,
            action_required="activate_ai" if level >= 2 else "monitor",
            details=details
        )
        
        # 记录触发
        self.trigger_history.append(signal)
        self.stats["total_triggers"] += 1
        self.stats[f"level_{level}_triggers"] += 1
        self.stats["last_trigger_time"] = datetime.now().isoformat()
        
        # 日志记录
        logger.warning(f"触发信号 - 级别:{level} 类型:{monitor_type.value} "
                      f"币种:{symbol} 值:{value:.4f}")
        
        # 发送到Window 6
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.window6_endpoint,
                    json=asdict(signal),
                    timeout=5
                ) as response:
                    if response.status == 200:
                        logger.info(f"成功发送触发信号到Window 6")
                    else:
                        logger.error(f"发送触发信号失败: {response.status}")
        except Exception as e:
            logger.error(f"发送触发信号到Window 6失败: {e}")
            # 即使发送失败，也要保存触发记录
            await self._save_trigger_to_file(signal)
    
    async def _save_trigger_to_file(self, signal: TriggerSignal):
        """保存触发信号到文件（备份）"""
        try:
            filename = f"trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"/tmp/{filename}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(signal), f, ensure_ascii=False, indent=2)
            
            logger.info(f"触发信号已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存触发信号失败: {e}")
    
    # 以下是模拟数据获取函数，实际应该从API获取
    
    async def _get_current_price(self, symbol: str) -> float:
        """获取当前价格（模拟）"""
        import random
        if symbol in self.price_cache:
            # 模拟价格波动 (-2% 到 +2%)
            base_price = self.price_cache[symbol]
            change = random.uniform(-0.02, 0.02)
            return base_price * (1 + change)
        return 0.0
    
    async def _get_current_volume(self, symbol: str) -> float:
        """获取当前成交量（模拟）"""
        import random
        if symbol in self.volume_cache:
            # 模拟成交量波动 (-50% 到 +200%)
            base_volume = self.volume_cache[symbol]
            change = random.uniform(-0.5, 2.0)
            return base_volume * (1 + change)
        return 0.0
    
    async def _get_whale_transfers(self) -> List[Dict[str, Any]]:
        """获取巨鲸转账（模拟）"""
        import random
        
        # 随机生成0-2个转账记录
        transfers = []
        for _ in range(random.randint(0, 2)):
            transfers.append({
                "symbol": random.choice(["BTC", "ETH", "USDT"]),
                "amount": random.uniform(1, 100),
                "amount_usd": random.uniform(10000, 2000000),
                "from": "whale_wallet_" + str(random.randint(1, 100)),
                "to": "exchange_" + random.choice(["binance", "coinbase", "okx"]),
                "transaction_type": random.choice(["transfer", "exchange_inflow", "exchange_outflow"])
            })
        
        return transfers
    
    async def _check_vip_activity(self, account: str) -> Optional[Dict[str, Any]]:
        """检查VIP账号活动（模拟）"""
        import random
        
        # 5%概率有新活动
        if random.random() < 0.05:
            return {
                "type": random.choice(["tweet", "reply", "retweet"]),
                "content": f"模拟内容 from {account}",
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    async def _get_news_alerts(self) -> List[Dict[str, Any]]:
        """获取新闻警报（模拟）"""
        import random
        
        # 随机生成0-1个新闻
        news = []
        if random.random() < 0.1:  # 10%概率有新闻
            news.append({
                "title": "模拟新闻标题",
                "summary": "模拟新闻摘要",
                "importance": random.randint(1, 10),
                "related_symbols": [random.choice(["BTC", "ETH", "BNB"])],
                "source": "CryptoPanic",
                "url": "https://example.com"
            })
        
        return news
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        return {
            **self.stats,
            "monitored_symbols": len(self.monitored_symbols),
            "vip_accounts": len(self.vip_accounts),
            "active_monitors": len([t for t in self.monitoring_tasks if not t.done()]),
            "trigger_history_count": len(self.trigger_history)
        }
    
    async def shutdown(self):
        """关闭监控系统"""
        logger.info("正在关闭三级监控激活系统...")
        
        # 取消所有监控任务
        for task in self.monitoring_tasks:
            task.cancel()
        
        # 等待任务结束
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        logger.info("三级监控激活系统已关闭")


async def main():
    """主函数 - 用于测试"""
    system = MonitoringActivationSystem()
    
    try:
        await system.initialize()
        
        # 运行监控系统
        logger.info("三级监控激活系统正在运行...")
        logger.info(f"监控统计: {system.get_statistics()}")
        
        # 持续运行
        while True:
            await asyncio.sleep(60)
            # 每分钟输出一次统计
            logger.info(f"运行统计: {system.get_statistics()}")
            
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())