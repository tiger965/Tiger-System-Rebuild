"""
Window 3 - 数据采集工具主程序
纯工具属性，为Window 6提供全方位的数据收集服务
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import json

# 导入核心组件
from monitoring_activation_system import MonitoringActivationSystem
from data_chain_integrator import DataChainIntegrator
from api_interface import Window3API, handle_window6_request

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Window3-Main] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Window3System:
    """
    Window 3系统主控制器
    整合所有数据收集组件，提供统一的服务
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("Window 3 - 数据采集工具系统")
        logger.info("纯工具属性，为Window 6提供全方位数据服务")
        logger.info("=" * 60)
        
        # 初始化组件
        self.monitoring_system = MonitoringActivationSystem()
        self.data_integrator = DataChainIntegrator()
        self.api = Window3API()
        
        # 运行状态
        self.is_running = False
        self.tasks = []
        
        # 统计信息
        self.stats = {
            "start_time": None,
            "triggers_sent": 0,
            "data_collected": 0,
            "api_calls": 0,
            "errors": 0
        }

    async def start(self):
        """启动Window 3系统"""
        self.is_running = True
        self.stats["start_time"] = datetime.now()
        
        logger.info("🚀 启动Window 3数据采集系统...")
        
        # 创建所有任务
        self.tasks = [
            # 核心监控任务
            asyncio.create_task(self.monitoring_system.start_monitoring()),
            
            # 数据收集任务
            asyncio.create_task(self.collect_market_data()),
            asyncio.create_task(self.collect_chain_data()),
            asyncio.create_task(self.collect_social_data()),
            
            # API服务任务
            asyncio.create_task(self.run_api_server()),
            
            # 状态报告任务
            asyncio.create_task(self.report_status())
        ]
        
        # 等待所有任务
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("收到停止信号")
        except Exception as e:
            logger.error(f"系统错误: {e}")
            self.stats["errors"] += 1

    async def collect_market_data(self):
        """收集市场数据（每30秒）"""
        while self.is_running:
            try:
                # 获取市场总览
                overview = await self.api.get_market_overview()
                
                # 记录关键指标
                logger.info(f"📊 市场数据 - BTC: ${overview['btc_price']:,.0f}, "
                          f"恐慌贪婪: {overview['fear_greed_index']}, "
                          f"情绪: {overview['dominant_sentiment']}")
                
                self.stats["data_collected"] += 1
                
                # 检查是否需要触发警报
                if overview["risk_level"] in ["high", "low"]:
                    await self.send_risk_alert(overview)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"收集市场数据错误: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(30)

    async def collect_chain_data(self):
        """收集链上数据（每60秒）"""
        while self.is_running:
            try:
                # 收集BTC和ETH的链上数据
                btc_data = await self.api.fetch_all_chain_data("BTC")
                eth_data = await self.api.fetch_all_chain_data("ETH")
                
                # 发送给数据整合器
                chain_data = {"btc": btc_data, "eth": eth_data}
                self.data_integrator.receive_chain_data(chain_data)
                
                logger.info(f"⛓️ 链上数据已更新")
                self.stats["data_collected"] += 1
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"收集链上数据错误: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(60)

    async def collect_social_data(self):
        """收集社交数据（每120秒）"""
        while self.is_running:
            try:
                # 收集社交媒体数据
                social_data = await self.api.fetch_all_social_data("BTC")
                
                # 发送给数据整合器
                self.data_integrator.receive_social_data(social_data)
                
                if "fear_greed" in social_data:
                    fg_value = social_data["fear_greed"]["value"]
                    logger.info(f"💬 社交数据 - 恐慌贪婪指数: {fg_value}")
                
                self.stats["data_collected"] += 1
                
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"收集社交数据错误: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(120)

    async def run_api_server(self):
        """运行API服务器，响应Window 6的请求"""
        # 这里应该启动一个HTTP服务器
        # 暂时使用模拟的消息处理
        while self.is_running:
            try:
                # 检查是否有来自Window 6的请求
                # 实际应该从消息队列或HTTP请求获取
                await asyncio.sleep(5)
                
                # 模拟处理请求
                self.stats["api_calls"] += 1
                
            except Exception as e:
                logger.error(f"API服务错误: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)

    async def send_risk_alert(self, overview: Dict):
        """发送风险警报"""
        alert = {
            "source": "window3",
            "type": "risk_alert",
            "level": 2 if overview["risk_level"] in ["high", "low"] else 1,
            "data": overview,
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存警报
        import os
        os.makedirs("/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/alerts", exist_ok=True)
        
        filename = f"risk_alert_{int(datetime.now().timestamp())}.json"
        filepath = f"/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/alerts/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(alert, f, ensure_ascii=False, indent=2)
        
        logger.warning(f"⚠️ 风险警报已生成: {overview['risk_level']}")
        self.stats["triggers_sent"] += 1

    async def report_status(self):
        """定期报告系统状态（每5分钟）"""
        while self.is_running:
            await asyncio.sleep(300)  # 5分钟
            
            if self.stats["start_time"]:
                uptime = datetime.now() - self.stats["start_time"]
                hours = uptime.total_seconds() / 3600
                
                logger.info("=" * 50)
                logger.info("📈 Window 3 系统状态报告")
                logger.info(f"运行时间: {hours:.1f} 小时")
                logger.info(f"触发信号: {self.stats['triggers_sent']} 个")
                logger.info(f"数据收集: {self.stats['data_collected']} 次")
                logger.info(f"API调用: {self.stats['api_calls']} 次")
                logger.info(f"错误次数: {self.stats['errors']} 次")
                logger.info("=" * 50)

    async def stop(self):
        """停止Window 3系统"""
        logger.info("⏹️ 正在停止Window 3系统...")
        self.is_running = False
        
        # 停止监控系统
        await self.monitoring_system.stop_monitoring()
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # 最终统计
        if self.stats["start_time"]:
            uptime = datetime.now() - self.stats["start_time"]
            logger.info(f"✅ Window 3系统已停止，运行时长: {uptime}")

    def handle_signal(self, sig, frame):
        """处理系统信号"""
        logger.info(f"\n收到信号 {sig}")
        asyncio.create_task(self.stop())
        sys.exit(0)


async def main():
    """主函数"""
    system = Window3System()
    
    # 设置信号处理
    signal.signal(signal.SIGINT, system.handle_signal)
    signal.signal(signal.SIGTERM, system.handle_signal)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("\n收到键盘中断")
        await system.stop()
    except Exception as e:
        logger.error(f"系统异常: {e}")
        await system.stop()


def test_mode():
    """测试模式 - 快速验证所有功能"""
    async def run_test():
        logger.info("=" * 60)
        logger.info("Window 3 功能测试")
        logger.info("=" * 60)
        
        api = Window3API()
        
        # 测试1: 获取市场总览
        logger.info("\n测试1: 获取市场总览")
        overview = await api.get_market_overview()
        logger.info(f"BTC价格: ${overview['btc_price']:,.0f}")
        logger.info(f"恐慌贪婪: {overview['fear_greed_index']}")
        logger.info(f"风险等级: {overview['risk_level']}")
        
        # 测试2: 追踪巨鲸
        logger.info("\n测试2: 追踪巨鲸转账")
        whales = await api.track_whale_transfers(
            min_amount_usd=100000,
            chains=["BTC"]
        )
        logger.info(f"发现巨鲸转账: {whales['total_count']} 笔")
        logger.info(f"总金额: ${whales['total_volume_usd']:,.0f}")
        
        # 测试3: 生成情报包
        logger.info("\n测试3: 生成综合情报包")
        package = await api.get_intelligence_package(
            symbol="BTC",
            include_window2_data=True,
            analysis_depth="deep"
        )
        logger.info(f"情报包ID: {package.get('package_id', 'N/A')}")
        logger.info(f"优先级: {package.get('priority', 'normal')}")
        logger.info(f"摘要: {package.get('summary', 'N/A')}")
        
        logger.info("\n✅ 所有测试完成")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 测试模式
        test_mode()
    else:
        # 正常运行
        asyncio.run(main())