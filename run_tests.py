# -*- coding: utf-8 -*-
"""
Window 3 简化测试运行器
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "collectors"))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_core_components():
    """测试核心组件"""
    logger.info("🚀 开始Window 3核心组件测试...")
    test_results = {}
    
    # 1. 测试配置文件
    try:
        logger.info("测试配置文件...")
        from config import get_config, validate_config
        
        config = get_config()
        assert config is not None, "配置加载失败"
        assert "whale_alert" in config, "缺少WhaleAlert配置"
        assert "valuescan" in config, "缺少ValueScan配置"
        
        # 验证关键配置
        whale_config = config["whale_alert"]
        valuescan_config = config["valuescan"]
        
        assert whale_config["api_key"] == "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU"
        assert valuescan_config["username"] == "3205381503@qq.com"
        assert valuescan_config["password"] == "Yzh198796&"
        
        test_results["配置文件"] = "✅ 通过"
        logger.info("✅ 配置文件测试通过")
        
    except Exception as e:
        test_results["配置文件"] = f"❌ 失败: {e}"
        logger.error(f"❌ 配置文件测试失败: {e}")
    
    # 2. 测试监控激活系统
    try:
        logger.info("测试三级监控激活系统...")
        from monitoring_activation_system import MonitoringActivationSystem
        
        monitor = MonitoringActivationSystem()
        await monitor.initialize()
        
        # 基本验证
        assert monitor.initialized, "监控系统未正确初始化"
        assert hasattr(monitor, 'thresholds'), "监控系统缺少阈值配置"
        assert len(monitor.vip_accounts) > 0, "VIP账号列表为空"
        
        # 验证阈值
        assert monitor.thresholds["price_change"][1] == 0.003
        assert monitor.thresholds["price_change"][2] == 0.005
        assert monitor.thresholds["price_change"][3] == 0.010
        
        test_results["监控激活系统"] = "✅ 通过"
        logger.info("✅ 监控激活系统测试通过")
        
        # 停止监控系统避免后台任务继续运行
        await monitor.shutdown()
        
    except Exception as e:
        test_results["监控激活系统"] = f"❌ 失败: {e}"
        logger.error(f"❌ 监控激活系统测试失败: {e}")
    
    # 3. 测试API接口
    try:
        logger.info("测试API接口...")
        from api_interface import Window3API
        
        api = Window3API()
        await api.initialize()
        
        # 基本验证
        assert api.initialized, "API接口未正确初始化"
        
        test_results["API接口"] = "✅ 通过"
        logger.info("✅ API接口测试通过")
        
        await api.shutdown()
        
    except Exception as e:
        test_results["API接口"] = f"❌ 失败: {e}"
        logger.error(f"❌ API接口测试失败: {e}")
    
    # 4. 测试触发发送器
    try:
        logger.info("测试触发发送器...")
        from trigger_sender import TriggerSender
        
        sender = TriggerSender()
        await sender.initialize()
        
        # 基本验证
        assert sender.initialized, "触发发送器未正确初始化"
        
        test_results["触发发送器"] = "✅ 通过"
        logger.info("✅ 触发发送器测试通过")
        
        await sender.shutdown()
        
    except Exception as e:
        test_results["触发发送器"] = f"❌ 失败: {e}"
        logger.error(f"❌ 触发发送器测试失败: {e}")
    
    # 5. 测试Twitter监控
    try:
        logger.info("测试Twitter监控...")
        from social.twitter_monitor import TwitterMonitor
        
        monitor = TwitterMonitor({})
        await monitor.initialize()
        
        # 基本验证
        assert monitor.initialized, "Twitter监控未正确初始化"
        
        test_results["Twitter监控"] = "✅ 通过"
        logger.info("✅ Twitter监控测试通过")
        
        await monitor.shutdown()
        
    except Exception as e:
        test_results["Twitter监控"] = f"❌ 失败: {e}"
        logger.error(f"❌ Twitter监控测试失败: {e}")
    
    # 6. 测试巨鲸追踪
    try:
        logger.info("测试巨鲸追踪...")
        from blockchain.whale_tracker import WhaleTracker
        
        tracker = WhaleTracker({})
        
        # 基本验证
        addresses = tracker.get_monitored_addresses()
        assert isinstance(addresses, dict), "监控地址格式错误"
        
        test_results["巨鲸追踪"] = "✅ 通过"
        logger.info("✅ 巨鲸追踪测试通过")
        
    except Exception as e:
        test_results["巨鲸追踪"] = f"❌ 失败: {e}"
        logger.error(f"❌ 巨鲸追踪测试失败: {e}")
    
    # 7. 测试ValueScan爬虫
    try:
        logger.info("测试ValueScan爬虫...")
        from signal_aggregator.valuescan_crawler import ValueScanCrawler
        
        crawler = ValueScanCrawler()
        await crawler.initialize()
        
        # 基本验证
        assert crawler.initialized, "ValueScan爬虫未正确初始化"
        assert crawler.config.username == "3205381503@qq.com"
        assert crawler.config.password == "Yzh198796&"
        
        test_results["ValueScan爬虫"] = "✅ 通过"
        logger.info("✅ ValueScan爬虫测试通过")
        
        await crawler.shutdown()
        
    except Exception as e:
        test_results["ValueScan爬虫"] = f"❌ 失败: {e}"
        logger.error(f"❌ ValueScan爬虫测试失败: {e}")
    
    # 8. 文件完整性检查
    try:
        logger.info("检查文件完整性...")
        required_files = [
            "collectors/monitoring_activation_system.py",
            "collectors/api_interface.py", 
            "collectors/trigger_sender.py",
            "collectors/config.py",
            "collectors/social/twitter_monitor.py",
            "collectors/blockchain/whale_tracker.py",
            "collectors/signal_aggregator/valuescan_crawler.py"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = current_dir / file
            if not file_path.exists():
                missing_files.append(file)
        
        assert not missing_files, f"缺少必要文件: {missing_files}"
        
        test_results["文件完整性"] = "✅ 通过"
        logger.info("✅ 文件完整性检查通过")
        
    except Exception as e:
        test_results["文件完整性"] = f"❌ 失败: {e}"
        logger.error(f"❌ 文件完整性检查失败: {e}")
    
    # 输出测试总结
    logger.info("\n" + "="*60)
    logger.info("🎯 Window 3 - 数据采集工具测试总结")
    logger.info("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result.startswith("✅"))
    
    for test_name, result in test_results.items():
        logger.info(f"{test_name:15} : {result}")
    
    logger.info("-"*60)
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过测试: {passed_tests}")
    logger.info(f"失败测试: {total_tests - passed_tests}")
    logger.info(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有测试通过！Window 3 ready for production!")
        return True
    else:
        logger.error("❌ 存在测试失败，请检查并修复")
        return False
    
    logger.info("="*60)


if __name__ == "__main__":
    success = asyncio.run(test_core_components())
    sys.exit(0 if success else 1)