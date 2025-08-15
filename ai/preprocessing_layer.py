"""
24/7运行的预处理层 - Window 6核心
永不停止，监控市场，触发AI决策
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/ai/logs/preprocessing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleContextManager:
    """简单的上下文管理器（避免复杂依赖）"""
    
    def __init__(self):
        self.context_data = {}
    
    def get_context(self):
        return self.context_data
    
    def update_context(self, data):
        self.context_data.update(data)


class PreprocessingLayer:
    """24/7运行的预处理层"""
    
    def __init__(self):
        """初始化预处理层"""
        logger.info("初始化预处理层...")
        
        # 延迟导入避免循环依赖
        from monitoring_activation_system import MonitoringActivationSystem
        from window_commander import WindowCommander
        from command_interface import CommandInterface
        
        # 核心组件 - 创建一个简单的上下文管理器
        self.context_manager = SimpleContextManager()
        self.monitoring_system = MonitoringActivationSystem()
        self.window_commander = WindowCommander()
        self.command_interface = CommandInterface()
        self.claude_client = None  # 按需初始化
        
        # 运行状态
        self.is_running = False
        self.last_activation_time = None
        self.activation_count = 0
        self.error_count = 0
        
        # 监控间隔
        self.monitoring_interval = 5  # 5秒检查一次
        self.max_errors = 10  # 最大错误次数
        
        # 定时激活时间（PST）
        self.scheduled_times = [
            "00:00",  # 日结分析
            "06:00",  # 美股开盘前
            "08:30",  # OKX交割前
            "18:00"   # 亚洲市场活跃
        ]
        
        logger.info("预处理层初始化完成")
    
    async def run_forever(self):
        """24/7永久运行"""
        logger.info("预处理层开始24/7运行...")
        self.is_running = True
        
        while self.is_running:
            try:
                # 1. 检查触发条件
                await self._check_triggers()
                
                # 2. 检查定时激活
                await self._check_scheduled_activation()
                
                # 3. 记录健康状态
                self._log_health_status()
                
                # 4. 休眠
                await asyncio.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                logger.info("收到停止信号，正在优雅关闭...")
                self.is_running = False
                break
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"预处理层运行错误: {e}", exc_info=True)
                
                if self.error_count >= self.max_errors:
                    logger.critical(f"错误次数达到上限({self.max_errors})，停止运行")
                    self.is_running = False
                    break
                
                # 错误后等待更长时间
                await asyncio.sleep(30)
    
    async def _check_triggers(self):
        """检查三级触发条件"""
        try:
            # 获取市场数据
            market_data = await self._get_market_data()
            
            # 检查触发级别
            trigger_level = self.monitoring_system.check_trigger_level(market_data)
            
            if trigger_level > 0:
                logger.info(f"检测到{trigger_level}级触发条件")
                
                # 根据级别决定是否激活AI
                if trigger_level == 1:
                    # 一级触发：增强监控
                    await self._enhance_monitoring()
                    
                elif trigger_level == 2:
                    # 二级触发：激活AI分析
                    await self._activate_ai_layer("二级触发", market_data)
                    
                elif trigger_level == 3:
                    # 三级触发：紧急响应
                    await self._emergency_response(market_data)
                    
        except Exception as e:
            logger.error(f"检查触发条件失败: {e}")
    
    async def _check_scheduled_activation(self):
        """检查定时激活"""
        try:
            current_time = datetime.now()
            current_time_str = current_time.strftime("%H:%M")
            
            # 检查是否到达定时激活时间
            if current_time_str in self.scheduled_times:
                # 确保每个时间点只激活一次
                if not self.last_activation_time or \
                   (current_time - self.last_activation_time) > timedelta(minutes=1):
                    
                    logger.info(f"定时激活: {current_time_str}")
                    market_data = await self._get_market_data()
                    await self._activate_ai_layer(f"定时激活({current_time_str})", market_data)
                    
        except Exception as e:
            logger.error(f"检查定时激活失败: {e}")
    
    async def _get_market_data(self) -> Dict:
        """获取市场数据"""
        try:
            # 调用Window 2获取市场数据
            command = {
                "window": 2,
                "function": "get_hot_ranking",
                "params": {"exchange": "binance", "top": 15}
            }
            
            hot_coins = await self.command_interface.execute_command(command)
            
            # 获取主要币种价格
            btc_command = {
                "window": 2,
                "function": "get_realtime_price",
                "params": {"symbol": "BTCUSDT", "exchange": "binance"}
            }
            btc_price = await self.command_interface.execute_command(btc_command)
            
            return {
                "hot_coins": hot_coins,
                "btc_price": btc_price,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {}
    
    async def _enhance_monitoring(self):
        """增强监控（一级触发）"""
        logger.info("进入增强监控模式")
        
        # 缩短监控间隔
        self.monitoring_interval = 2
        
        # 获取更多数据
        commands = [
            {
                "window": 3,
                "function": "crawl_twitter",
                "params": {"keyword": "BTC", "time_range_minutes": 30}
            },
            {
                "window": 3,
                "function": "track_whale_transfers",
                "params": {"min_amount_usd": 1000000, "chains": ["ETH", "BSC"], "direction": "all"}
            }
        ]
        
        for cmd in commands:
            try:
                result = await self.command_interface.execute_command(cmd)
                logger.info(f"增强监控数据: {cmd['function']} - {len(result) if result else 0}条")
            except Exception as e:
                logger.error(f"增强监控失败: {e}")
    
    async def _activate_ai_layer(self, reason: str, market_data: Dict):
        """激活AI决策层"""
        logger.info(f"激活AI决策层 - 原因: {reason}")
        
        try:
            # 准备上下文
            context = await self._prepare_context(market_data)
            
            # 模拟AI决策（避免Claude客户端依赖）
            decision = self._simulate_ai_decision(context, reason)
            
            # 执行决策
            await self._execute_decision(decision)
            
            # 记录激活
            self.last_activation_time = datetime.now()
            self.activation_count += 1
            
            logger.info(f"AI决策完成 - 第{self.activation_count}次激活")
            
        except Exception as e:
            logger.error(f"激活AI层失败: {e}", exc_info=True)
    
    def _simulate_ai_decision(self, context: Dict, reason: str) -> Dict:
        """模拟AI决策（测试用）"""
        # 简单的决策逻辑
        market_data = context.get("market_data", {})
        btc_price = market_data.get("btc_price", {}).get("price", 0)
        
        if "紧急" in reason or "三级" in reason:
            action = "观望"
            confidence = 0.9
        elif btc_price > 68000:
            action = "sell"
            confidence = 0.7
        elif btc_price < 66000:
            action = "buy"
            confidence = 0.7
        else:
            action = "观望"
            confidence = 0.5
            
        return {
            "action": action,
            "symbol": "BTCUSDT",
            "confidence": confidence,
            "risk_reward_ratio": 2.0,
            "order_type": "market",
            "reasoning": f"基于{reason}的决策分析",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _emergency_response(self, market_data: Dict):
        """紧急响应（三级触发）"""
        logger.critical("进入紧急响应模式！")
        
        # 立即激活AI
        await self._activate_ai_layer("三级紧急触发", market_data)
        
        # 发送紧急通知
        notification_command = {
            "window": 8,
            "function": "send_emergency_alert",
            "params": {
                "level": "critical",
                "message": "检测到三级市场异动，已激活紧急响应",
                "data": market_data
            }
        }
        
        try:
            await self.command_interface.execute_command(notification_command)
        except Exception as e:
            logger.error(f"发送紧急通知失败: {e}")
    
    async def _prepare_context(self, market_data: Dict) -> Dict:
        """准备AI决策上下文"""
        try:
            # 获取账户状态
            account_command = {
                "window": 1,
                "function": "get_account_cache",
                "params": {"user_id": "default"}
            }
            account_status = await self.command_interface.execute_command(account_command)
            
            return {
                "market_data": market_data,
                "account_status": account_status,
                "activation_time": datetime.now().isoformat(),
                "activation_count": self.activation_count
            }
            
        except Exception as e:
            logger.error(f"准备上下文失败: {e}")
            return {"error": str(e)}
    
    async def _execute_decision(self, decision: Dict):
        """执行AI决策"""
        if not decision or decision.get("action") == "观望":
            logger.info("AI决策: 观望，不执行交易")
            return
        
        try:
            # 风控检查
            risk_command = {
                "window": 7,
                "function": "calculate_kelly_position",
                "params": {
                    "win_probability": decision.get("confidence", 0.5),
                    "odds": decision.get("risk_reward_ratio", 2),
                    "max_risk": 0.02,
                    "account_balance": 100000
                }
            }
            position_size = await self.command_interface.execute_command(risk_command)
            
            # 记录决策
            record_command = {
                "window": 1,
                "function": "record_decision",
                "params": {"decision_data": decision}
            }
            await self.command_interface.execute_command(record_command)
            
            logger.info(f"决策已记录: {decision['action']}")
            
        except Exception as e:
            logger.error(f"执行决策失败: {e}")
    
    def _log_health_status(self):
        """记录健康状态"""
        if self.activation_count % 100 == 0:  # 每100次循环记录一次
            status = {
                "运行时间": time.time(),
                "激活次数": self.activation_count,
                "错误次数": self.error_count,
                "最后激活": self.last_activation_time.isoformat() if self.last_activation_time else "未激活",
                "监控间隔": self.monitoring_interval
            }
            logger.info(f"健康状态: {json.dumps(status, ensure_ascii=False)}")
    
    async def stop(self):
        """停止运行"""
        logger.info("正在停止预处理层...")
        self.is_running = False
        logger.info("预处理层已停止")


async def main():
    """主函数"""
    # 确保日志目录存在
    os.makedirs('/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/ai/logs', exist_ok=True)
    
    # 创建并运行预处理层
    preprocessing = PreprocessingLayer()
    
    try:
        await preprocessing.run_forever()
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        await preprocessing.stop()


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())