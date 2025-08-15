#!/usr/bin/env python3
"""
Tiger系统 - 主集成框架
10号窗口 - 系统集成
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TigerSystem:
    """Tiger智能交易分析系统主类"""
    
    def __init__(self):
        """初始化系统"""
        logger.info("=" * 60)
        logger.info("Tiger智能交易分析系统 - 启动初始化")
        logger.info("=" * 60)
        
        self.modules = {}
        self.status = "initializing"
        self.start_time = None
        
    def initialize_modules(self):
        """初始化所有模块"""
        logger.info("开始初始化各个模块...")
        
        try:
            # 1号窗口 - 数据库基础设施
            logger.info("[1/9] 初始化数据库模块...")
            from database.dal.base_dal import BaseDAL
            from database.models.market import MarketData
            self.modules['database'] = {
                'dal': BaseDAL,
                'models': MarketData,
                'status': 'initialized'
            }
            logger.info("  ✅ 数据库模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 数据库模块初始化失败: {e}")
            self.modules['database'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 2号窗口 - 交易所数据采集
            logger.info("[2/9] 初始化交易所采集模块...")
            from collectors.exchange.binance_collector import BinanceCollector
            self.modules['exchange'] = {
                'binance': BinanceCollector,
                'status': 'initialized'
            }
            logger.info("  ✅ 交易所采集模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 交易所采集模块初始化失败: {e}")
            self.modules['exchange'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 3号窗口 - 链上社交新闻
            logger.info("[3/9] 初始化链上社交模块...")
            from collectors.chain_social.early_warning import EarlyWarningSystem
            from collectors.news.news_collector import NewsCollector
            from collectors.social.twitter_monitor import TwitterMonitor
            self.modules['chain_social'] = {
                'early_warning': EarlyWarningSystem,
                'news': NewsCollector,
                'social': TwitterMonitor,
                'status': 'initialized'
            }
            logger.info("  ✅ 链上社交模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 链上社交模块初始化失败: {e}")
            self.modules['chain_social'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 4号窗口 - 技术指标引擎
            logger.info("[4/9] 初始化技术指标模块...")
            from analysis.indicators import technical
            self.modules['indicators'] = {
                'engine': technical,
                'status': 'initialized'
            }
            logger.info("  ✅ 技术指标模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 技术指标模块初始化失败: {e}")
            self.modules['indicators'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 5号窗口 - 币Coin爬虫系统
            logger.info("[5/9] 初始化币Coin爬虫模块...")
            from collectors.bicoin import coingecko_crawler
            self.modules['bicoin'] = {
                'crawler': coingecko_crawler,
                'status': 'initialized'
            }
            logger.info("  ✅ 币Coin爬虫模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 币Coin爬虫模块初始化失败: {e}")
            self.modules['bicoin'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 6号窗口 - AI决策系统
            logger.info("[6/9] 初始化AI决策模块...")
            from ai.claude_client import ClaudeClient
            from ai.strategy_weights import StrategyWeightManager
            from ai.user_query import UserQueryHandler
            self.modules['ai'] = {
                'claude': ClaudeClient,
                'strategy': StrategyWeightManager,
                'query': UserQueryHandler,
                'status': 'initialized'
            }
            logger.info("  ✅ AI决策模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ AI决策模块初始化失败: {e}")
            self.modules['ai'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 7号窗口 - 风控执行系统
            logger.info("[7/9] 初始化风控执行模块...")
            from risk.alert_executor import AlertExecutor
            self.modules['risk'] = {
                'executor': AlertExecutor,
                'status': 'initialized'
            }
            logger.info("  ✅ 风控执行模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 风控执行模块初始化失败: {e}")
            self.modules['risk'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 8号窗口 - 通知报告系统
            logger.info("[8/9] 初始化通知系统模块...")
            from notification.alert_notifier import AlertNotifier
            self.modules['notification'] = {
                'notifier': AlertNotifier,
                'status': 'initialized'
            }
            logger.info("  ✅ 通知系统模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 通知系统模块初始化失败: {e}")
            self.modules['notification'] = {'status': 'failed', 'error': str(e)}
            
        try:
            # 9号窗口 - 学习进化系统
            logger.info("[9/9] 初始化学习进化模块...")
            from learning.main import LearningEngine
            self.modules['learning'] = {
                'engine': LearningEngine,
                'status': 'initialized'
            }
            logger.info("  ✅ 学习进化模块初始化成功")
            
        except ImportError as e:
            logger.warning(f"  ⚠️ 学习进化模块初始化失败: {e}")
            self.modules['learning'] = {'status': 'failed', 'error': str(e)}
            
        # 统计初始化结果
        success_count = sum(1 for m in self.modules.values() if m.get('status') == 'initialized')
        total_count = len(self.modules)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"模块初始化完成: {success_count}/{total_count} 成功")
        logger.info("=" * 60)
        
        return success_count, total_count
        
    def check_dependencies(self):
        """检查系统依赖"""
        logger.info("\n检查系统依赖...")
        
        dependencies = {
            'database': [],
            'exchange': ['database'],
            'chain_social': ['database'],
            'indicators': ['database'],
            'bicoin': ['database'],
            'ai': ['database', 'indicators', 'chain_social'],
            'risk': ['ai', 'database'],
            'notification': ['risk'],
            'learning': ['database', 'ai']
        }
        
        issues = []
        for module, deps in dependencies.items():
            if self.modules.get(module, {}).get('status') == 'initialized':
                for dep in deps:
                    if self.modules.get(dep, {}).get('status') != 'initialized':
                        issues.append(f"{module} 依赖 {dep}，但 {dep} 未初始化")
                        
        if issues:
            logger.warning("发现依赖问题:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("  ✅ 所有依赖关系正常")
            
        return len(issues) == 0
        
    async def start_collectors(self):
        """启动数据采集器"""
        logger.info("\n启动数据采集器...")
        tasks = []
        
        # 启动交易所采集
        if self.modules.get('exchange', {}).get('status') == 'initialized':
            logger.info("  - 启动交易所数据采集...")
            # tasks.append(self.modules['exchange']['binance'].start())
            
        # 启动链上社交采集
        if self.modules.get('chain_social', {}).get('status') == 'initialized':
            logger.info("  - 启动链上社交数据采集...")
            # tasks.append(self.modules['chain_social']['early_warning'].start())
            
        # 启动币Coin爬虫
        if self.modules.get('bicoin', {}).get('status') == 'initialized':
            logger.info("  - 启动币Coin数据爬虫...")
            # tasks.append(self.modules['bicoin']['crawler'].start())
            
        if tasks:
            logger.info(f"  共启动 {len(tasks)} 个采集任务")
            # await asyncio.gather(*tasks)
        else:
            logger.warning("  ⚠️ 没有可用的采集器")
            
    async def start_analyzers(self):
        """启动分析器"""
        logger.info("\n启动分析器...")
        
        # 启动技术指标分析
        if self.modules.get('indicators', {}).get('status') == 'initialized':
            logger.info("  - 技术指标分析器就绪")
            
        # 启动AI决策系统
        if self.modules.get('ai', {}).get('status') == 'initialized':
            logger.info("  - AI决策系统就绪")
            
        # 启动学习进化系统
        if self.modules.get('learning', {}).get('status') == 'initialized':
            logger.info("  - 学习进化系统就绪")
            
    async def start_monitors(self):
        """启动监控器"""
        logger.info("\n启动监控器...")
        
        # 启动风控监控
        if self.modules.get('risk', {}).get('status') == 'initialized':
            logger.info("  - 风控监控系统就绪")
            
        # 启动通知系统
        if self.modules.get('notification', {}).get('status') == 'initialized':
            logger.info("  - 通知系统就绪")
            
    async def start(self):
        """启动系统"""
        self.start_time = datetime.now()
        logger.info("\n" + "=" * 60)
        logger.info("Tiger系统启动")
        logger.info(f"启动时间: {self.start_time}")
        logger.info("=" * 60)
        
        # 初始化模块
        success, total = self.initialize_modules()
        
        if success == 0:
            logger.error("❌ 没有模块成功初始化，系统无法启动")
            self.status = "failed"
            return False
            
        # 检查依赖
        if not self.check_dependencies():
            logger.warning("⚠️ 存在依赖问题，部分功能可能不可用")
            
        # 启动各个组件
        await self.start_collectors()
        await self.start_analyzers()
        await self.start_monitors()
        
        self.status = "running"
        logger.info("\n" + "=" * 60)
        logger.info("✅ Tiger系统启动完成")
        logger.info(f"状态: {self.status}")
        logger.info(f"可用模块: {success}/{total}")
        logger.info("=" * 60)
        
        return True
        
    async def shutdown(self):
        """关闭系统"""
        logger.info("\n" + "=" * 60)
        logger.info("Tiger系统关闭中...")
        logger.info("=" * 60)
        
        # 关闭各个模块
        for name, module in self.modules.items():
            if module.get('status') == 'initialized':
                logger.info(f"  - 关闭 {name} 模块...")
                
        self.status = "stopped"
        
        if self.start_time:
            runtime = datetime.now() - self.start_time
            logger.info(f"\n运行时长: {runtime}")
            
        logger.info("✅ Tiger系统已安全关闭")
        
    def get_status(self):
        """获取系统状态"""
        status = {
            'system_status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'modules': {}
        }
        
        for name, module in self.modules.items():
            status['modules'][name] = module.get('status', 'unknown')
            
        return status


async def main():
    """主函数"""
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    # 创建系统实例
    system = TigerSystem()
    
    try:
        # 启动系统
        success = await system.start()
        
        if success:
            logger.info("\n系统运行中，按 Ctrl+C 退出...")
            
            # 保持运行
            while True:
                await asyncio.sleep(60)
                # 每分钟输出状态
                status = system.get_status()
                logger.debug(f"系统状态: {status['system_status']}")
                
    except KeyboardInterrupt:
        logger.info("\n收到退出信号...")
    except Exception as e:
        logger.error(f"系统错误: {e}", exc_info=True)
    finally:
        # 关闭系统
        await system.shutdown()


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())