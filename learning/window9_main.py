"""
Window 9 - 学习进化工具主程序 (工业级版本)
集成所有学习工具，提供统一接口，确保零错误运行
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 导入新的学习工具
from thinking_recorder import ThinkingRecorder
from external_signal_learning import ExternalSignalLearning
from black_swan_learning import BlackSwanLearning
from prompt_evolution import PromptEvolution
from decision_tracker import DecisionTracker


# 配置日志
def setup_logging():
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f'window9_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


class Window9Learning:
    """Window 9 学习系统主类 - 工业级版本"""
    
    def __init__(self, base_path: str = "learning_data"):
        """
        初始化Window 9学习系统
        
        Args:
            base_path: 数据存储基础路径
        """
        try:
            self.base_path = Path(base_path)
            self.base_path.mkdir(exist_ok=True)
            
            # 初始化所有学习工具
            logger.info("开始初始化Window 9学习系统组件...")
            
            self.thinking_recorder = ThinkingRecorder(base_path)
            logger.info("✅ ThinkingRecorder 初始化完成")
            
            self.signal_learning = ExternalSignalLearning(base_path)
            logger.info("✅ ExternalSignalLearning 初始化完成")
            
            self.black_swan = BlackSwanLearning(base_path)
            logger.info("✅ BlackSwanLearning 初始化完成")
            
            self.prompt_evolution = PromptEvolution(base_path)
            logger.info("✅ PromptEvolution 初始化完成")
            
            self.decision_tracker = DecisionTracker(base_path)
            logger.info("✅ DecisionTracker 初始化完成")
            
            # 创建报告目录
            self.reports_path = self.base_path / "reports"
            self.reports_path.mkdir(exist_ok=True)
            
            logger.info("🎯 Window 9 学习系统初始化完成")
            
        except Exception as e:
            logger.error(f"❌ Window 9学习系统初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise
            
    def validate_input(self, data: Any, required_fields: List[str], data_type: str) -> bool:
        """
        验证输入数据
        
        Args:
            data: 输入数据
            required_fields: 必需字段列表
            data_type: 数据类型描述
            
        Returns:
            验证结果
        """
        try:
            if not isinstance(data, dict):
                logger.error(f"❌ {data_type}数据必须是字典格式")
                return False
                
            for field in required_fields:
                if field not in data:
                    logger.error(f"❌ {data_type}缺少必需字段: {field}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"❌ 验证{data_type}数据时发生错误: {e}")
            return False
            
    def process_ai_thinking(self, decision_id: str, thinking_chain: List[Dict]) -> Dict:
        """
        处理AI思考过程 (带完整错误处理)
        
        Args:
            decision_id: 决策ID
            thinking_chain: 思考链
            
        Returns:
            处理结果
        """
        try:
            # 输入验证
            if not decision_id or not isinstance(decision_id, str):
                return {"success": False, "error": "决策ID无效"}
                
            if not thinking_chain or not isinstance(thinking_chain, list):
                return {"success": False, "error": "思考链格式无效"}
                
            if len(thinking_chain) == 0:
                return {"success": False, "error": "思考链不能为空"}
                
            # 处理思考过程
            result = self.thinking_recorder.record_thinking_process(decision_id, thinking_chain)
            
            logger.info(f"✅ AI思考过程已记录: {decision_id}")
            return {
                "success": True,
                "decision_id": result["decision_id"],
                "confidence": result["confidence"],
                "timestamp": result["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"❌ 处理AI思考过程错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def process_external_signal(self, signal_data: Dict) -> Dict:
        """
        处理外部信号 (带完整错误处理)
        
        Args:
            signal_data: 信号数据
            
        Returns:
            处理结果
        """
        try:
            # 验证必需字段
            required_fields = ["source", "type", "prediction"]
            if not self.validate_input(signal_data, required_fields, "外部信号"):
                return {"success": False, "error": "信号数据验证失败"}
                
            # 处理信号
            signal_id = self.signal_learning.track_signal(signal_data)
            
            logger.info(f"✅ 外部信号已追踪: {signal_id}")
            return {
                "success": True,
                "signal_id": signal_id,
                "source": signal_data.get("source", "unknown")
            }
            
        except Exception as e:
            logger.error(f"❌ 处理外部信号错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def check_black_swan_risk(self, current_signals: List[str]) -> Dict:
        """
        检查黑天鹅风险 (带完整错误处理)
        
        Args:
            current_signals: 当前市场信号
            
        Returns:
            风险评估结果
        """
        try:
            # 输入验证
            if not current_signals or not isinstance(current_signals, list):
                return {"success": False, "error": "市场信号格式无效"}
                
            if len(current_signals) == 0:
                logger.warning("⚠️ 市场信号为空，风险评估可能不准确")
                
            # 生成风险报告
            risk_report = self.black_swan.generate_risk_report(current_signals)
            risk_level = risk_report["risk_assessment"]["overall_risk"]
            
            logger.info(f"🦢 黑天鹅风险评估: {risk_level}")
            return {
                "success": True,
                "risk_level": risk_level,
                "confidence": risk_report["risk_assessment"]["confidence"],
                "report": risk_report
            }
            
        except Exception as e:
            logger.error(f"❌ 黑天鹅风险检查错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def evolve_strategy_weights(self, performance_data: Dict) -> Dict:
        """
        进化策略权重 (带完整错误处理)
        
        Args:
            performance_data: 性能数据
            
        Returns:
            进化结果
        """
        try:
            # 验证性能数据格式
            if not performance_data or not isinstance(performance_data, dict):
                return {"success": False, "error": "性能数据格式无效"}
                
            # 验证每个策略的数据格式
            for strategy, data in performance_data.items():
                if not isinstance(data, dict):
                    return {"success": False, "error": f"策略 {strategy} 数据格式无效"}
                    
                if "success_rate" not in data or "sample_count" not in data:
                    return {"success": False, "error": f"策略 {strategy} 缺少必需字段"}
                    
            # 进化权重
            result = self.prompt_evolution.evolve_weights(performance_data)
            
            adjustments_count = len(result.get("adjustments", {}))
            logger.info(f"🧬 权重进化完成，调整了 {adjustments_count} 个策略")
            
            return {
                "success": True,
                "adjustments_count": adjustments_count,
                "new_weights": result["new_weights"],
                "adjustments": result.get("adjustments", {})
            }
            
        except Exception as e:
            logger.error(f"❌ 权重进化错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def record_decision(self, decision_data: Dict) -> Dict:
        """
        记录决策 (带完整错误处理)
        
        Args:
            decision_data: 决策数据
            
        Returns:
            记录结果
        """
        try:
            # 验证必需字段
            required_fields = ["symbol", "action", "confidence"]
            if not self.validate_input(decision_data, required_fields, "决策"):
                return {"success": False, "error": "决策数据验证失败"}
                
            # 记录决策
            decision_id = self.decision_tracker.record_decision(decision_data)
            
            logger.info(f"📝 决策已记录: {decision_id}")
            return {
                "success": True,
                "decision_id": decision_id,
                "symbol": decision_data["symbol"],
                "action": decision_data["action"]
            }
            
        except Exception as e:
            logger.error(f"❌ 记录决策错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def update_decision_result(self, decision_id: str, result_data: Dict) -> Dict:
        """
        更新决策结果 (带完整错误处理)
        
        Args:
            decision_id: 决策ID
            result_data: 结果数据
            
        Returns:
            更新结果
        """
        try:
            # 输入验证
            if not decision_id or not isinstance(decision_id, str):
                return {"success": False, "error": "决策ID无效"}
                
            required_fields = ["result", "exit_price"]
            if not self.validate_input(result_data, required_fields, "决策结果"):
                return {"success": False, "error": "结果数据验证失败"}
                
            # 更新结果
            updated_decision = self.decision_tracker.update_decision_result(decision_id, result_data)
            
            if "error" in updated_decision:
                return {"success": False, "error": updated_decision["error"]}
                
            status = updated_decision.get("status", "unknown")
            pnl = updated_decision.get("pnl", 0)
            
            logger.info(f"📊 决策结果已更新: {decision_id} - {status} - PnL: {pnl:.2%}")
            
            return {
                "success": True,
                "decision_id": decision_id,
                "status": status,
                "pnl": pnl
            }
            
        except Exception as e:
            logger.error(f"❌ 更新决策结果错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def generate_comprehensive_report(self) -> Dict:
        """生成综合学习报告 (带完整错误处理)"""
        try:
            logger.info("📈 开始生成综合学习报告...")
            
            # 收集所有组件的数据
            thinking_analysis = self.thinking_recorder.analyze_thinking_patterns()
            signal_report = self.signal_learning.generate_learning_report()
            weight_analysis = self.prompt_evolution.analyze_weight_performance()
            success_patterns = self.decision_tracker.analyze_success_patterns()
            failure_patterns = self.decision_tracker.analyze_failure_patterns()
            performance_metrics = self.decision_tracker.get_performance_metrics(30)
            
            # 构建综合报告
            comprehensive_report = {
                "report_info": {
                    "generated_at": datetime.now().isoformat(),
                    "system_version": "9.1",
                    "components": ["thinking", "signals", "black_swan", "evolution", "decisions"]
                },
                "executive_summary": {
                    "total_decisions": performance_metrics.get("total_decisions", 0),
                    "success_rate": performance_metrics.get("success_rate", 0),
                    "total_pnl": performance_metrics.get("total_pnl", 0),
                    "avg_confidence": thinking_analysis.get("average_confidence", 0),
                    "signals_tracked": signal_report.get("total_signals_tracked", 0),
                    "weight_evolutions": weight_analysis.get("total_evolutions", 0)
                },
                "detailed_analysis": {
                    "thinking_patterns": thinking_analysis,
                    "signal_learning": signal_report,
                    "weight_evolution": weight_analysis,
                    "success_patterns": success_patterns,
                    "failure_patterns": failure_patterns,
                    "performance_metrics": performance_metrics
                },
                "recommendations": self._generate_recommendations(
                    thinking_analysis, signal_report, success_patterns, failure_patterns
                )
            }
            
            # 保存报告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.reports_path / f"comprehensive_report_{timestamp}.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
                
            logger.info(f"✅ 综合学习报告已生成: {report_path}")
            
            return {
                "success": True,
                "report": comprehensive_report,
                "saved_to": str(report_path)
            }
            
        except Exception as e:
            logger.error(f"❌ 生成综合报告错误: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
            
    def _generate_recommendations(self, thinking_analysis: Dict, signal_report: Dict, 
                                success_patterns: Dict, failure_patterns: Dict) -> List[Dict]:
        """生成建议 (内部方法)"""
        try:
            recommendations = []
            
            # 基于成功率的建议
            success_count = success_patterns.get("total_successes", 0)
            if success_count > 0:
                best_time = success_patterns.get("best_time", "unknown")
                if best_time != "unknown":
                    recommendations.append({
                        "type": "timing",
                        "priority": "high",
                        "suggestion": f"优先在 {best_time} 时段进行交易",
                        "reason": "该时段历史成功率最高"
                    })
                    
            # 基于信号准确率的建议
            best_sources = signal_report.get("best_performing_sources", [])
            if best_sources:
                recommendations.append({
                    "type": "signals",
                    "priority": "medium",
                    "suggestion": f"重点关注 {best_sources[0]['source']} 的信号",
                    "reason": f"该信号源准确率达 {best_sources[0]['accuracy']:.1%}"
                })
                
            # 基于失败模式的建议
            common_mistakes = failure_patterns.get("common_mistakes", [])
            if common_mistakes:
                recommendations.append({
                    "type": "risk_management",
                    "priority": "high",
                    "suggestion": f"注意避免: {common_mistakes[0]}",
                    "reason": "这是最常见的失败原因"
                })
                
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 生成建议时发生错误: {e}")
            return []
            
    def system_health_check(self) -> Dict:
        """系统健康检查"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "components": {},
                "data_integrity": {},
                "warnings": [],
                "errors": []
            }
            
            # 检查各组件
            try:
                recent_thoughts = self.thinking_recorder.get_recent_thoughts(1)
                health_status["components"]["thinking_recorder"] = "healthy"
                health_status["data_integrity"]["thinking_data"] = len(recent_thoughts)
            except Exception as e:
                health_status["components"]["thinking_recorder"] = "error"
                health_status["errors"].append(f"ThinkingRecorder: {str(e)}")
                
            try:
                signal_stats = self.signal_learning.update_accuracy_stats()
                health_status["components"]["signal_learning"] = "healthy"
                health_status["data_integrity"]["signal_data"] = len(signal_stats)
            except Exception as e:
                health_status["components"]["signal_learning"] = "error"
                health_status["errors"].append(f"SignalLearning: {str(e)}")
                
            try:
                risk_report = self.black_swan.generate_risk_report([])
                health_status["components"]["black_swan"] = "healthy"
            except Exception as e:
                health_status["components"]["black_swan"] = "error"
                health_status["errors"].append(f"BlackSwan: {str(e)}")
                
            try:
                current_weights = self.prompt_evolution.current_weights
                health_status["components"]["prompt_evolution"] = "healthy"
                health_status["data_integrity"]["weights_count"] = len(current_weights)
            except Exception as e:
                health_status["components"]["prompt_evolution"] = "error"
                health_status["errors"].append(f"PromptEvolution: {str(e)}")
                
            try:
                metrics = self.decision_tracker.get_performance_metrics(7)
                health_status["components"]["decision_tracker"] = "healthy"
                health_status["data_integrity"]["decisions_count"] = metrics.get("total_decisions", 0)
            except Exception as e:
                health_status["components"]["decision_tracker"] = "error"
                health_status["errors"].append(f"DecisionTracker: {str(e)}")
                
            # 判断整体状态
            if health_status["errors"]:
                health_status["overall_status"] = "error"
            elif len([c for c in health_status["components"].values() if c == "healthy"]) < 5:
                health_status["overall_status"] = "warning"
                
            return health_status
            
        except Exception as e:
            logger.error(f"❌ 系统健康检查错误: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "critical_error",
                "error": str(e)
            }


async def run_comprehensive_test():
    """运行全面测试"""
    logger.info("🔬 开始运行Window 9全面测试...")
    
    try:
        # 初始化学习系统
        learning_system = Window9Learning()
        
        # 系统健康检查
        health_check = learning_system.system_health_check()
        logger.info(f"🏥 系统健康状态: {health_check['overall_status']}")
        
        if health_check["errors"]:
            logger.error("❌ 系统健康检查发现错误:")
            for error in health_check["errors"]:
                logger.error(f"   - {error}")
            return False
            
        # 测试1: AI思考过程记录
        logger.info("🧠 测试1: AI思考过程记录")
        thinking_chain = [
            {"step": 1, "action": "collect", "data": "收集BTC市场数据", "sources": ["Binance"]},
            {"step": 2, "action": "analyze", "pattern": "发现突破形态", "confidence": 0.75},
            {"step": 3, "action": "assess", "risk": "中等风险", "reward": "高收益潜力"},
            {"step": 4, "action": "decide", "decision": "做多", "confidence": 0.85}
        ]
        
        decision_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result1 = learning_system.process_ai_thinking(decision_id, thinking_chain)
        
        if not result1["success"]:
            logger.error(f"❌ 测试1失败: {result1['error']}")
            return False
        logger.info("✅ 测试1通过: AI思考过程记录")
        
        # 测试2: 外部信号处理
        logger.info("📡 测试2: 外部信号处理")
        signal_data = {
            "source": "ValueScan.io",
            "type": "OPPORTUNITY",
            "prediction": {"direction": "UP", "target": 50000, "probability": 0.7},
            "confidence": 0.7,
            "symbol": "BTC/USDT",
            "timeframe": "4h"
        }
        
        result2 = learning_system.process_external_signal(signal_data)
        
        if not result2["success"]:
            logger.error(f"❌ 测试2失败: {result2['error']}")
            return False
        logger.info("✅ 测试2通过: 外部信号处理")
        
        # 测试3: 黑天鹅风险检查
        logger.info("🦢 测试3: 黑天鹅风险检查")
        current_signals = [
            "大型交易所资金流出",
            "监管政策不确定性",
            "市场恐慌情绪上升"
        ]
        
        result3 = learning_system.check_black_swan_risk(current_signals)
        
        if not result3["success"]:
            logger.error(f"❌ 测试3失败: {result3['error']}")
            return False
        logger.info(f"✅ 测试3通过: 黑天鹅风险检查 - 风险级别: {result3['risk_level']}")
        
        # 测试4: 策略权重进化
        logger.info("🧬 测试4: 策略权重进化")
        performance_data = {
            "trend_following": {"success_rate": 0.78, "sample_count": 25},
            "mean_reversion": {"success_rate": 0.42, "sample_count": 18},
            "news_impact": {"success_rate": 0.65, "sample_count": 12}
        }
        
        result4 = learning_system.evolve_strategy_weights(performance_data)
        
        if not result4["success"]:
            logger.error(f"❌ 测试4失败: {result4['error']}")
            return False
        logger.info(f"✅ 测试4通过: 策略权重进化 - 调整了{result4['adjustments_count']}个策略")
        
        # 测试5: 决策记录和更新
        logger.info("📝 测试5: 决策记录和更新")
        decision_data = {
            "symbol": "BTC/USDT",
            "action": "BUY",
            "confidence": 0.85,
            "position_size": 0.1,
            "entry_price": 45000,
            "stop_loss": 43000,
            "take_profit": 48000,
            "reasoning": {"technical": "突破关键阻力", "sentiment": "积极"}
        }
        
        result5a = learning_system.record_decision(decision_data)
        
        if not result5a["success"]:
            logger.error(f"❌ 测试5a失败: {result5a['error']}")
            return False
            
        # 更新决策结果
        result_data = {
            "result": "success",
            "exit_price": 47000,
            "exit_time": datetime.now().isoformat()
        }
        
        result5b = learning_system.update_decision_result(result5a["decision_id"], result_data)
        
        if not result5b["success"]:
            logger.error(f"❌ 测试5b失败: {result5b['error']}")
            return False
        logger.info(f"✅ 测试5通过: 决策记录和更新 - PnL: {result5b['pnl']:.2%}")
        
        # 测试6: 综合报告生成
        logger.info("📊 测试6: 综合报告生成")
        result6 = learning_system.generate_comprehensive_report()
        
        if not result6["success"]:
            logger.error(f"❌ 测试6失败: {result6['error']}")
            return False
        logger.info("✅ 测试6通过: 综合报告生成")
        
        # 最终系统健康检查
        final_health = learning_system.system_health_check()
        logger.info(f"🏥 最终系统状态: {final_health['overall_status']}")
        
        if final_health["errors"]:
            logger.warning("⚠️ 测试完成后发现系统警告:")
            for error in final_health["errors"]:
                logger.warning(f"   - {error}")
                
        logger.info("🎉 Window 9全面测试完成 - 所有测试通过!")
        
        # 输出测试总结
        print("\n" + "="*60)
        print("Window 9学习工具测试总结")
        print("="*60)
        print(f"✅ AI思考过程记录: 通过")
        print(f"✅ 外部信号处理: 通过") 
        print(f"✅ 黑天鹅风险检查: 通过 (风险级别: {result3['risk_level']})")
        print(f"✅ 策略权重进化: 通过 (调整{result4['adjustments_count']}个策略)")
        print(f"✅ 决策记录和更新: 通过 (PnL: {result5b['pnl']:.2%})")
        print(f"✅ 综合报告生成: 通过")
        print(f"🏥 系统整体状态: {final_health['overall_status']}")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 全面测试执行失败: {e}")
        logger.error(traceback.format_exc())
        return False


async def main():
    """主程序入口"""
    try:
        logger.info("🚀 启动Window 9学习系统测试...")
        
        # 运行全面测试
        test_result = await run_comprehensive_test()
        
        if test_result:
            logger.info("✅ Window 9学习系统测试成功完成")
            return {"success": True, "message": "所有测试通过"}
        else:
            logger.error("❌ Window 9学习系统测试失败")
            return {"success": False, "message": "测试失败"}
            
    except Exception as e:
        logger.error(f"❌ 主程序执行错误: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 运行主程序
    result = asyncio.run(main())
    
    print(f"\n🏁 程序执行完成")
    print(f"结果: {'成功' if result.get('success') else '失败'}")
    if 'message' in result:
        print(f"信息: {result['message']}")
    if 'error' in result:
        print(f"错误: {result['error']}")
        
    # 退出码
    sys.exit(0 if result.get('success') else 1)