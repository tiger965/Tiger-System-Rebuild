"""
Window 6 AI决策大脑 - 完整测试套件
"""

import pytest
import asyncio
import json
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

# 添加父目录到系统路径  
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from preprocessing_layer import PreprocessingLayer
from monitoring_activation_system import MonitoringActivationSystem
from window_commander import WindowCommander
from command_interface import CommandInterface


class TestMonitoringActivationSystem:
    """三级触发系统测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.monitoring = MonitoringActivationSystem()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.monitoring.trigger_thresholds[1] == 0.003
        assert self.monitoring.trigger_thresholds[2] == 0.005
        assert self.monitoring.trigger_thresholds[3] == 0.010
        assert len(self.monitoring.monitored_symbols) == 6
    
    def test_price_extraction(self):
        """测试价格提取"""
        market_data = {
            "btc_price": {"price": 67500},
            "hot_coins": [
                {"symbol": "ETHUSDT", "price": 3800},
                {"symbol": "BNBUSDT", "price": 600}
            ]
        }
        
        prices = self.monitoring._extract_prices(market_data)
        
        assert prices["BTCUSDT"] == 67500
        assert prices["ETHUSDT"] == 3800
        assert prices["BNBUSDT"] == 600
    
    def test_no_trigger_on_first_check(self):
        """测试首次检查无触发"""
        market_data = {
            "btc_price": {"price": 67500},
            "hot_coins": []
        }
        
        level = self.monitoring.check_trigger_level(market_data)
        assert level == 0  # 首次检查无缓存数据，不应触发
    
    def test_trigger_levels(self):
        """测试不同触发级别"""
        # 第一次调用建立基线
        market_data = {
            "btc_price": {"price": 67500},
            "hot_coins": []
        }
        self.monitoring.check_trigger_level(market_data)
        
        # 测试一级触发 (0.3%)
        market_data["btc_price"]["price"] = 67500 * 1.004  # 0.4%变化
        level = self.monitoring.check_trigger_level(market_data)
        assert level == 1
        
        # 等待重置价格缓存
        self.monitoring.price_cache["BTCUSDT"] = 67500
        
        # 测试二级触发 (0.5%)
        market_data["btc_price"]["price"] = 67500 * 1.007  # 0.7%变化
        level = self.monitoring.check_trigger_level(market_data)
        assert level == 2
        
        # 重置价格缓存
        self.monitoring.price_cache["BTCUSDT"] = 67500
        
        # 测试三级触发 (1.0%)
        market_data["btc_price"]["price"] = 67500 * 1.015  # 1.5%变化
        level = self.monitoring.check_trigger_level(market_data)
        assert level == 3
    
    def test_sensitivity_adjustment(self):
        """测试灵敏度调整"""
        original_threshold = self.monitoring.trigger_thresholds[1]
        
        self.monitoring.adjust_sensitivity(2.0)  # 降低灵敏度
        assert self.monitoring.trigger_thresholds[1] == original_threshold * 2.0
        
        self.monitoring.adjust_sensitivity(0.5)  # 提高灵敏度
        assert self.monitoring.trigger_thresholds[1] == original_threshold
    
    def test_trigger_stats(self):
        """测试触发统计"""
        # 模拟一些触发事件
        self.monitoring.trigger_history = [
            {"level": 1, "timestamp": datetime.now().isoformat()},
            {"level": 2, "timestamp": datetime.now().isoformat()},
            {"level": 1, "timestamp": datetime.now().isoformat()}
        ]
        
        stats = self.monitoring.get_trigger_stats()
        
        assert stats["total_triggers"] == 3
        assert stats["level_distribution"][1] == 2
        assert stats["level_distribution"][2] == 1
        assert stats["level_distribution"][3] == 0


class TestCommandInterface:
    """命令接口测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.interface = CommandInterface()
    
    def test_initialization(self):
        """测试初始化"""
        assert len(self.interface.WINDOW_FUNCTIONS) > 0
        assert 1 in self.interface.WINDOW_FUNCTIONS
        assert 2 in self.interface.WINDOW_FUNCTIONS
    
    def test_command_validation(self):
        """测试命令验证"""
        # 有效命令
        valid_command = {
            "window": 1,
            "function": "get_account_cache",
            "params": {"user_id": "default"}
        }
        assert self.interface._validate_command(valid_command)
        
        # 无效命令 - 缺少window
        invalid_command = {
            "function": "get_account_cache"
        }
        assert not self.interface._validate_command(invalid_command)
        
        # 无效命令 - window类型错误
        invalid_command = {
            "window": "1",
            "function": "get_account_cache"
        }
        assert not self.interface._validate_command(invalid_command)
    
    def test_parameter_validation(self):
        """测试参数验证"""
        # 完整参数
        provided = {"user_id": "default", "extra": "value"}
        required = ["user_id"]
        assert self.interface._validate_params(provided, required)
        
        # 缺少必需参数
        provided = {"extra": "value"}
        required = ["user_id"]
        assert not self.interface._validate_params(provided, required)
    
    @pytest.mark.asyncio
    async def test_execute_command(self):
        """测试命令执行"""
        command = {
            "window": 1,
            "function": "get_account_cache",
            "params": {"user_id": "default"}
        }
        
        result = await self.interface.execute_command(command)
        
        # 应该返回模拟数据
        assert result is not None
        assert "user_id" in result
    
    def test_ai_command_validation(self):
        """测试AI命令验证"""
        # 有效的JSON命令
        valid_json = {
            "window": 2,
            "function": "get_hot_ranking",
            "params": {"exchange": "binance", "top": 10}
        }
        assert self.interface.validate_ai_command(valid_json)
        
        # 无效的自然语言命令
        invalid_natural = "请查看BTC价格"
        assert not self.interface.validate_ai_command(invalid_natural)
        
        invalid_english = "please check BTC price"
        assert not self.interface.validate_ai_command(invalid_english)
    
    def test_available_commands(self):
        """测试获取可用命令"""
        commands = self.interface.get_available_commands()
        
        assert "Window_1" in commands
        assert "get_account_cache" in commands["Window_1"]
        assert "params" in commands["Window_1"]["get_account_cache"]
    
    def test_command_example_generation(self):
        """测试命令示例生成"""
        example = self.interface.format_command_example(1, "get_account_cache")
        
        parsed = json.loads(example)
        assert parsed["window"] == 1
        assert parsed["function"] == "get_account_cache"
        assert "user_id" in parsed["params"]


class TestWindowCommander:
    """窗口指挥官测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.commander = WindowCommander()
    
    def test_initialization(self):
        """测试初始化"""
        assert len(self.commander.window_status) > 0
        assert 1 in self.commander.window_status
        assert self.commander.window_status[1]["name"] == "数据库"
    
    @pytest.mark.asyncio
    async def test_call_window(self):
        """测试窗口调用"""
        result = await self.commander.call_window(
            1, "get_account_cache", {"user_id": "default"}
        )
        
        assert result is not None
        assert 1 in self.commander.call_stats
        assert self.commander.call_stats[1]["calls"] == 1
    
    @pytest.mark.asyncio
    async def test_market_scan_workflow(self):
        """测试市场扫描工作流"""
        result = await self.commander.execute_workflow("market_scan")
        
        assert result["status"] == "success"
        assert "hot_coins" in result["result"]
        assert "volume_surge" in result["result"]
    
    @pytest.mark.asyncio
    async def test_risk_assessment_workflow(self):
        """测试风险评估工作流"""
        params = {
            "symbol": "BTCUSDT",
            "prices": [67000, 67100, 67200, 67150, 67300]
        }
        
        result = await self.commander.execute_workflow("risk_assessment", params)
        
        assert result["status"] == "success"
        assert "account" in result["result"]
        assert "rsi" in result["result"]
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        health = await self.commander.health_check()
        
        assert "status" in health
        assert "windows" in health
        assert len(health["windows"]) > 0
    
    def test_call_statistics(self):
        """测试调用统计"""
        stats = self.commander.get_call_statistics()
        
        assert "total_calls" in stats
        assert "by_window" in stats
        assert "recent_calls" in stats


class TestIntegration:
    """集成测试"""
    
    def setup_method(self):
        """设置集成测试环境"""
        self.preprocessing = None
    
    @pytest.mark.asyncio
    async def test_preprocessing_layer_initialization(self):
        """测试预处理层初始化"""
        # 创建日志目录
        os.makedirs('/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/ai/logs', exist_ok=True)
        
        self.preprocessing = PreprocessingLayer()
        
        assert self.preprocessing.context_manager is not None
        assert self.preprocessing.monitoring_system is not None
        assert self.preprocessing.window_commander is not None
        assert self.preprocessing.command_interface is not None
    
    @pytest.mark.asyncio
    async def test_trigger_to_activation_flow(self):
        """测试从触发到激活的完整流程"""
        monitoring = MonitoringActivationSystem()
        interface = CommandInterface()
        
        # 模拟市场数据
        market_data = {
            "btc_price": {"price": 67500},
            "hot_coins": []
        }
        
        # 首次检查建立基线
        monitoring.check_trigger_level(market_data)
        
        # 模拟价格大幅变动
        market_data["btc_price"]["price"] = 67500 * 1.012  # 1.2%变化
        level = monitoring.check_trigger_level(market_data)
        
        assert level == 3  # 应该是三级触发
        
        # 如果是三级触发，应该能够执行相应的命令
        if level >= 2:
            command = {
                "window": 1,
                "function": "get_account_cache",
                "params": {"user_id": "default"}
            }
            result = await interface.execute_command(command)
            assert result is not None
    
    def test_configuration_integrity(self):
        """测试配置完整性"""
        interface = CommandInterface()
        
        # 检查所有窗口的函数配置
        for window_id, functions in interface.WINDOW_FUNCTIONS.items():
            assert isinstance(window_id, int)
            assert window_id > 0
            
            for func_name, config in functions.items():
                assert "params" in config
                assert "module" in config
                assert isinstance(config["params"], list)
                
                # 必须有class+method或者function
                assert ("class" in config and "method" in config) or "function" in config


def run_performance_test():
    """性能测试"""
    print("开始性能测试...")
    
    import time
    
    # 测试命令接口性能
    interface = CommandInterface()
    
    start_time = time.time()
    
    # 执行100次命令
    for i in range(100):
        command = {
            "window": 1,
            "function": "get_account_cache",
            "params": {"user_id": f"user_{i}"}
        }
        
        # 同步验证命令
        interface._validate_command(command)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000  # 转换为毫秒
    
    print(f"平均命令验证时间: {avg_time:.2f}ms")
    
    # 验证是否满足性能要求 (< 100ms)
    assert avg_time < 100, f"命令验证时间过长: {avg_time}ms"
    
    print("性能测试通过 ✓")


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs('/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/ai/logs', exist_ok=True)
    
    print("开始Window 6 AI决策大脑测试...")
    
    # 运行pytest
    pytest_args = [
        "-v",  # 详细输出
        "-s",  # 不捕获输出
        __file__,  # 当前文件
        "--tb=short"  # 简化错误信息
    ]
    
    exit_code = pytest.main(pytest_args)
    
    # 运行性能测试
    if exit_code == 0:
        try:
            run_performance_test()
            print("\n🎉 所有测试通过！Window 6 AI决策大脑验证完成！")
        except Exception as e:
            print(f"\n❌ 性能测试失败: {e}")
            exit_code = 1
    else:
        print(f"\n❌ 测试失败，退出码: {exit_code}")
    
    exit(exit_code)