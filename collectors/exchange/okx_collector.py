"""
OKX交易所数据采集器
实现REST API和WebSocket数据采集
"""
import asyncio
import json
import time
import hmac
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import aiohttp
import websockets
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class OKXConfig:
    """OKX配置"""
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""
    rest_url: str = "https://www.okx.com"
    ws_public: str = "wss://ws.okx.com:8443/ws/v5/public"
    ws_private: str = "wss://ws.okx.com:8443/ws/v5/private"
    demo_mode: bool = True  # 模拟模式，用于开发测试

class OKXCollector:
    """OKX数据采集器"""
    
    def __init__(self, config: OKXConfig = None):
        self.config = config or OKXConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_public_conn = None
        self.ws_private_conn = None
        self.running = False
        self.subscriptions = set()
        self.rate_limiter = RateLimiter(max_requests=20, window=2)  # 20次/2秒
        
    async def initialize(self):
        """初始化采集器"""
        self.session = aiohttp.ClientSession()
        logger.info("OKX采集器初始化完成")
        
    async def close(self):
        """关闭采集器"""
        self.running = False
        if self.ws_public_conn:
            await self.ws_public_conn.close()
        if self.ws_private_conn:
            await self.ws_private_conn.close()
        if self.session:
            await self.session.close()
        logger.info("OKX采集器已关闭")
    
    # REST API 方法
    async def get_ticker(self, inst_id: str) -> Dict:
        """获取单个产品行情信息"""
        endpoint = "/api/v5/market/ticker"
        params = {"instId": inst_id}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_tickers(self, inst_type: str = "SPOT") -> List[Dict]:
        """获取所有产品行情信息"""
        endpoint = "/api/v5/market/tickers"
        params = {"instType": inst_type}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_order_book(self, inst_id: str, sz: int = 20) -> Dict:
        """获取深度数据"""
        endpoint = "/api/v5/market/books"
        params = {"instId": inst_id, "sz": sz}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_trades(self, inst_id: str, limit: int = 100) -> List[Dict]:
        """获取成交数据"""
        endpoint = "/api/v5/market/trades"
        params = {"instId": inst_id, "limit": limit}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_funding_rate(self, inst_id: str) -> Dict:
        """获取资金费率"""
        endpoint = "/api/v5/public/funding-rate"
        params = {"instId": inst_id}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_open_interest(self, inst_type: str = "SWAP") -> List[Dict]:
        """获取持仓量"""
        endpoint = "/api/v5/public/open-interest"
        params = {"instType": inst_type}
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_large_trades(self, inst_id: str) -> List[Dict]:
        """获取大单成交数据"""
        endpoint = "/api/v5/market/block-trades"
        params = {"instId": inst_id}
        return await self._make_request("GET", endpoint, params=params)
    
    # WebSocket 方法
    async def connect_public_ws(self):
        """连接公共WebSocket"""
        try:
            self.ws_public_conn = await websockets.connect(self.config.ws_public)
            self.running = True
            logger.info("已连接到OKX公共WebSocket")
            
            # 启动消息处理循环
            asyncio.create_task(self._handle_ws_messages(self.ws_public_conn, "public"))
            
            # 发送ping保持连接
            asyncio.create_task(self._keep_alive(self.ws_public_conn))
            
        except Exception as e:
            logger.error(f"连接OKX公共WebSocket失败: {e}")
            await self._reconnect_ws("public")
    
    async def subscribe_ticker(self, inst_ids: List[str]):
        """订阅行情数据"""
        args = [{"channel": "tickers", "instId": inst_id} for inst_id in inst_ids]
        await self._subscribe(args)
    
    async def subscribe_trades(self, inst_ids: List[str]):
        """订阅成交数据"""
        args = [{"channel": "trades", "instId": inst_id} for inst_id in inst_ids]
        await self._subscribe(args)
    
    async def subscribe_books(self, inst_ids: List[str], depth: str = "books"):
        """订阅深度数据"""
        args = [{"channel": depth, "instId": inst_id} for inst_id in inst_ids]
        await self._subscribe(args)
    
    async def subscribe_funding_rate(self, inst_ids: List[str]):
        """订阅资金费率"""
        args = [{"channel": "funding-rate", "instId": inst_id} for inst_id in inst_ids]
        await self._subscribe(args)
    
    # 内部方法
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, body: Dict = None) -> Any:
        """发送REST请求"""
        await self.rate_limiter.acquire()
        
        url = f"{self.config.rest_url}{endpoint}"
        
        if self.config.demo_mode:
            # 模拟模式返回模拟数据
            return self._get_mock_data(endpoint, params)
        
        try:
            if method == "GET":
                async with self.session.get(url, params=params) as response:
                    data = await response.json()
            else:
                headers = self._get_auth_headers(method, endpoint, body)
                async with self.session.request(method, url, json=body, headers=headers) as response:
                    data = await response.json()
            
            if data.get("code") != "0":
                raise Exception(f"OKX API错误: {data.get('msg')}")
                
            return data.get("data", [])
            
        except Exception as e:
            logger.error(f"请求失败 {url}: {e}")
            raise
    
    def _get_mock_data(self, endpoint: str, params: Dict) -> Any:
        """获取模拟数据"""
        mock_data = {
            "/api/v5/market/ticker": {
                "instId": params.get("instId", "BTC-USDT"),
                "last": "67500.5",
                "lastSz": "0.12",
                "askPx": "67501.0",
                "askSz": "1.5",
                "bidPx": "67500.0",
                "bidSz": "2.0",
                "open24h": "66800.0",
                "high24h": "68000.0",
                "low24h": "66500.0",
                "vol24h": "12345.67",
                "ts": str(int(time.time() * 1000))
            },
            "/api/v5/market/books": {
                "asks": [["67501.0", "1.5", "0", "2"], ["67502.0", "2.0", "0", "3"]],
                "bids": [["67500.0", "2.0", "0", "2"], ["67499.0", "1.8", "0", "1"]],
                "ts": str(int(time.time() * 1000))
            },
            "/api/v5/public/funding-rate": {
                "instId": params.get("instId", "BTC-USDT-SWAP"),
                "fundingRate": "0.0001",
                "nextFundingRate": "0.00012",
                "fundingTime": str(int(time.time() * 1000) + 28800000)
            }
        }
        return mock_data.get(endpoint, {})
    
    async def _subscribe(self, args: List[Dict]):
        """发送订阅消息"""
        if not self.ws_public_conn:
            await self.connect_public_ws()
        
        msg = {
            "op": "subscribe",
            "args": args
        }
        
        await self.ws_public_conn.send(json.dumps(msg))
        self.subscriptions.update(str(arg) for arg in args)
        logger.info(f"已订阅: {args}")
    
    async def _handle_ws_messages(self, ws, ws_type: str):
        """处理WebSocket消息"""
        while self.running:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(msg)
                
                if "event" in data:
                    if data["event"] == "subscribe":
                        logger.info(f"订阅成功: {data.get('arg')}")
                    elif data["event"] == "error":
                        logger.error(f"订阅错误: {data}")
                else:
                    # 处理数据推送
                    await self._process_ws_data(data)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"处理{ws_type} WebSocket消息失败: {e}")
                await self._reconnect_ws(ws_type)
                break
    
    async def _process_ws_data(self, data: Dict):
        """处理WebSocket推送数据"""
        if "arg" in data and "data" in data:
            channel = data["arg"].get("channel")
            inst_id = data["arg"].get("instId")
            
            for item in data["data"]:
                # 这里可以将数据发送到消息队列或直接存储到数据库
                processed_data = {
                    "source": "OKX",
                    "channel": channel,
                    "inst_id": inst_id,
                    "data": item,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # TODO: 发送到消息队列
                logger.debug(f"收到{channel}数据: {inst_id}")
    
    async def _keep_alive(self, ws):
        """保持WebSocket连接"""
        while self.running:
            try:
                await asyncio.sleep(25)
                await ws.send("ping")
            except Exception as e:
                logger.error(f"发送ping失败: {e}")
                break
    
    async def _reconnect_ws(self, ws_type: str):
        """重连WebSocket"""
        logger.info(f"正在重连{ws_type} WebSocket...")
        await asyncio.sleep(5)
        
        if ws_type == "public":
            await self.connect_public_ws()
            # 重新订阅
            for sub in self.subscriptions:
                await self._subscribe([eval(sub)])

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int, window: float):
        self.max_requests = max_requests
        self.window = window
        self.requests = []
    
    async def acquire(self):
        """获取请求许可"""
        now = time.time()
        # 清理过期的请求记录
        self.requests = [t for t in self.requests if now - t < self.window]
        
        if len(self.requests) >= self.max_requests:
            # 需要等待
            sleep_time = self.window - (now - self.requests[0])
            await asyncio.sleep(sleep_time)
            return await self.acquire()
        
        self.requests.append(now)


# 测试函数
async def test_okx_collector():
    """测试OKX采集器"""
    collector = OKXCollector()
    await collector.initialize()
    
    try:
        # 测试REST API
        print("测试REST API...")
        ticker = await collector.get_ticker("BTC-USDT")
        print(f"BTC-USDT行情: {ticker}")
        
        # 测试WebSocket
        print("\n测试WebSocket...")
        await collector.connect_public_ws()
        await collector.subscribe_ticker(["BTC-USDT", "ETH-USDT"])
        
        # 运行30秒接收数据
        await asyncio.sleep(30)
        
    finally:
        await collector.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_okx_collector())