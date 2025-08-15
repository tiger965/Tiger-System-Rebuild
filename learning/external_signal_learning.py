"""
外部AI信号准确率学习工具 - Window 9组件
学习外部AI信号的准确率，特别是ValueScan.io
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import numpy as np


class ExternalSignalLearning:
    """学习外部AI信号的准确率，特别是ValueScan.io"""
    
    def __init__(self, base_path: str = "learning_data"):
        """
        初始化外部信号学习器
        
        Args:
            base_path: 学习数据存储基础路径
        """
        self.base_path = Path(base_path)
        self.signals_path = self.base_path / "signals"
        self.signals_path.mkdir(parents=True, exist_ok=True)
        
        # 信号追踪数据库
        self.tracking_db_path = self.signals_path / "tracking.json"
        self.accuracy_stats_path = self.signals_path / "accuracy_stats.json"
        
        # 加载现有数据
        self.tracking_data = self._load_tracking_data()
        self.accuracy_stats = self._load_accuracy_stats()
        
        # 初始化权重建议
        self.weight_suggestions = {
            "ValueScan.io": 0.3,  # 初始权重
            "TradingView": 0.4,
            "CryptoQuant": 0.3,
            "Glassnode": 0.35,
            "IntoTheBlock": 0.3
        }
        
    def _load_tracking_data(self) -> Dict:
        """加载追踪数据"""
        if self.tracking_db_path.exists():
            with open(self.tracking_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def _load_accuracy_stats(self) -> Dict:
        """加载准确率统计"""
        if self.accuracy_stats_path.exists():
            with open(self.accuracy_stats_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._init_accuracy_stats()
        
    def _init_accuracy_stats(self) -> Dict:
        """初始化准确率统计"""
        return {
            "ValueScan.io": {
                "total_signals": 0,
                "correct": 0,
                "incorrect": 0,
                "pending": 0,
                "accuracy": 0.0,
                "weight_suggestion": 0.3,
                "signal_types": {
                    "HIGH_RISK": {"total": 0, "correct": 0},
                    "OPPORTUNITY": {"total": 0, "correct": 0},
                    "NEUTRAL": {"total": 0, "correct": 0}
                },
                "performance_history": []
            },
            "TradingView": {
                "total_signals": 0,
                "correct": 0,
                "incorrect": 0,
                "pending": 0,
                "accuracy": 0.0,
                "weight_suggestion": 0.4,
                "signal_types": {},
                "performance_history": []
            }
        }
        
    def track_signal(self, signal: Dict) -> str:
        """
        追踪外部信号
        
        Args:
            signal: 信号数据，包含source, type, prediction等
            
        Returns:
            信号追踪ID
        """
        signal_id = f"{signal.get('source', 'unknown')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.tracking_data)}"
        
        tracking_record = {
            "signal_id": signal_id,
            "source": signal.get('source', 'unknown'),
            "signal_type": signal.get('type', 'UNKNOWN'),
            "prediction": signal.get('prediction'),
            "confidence": signal.get('confidence', 0.5),
            "timestamp": datetime.now().isoformat(),
            "symbol": signal.get('symbol', ''),
            "timeframe": signal.get('timeframe', '1h'),
            "actual_outcome": None,
            "accuracy": None,
            "time_to_verify": None,
            "status": "pending",  # pending, correct, incorrect
            "metadata": signal.get('metadata', {})
        }
        
        # 保存追踪记录
        self.tracking_data[signal_id] = tracking_record
        self._save_tracking_data()
        
        # 更新统计
        source = signal.get('source', 'unknown')
        if source in self.accuracy_stats:
            self.accuracy_stats[source]["total_signals"] += 1
            self.accuracy_stats[source]["pending"] += 1
            
            # 更新信号类型统计
            signal_type = signal.get('type', 'UNKNOWN')
            if signal_type not in self.accuracy_stats[source]["signal_types"]:
                self.accuracy_stats[source]["signal_types"][signal_type] = {"total": 0, "correct": 0}
            self.accuracy_stats[source]["signal_types"][signal_type]["total"] += 1
            
        self._save_accuracy_stats()
        
        return signal_id
        
    def update_signal_outcome(self, signal_id: str, outcome: Dict) -> Dict:
        """
        更新信号结果
        
        Args:
            signal_id: 信号ID
            outcome: 实际结果数据
            
        Returns:
            更新后的准确率信息
        """
        if signal_id not in self.tracking_data:
            return {"error": f"Signal {signal_id} not found"}
            
        record = self.tracking_data[signal_id]
        
        # 更新结果
        record["actual_outcome"] = outcome
        record["time_to_verify"] = (datetime.now() - datetime.fromisoformat(record["timestamp"])).total_seconds() / 3600  # 小时
        
        # 判断准确性
        is_correct = self._evaluate_prediction(record["prediction"], outcome)
        record["status"] = "correct" if is_correct else "incorrect"
        record["accuracy"] = 1.0 if is_correct else 0.0
        
        # 保存更新
        self._save_tracking_data()
        
        # 更新统计
        source = record["source"]
        if source in self.accuracy_stats:
            stats = self.accuracy_stats[source]
            stats["pending"] -= 1
            
            if is_correct:
                stats["correct"] += 1
            else:
                stats["incorrect"] += 1
                
            # 更新信号类型准确率
            signal_type = record["signal_type"]
            if signal_type in stats["signal_types"] and is_correct:
                stats["signal_types"][signal_type]["correct"] += 1
                
            # 计算总体准确率
            if stats["correct"] + stats["incorrect"] > 0:
                stats["accuracy"] = stats["correct"] / (stats["correct"] + stats["incorrect"])
                
            # 更新权重建议
            stats["weight_suggestion"] = self._calculate_weight_suggestion(stats["accuracy"])
            
            # 记录历史表现
            stats["performance_history"].append({
                "date": datetime.now().isoformat(),
                "accuracy": stats["accuracy"],
                "total_evaluated": stats["correct"] + stats["incorrect"]
            })
            
        self._save_accuracy_stats()
        
        return {
            "signal_id": signal_id,
            "is_correct": is_correct,
            "source_accuracy": self.accuracy_stats.get(source, {}).get("accuracy", 0),
            "weight_suggestion": self.accuracy_stats.get(source, {}).get("weight_suggestion", 0.3)
        }
        
    def _evaluate_prediction(self, prediction: Dict, outcome: Dict) -> bool:
        """
        评估预测准确性
        
        Args:
            prediction: 预测内容
            outcome: 实际结果
            
        Returns:
            是否准确
        """
        if not prediction or not outcome:
            return False
            
        # 价格预测评估
        if "price_target" in prediction and "actual_price" in outcome:
            predicted_price = prediction["price_target"]
            actual_price = outcome["actual_price"]
            
            # 允许2%的误差
            tolerance = 0.02
            if abs(predicted_price - actual_price) / predicted_price <= tolerance:
                return True
                
        # 方向预测评估
        if "direction" in prediction and "actual_direction" in outcome:
            return prediction["direction"] == outcome["actual_direction"]
            
        # 风险预警评估
        if "risk_level" in prediction and "actual_risk_realized" in outcome:
            if prediction["risk_level"] == "HIGH" and outcome["actual_risk_realized"]:
                return True
            elif prediction["risk_level"] == "LOW" and not outcome["actual_risk_realized"]:
                return True
                
        return False
        
    def _calculate_weight_suggestion(self, accuracy: float) -> float:
        """
        根据准确率计算权重建议
        
        Args:
            accuracy: 准确率(0-1)
            
        Returns:
            建议权重(0-1)
        """
        # 基础权重映射
        if accuracy >= 0.8:
            base_weight = 0.7
        elif accuracy >= 0.7:
            base_weight = 0.5
        elif accuracy >= 0.6:
            base_weight = 0.4
        elif accuracy >= 0.5:
            base_weight = 0.3
        else:
            base_weight = 0.2
            
        # 根据样本量调整
        # 样本太少时降低权重
        total_evaluated = self.get_total_evaluated_signals()
        if total_evaluated < 10:
            base_weight *= 0.5
        elif total_evaluated < 30:
            base_weight *= 0.7
        elif total_evaluated < 100:
            base_weight *= 0.9
            
        return min(base_weight, 1.0)
        
    def get_total_evaluated_signals(self) -> int:
        """获取总评估信号数"""
        total = 0
        for source_stats in self.accuracy_stats.values():
            total += source_stats.get("correct", 0) + source_stats.get("incorrect", 0)
        return total
        
    def update_accuracy_stats(self) -> Dict:
        """
        更新所有来源的准确率统计
        
        Returns:
            更新后的统计数据
        """
        # 重新计算所有统计
        for source in self.accuracy_stats:
            stats = self.accuracy_stats[source]
            
            # 计算准确率
            total_evaluated = stats["correct"] + stats["incorrect"]
            if total_evaluated > 0:
                stats["accuracy"] = stats["correct"] / total_evaluated
            else:
                stats["accuracy"] = 0.0
                
            # 更新权重建议
            stats["weight_suggestion"] = self._calculate_weight_suggestion(stats["accuracy"])
            
            # 动态调整权重
            if stats["accuracy"] > 0.75:
                self.increase_signal_weight(source)
            elif stats["accuracy"] < 0.5:
                self.decrease_signal_weight(source)
                
        self._save_accuracy_stats()
        return self.accuracy_stats
        
    def increase_signal_weight(self, source: str, increment: float = 0.05):
        """增加信号源权重"""
        if source in self.weight_suggestions:
            self.weight_suggestions[source] = min(1.0, self.weight_suggestions[source] + increment)
            
    def decrease_signal_weight(self, source: str, decrement: float = 0.05):
        """降低信号源权重"""
        if source in self.weight_suggestions:
            self.weight_suggestions[source] = max(0.1, self.weight_suggestions[source] - decrement)
            
    def get_source_performance(self, source: str) -> Dict:
        """
        获取特定来源的表现
        
        Args:
            source: 信号源名称
            
        Returns:
            表现数据
        """
        if source not in self.accuracy_stats:
            return {"error": f"Source {source} not found"}
            
        stats = self.accuracy_stats[source]
        
        # 计算额外指标
        total_evaluated = stats["correct"] + stats["incorrect"]
        
        performance = {
            "source": source,
            "total_signals": stats["total_signals"],
            "evaluated": total_evaluated,
            "pending": stats["pending"],
            "accuracy": stats["accuracy"],
            "weight_suggestion": stats["weight_suggestion"],
            "signal_types_performance": {}
        }
        
        # 计算每种信号类型的准确率
        for signal_type, type_stats in stats["signal_types"].items():
            if type_stats["total"] > 0:
                type_accuracy = type_stats["correct"] / type_stats["total"] if type_stats["total"] > 0 else 0
                performance["signal_types_performance"][signal_type] = {
                    "total": type_stats["total"],
                    "correct": type_stats["correct"],
                    "accuracy": type_accuracy
                }
                
        return performance
        
    def get_best_performing_sources(self, min_signals: int = 10) -> List[Dict]:
        """
        获取表现最好的信号源
        
        Args:
            min_signals: 最少信号数量要求
            
        Returns:
            排序后的信号源列表
        """
        sources = []
        
        for source, stats in self.accuracy_stats.items():
            total_evaluated = stats["correct"] + stats["incorrect"]
            if total_evaluated >= min_signals:
                sources.append({
                    "source": source,
                    "accuracy": stats["accuracy"],
                    "total_evaluated": total_evaluated,
                    "weight_suggestion": stats["weight_suggestion"]
                })
                
        # 按准确率排序
        sources.sort(key=lambda x: x["accuracy"], reverse=True)
        
        return sources
        
    def generate_learning_report(self) -> Dict:
        """生成学习报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_signals_tracked": len(self.tracking_data),
            "sources_analyzed": len(self.accuracy_stats),
            "best_performing_sources": self.get_best_performing_sources(),
            "weight_recommendations": self.weight_suggestions,
            "insights": []
        }
        
        # 生成洞察
        for source in self.get_best_performing_sources(min_signals=5):
            if source["accuracy"] > 0.7:
                report["insights"].append(f"{source['source']} 表现优异，准确率 {source['accuracy']:.1%}")
            elif source["accuracy"] < 0.4:
                report["insights"].append(f"{source['source']} 表现不佳，建议降低权重")
                
        return report
        
    def _save_tracking_data(self):
        """保存追踪数据"""
        with open(self.tracking_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.tracking_data, f, ensure_ascii=False, indent=2)
            
    def _save_accuracy_stats(self):
        """保存准确率统计"""
        with open(self.accuracy_stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.accuracy_stats, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试代码
    learner = ExternalSignalLearning()
    
    # 模拟追踪信号
    test_signal = {
        "source": "ValueScan.io",
        "type": "HIGH_RISK",
        "prediction": {
            "direction": "DOWN",
            "price_target": 40000,
            "risk_level": "HIGH"
        },
        "confidence": 0.75,
        "symbol": "BTC/USDT",
        "timeframe": "4h"
    }
    
    signal_id = learner.track_signal(test_signal)
    print(f"✅ 信号已追踪: {signal_id}")
    
    # 模拟更新结果
    outcome = {
        "actual_direction": "DOWN",
        "actual_price": 39500,
        "actual_risk_realized": True
    }
    
    result = learner.update_signal_outcome(signal_id, outcome)
    print(f"📊 信号评估结果:")
    print(f"  - 是否准确: {result['is_correct']}")
    print(f"  - 源准确率: {result['source_accuracy']:.1%}")
    print(f"  - 权重建议: {result['weight_suggestion']:.2f}")
    
    # 生成报告
    report = learner.generate_learning_report()
    print(f"\n📈 学习报告:")
    print(f"  - 总追踪信号: {report['total_signals_tracked']}")
    print(f"  - 分析源数量: {report['sources_analyzed']}")
    for insight in report['insights']:
        print(f"  - {insight}")