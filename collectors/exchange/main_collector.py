"""
主数据采集器
整合OKX和Binance数据采集，提供统一接口
"""
import asyncio
import yaml
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path

from .okx_collector import OKXCollector, OKXConfig
from .binance_collector import BinanceCollector, BinanceConfig
from .normalizer import DataNormalizer
from .detector import AnomalyDetector
from .validator import DataValidator

logger = logging.getLogger(__name__)

class ExchangeDataCollector:
    """交易所数据采集主控制器"""
    
    def __init__(self, config_path: str = None):
        # 加载配置
        self.config = self._load_config(config_path)
        self.watch_list = self._load_watch_list()
        
        # 初始化各模块
        self.okx_collector = None
        self.binance_collector = None
        self.normalizer = DataNormalizer()
        self.detector = AnomalyDetector(self.config.get("anomaly_detection"))
        self.validator = DataValidator(self.config.get("validation"))
        
        # 数据缓存
        self.latest_data = {}
        
        # 运行状态
        self.running = False
        self.tasks = []
        
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "exchange_config.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _load_watch_list(self) -> Dict:
        """加载监控列表"""
        watch_list_path = Path(__file__).parent.parent.parent / "config" / "watch_list.yaml"
        
        try:
            with open(watch_list_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载监控列表失败: {e}")
            return {}
    
    async def initialize(self):
        """初始化采集器"""
        logger.info("正在初始化交易所数据采集器...")
        
        # 初始化OKX采集器
        okx_cfg = self.config.get("okx", {})
        # 只传递OKXConfig支持的参数
        okx_config = OKXConfig(
            api_key=okx_cfg.get("api_key", ""),
            api_secret=okx_cfg.get("api_secret", ""),
            passphrase=okx_cfg.get("passphrase", ""),
            rest_url=okx_cfg.get("rest_url", "https://www.okx.com"),
            ws_public=okx_cfg.get("ws_public", "wss://ws.okx.com:8443/ws/v5/public"),
            ws_private=okx_cfg.get("ws_private", "wss://ws.okx.com:8443/ws/v5/private"),
            demo_mode=okx_cfg.get("demo_mode", True)
        )
        self.okx_collector = OKXCollector(okx_config)
        await self.okx_collector.initialize()
        
        # 初始化Binance采集器
        binance_cfg = self.config.get("binance", {})
        # 只传递BinanceConfig支持的参数
        binance_config = BinanceConfig(
            api_key=binance_cfg.get("api_key", ""),
            api_secret=binance_cfg.get("api_secret", ""),
            rest_url=binance_cfg.get("rest_url", "https://api.binance.com"),
            ws_url=binance_cfg.get("ws_url", "wss://stream.binance.com:9443/ws"),
            futures_rest_url=binance_cfg.get("futures_rest_url", "https://fapi.binance.com"),
            futures_ws_url=binance_cfg.get("futures_ws_url", "wss://fstream.binance.com/ws"),
            demo_mode=binance_cfg.get("demo_mode", True)
        )
        self.binance_collector = BinanceCollector(binance_config)
        await self.binance_collector.initialize()
        
        # 注册异常检测回调
        self.detector.register_callback(self._handle_anomaly)
        
        logger.info("交易所数据采集器初始化完成")
    
    async def start(self):
        """启动采集"""
        if self.running:
            logger.warning("采集器已在运行")
            return
        
        self.running = True
        logger.info("启动数据采集...")
        
        # 连接WebSocket
        await self._connect_websockets()
        
        # 订阅数据
        await self._subscribe_all()
        
        # 启动定时任务
        self.tasks = [
            asyncio.create_task(self._collect_ticker_data()),
            asyncio.create_task(self._collect_depth_data()),
            asyncio.create_task(self._collect_trade_data()),
            asyncio.create_task(self._collect_funding_rate()),
            asyncio.create_task(self._collect_open_interest()),
            asyncio.create_task(self._monitor_anomalies()),
            asyncio.create_task(self._health_check())
        ]
        
        logger.info("数据采集已启动")
    
    async def stop(self):
        """停止采集"""
        logger.info("停止数据采集...")
        self.running = False
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        # 等待任务结束
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # 关闭连接
        if self.okx_collector:
            await self.okx_collector.close()
        if self.binance_collector:
            await self.binance_collector.close()
        
        logger.info("数据采集已停止")
    
    async def _connect_websockets(self):
        """连接WebSocket"""
        try:
            await self.okx_collector.connect_public_ws()
            await self.binance_collector.connect_ws()
            await self.binance_collector.connect_futures_ws()
        except Exception as e:
            logger.error(f"连接WebSocket失败: {e}")
    
    async def _subscribe_all(self):
        """订阅所有监控币种"""
        # 获取需要监控的币种
        okx_symbols = []
        binance_symbols = []
        
        for category in ["core_symbols", "major_symbols"]:
            symbols = self.watch_list.get(category, [])
            for symbol_config in symbols:
                symbol = symbol_config["symbol"]
                exchanges = symbol_config.get("exchanges", [])
                
                if "OKX" in exchanges:
                    okx_symbols.append(symbol)
                if "Binance" in exchanges:
                    binance_symbol = symbol.replace("-", "")
                    binance_symbols.append(binance_symbol)
        
        # OKX订阅
        if okx_symbols:
            await self.okx_collector.subscribe_ticker(okx_symbols)
            await self.okx_collector.subscribe_trades(okx_symbols[:5])  # 限制数量
            await self.okx_collector.subscribe_books(okx_symbols[:3])   # 限制数量
        
        # Binance订阅
        if binance_symbols:
            await self.binance_collector.subscribe_ticker(binance_symbols)
            await self.binance_collector.subscribe_trades(binance_symbols[:5])
            await self.binance_collector.subscribe_depth(binance_symbols[:3])
    
    async def _collect_ticker_data(self):
        """定时采集行情数据"""
        interval = self.config["collection"]["intervals"]["ticker"]
        
        while self.running:
            try:
                # 采集核心币种行情
                for symbol_config in self.watch_list.get("core_symbols", []):
                    symbol = symbol_config["symbol"]
                    
                    # OKX数据
                    if "OKX" in symbol_config.get("exchanges", []):
                        data = await self.okx_collector.get_ticker(symbol)
                        if data:
                            normalized = self.normalizer.normalize_ticker(data, "OKX")
                            valid, error = self.validator.validate_ticker(normalized)
                            
                            if valid:
                                await self._store_data("ticker", symbol, normalized)
                                await self.detector.detect_price_anomaly(
                                    symbol, normalized["last_price"]
                                )
                            else:
                                logger.error(f"OKX行情数据验证失败: {error}")
                    
                    # Binance数据
                    if "Binance" in symbol_config.get("exchanges", []):
                        binance_symbol = symbol.replace("-", "")
                        data = await self.binance_collector.get_ticker_24hr(binance_symbol)
                        if data:
                            normalized = self.normalizer.normalize_ticker(data, "Binance")
                            valid, error = self.validator.validate_ticker(normalized)
                            
                            if valid:
                                await self._store_data("ticker", binance_symbol, normalized)
                                await self.detector.detect_price_anomaly(
                                    binance_symbol, normalized["last_price"]
                                )
                            else:
                                logger.error(f"Binance行情数据验证失败: {error}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"采集行情数据失败: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_depth_data(self):
        """定时采集深度数据"""
        interval = self.config["collection"]["intervals"]["depth"]
        
        while self.running:
            try:
                # 只采集核心币种深度
                for symbol_config in self.watch_list.get("core_symbols", []):
                    symbol = symbol_config["symbol"]
                    
                    if "depth" in symbol_config.get("features", []):
                        # OKX深度
                        if "OKX" in symbol_config.get("exchanges", []):
                            data = await self.okx_collector.get_order_book(symbol)
                            if data:
                                normalized = self.normalizer.normalize_depth(data, "OKX", symbol)
                                valid, error = self.validator.validate_depth(normalized)
                                
                                if valid:
                                    await self._store_data("depth", symbol, normalized)
                                    await self.detector.detect_depth_anomaly(symbol, normalized)
                                else:
                                    logger.error(f"OKX深度数据验证失败: {error}")
                        
                        # Binance深度
                        if "Binance" in symbol_config.get("exchanges", []):
                            binance_symbol = symbol.replace("-", "")
                            data = await self.binance_collector.get_order_book(binance_symbol)
                            if data:
                                normalized = self.normalizer.normalize_depth(
                                    data, "Binance", binance_symbol
                                )
                                valid, error = self.validator.validate_depth(normalized)
                                
                                if valid:
                                    await self._store_data("depth", binance_symbol, normalized)
                                    await self.detector.detect_depth_anomaly(
                                        binance_symbol, normalized
                                    )
                                else:
                                    logger.error(f"Binance深度数据验证失败: {error}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"采集深度数据失败: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_trade_data(self):
        """定时采集成交数据"""
        interval = self.config["collection"]["intervals"]["trades"]
        
        while self.running:
            try:
                # WebSocket已经在推送成交数据，这里可以做额外处理
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"处理成交数据失败: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_funding_rate(self):
        """定时采集资金费率"""
        interval = self.config["collection"]["intervals"]["funding_rate"]
        
        while self.running:
            try:
                # 采集永续合约资金费率
                for symbol_config in self.watch_list.get("futures_symbols", []):
                    symbol = symbol_config["symbol"]
                    exchange = symbol_config["exchange"]
                    
                    if "funding_rate" in symbol_config.get("features", []):
                        if exchange == "OKX":
                            data = await self.okx_collector.get_funding_rate(symbol)
                            if data:
                                normalized = self.normalizer.normalize_funding_rate(data, "OKX")
                                await self._store_data("funding_rate", symbol, normalized)
                                await self.detector.detect_funding_rate_anomaly(
                                    symbol, normalized["funding_rate"]
                                )
                        
                        elif exchange == "Binance":
                            data = await self.binance_collector.get_funding_rate(symbol)
                            if data:
                                normalized = self.normalizer.normalize_funding_rate(data, "Binance")
                                await self._store_data("funding_rate", symbol, normalized)
                                await self.detector.detect_funding_rate_anomaly(
                                    symbol, normalized["funding_rate"]
                                )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"采集资金费率失败: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_open_interest(self):
        """定时采集持仓量"""
        interval = self.config["collection"]["intervals"]["open_interest"]
        
        while self.running:
            try:
                # 采集持仓量数据
                okx_data = await self.okx_collector.get_open_interest("SWAP")
                if okx_data:
                    for item in okx_data[:10]:  # 限制数量
                        normalized = self.normalizer.normalize_open_interest(item, "OKX")
                        await self._store_data("open_interest", normalized["symbol"], normalized)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"采集持仓量失败: {e}")
                await asyncio.sleep(interval)
    
    async def _monitor_anomalies(self):
        """监控异常"""
        while self.running:
            try:
                # 交叉验证价格
                btc_okx = self.latest_data.get("ticker", {}).get("BTC-USDT")
                btc_binance = self.latest_data.get("ticker", {}).get("BTCUSDT")
                
                if btc_okx and btc_binance:
                    await self.detector.detect_cross_exchange_anomaly(
                        "BTCUSDT",
                        btc_okx.get("last_price", 0),
                        btc_binance.get("last_price", 0)
                    )
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"异常监控失败: {e}")
                await asyncio.sleep(5)
    
    async def _health_check(self):
        """健康检查"""
        while self.running:
            try:
                # 检查WebSocket连接
                # 检查数据更新时间
                # 检查内存使用
                
                stats = {
                    "detector_stats": self.detector.get_statistics(),
                    "validator_stats": self.validator.get_stats(),
                    "latest_data_count": len(self.latest_data)
                }
                
                logger.info(f"健康检查: {stats}")
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                await asyncio.sleep(60)
    
    async def _store_data(self, data_type: str, symbol: str, data: Dict):
        """存储数据"""
        # 更新最新数据缓存
        if data_type not in self.latest_data:
            self.latest_data[data_type] = {}
        self.latest_data[data_type][symbol] = data
        
        # TODO: 存储到数据库
        # TODO: 发送到消息队列
        
        logger.debug(f"存储{data_type}数据: {symbol}")
    
    async def _handle_anomaly(self, anomaly: Dict):
        """处理异常事件"""
        logger.warning(f"检测到异常: {anomaly}")
        
        # TODO: 发送告警
        # TODO: 记录到数据库
        # TODO: 触发策略调整
    
    def get_latest_data(self, data_type: str = None, symbol: str = None) -> Any:
        """获取最新数据"""
        if data_type and symbol:
            return self.latest_data.get(data_type, {}).get(symbol)
        elif data_type:
            return self.latest_data.get(data_type, {})
        else:
            return self.latest_data


# 主函数
async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建采集器
    collector = ExchangeDataCollector()
    
    try:
        # 初始化
        await collector.initialize()
        
        # 启动采集
        await collector.start()
        
        # 运行
        logger.info("数据采集器正在运行，按Ctrl+C停止...")
        while True:
            await asyncio.sleep(10)
            
            # 打印最新数据
            btc_data = collector.get_latest_data("ticker", "BTC-USDT")
            if btc_data:
                logger.info(f"BTC-USDT最新价格: {btc_data.get('last_price')}")
            
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        # 停止采集
        await collector.stop()

if __name__ == "__main__":
    asyncio.run(main())