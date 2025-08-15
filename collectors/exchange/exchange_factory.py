"""
Window 2 - 交易所工厂类
统一管理所有交易所功能
"""

import time
from typing import Dict, List, Optional
try:
    from .ranking_monitor import RankingMonitor
    from .realtime_collector import RealtimeDataCollector
    from .account_manager import AccountManager
    from .websocket_streamer import WebSocketStreamer
except ImportError:
    from ranking_monitor import RankingMonitor
    from realtime_collector import RealtimeDataCollector
    from account_manager import AccountManager
    from websocket_streamer import WebSocketStreamer
from loguru import logger


class ExchangeFactory:
    """交易所工厂类 - Window 2的主入口"""
    
    def __init__(self):
        """初始化所有组件"""
        self.ranking_monitor = RankingMonitor()
        self.realtime_collector = RealtimeDataCollector()
        self.account_manager = AccountManager()
        self.websocket_streamer = WebSocketStreamer()
        
        logger.info("Window 2 - 交易所工具工厂初始化完成")
        
    # ==================== 榜单监控接口 ====================
    
    def get_hot_ranking(self, exchange: str, top: int = 15) -> List[Dict]:
        """获取热门榜 - Window 6调用"""
        return self.ranking_monitor.get_hot_ranking(exchange, top)
        
    def get_gainers_ranking(self, exchange: str, top: int = 5) -> List[Dict]:
        """获取涨幅榜 - Window 6调用"""
        return self.ranking_monitor.get_gainers_ranking(exchange, top)
        
    def get_losers_ranking(self, exchange: str, top: int = 5) -> List[Dict]:
        """获取跌幅榜 - Window 6调用"""
        return self.ranking_monitor.get_losers_ranking(exchange, top)
        
    def get_new_listings(self, exchange: str, top: int = 3) -> List[Dict]:
        """获取新币榜 - Window 6调用"""
        return self.ranking_monitor.get_new_listings(exchange, top)
        
    def get_volume_surge(self, threshold: float = 2.0, timeframe: str = '5m') -> List[Dict]:
        """获取成交量异动 - Window 6调用"""
        return self.ranking_monitor.get_volume_surge(threshold, timeframe)
        
    # ==================== 实时数据接口 ====================
    
    def get_realtime_price(self, symbol: str, exchange: str) -> Dict:
        """获取实时价格 - Window 6调用"""
        return self.realtime_collector.get_realtime_price(symbol, exchange)
        
    def get_orderbook_depth(self, symbol: str, exchange: str, depth: int = 10) -> Dict:
        """获取订单簿深度 - Window 6调用"""
        return self.realtime_collector.get_orderbook_depth(symbol, exchange, depth)
        
    def get_recent_trades(self, symbol: str, exchange: str, limit: int = 100) -> List[Dict]:
        """获取最近成交 - Window 6调用"""
        return self.realtime_collector.get_recent_trades(symbol, exchange, limit)
        
    def get_volume_change(self, symbol: str, exchange: str, minutes: int = 5) -> Dict:
        """获取成交量变化 - Window 6调用"""
        return self.realtime_collector.get_volume_change(symbol, exchange, minutes)
        
    def get_multiple_prices(self, symbols: List[str], exchange: str) -> Dict[str, Dict]:
        """批量获取价格 - Window 6调用"""
        return self.realtime_collector.get_multiple_prices(symbols, exchange)
        
    # ==================== 账户管理接口 ====================
    
    def get_okx_account(self) -> Dict:
        """获取OKX账户信息 - Window 6调用"""
        return self.account_manager.get_okx_account()
        
    def get_binance_account(self) -> Dict:
        """获取Binance账户信息 - Window 6调用"""
        return self.account_manager.get_binance_account()
        
    def get_positions(self, exchange: str) -> List[Dict]:
        """获取持仓信息 - Window 6调用"""
        return self.account_manager.get_positions(exchange)
        
    def get_account_summary(self, exchange: str) -> Dict:
        """获取账户概要 - Window 6调用"""
        return self.account_manager.get_account_summary(exchange)
        
    # ==================== WebSocket接口 ====================
    
    async def start_price_stream(self, symbols: List[str], exchange: str = 'binance', callback=None):
        """启动价格流 - Window 6调用"""
        return await self.websocket_streamer.subscribe_price_stream(symbols, exchange, callback)
        
    async def start_trade_stream(self, symbols: List[str], exchange: str = 'binance', callback=None):
        """启动成交流 - Window 6调用"""
        return await self.websocket_streamer.subscribe_trade_stream(symbols, exchange, callback)
        
    def stop_all_streams(self):
        """停止所有流 - Window 6调用"""
        self.websocket_streamer.stop_streaming()
        
    # ==================== Window 6专用命令处理 ====================
    
    def process_window6_command(self, command: Dict) -> Dict:
        """
        处理Window 6发来的命令
        
        Args:
            command: {
                "window": 2,
                "function": "get_hot_ranking",
                "params": {"exchange": "binance", "top": 15}
            }
            
        Returns:
            {
                "status": "success",
                "data": [...],
                "timestamp": 1234567890
            }
        """
        try:
            function_name = command.get('function')
            params = command.get('params', {})
            
            # 路由到对应的函数
            if hasattr(self, function_name):
                func = getattr(self, function_name)
                result = func(**params)
                
                return {
                    "status": "success", 
                    "data": result,
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown function: {function_name}",
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            logger.error(f"处理Window 6命令失败: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": int(time.time() * 1000)
            }
            
    # ==================== 批量扫描接口 ====================
    
    def scan_market(self, config: Dict) -> Dict:
        """
        市场扫描 - Window 6主动扫描时调用
        
        Args:
            config: {
                "get_hot_ranking": {"exchange": "binance", "top": 15},
                "get_gainers": {"exchange": "okx", "top": 5},
                "get_new_listings": {"exchange": "binance", "top": 3}
            }
            
        Returns:
            {
                "hot_ranking": [...],
                "gainers": [...],
                "new_listings": [...],
                "timestamp": 1234567890
            }
        """
        import time
        result = {}
        
        try:
            # 获取热门榜
            if 'get_hot_ranking' in config:
                params = config['get_hot_ranking']
                result['hot_ranking'] = self.get_hot_ranking(**params)
                
            # 获取涨幅榜
            if 'get_gainers' in config:
                params = config['get_gainers']
                result['gainers'] = self.get_gainers_ranking(**params)
                
            # 获取跌幅榜
            if 'get_losers' in config:
                params = config['get_losers']
                result['losers'] = self.get_losers_ranking(**params)
                
            # 获取新币榜
            if 'get_new_listings' in config:
                params = config['get_new_listings']
                result['new_listings'] = self.get_new_listings(**params)
                
            result['timestamp'] = int(time.time() * 1000)
            
            logger.info(f"市场扫描完成，获取{len(result)-1}项数据")
            return result
            
        except Exception as e:
            logger.error(f"市场扫描失败: {e}")
            return {"error": str(e), "timestamp": int(time.time() * 1000)}
            
    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict:
        """
        健康检查 - 检查所有组件状态
        
        Returns:
            {
                "status": "healthy",
                "components": {
                    "ranking_monitor": "ok",
                    "realtime_collector": "ok",
                    "account_manager": "ok", 
                    "websocket_streamer": "ok"
                },
                "timestamp": 1234567890
            }
        """
        import time
        
        components = {}
        overall_status = "healthy"
        
        try:
            # 检查榜单监控器
            if self.ranking_monitor and hasattr(self.ranking_monitor, 'okx_client'):
                components['ranking_monitor'] = "ok"
            else:
                components['ranking_monitor'] = "error"
                overall_status = "unhealthy"
                
            # 检查实时数据采集器  
            if self.realtime_collector and hasattr(self.realtime_collector, 'price_cache'):
                components['realtime_collector'] = "ok"
            else:
                components['realtime_collector'] = "error"
                overall_status = "unhealthy"
                
            # 检查账户管理器
            if self.account_manager and hasattr(self.account_manager, 'account_cache'):
                components['account_manager'] = "ok"
            else:
                components['account_manager'] = "error"
                overall_status = "unhealthy"
                
            # 检查WebSocket推送器
            if self.websocket_streamer and hasattr(self.websocket_streamer, 'subscribers'):
                components['websocket_streamer'] = "ok"
            else:
                components['websocket_streamer'] = "error"
                overall_status = "unhealthy"
                
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            overall_status = "unhealthy"
            components['error'] = str(e)
            
        return {
            "status": overall_status,
            "components": components,
            "timestamp": int(time.time() * 1000)
        }


# 全局单例
window2_exchange = ExchangeFactory()


# 测试代码
if __name__ == "__main__":
    import time
    
    print("=== Window 2 交易所工具测试 ===")
    
    exchange = ExchangeFactory()
    
    # 健康检查
    print("\\n--- 健康检查 ---")
    health = exchange.health_check()
    print(f"总体状态: {health['status']}")
    for component, status in health['components'].items():
        print(f"  {component}: {status}")
    
    # 测试批量扫描
    print("\\n--- 市场扫描测试 ---")
    scan_config = {
        "get_hot_ranking": {"exchange": "binance", "top": 3},
        "get_gainers": {"exchange": "binance", "top": 2}
    }
    
    try:
        scan_result = exchange.scan_market(scan_config)
        if 'hot_ranking' in scan_result:
            print(f"热门榜: {len(scan_result['hot_ranking'])}个币种")
        if 'gainers' in scan_result:  
            print(f"涨幅榜: {len(scan_result['gainers'])}个币种")
    except Exception as e:
        print(f"扫描测试失败: {e}")
    
    # 测试Window 6命令处理
    print("\\n--- Window 6命令处理测试 ---")
    test_command = {
        "window": 2,
        "function": "get_hot_ranking", 
        "params": {"exchange": "binance", "top": 2}
    }
    
    try:
        cmd_result = exchange.process_window6_command(test_command)
        print(f"命令处理结果: {cmd_result['status']}")
        if cmd_result['status'] == 'success' and cmd_result.get('data'):
            print(f"数据条数: {len(cmd_result['data'])}")
    except Exception as e:
        print(f"命令处理测试失败: {e}")
    
    print("\\n=== 测试完成 ===")