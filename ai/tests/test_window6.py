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
from opportunity_manager import OpportunityManager, OpportunitySignal, AllocationMode
from simple_simulator import SimpleSimulator
from decision_tracker import DecisionTracker
from quality_ranker import QualityRanker


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


class TestOpportunityManager:
    """10币种精准管理系统测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.manager = OpportunityManager()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.manager.MAX_TOTAL_COINS == 10
        assert self.manager.MAX_USER_COINS == 5
        assert self.manager.MAX_SIM_COINS == 5
        assert len(self.manager.managed_positions) == 0
    
    def test_signal_allocation(self):
        """测试信号分配"""
        # 创建测试信号
        signals = []
        for i in range(12):  # 超过上限的信号数量
            signal = OpportunitySignal(
                symbol=f"TEST{i}USDT",
                signal_type="buy",
                quality_score=0.8 - i * 0.05,  # 递减的质量分数
                confidence=0.7,
                entry_price=100.0,
                target_price=110.0,
                stop_loss=95.0,
                source="test",
                timestamp=datetime.now().isoformat(),
                risk_reward_ratio=2.0,
                timeframe="1h",
                volume_score=0.7,
                technical_score=0.8,
                sentiment_score=0.6
            )
            signals.append(signal)
        
        # 处理信号分配
        allocation = self.manager.process_opportunities(signals)
        
        # 验证分配结果
        assert "user" in allocation
        assert "simulation" in allocation
        assert "rejected" in allocation
        
        # 验证数量限制
        total_allocated = len(allocation["user"]) + len(allocation["simulation"])
        assert total_allocated <= self.manager.MAX_TOTAL_COINS
        assert len(allocation["user"]) <= self.manager.MAX_USER_COINS
        assert len(allocation["simulation"]) <= self.manager.MAX_SIM_COINS
    
    def test_quality_ranking(self):
        """测试质量排序"""
        signals = [
            OpportunitySignal("BTC", "buy", 0.9, 0.8, 50000, 55000, 48000, "high_quality", datetime.now().isoformat(), 2.5, "4h", 0.9, 0.9, 0.8),
            OpportunitySignal("ETH", "buy", 0.6, 0.7, 3000, 3200, 2900, "medium_quality", datetime.now().isoformat(), 2.0, "1h", 0.6, 0.7, 0.5),
            OpportunitySignal("ADA", "buy", 0.4, 0.5, 1.0, 1.1, 0.95, "low_quality", datetime.now().isoformat(), 1.5, "30m", 0.4, 0.5, 0.3)
        ]
        
        allocation = self.manager.process_opportunities(signals)
        
        # 高质量信号应该分配给用户
        if allocation["user"]:
            assert allocation["user"][0].quality_score >= 0.7
    
    def test_portfolio_full_replacement(self):
        """测试组合满时的替换逻辑"""
        # 先填满组合 - 创建混合质量的信号以填满用户和模拟槽位
        signals = []
        # 前5个高质量信号分配给用户
        for i in range(5):
            signals.append(OpportunitySignal(
                f"USER{i}", "buy", 0.75, 0.7, 100, 110, 95, "user_fill", 
                datetime.now().isoformat(), 2.0, "1h", 0.7, 0.7, 0.7
            ))
        # 后5个中等质量信号分配给模拟
        for i in range(5):
            signals.append(OpportunitySignal(
                f"SIM{i}", "buy", 0.6, 0.6, 100, 110, 95, "sim_fill", 
                datetime.now().isoformat(), 2.0, "1h", 0.6, 0.6, 0.6
            ))
        
        self.manager.process_opportunities(signals)
        assert len(self.manager.managed_positions) == 10
        
        # 测试高质量信号替换
        high_quality_signal = OpportunitySignal(
            "PREMIUM", "buy", 0.95, 0.9, 200, 220, 190, "premium", 
            datetime.now().isoformat(), 3.0, "4h", 0.9, 0.9, 0.9
        )
        
        allocation = self.manager.process_opportunities([high_quality_signal])
        
        # 应该仍然是10个持仓，但包含新的高质量信号
        assert len(self.manager.managed_positions) <= 10


class TestSimpleSimulator:
    """虚拟交易模拟器测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.simulator = SimpleSimulator(initial_balance=100000)
    
    def test_initialization(self):
        """测试初始化"""
        assert self.simulator.initial_balance == 100000
        assert self.simulator.current_balance == 100000
        assert len(self.simulator.positions) == 0
        assert len(self.simulator.completed_trades) == 0
    
    def test_virtual_buy(self):
        """测试虚拟买入"""
        success = self.simulator.virtual_buy(
            symbol="BTCUSDT",
            entry_price=50000,
            target_price=55000,
            stop_loss=47500,
            position_size_pct=0.02
        )
        
        assert success is True
        assert "BTCUSDT" in self.simulator.positions
        assert self.simulator.positions["BTCUSDT"].signal_type == "buy"
    
    def test_position_limit(self):
        """测试持仓数量限制"""
        # 测试单仓位大小限制
        success = self.simulator.virtual_buy(
            "TEST1", 100, 110, 95, position_size_pct=0.15  # 超过max_position_size
        )
        assert success is True
        assert self.simulator.positions["TEST1"].position_size <= self.simulator.max_position_size
    
    def test_exit_conditions(self):
        """测试出场条件"""
        # 开仓
        self.simulator.virtual_buy("BTCUSDT", 50000, 55000, 47500, 0.02)
        
        # 测试止盈
        self.simulator.check_exits({"BTCUSDT": 55500})  # 超过目标价
        assert len(self.simulator.positions) == 0
        assert len(self.simulator.completed_trades) == 1
        assert self.simulator.completed_trades[0].status.value == "win"
    
    def test_performance_calculation(self):
        """测试性能计算"""
        # 执行几笔虚拟交易
        self.simulator.virtual_buy("BTC1", 50000, 55000, 47500, 0.02)
        self.simulator.check_exits({"BTC1": 55000})  # 盈利
        
        self.simulator.virtual_buy("BTC2", 50000, 55000, 47500, 0.02)
        self.simulator.check_exits({"BTC2": 47500})  # 亏损
        
        report = self.simulator.get_performance_report()
        
        assert "balance" in report
        assert "statistics" in report
        assert report["statistics"]["total_trades"] == 2
        assert report["statistics"]["winning_trades"] == 1
        assert report["statistics"]["losing_trades"] == 1


class TestDecisionTracker:
    """决策跟踪记录测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.tracker = DecisionTracker()
    
    def test_initialization(self):
        """测试初始化"""
        assert len(self.tracker.pending_decisions) == 0
        assert len(self.tracker.completed_decisions) == 0
        assert self.tracker.accuracy_stats["total_decisions"] == 0
    
    def test_record_decision(self):
        """测试记录决策"""
        decision_data = {
            "action": "buy",
            "symbol": "BTCUSDT",
            "confidence": 0.8,
            "entry_price": 50000,
            "target_price": 55000,
            "stop_loss": 47500,
            "reasoning": "强势突破",
            "trigger_source": "technical"
        }
        
        decision_id = self.tracker.record_decision(decision_data)
        
        assert decision_id is not None
        assert decision_id in self.tracker.pending_decisions
        assert self.tracker.pending_decisions[decision_id].symbol == "BTCUSDT"
    
    def test_update_result(self):
        """测试更新结果"""
        # 先记录决策
        decision_data = {
            "action": "buy",
            "symbol": "BTCUSDT", 
            "confidence": 0.8,
            "entry_price": 50000
        }
        decision_id = self.tracker.record_decision(decision_data)
        
        # 更新结果
        result_data = {
            "result": "win",
            "exit_price": 55000,
            "pnl": 1000,
            "pnl_pct": 0.1
        }
        self.tracker.update_result(decision_id, result_data)
        
        # 验证
        assert decision_id not in self.tracker.pending_decisions
        assert len(self.tracker.completed_decisions) == 1
        assert self.tracker.completed_decisions[0].result.value == "win"
    
    def test_accuracy_calculation(self):
        """测试准确率计算"""
        # 记录几个决策和结果
        decisions = [
            {"action": "buy", "symbol": "BTC1", "confidence": 0.8, "entry_price": 50000},
            {"action": "buy", "symbol": "BTC2", "confidence": 0.7, "entry_price": 51000},
            {"action": "sell", "symbol": "BTC3", "confidence": 0.9, "entry_price": 52000}
        ]
        
        results = [
            {"result": "win", "pnl": 1000},
            {"result": "loss", "pnl": -500},
            {"result": "win", "pnl": 800}
        ]
        
        decision_ids = []
        for decision in decisions:
            decision_id = self.tracker.record_decision(decision)
            decision_ids.append(decision_id)
        
        for i, result in enumerate(results):
            self.tracker.update_result(decision_ids[i], result)
        
        # 检查统计
        assert self.tracker.accuracy_stats["total_decisions"] == 3
        assert self.tracker.accuracy_stats["correct_predictions"] == 2
        assert abs(self.tracker.accuracy_stats["accuracy_rate"] - 2/3) < 0.01


class TestQualityRanker:
    """信号质量评估测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.ranker = QualityRanker()
    
    def test_initialization(self):
        """测试初始化"""
        assert sum(self.ranker.weights.values()) == 1.0  # 权重总和为1
        assert len(self.ranker.tier_thresholds) == 6  # 6个质量等级
    
    def test_signal_evaluation(self):
        """测试信号评估"""
        signal_data = {
            "symbol": "BTCUSDT",
            "action": "buy",
            "confidence": 0.8,
            "technical_strength": 0.9,
            "volume_score": 0.8,
            "sentiment_score": 0.7,
            "risk_reward_ratio": 2.5,
            "volatility": 0.03,
            "entry_price": 50000,
            "support_level": 49000,
            "resistance_level": 52000
        }
        
        score, tier, details = self.ranker.evaluate_signal_quality(signal_data)
        
        assert 0 <= score <= 1
        assert tier in [t for t in self.ranker.tier_thresholds.keys()]
        assert "overall_score" in details
        assert "category_scores" in details
    
    def test_signal_ranking(self):
        """测试信号排序"""
        signals = [
            {"symbol": "BTC", "confidence": 0.9, "technical_strength": 0.9, "risk_reward_ratio": 3.0},
            {"symbol": "ETH", "confidence": 0.6, "technical_strength": 0.6, "risk_reward_ratio": 1.5},
            {"symbol": "ADA", "confidence": 0.8, "technical_strength": 0.8, "risk_reward_ratio": 2.0}
        ]
        
        ranked = self.ranker.rank_signals(signals)
        
        assert len(ranked) == 3
        # 验证是按分数降序排列
        assert ranked[0][1] >= ranked[1][1] >= ranked[2][1]
    
    def test_quality_distribution(self):
        """测试质量分布统计"""
        signals = [
            {"confidence": 0.9, "technical_strength": 0.9},
            {"confidence": 0.7, "technical_strength": 0.7},
            {"confidence": 0.5, "technical_strength": 0.5},
            {"confidence": 0.3, "technical_strength": 0.3}
        ]
        
        distribution = self.ranker.get_quality_distribution(signals)
        
        assert "total_signals" in distribution
        assert "average_score" in distribution
        assert "tier_distribution" in distribution
        assert distribution["total_signals"] == 4
    
    def test_weight_adjustment(self):
        """测试权重调整"""
        new_weights = {
            "technical": 0.3,
            "market": 0.2,
            "sentiment": 0.2,
            "risk": 0.2,
            "timing": 0.1
        }
        
        self.ranker.adjust_weights(new_weights)
        
        assert abs(sum(self.ranker.weights.values()) - 1.0) < 0.01
        assert abs(self.ranker.weights["technical"] - 0.3) < 0.01


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