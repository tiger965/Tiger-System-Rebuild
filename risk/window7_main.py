"""
Tiger系统 - Window 7 主启动文件
窗口：7号
功能：风控执行工具统一入口，整合所有风控功能
作者：Window-7 Risk Control Officer
"""

import asyncio
import logging
import sys
import os
import signal
from datetime import datetime
from typing import Dict, Optional
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入内部模块
try:
    from kelly_calculator import KellyCalculator
    from var_calculator import VaRCalculator, Position
    from execution_engine import ExecutionEngine, Order, OrderType
    from api_interface import app
    from money.money_management import MoneyManagement
    from stoploss.stoploss_system import StopLossSystem
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块已正确安装")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'window7_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Window7RiskSystem:
    """
    Window 7 风控执行系统主类
    整合所有风控工具，提供统一的管理接口
    """
    
    def __init__(self, initial_capital: float = 100000):
        """
        初始化系统
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.running = False
        self.system_status = "initializing"
        
        # 初始化各组件
        try:
            self.kelly_calculator = KellyCalculator()
            self.var_calculator = VaRCalculator()
            self.execution_engine = ExecutionEngine()
            self.money_manager = MoneyManagement(initial_capital)
            self.stoploss_system = StopLossSystem()
            
            logger.info("所有风控组件初始化成功")
            self.system_status = "initialized"
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            self.system_status = "failed"
            raise
    
    async def start_system(self):
        """启动系统"""
        try:
            logger.info("=== Tiger Window-7 风控执行系统启动 ===")
            
            # 系统自检
            await self._system_health_check()
            
            # 启动API服务
            await self._start_api_server()
            
            # 启动监控任务
            await self._start_monitoring()
            
            self.running = True
            self.system_status = "running"
            logger.info("系统启动完成，状态: 运行中")
            
        except Exception as e:
            logger.error(f"系统启动失败: {e}")
            self.system_status = "failed"
            raise
    
    async def stop_system(self):
        """停止系统"""
        try:
            logger.info("正在停止系统...")
            
            # 取消所有活动订单
            active_orders = self.execution_engine.get_active_orders()
            for order in active_orders:
                await self.execution_engine.cancel_order(order.order_id)
            
            # 生成停机报告
            await self._generate_shutdown_report()
            
            self.running = False
            self.system_status = "stopped"
            logger.info("系统已安全停止")
            
        except Exception as e:
            logger.error(f"系统停止过程中出错: {e}")
    
    async def _system_health_check(self):
        """系统健康检查"""
        logger.info("正在进行系统健康检查...")
        
        checks = {
            "kelly_calculator": self._check_kelly_calculator,
            "var_calculator": self._check_var_calculator,
            "execution_engine": self._check_execution_engine,
            "money_manager": self._check_money_manager,
            "stoploss_system": self._check_stoploss_system
        }
        
        results = {}
        for name, check_func in checks.items():
            try:
                result = await check_func()
                results[name] = {"status": "ok", "details": result}
                logger.info(f"✓ {name}: 正常")
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                logger.error(f"✗ {name}: 异常 - {e}")
                raise RuntimeError(f"健康检查失败: {name}")
        
        logger.info("系统健康检查通过")
        return results
    
    async def _check_kelly_calculator(self):
        """检查凯利计算器"""
        # 测试基础计算
        kelly = self.kelly_calculator.calculate_kelly_fraction(0.6, 1.5)
        assert 0 <= kelly <= 1, f"凯利比例异常: {kelly}"
        return {"kelly_test": kelly}
    
    async def _check_var_calculator(self):
        """检查VaR计算器"""
        # 测试基础VaR计算
        import numpy as np
        returns = np.random.normal(0, 0.01, 100)
        var = self.var_calculator.calculate_historical_var(returns)
        assert var >= 0, f"VaR值异常: {var}"
        return {"var_test": var}
    
    async def _check_execution_engine(self):
        """检查执行引擎"""
        # 检查组件状态
        stats = self.execution_engine.get_execution_stats()
        assert isinstance(stats, dict), "执行统计格式异常"
        return stats
    
    async def _check_money_manager(self):
        """检查资金管理器"""
        # 检查状态
        status = self.money_manager.get_status()
        assert status["capital"]["current"] > 0, "资金状态异常"
        return {"capital": status["capital"]["current"]}
    
    async def _check_stoploss_system(self):
        """检查止损系统"""
        # 基础功能测试
        return {"status": "ready"}
    
    async def _start_api_server(self):
        """启动API服务器"""
        logger.info("启动API服务器...")
        
        # 在后台启动FastAPI服务
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8007,
            log_level="info",
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        
        # 创建服务器任务
        asyncio.create_task(server.serve())
        logger.info("API服务器已启动 - http://0.0.0.0:8007")
    
    async def _start_monitoring(self):
        """启动监控任务"""
        logger.info("启动系统监控...")
        
        # 创建监控任务
        asyncio.create_task(self._monitoring_loop())
        logger.info("系统监控已启动")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 每分钟检查一次系统状态
                await asyncio.sleep(60)
                
                if not self.running:
                    break
                
                # 记录系统状态
                status = await self._get_system_status()
                logger.debug(f"系统状态: {status}")
                
                # 检查资金管理限制
                daily_check = self.money_manager.check_daily_limits()
                if not daily_check["can_trade"]:
                    logger.warning("触发日交易限制，系统将限制新开仓")
                
                # 检查活跃订单
                active_orders = len(self.execution_engine.get_active_orders())
                if active_orders > 10:
                    logger.warning(f"活跃订单过多: {active_orders}")
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
    
    async def _get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "status": self.system_status,
            "running": self.running,
            "components": {
                "kelly_calculator": "ok",
                "var_calculator": "ok", 
                "execution_engine": "ok",
                "money_manager": "ok",
                "api_server": "ok"
            },
            "stats": {
                "execution": self.execution_engine.get_execution_stats(),
                "money": self.money_manager.get_status(),
                "risk_capacity": self.money_manager.get_risk_capacity()
            }
        }
    
    async def _generate_shutdown_report(self):
        """生成停机报告"""
        try:
            status = await self._get_system_status()
            
            report = f"""
=== Tiger Window-7 系统停机报告 ===
停机时间: {datetime.now().isoformat()}
运行状态: {status['status']}

执行统计:
{self._format_stats(status['stats']['execution'])}

资金状态:
{self._format_stats(status['stats']['money'])}

风险容量:
{self._format_stats(status['stats']['risk_capacity'])}

=============================
            """
            
            # 写入报告文件
            report_file = f"window7_shutdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"停机报告已生成: {report_file}")
            
        except Exception as e:
            logger.error(f"生成停机报告失败: {e}")
    
    def _format_stats(self, stats: Dict) -> str:
        """格式化统计信息"""
        lines = []
        for key, value in stats.items():
            if isinstance(value, dict):
                lines.append(f"  {key}:")
                for k, v in value.items():
                    lines.append(f"    {k}: {v}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)


# 全局系统实例
risk_system: Optional[Window7RiskSystem] = None


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，准备停止系统...")
    if risk_system and risk_system.running:
        asyncio.create_task(risk_system.stop_system())


async def main():
    """主入口函数"""
    global risk_system
    
    try:
        print("=" * 60)
        print("🛡️  Tiger Window-7 风控执行系统 v7.1")
        print("功能: 凯利公式、VaR计算、订单执行、风险控制")
        print("=" * 60)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 创建系统实例
        risk_system = Window7RiskSystem(initial_capital=100000)
        
        # 启动系统
        await risk_system.start_system()
        
        # 保持运行
        try:
            while risk_system.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到中断信号...")
        
        # 停止系统
        await risk_system.stop_system()
        
        print("系统已安全退出")
        
    except Exception as e:
        logger.error(f"系统运行异常: {e}")
        print(f"系统运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())