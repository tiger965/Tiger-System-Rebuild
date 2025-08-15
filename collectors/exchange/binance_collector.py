"""
Binance交易所数据采集器
实现REST API和WebSocket数据采集
"""
import asyncio
import json
import time
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import aiohttp
import websockets
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BinanceConfig:
    """Binance配置"""
    api_key: str = ""
    api_secret: str = ""
    rest_url: str = "https://api.binance.com"
    ws_url: str = "wss://stream.binance.com:9443/ws"
    futures_rest_url: str = "https://fapi.binance.com"
    futures_ws_url: str = "wss://fstream.binance.com/ws"
    demo_mode: bool = True  # 模拟模式

class BinanceCollector:
    """Binance数据采集器"""
    
    def __init__(self, config: BinanceConfig = None):
        self.config = config or BinanceConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_conn = None
        self.futures_ws_conn = None
        self.running = False
        self.subscriptions = set()
        self.rate_limiter = BinanceRateLimiter()
        
    async def initialize(self):
        """初始化采集器"""
        self.session = aiohttp.ClientSession()
        logger.info("Binance采集器初始化完成")
        
    async def close(self):
        """关闭采集器"""
        self.running = False
        if self.ws_conn:
            await self.ws_conn.close()
        if self.futures_ws_conn:
            await self.futures_ws_conn.close()
        if self.session:
            await self.session.close()
        logger.info("Binance采集器已关闭")
    
    # REST API 方法
    async def get_ticker_24hr(self, symbol: str = None) -> Any:
        """获取24小时价格变动"""
        endpoint = "/api/v3/ticker/24hr"
        params = {"symbol": symbol} if symbol else {}
        return await self._make_request("GET", endpoint, params=params, weight=1 if symbol else 40)
    
    async def get_ticker_price(self, symbol: str = None) -> Any:
        """获取最新价格"""
        endpoint = "/api/v3/ticker/price"
        params = {"symbol": symbol} if symbol else {}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """获取深度数据"""
        endpoint = "/api/v3/depth"
        params = {"symbol": symbol, "limit": limit}
        weight = 1 if limit <= 100 else 5 if limit <= 500 else 10
        return await self._make_request("GET", endpoint, params=params, weight=weight)
    
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict]:
        """获取最近成交"""
        endpoint = "/api/v3/trades"
        params = {"symbol": symbol, "limit": limit}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_agg_trades(self, symbol: str, limit: int = 500) -> List[Dict]:
        """获取归集交易"""
        endpoint = "/api/v3/aggTrades"
        params = {"symbol": symbol, "limit": limit}
        return await self._make_request("GET", endpoint, params=params)
    
    # 期货相关
    async def get_funding_rate(self, symbol: str = None) -> Any:
        """获取资金费率"""
        endpoint = "/fapi/v1/fundingRate"
        params = {"symbol": symbol} if symbol else {"limit": 100}
        return await self._make_request("GET", endpoint, params=params, is_futures=True)
    
    async def get_open_interest(self, symbol: str) -> Dict:
        """获取持仓量"""
        endpoint = "/fapi/v1/openInterest"
        params = {"symbol": symbol}
        return await self._make_request("GET", endpoint, params=params, is_futures=True)
    
    async def get_liquidations(self, symbol: str = None) -> List[Dict]:
        """获取强平订单"""
        endpoint = "/fapi/v1/allForceOrders"
        params = {"symbol": symbol} if symbol else {"limit": 100}
        return await self._make_request("GET", endpoint, params=params, is_futures=True)
    
    # WebSocket 方法
    async def connect_ws(self):
        """连接现货WebSocket"""
        try:
            self.ws_conn = await websockets.connect(self.config.ws_url)
            self.running = True
            logger.info("已连接到Binance现货WebSocket")
            
            # 启动消息处理
            asyncio.create_task(self._handle_ws_messages(self.ws_conn, "spot"))
            
        except Exception as e:
            logger.error(f"连接Binance WebSocket失败: {e}")
            await self._reconnect_ws("spot")
    
    async def connect_futures_ws(self):
        """连接期货WebSocket"""
        try:
            self.futures_ws_conn = await websockets.connect(self.config.futures_ws_url)
            logger.info("已连接到Binance期货WebSocket")
            
            # 启动消息处理
            asyncio.create_task(self._handle_ws_messages(self.futures_ws_conn, "futures"))
            
        except Exception as e:
            logger.error(f"连接Binance期货WebSocket失败: {e}")
            await self._reconnect_ws("futures")
    
    async def subscribe_ticker(self, symbols: List[str]):
        """订阅行情数据"""
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        await self._subscribe(streams)
    
    async def subscribe_trades(self, symbols: List[str]):
        """订阅成交数据"""
        streams = [f"{symbol.lower()}@trade" for symbol in symbols]
        await self._subscribe(streams)
    
    async def subscribe_depth(self, symbols: List[str], levels: int = 20):
        """订阅深度数据"""
        streams = [f"{symbol.lower()}@depth{levels}" for symbol in symbols]
        await self._subscribe(streams)
    
    async def subscribe_agg_trades(self, symbols: List[str]):
        """订阅归集交易"""
        streams = [f"{symbol.lower()}@aggTrade" for symbol in symbols]
        await self._subscribe(streams)
    
    # 内部方法
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                           body: Dict = None, weight: int = 1, is_futures: bool = False) -> Any:
        """发送REST请求"""
        await self.rate_limiter.acquire(weight)
        
        base_url = self.config.futures_rest_url if is_futures else self.config.rest_url
        url = f"{base_url}{endpoint}"
        
        if self.config.demo_mode:
            return self._get_mock_data(endpoint, params)
        
        try:
            headers = {}
            if self.config.api_key:
                headers["X-MBX-APIKEY"] = self.config.api_key
                
            if method == "GET":
                async with self.session.get(url, params=params, headers=headers) as response:
                    return await response.json()
            else:
                async with self.session.request(method, url, json=body, headers=headers) as response:
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"请求失败 {url}: {e}")
            raise
    
    def _get_mock_data(self, endpoint: str, params: Dict) -> Any:
        """获取模拟数据"""
        mock_data = {
            "/api/v3/ticker/24hr": {
                "symbol": params.get("symbol", "BTCUSDT"),
                "priceChange": "500.00",
                "priceChangePercent": "0.75",
                "weightedAvgPrice": "67000.00",
                "lastPrice": "67500.50",
                "lastQty": "0.05",
                "bidPrice": "67500.00",
                "bidQty": "1.2",
                "askPrice": "67501.00",
                "askQty": "0.8",
                "openPrice": "67000.00",
                "highPrice": "68000.00",
                "lowPrice": "66500.00",
                "volume": "5432.10",
                "quoteVolume": "365000000.00",
                "openTime": int(time.time() * 1000) - 86400000,
                "closeTime": int(time.time() * 1000),
                "count": 150000
            },
            "/api/v3/depth": {
                "lastUpdateId": 123456789,
                "bids": [
                    ["67500.00", "2.50"],
                    ["67499.00", "1.80"],
                    ["67498.00", "3.20"]
                ],
                "asks": [
                    ["67501.00", "1.50"],
                    ["67502.00", "2.00"],
                    ["67503.00", "1.75"]
                ]
            },
            "/fapi/v1/fundingRate": {
                "symbol": params.get("symbol", "BTCUSDT"),
                "fundingRate": "0.000100",
                "fundingTime": int(time.time() * 1000) + 28800000
            },
            "/fapi/v1/openInterest": {
                "symbol": params.get("symbol", "BTCUSDT"),
                "openInterest": "12345.678",
                "time": int(time.time() * 1000)
            }
        }
        return mock_data.get(endpoint, {})
    
    async def _subscribe(self, streams: List[str]):
        """发送订阅消息"""
        if not self.ws_conn:
            await self.connect_ws()
        
        msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": int(time.time())
        }
        
        await self.ws_conn.send(json.dumps(msg))
        self.subscriptions.update(streams)
        logger.info(f"已订阅: {streams}")
    
    async def _handle_ws_messages(self, ws, ws_type: str):
        """处理WebSocket消息"""
        while self.running:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(msg)
                
                if "result" in data:
                    # 订阅响应
                    if data["result"] is None:
                        logger.info(f"订阅成功: {data.get('id')}")
                else:
                    # 数据推送
                    await self._process_ws_data(data, ws_type)
                    
            except asyncio.TimeoutError:
                # 发送ping
                pong_msg = {"method": "ping"}
                await ws.send(json.dumps(pong_msg))
            except Exception as e:
                logger.error(f"处理{ws_type} WebSocket消息失败: {e}")
                await self._reconnect_ws(ws_type)
                break
    
    async def _process_ws_data(self, data: Dict, ws_type: str):
        """处理WebSocket推送数据"""
        if "stream" in data:
            stream = data["stream"]
            stream_data = data["data"]
            
            # 解析stream类型
            parts = stream.split("@")
            if len(parts) == 2:
                symbol = parts[0].upper()
                stream_type = parts[1]
                
                processed_data = {
                    "source": "Binance",
                    "type": ws_type,
                    "symbol": symbol,
                    "stream_type": stream_type,
                    "data": stream_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # TODO: 发送到消息队列
                logger.debug(f"收到{stream_type}数据: {symbol}")
    
    async def _reconnect_ws(self, ws_type: str):
        """重连WebSocket"""
        logger.info(f"正在重连{ws_type} WebSocket...")
        await asyncio.sleep(5)
        
        if ws_type == "spot":
            await self.connect_ws()
        else:
            await self.connect_futures_ws()
            
        # 重新订阅
        if self.subscriptions:
            msg = {
                "method": "SUBSCRIBE",
                "params": list(self.subscriptions),
                "id": int(time.time())
            }
            ws = self.ws_conn if ws_type == "spot" else self.futures_ws_conn
            await ws.send(json.dumps(msg))

class BinanceRateLimiter:
    """Binance速率限制器"""
    
    def __init__(self):
        self.weight_limit = 1200  # 每分钟权重限制
        self.order_limit = 100    # 每10秒订单限制
        self.raw_limit = 6100     # 每5分钟原始请求限制
        
        self.weight_used = 0
        self.weight_reset = time.time() + 60
        
    async def acquire(self, weight: int = 1):
        """获取请求许可"""
        now = time.time()
        
        # 重置计数器
        if now >= self.weight_reset:
            self.weight_used = 0
            self.weight_reset = now + 60
        
        # 检查是否超限
        if self.weight_used + weight > self.weight_limit:
            sleep_time = self.weight_reset - now
            logger.warning(f"达到速率限制，等待{sleep_time:.1f}秒")
            await asyncio.sleep(sleep_time)
            return await self.acquire(weight)
        
        self.weight_used += weight


# 测试函数
async def test_binance_collector():
    """测试Binance采集器"""
    collector = BinanceCollector()
    await collector.initialize()
    
    try:
        # 测试REST API
        print("测试REST API...")
        ticker = await collector.get_ticker_24hr("BTCUSDT")
        print(f"BTCUSDT 24小时行情: {ticker}")
        
        depth = await collector.get_order_book("BTCUSDT", 10)
        print(f"BTCUSDT 深度数据: 买单{len(depth.get('bids', []))}个，卖单{len(depth.get('asks', []))}个")
        
        # 测试WebSocket
        print("\n测试WebSocket...")
        await collector.connect_ws()
        await collector.subscribe_ticker(["BTCUSDT", "ETHUSDT"])
        
        # 运行30秒接收数据
        await asyncio.sleep(30)
        
    finally:
        await collector.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_binance_collector())