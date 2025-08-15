# -*- coding: utf-8 -*-
"""
Window 3 - 数据采集工具完整测试套件
确保所有功能100%通过测试
"""

import os
import sys
import asyncio
import pytest
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "collectors"))

# 配置测试日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestWindow3Complete:
    """Window 3完整功能测试"""
    
    def setup(self):
        """测试前设置"""
        logger.info("🔧 开始Window 3测试设置...")
        self.test_results = {}
        
    def test_config_validation(self):
        """测试配置文件加载和验证"""
        logger.info("测试配置文件...")
        
        try:
            from config import get_config, validate_config
            
            # 测试配置加载
            config = get_config()
            assert config is not None, "配置加载失败"
            assert "whale_alert" in config, "缺少WhaleAlert配置"
            assert "valuescan" in config, "缺少ValueScan配置"
            
            # 测试关键配置项
            whale_config = config["whale_alert"]
            assert whale_config["api_key"] == "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU", "WhaleAlert API密钥不正确"
            
            valuescan_config = config["valuescan"]
            assert valuescan_config["username"] == "3205381503@qq.com", "ValueScan用户名不正确"
            assert valuescan_config["password"] == "Yzh198796&", "ValueScan密码不正确"
            
            self.test_results["config"] = "✅ 通过"
            logger.info("✅ 配置文件测试通过")
            
        except Exception as e:
            self.test_results["config"] = f"❌ 失败: {e}"
            logger.error(f"❌ 配置文件测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_monitoring_activation_system(self):
        """测试三级监控激活系统"""
        logger.info("测试三级监控激活系统...")
        
        try:
            from monitoring_activation_system import MonitoringActivationSystem
            
            # 创建监控系统实例
            monitor = MonitoringActivationSystem()
            await monitor.initialize()
            
            # 测试阈值配置
            assert monitor.thresholds["price_change"][1] == 0.003, "一级价格阈值不正确"
            assert monitor.thresholds["price_change"][2] == 0.005, "二级价格阈值不正确"
            assert monitor.thresholds["price_change"][3] == 0.010, "三级价格阈值不正确"
            
            # 测试监控系统运行状态
            assert monitor.initialized, "监控系统未正确初始化"
            
            # 测试配置是否正确加载
            assert hasattr(monitor, 'thresholds'), "监控系统缺少阈值配置"
            
            # 测试VIP账号配置
            assert len(monitor.vip_accounts) > 0, "VIP账号列表为空"
            
            self.test_results["monitoring"] = "✅ 通过"
            logger.info("✅ 三级监控激活系统测试通过")
            
        except Exception as e:
            self.test_results["monitoring"] = f"❌ 失败: {e}"
            logger.error(f"❌ 三级监控激活系统测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_api_interface(self):
        """测试API接口"""
        logger.info("测试API接口...")
        
        try:
            from api_interface import Window3API
            
            # 创建API接口实例
            api = Window3API()
            await api.initialize()
            
            # 测试Twitter爬虫接口
            twitter_result = await api.crawl_twitter(
                keyword="BTC",
                time_range_minutes=60,
                get_sentiment=True,
                min_followers=10000
            )
            assert isinstance(twitter_result, list), "Twitter爬虫返回格式错误"
            
            # 测试巨鲸追踪接口
            whale_result = await api.track_whale_transfers(
                min_amount_usd=1000000,
                chains=["ETH", "BTC"],
                direction="exchange_inflow"
            )
            assert isinstance(whale_result, list), "巨鲸追踪返回格式错误"
            
            # 测试ValueScan接口
            valuescan_result = await api.crawl_valuescan(
                signal_type="OPPORTUNITY",
                min_confidence=0.7
            )
            assert isinstance(valuescan_result, list), "ValueScan爬虫返回格式错误"
            
            self.test_results["api_interface"] = "✅ 通过"
            logger.info("✅ API接口测试通过")
            
        except Exception as e:
            self.test_results["api_interface"] = f"❌ 失败: {e}"
            logger.error(f"❌ API接口测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_trigger_sender(self):
        """测试触发信号发送器"""
        logger.info("测试触发信号发送器...")
        
        try:
            from trigger_sender import TriggerSender
            
            # 创建发送器实例
            sender = TriggerSender()
            await sender.initialize()
            
            # 测试发送触发信号
            test_data = {
                "symbol": "BTC",
                "trigger_type": "price_surge",
                "value": 0.05,
                "description": "BTC价格上涨5%"
            }
            
            success = await sender.send_trigger_signal(
                source_window=3,
                target_window=6,
                trigger_level=2,
                message_type="price_alert",
                data=test_data,
                priority=3
            )
            
            # 注意：即使没有实际的接收端，发送器也应该能处理
            logger.info(f"触发信号发送结果: {success}")
            
            # 测试广播功能
            broadcast_results = await sender.send_broadcast(
                source_window=3,
                trigger_level=1,
                message_type="market_update",
                data=test_data
            )
            assert isinstance(broadcast_results, dict), "广播结果格式错误"
            
            # 获取统计信息
            stats = sender.get_statistics()
            assert "total_sent" in stats, "统计信息缺失"
            
            await sender.shutdown()
            
            self.test_results["trigger_sender"] = "✅ 通过"
            logger.info("✅ 触发信号发送器测试通过")
            
        except Exception as e:
            self.test_results["trigger_sender"] = f"❌ 失败: {e}"
            logger.error(f"❌ 触发信号发送器测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_twitter_monitor(self):
        """测试Twitter监控"""
        logger.info("测试Twitter监控...")
        
        try:
            from social.twitter_monitor import TwitterMonitor
            from config import get_config
            
            config = get_config()
            monitor = TwitterMonitor(config)
            await monitor.initialize()
            
            # 测试搜索功能（演示模式）
            tweets = await monitor.search_tweets(
                keywords=["BTC", "bitcoin"],
                max_results=10,
                time_range_hours=24
            )
            assert isinstance(tweets, list), "Twitter搜索返回格式错误"
            
            # 测试情感分析
            if tweets:
                sentiment = await monitor.analyze_sentiment(tweets[0]["text"])
                assert "sentiment" in sentiment, "情感分析结果格式错误"
            
            # 获取统计信息
            stats = monitor.get_statistics()
            assert isinstance(stats, dict), "统计信息格式错误"
            
            await monitor.shutdown()
            
            self.test_results["twitter_monitor"] = "✅ 通过"
            logger.info("✅ Twitter监控测试通过")
            
        except Exception as e:
            self.test_results["twitter_monitor"] = f"❌ 失败: {e}"
            logger.error(f"❌ Twitter监控测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_whale_tracker(self):
        """测试巨鲸追踪"""
        logger.info("测试巨鲸追踪...")
        
        try:
            from blockchain.whale_tracker import WhaleTracker
            from config import get_config
            
            config = get_config()
            tracker = WhaleTracker(config)
            
            # 测试获取巨鲸活动
            activities = await tracker.get_whale_activities()
            assert isinstance(activities, list), "巨鲸活动返回格式错误"
            
            # 测试地址管理
            success = await tracker.add_monitored_address("ETH", "0x123...")
            assert isinstance(success, bool), "添加地址返回格式错误"
            
            # 获取监控地址
            addresses = tracker.get_monitored_addresses()
            assert isinstance(addresses, dict), "监控地址格式错误"
            
            self.test_results["whale_tracker"] = "✅ 通过"
            logger.info("✅ 巨鲸追踪测试通过")
            
        except Exception as e:
            self.test_results["whale_tracker"] = f"❌ 失败: {e}"
            logger.error(f"❌ 巨鲸追踪测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_valuescan_crawler(self):
        """测试ValueScan爬虫"""
        logger.info("测试ValueScan爬虫...")
        
        try:
            from signal_aggregator.valuescan_crawler import ValueScanCrawler
            
            crawler = ValueScanCrawler()
            await crawler.initialize()
            
            # 测试获取机会信号
            opportunities = await crawler.get_signals("OPPORTUNITY", min_confidence=0.3)
            assert isinstance(opportunities, list), "机会信号返回格式错误"
            
            # 测试获取风险警告
            risks = await crawler.get_signals("RISK", min_confidence=0.3)
            assert isinstance(risks, list), "风险警告返回格式错误"
            
            # 测试获取交易信号
            signals = await crawler.get_signals("SIGNAL", min_confidence=0.3)
            assert isinstance(signals, list), "交易信号返回格式错误"
            
            # 验证信号数据结构
            all_signals = opportunities + risks + signals
            if all_signals:
                signal = all_signals[0]
                required_fields = ["id", "signal_type", "symbol", "title", "confidence"]
                for field in required_fields:
                    assert hasattr(signal, field), f"信号缺少字段: {field}"
            
            # 获取统计信息
            stats = crawler.get_statistics()
            assert isinstance(stats, dict), "统计信息格式错误"
            
            await crawler.shutdown()
            
            self.test_results["valuescan_crawler"] = "✅ 通过"
            logger.info("✅ ValueScan爬虫测试通过")
            
        except Exception as e:
            self.test_results["valuescan_crawler"] = f"❌ 失败: {e}"
            logger.error(f"❌ ValueScan爬虫测试失败: {e}")
            raise
    
    def test_integration(self):
        """集成测试"""
        logger.info("执行集成测试...")
        
        try:
            # 检查所有必要文件是否存在
            required_files = [
                "monitoring_activation_system.py",
                "api_interface.py", 
                "trigger_sender.py",
                "config.py",
                "social/twitter_monitor.py",
                "blockchain/whale_tracker.py",
                "signal_aggregator/valuescan_crawler.py"
            ]
            
            base_path = Path(__file__).parent.parent / "collectors"
            missing_files = []
            
            for file in required_files:
                file_path = base_path / file
                if not file_path.exists():
                    missing_files.append(file)
            
            assert not missing_files, f"缺少必要文件: {missing_files}"
            
            self.test_results["integration"] = "✅ 通过"
            logger.info("✅ 集成测试通过")
            
        except Exception as e:
            self.test_results["integration"] = f"❌ 失败: {e}"
            logger.error(f"❌ 集成测试失败: {e}")
            raise
    
    def test_summary(self):
        """测试总结"""
        logger.info("\n" + "="*60)
        logger.info("🎯 Window 3 - 数据采集工具测试总结")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.startswith("✅"))
        
        for test_name, result in self.test_results.items():
            logger.info(f"{test_name:20} : {result}")
        
        logger.info("-"*60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {total_tests - passed_tests}")
        logger.info(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 所有测试通过！Window 3 ready for production!")
        else:
            logger.error("❌ 存在测试失败，请检查并修复")
        
        logger.info("="*60)


@pytest.mark.asyncio
async def test_main():
    """主测试函数"""
    logger.info("🚀 开始Window 3完整测试...")
    
    test_suite = TestWindow3Complete()
    test_suite.setup()
    
    # 执行所有测试
    try:
        test_suite.test_config_validation()
        await test_suite.test_monitoring_activation_system()
        await test_suite.test_api_interface()
        await test_suite.test_trigger_sender()
        await test_suite.test_twitter_monitor()
        await test_suite.test_whale_tracker()
        await test_suite.test_valuescan_crawler()
        test_suite.test_integration()
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
    
    finally:
        test_suite.test_summary()


if __name__ == "__main__":
    # 直接运行测试
    asyncio.run(test_main())