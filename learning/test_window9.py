#!/usr/bin/env python3
"""
Window 9学习工具完整测试脚本
确保所有功能工作正常
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

def test_module_imports():
    """测试模块导入"""
    print("🔍 测试1: 模块导入测试")
    try:
        from thinking_recorder import ThinkingRecorder
        from external_signal_learning import ExternalSignalLearning  
        from black_swan_learning import BlackSwanLearning
        from prompt_evolution import PromptEvolution
        from decision_tracker import DecisionTracker
        from window9_api import app
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_thinking_recorder():
    """测试AI思考记录器"""
    print("\n🧠 测试2: AI思考记录器")
    try:
        from thinking_recorder import ThinkingRecorder
        
        recorder = ThinkingRecorder("test_data")
        
        # 测试记录思考过程
        thinking_chain = [
            {"step": 1, "content": "数据收集", "sources": ["test"]},
            {"step": 2, "content": "模式分析", "patterns": ["test_pattern"]},
            {"step": 3, "content": "决策输出", "decision": "BUY"}
        ]
        
        decision_id = f"test_{int(time.time())}"
        result = recorder.record_thinking_process(decision_id, thinking_chain)
        
        if result and "decision_id" in result:
            print("✅ 思考过程记录成功")
            
            # 测试获取最近思考
            recent = recorder.get_recent_thoughts(1)
            if recent:
                print("✅ 获取最近思考成功")
                
            # 测试分析思考模式
            analysis = recorder.analyze_thinking_patterns()
            if analysis:
                print("✅ 思考模式分析成功")
                return True
                
        print("❌ 思考记录器功能不完整")
        return False
        
    except Exception as e:
        print(f"❌ 思考记录器测试失败: {e}")
        return False

def test_signal_learning():
    """测试外部信号学习"""
    print("\n📡 测试3: 外部信号学习")
    try:
        from external_signal_learning import ExternalSignalLearning
        
        learner = ExternalSignalLearning("test_data")
        
        # 测试追踪信号
        signal_data = {
            "source": "TestSource",
            "type": "TEST",
            "prediction": {"direction": "UP", "confidence": 0.7},
            "confidence": 0.7
        }
        
        signal_id = learner.track_signal(signal_data)
        if signal_id:
            print("✅ 信号追踪成功")
            
            # 测试更新结果
            outcome = {
                "actual_direction": "UP",
                "actual_price": 100
            }
            
            update_result = learner.update_signal_outcome(signal_id, outcome)
            if update_result and not update_result.get("error"):
                print("✅ 信号结果更新成功")
                
                # 测试生成报告
                report = learner.generate_learning_report()
                if report:
                    print("✅ 学习报告生成成功")
                    return True
                    
        print("❌ 信号学习功能不完整")
        return False
        
    except Exception as e:
        print(f"❌ 信号学习测试失败: {e}")
        return False

def test_black_swan():
    """测试黑天鹅分析"""
    print("\n🦢 测试4: 黑天鹅分析")
    try:
        from black_swan_learning import BlackSwanLearning
        
        black_swan = BlackSwanLearning("test_data")
        
        # 测试风险分析
        current_signals = [
            "市场波动异常",
            "交易量激增",
            "负面新闻增加"
        ]
        
        similarities = black_swan.analyze_current_vs_historical(current_signals)
        if isinstance(similarities, list):
            print("✅ 历史相似度分析成功")
            
            # 测试风险报告
            risk_report = black_swan.generate_risk_report(current_signals)
            if risk_report and "risk_assessment" in risk_report:
                print("✅ 风险报告生成成功")
                return True
                
        print("❌ 黑天鹅分析功能不完整")
        return False
        
    except Exception as e:
        print(f"❌ 黑天鹅分析测试失败: {e}")
        return False

def test_prompt_evolution():
    """测试提示词进化"""
    print("\n🧬 测试5: 提示词进化")
    try:
        from prompt_evolution import PromptEvolution
        
        evolver = PromptEvolution("test_data")
        
        # 测试权重进化
        performance_data = {
            "test_strategy": {"success_rate": 0.8, "sample_count": 20}
        }
        
        result = evolver.evolve_weights(performance_data)
        if result and "new_weights" in result:
            print("✅ 权重进化成功")
            
            # 测试生成提示词
            prompt = evolver.generate_evolved_prompt()
            if prompt and len(prompt) > 100:
                print("✅ 进化提示词生成成功")
                
                # 测试权重分析
                analysis = evolver.analyze_weight_performance()
                if analysis:
                    print("✅ 权重分析成功")
                    return True
                    
        print("❌ 提示词进化功能不完整")
        return False
        
    except Exception as e:
        print(f"❌ 提示词进化测试失败: {e}")
        return False

def test_decision_tracker():
    """测试决策追踪"""
    print("\n📊 测试6: 决策追踪")
    try:
        from decision_tracker import DecisionTracker
        
        tracker = DecisionTracker("test_data")
        
        # 测试记录决策
        decision_data = {
            "symbol": "TEST/USDT",
            "action": "BUY",
            "confidence": 0.8,
            "entry_price": 100
        }
        
        decision_id = tracker.record_decision(decision_data)
        if decision_id:
            print("✅ 决策记录成功")
            
            # 测试更新结果
            result_data = {
                "result": "success",
                "exit_price": 110
            }
            
            updated = tracker.update_decision_result(decision_id, result_data)
            if updated and not updated.get("error"):
                print("✅ 决策结果更新成功")
                
                # 测试性能指标
                metrics = tracker.get_performance_metrics(1)
                if metrics:
                    print("✅ 性能指标获取成功")
                    
                    # 测试成功模式分析
                    success_patterns = tracker.analyze_success_patterns()
                    if success_patterns:
                        print("✅ 成功模式分析成功")
                        return True
                        
        print("❌ 决策追踪功能不完整")
        return False
        
    except Exception as e:
        print(f"❌ 决策追踪测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("\n🔗 测试7: 集成功能测试")
    try:
        from window9_main import Window9Learning
        
        system = Window9Learning("test_data")
        
        # 测试系统健康检查
        health = system.system_health_check()
        if health and health.get("overall_status") in ["healthy", "warning"]:
            print("✅ 系统健康检查通过")
            
            # 测试综合报告
            report = system.generate_comprehensive_report()
            if report and report.get("success"):
                print("✅ 综合报告生成成功")
                return True
                
        print("❌ 集成测试功能不完整")
        return False
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def cleanup_test_data():
    """清理测试数据"""
    try:
        import shutil
        test_path = Path("test_data")
        if test_path.exists():
            shutil.rmtree(test_path)
        print("🧹 测试数据清理完成")
    except Exception as e:
        print(f"⚠️ 清理测试数据时出现问题: {e}")

def main():
    """主测试函数"""
    print("🚀 Window 9学习工具完整测试开始")
    print("="*60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("模块导入", test_module_imports),
        ("AI思考记录器", test_thinking_recorder),
        ("外部信号学习", test_signal_learning),
        ("黑天鹅分析", test_black_swan),
        ("提示词进化", test_prompt_evolution),
        ("决策追踪", test_decision_tracker),
        ("集成功能", test_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    print("\n" + "="*60)
    print("🏁 测试总结")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"总计: {passed}/{total} 通过")
    print(f"成功率: {passed/total*100:.1f}%")
    
    # 清理测试数据
    cleanup_test_data()
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常")
        return True
    else:
        print("⚠️ 存在测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)