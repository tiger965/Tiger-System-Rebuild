"""
决策记录和分析工具 - Window 9组件
记录所有交易决策并分析成功/失败模式
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import uuid4
import numpy as np
from collections import defaultdict


class DecisionTracker:
    """记录和分析所有决策"""
    
    def __init__(self, base_path: str = "learning_data"):
        """
        初始化决策追踪器
        
        Args:
            base_path: 学习数据存储基础路径
        """
        self.base_path = Path(base_path)
        self.decisions_path = self.base_path / "decisions"
        self.decisions_path.mkdir(parents=True, exist_ok=True)
        
        # 决策数据库
        self.decisions_db_path = self.decisions_path / "decisions.json"
        self.patterns_db_path = self.decisions_path / "patterns.json"
        
        # 加载现有数据
        self.decisions = self._load_decisions()
        self.patterns = self._load_patterns()
        
        # 分析参数
        self.min_confidence_threshold = 0.6
        self.success_pnl_threshold = 0.02  # 2%收益算成功
        
    def _load_decisions(self) -> Dict:
        """加载决策数据"""
        if self.decisions_db_path.exists():
            with open(self.decisions_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def _load_patterns(self) -> Dict:
        """加载模式数据"""
        if self.patterns_db_path.exists():
            with open(self.patterns_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "success_patterns": [],
            "failure_patterns": [],
            "neutral_patterns": []
        }
        
    def record_decision(self, decision: Dict) -> str:
        """
        记录决策
        
        Args:
            decision: 决策数据
            
        Returns:
            决策ID
        """
        decision_id = decision.get('id', str(uuid4()))
        
        record = {
            "id": decision_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": decision.get('symbol', ''),
            "action": decision.get('action', ''),  # BUY/SELL/HOLD
            "confidence": decision.get('confidence', 0.5),
            "position_size": decision.get('position_size', 0),
            "entry_price": decision.get('entry_price', 0),
            "stop_loss": decision.get('stop_loss', 0),
            "take_profit": decision.get('take_profit', 0),
            "reasoning": decision.get('reasoning', {}),
            "market_conditions": decision.get('market_conditions', {}),
            "signals_used": decision.get('signals_used', []),
            "result": None,  # 后续更新
            "pnl": None,  # 后续更新
            "exit_price": None,  # 后续更新
            "exit_time": None,  # 后续更新
            "duration_hours": None,  # 后续更新
            "status": "pending",  # pending/success/failure/cancelled
            "metadata": decision.get('metadata', {})
        }
        
        # 保存决策
        self.decisions[decision_id] = record
        self._save_decisions()
        
        # 分析决策特征
        self._analyze_decision_features(record)
        
        return decision_id
        
    def update_decision_result(self, decision_id: str, result: Dict) -> Dict:
        """
        更新决策结果
        
        Args:
            decision_id: 决策ID
            result: 结果数据
            
        Returns:
            更新后的决策信息
        """
        if decision_id not in self.decisions:
            return {"error": f"Decision {decision_id} not found"}
            
        decision = self.decisions[decision_id]
        
        # 更新结果
        decision["result"] = result.get('result', 'unknown')
        decision["exit_price"] = result.get('exit_price', 0)
        decision["exit_time"] = result.get('exit_time', datetime.now().isoformat())
        
        # 计算PnL
        if decision["entry_price"] and decision["exit_price"]:
            if decision["action"] == "BUY":
                pnl = (decision["exit_price"] - decision["entry_price"]) / decision["entry_price"]
            elif decision["action"] == "SELL":
                pnl = (decision["entry_price"] - decision["exit_price"]) / decision["entry_price"]
            else:
                pnl = 0
                
            decision["pnl"] = pnl
            
            # 判断成功/失败
            if pnl >= self.success_pnl_threshold:
                decision["status"] = "success"
            elif pnl <= -self.success_pnl_threshold:
                decision["status"] = "failure"
            else:
                decision["status"] = "neutral"
                
        # 计算持续时间
        if decision["exit_time"]:
            entry_time = datetime.fromisoformat(decision["timestamp"])
            exit_time = datetime.fromisoformat(decision["exit_time"])
            duration = (exit_time - entry_time).total_seconds() / 3600
            decision["duration_hours"] = duration
            
        # 保存更新
        self._save_decisions()
        
        # 更新模式分析
        self._update_patterns(decision)
        
        return decision
        
    def _analyze_decision_features(self, decision: Dict):
        """分析决策特征"""
        features = {
            "confidence_level": self._categorize_confidence(decision["confidence"]),
            "market_condition": decision.get("market_conditions", {}).get("trend", "unknown"),
            "volatility": decision.get("market_conditions", {}).get("volatility", "normal"),
            "volume": decision.get("market_conditions", {}).get("volume", "average"),
            "time_of_day": self._get_time_category(decision["timestamp"]),
            "signals_count": len(decision.get("signals_used", [])),
            "has_stop_loss": bool(decision.get("stop_loss")),
            "has_take_profit": bool(decision.get("take_profit"))
        }
        
        decision["features"] = features
        
    def _categorize_confidence(self, confidence: float) -> str:
        """分类信心度"""
        if confidence >= 0.8:
            return "very_high"
        elif confidence >= 0.6:
            return "high"
        elif confidence >= 0.4:
            return "medium"
        else:
            return "low"
            
    def _get_time_category(self, timestamp: str) -> str:
        """获取时间分类"""
        dt = datetime.fromisoformat(timestamp)
        hour = dt.hour
        
        if 0 <= hour < 6:
            return "asia_night"
        elif 6 <= hour < 12:
            return "asia_morning"
        elif 12 <= hour < 18:
            return "europe_active"
        else:
            return "us_active"
            
    def _update_patterns(self, decision: Dict):
        """更新模式库"""
        if decision["status"] == "success":
            self._extract_success_pattern(decision)
        elif decision["status"] == "failure":
            self._extract_failure_pattern(decision)
            
        self._save_patterns()
        
    def _extract_success_pattern(self, decision: Dict):
        """提取成功模式"""
        pattern = {
            "timestamp": datetime.now().isoformat(),
            "confidence": decision["confidence"],
            "pnl": decision["pnl"],
            "duration_hours": decision.get("duration_hours", 0),
            "features": decision.get("features", {}),
            "market_conditions": decision.get("market_conditions", {}),
            "signals_used": decision.get("signals_used", []),
            "key_factors": self._identify_key_factors(decision)
        }
        
        self.patterns["success_patterns"].append(pattern)
        
        # 只保留最近的100个模式
        if len(self.patterns["success_patterns"]) > 100:
            self.patterns["success_patterns"] = self.patterns["success_patterns"][-100:]
            
    def _extract_failure_pattern(self, decision: Dict):
        """提取失败模式"""
        pattern = {
            "timestamp": datetime.now().isoformat(),
            "confidence": decision["confidence"],
            "pnl": decision["pnl"],
            "duration_hours": decision.get("duration_hours", 0),
            "features": decision.get("features", {}),
            "market_conditions": decision.get("market_conditions", {}),
            "signals_used": decision.get("signals_used", []),
            "failure_reasons": self._identify_failure_reasons(decision)
        }
        
        self.patterns["failure_patterns"].append(pattern)
        
        # 只保留最近的100个模式
        if len(self.patterns["failure_patterns"]) > 100:
            self.patterns["failure_patterns"] = self.patterns["failure_patterns"][-100:]
            
    def _identify_key_factors(self, decision: Dict) -> List[str]:
        """识别关键成功因素"""
        factors = []
        
        if decision["confidence"] >= 0.8:
            factors.append("高信心度决策")
            
        if decision.get("features", {}).get("signals_count", 0) >= 3:
            factors.append("多信号共振")
            
        market_conditions = decision.get("market_conditions", {})
        if market_conditions.get("trend") == "strong_up":
            factors.append("强势上涨趋势")
            
        if market_conditions.get("volume") == "high":
            factors.append("高成交量支撑")
            
        return factors
        
    def _identify_failure_reasons(self, decision: Dict) -> List[str]:
        """识别失败原因"""
        reasons = []
        
        if decision["confidence"] < 0.6:
            reasons.append("信心度不足")
            
        if not decision.get("stop_loss"):
            reasons.append("未设置止损")
            
        market_conditions = decision.get("market_conditions", {})
        if market_conditions.get("volatility") == "extreme":
            reasons.append("极端波动市场")
            
        if decision.get("features", {}).get("time_of_day") == "asia_night":
            reasons.append("低流动性时段")
            
        return reasons
        
    def analyze_success_patterns(self) -> Dict:
        """分析成功模式"""
        if not self.patterns["success_patterns"]:
            return {"message": "暂无成功模式数据"}
            
        successful_decisions = [d for d in self.decisions.values() if d["status"] == "success"]
        
        analysis = {
            "total_successes": len(successful_decisions),
            "average_pnl": 0,
            "average_confidence": 0,
            "average_duration": 0,
            "best_time": "",
            "best_confidence_range": "",
            "best_market_condition": "",
            "best_signal_combination": [],
            "common_features": {}
        }
        
        if not successful_decisions:
            return analysis
            
        # 计算平均值
        total_pnl = sum(d.get("pnl", 0) for d in successful_decisions)
        total_confidence = sum(d.get("confidence", 0) for d in successful_decisions)
        total_duration = sum(d.get("duration_hours", 0) for d in successful_decisions)
        
        analysis["average_pnl"] = total_pnl / len(successful_decisions)
        analysis["average_confidence"] = total_confidence / len(successful_decisions)
        analysis["average_duration"] = total_duration / len(successful_decisions)
        
        # 分析最佳时间
        time_stats = defaultdict(list)
        for decision in successful_decisions:
            time_cat = decision.get("features", {}).get("time_of_day", "unknown")
            time_stats[time_cat].append(decision.get("pnl", 0))
            
        best_time = max(time_stats.items(), key=lambda x: np.mean(x[1]) if x[1] else 0)
        analysis["best_time"] = best_time[0]
        
        # 分析最佳信心度范围
        if analysis["average_confidence"] >= 0.8:
            analysis["best_confidence_range"] = ">0.8"
        elif analysis["average_confidence"] >= 0.6:
            analysis["best_confidence_range"] = "0.6-0.8"
        else:
            analysis["best_confidence_range"] = "<0.6"
            
        # 分析市场条件
        market_stats = defaultdict(int)
        for decision in successful_decisions:
            condition = decision.get("market_conditions", {}).get("trend", "unknown")
            market_stats[condition] += 1
            
        if market_stats:
            analysis["best_market_condition"] = max(market_stats.items(), key=lambda x: x[1])[0]
            
        # 分析信号组合
        signal_combinations = defaultdict(int)
        for decision in successful_decisions:
            signals = tuple(sorted(decision.get("signals_used", [])))
            if signals:
                signal_combinations[signals] += 1
                
        if signal_combinations:
            best_combo = max(signal_combinations.items(), key=lambda x: x[1])[0]
            analysis["best_signal_combination"] = list(best_combo)
            
        return analysis
        
    def analyze_failure_patterns(self) -> Dict:
        """分析失败模式"""
        if not self.patterns["failure_patterns"]:
            return {"message": "暂无失败模式数据"}
            
        failed_decisions = [d for d in self.decisions.values() if d["status"] == "failure"]
        
        analysis = {
            "total_failures": len(failed_decisions),
            "average_loss": 0,
            "common_mistakes": [],
            "worst_time": "",
            "dangerous_signals": [],
            "risk_factors": {}
        }
        
        if not failed_decisions:
            return analysis
            
        # 计算平均损失
        total_loss = sum(d.get("pnl", 0) for d in failed_decisions)
        analysis["average_loss"] = total_loss / len(failed_decisions)
        
        # 统计常见错误
        mistake_counts = defaultdict(int)
        for pattern in self.patterns["failure_patterns"]:
            for reason in pattern.get("failure_reasons", []):
                mistake_counts[reason] += 1
                
        analysis["common_mistakes"] = [
            mistake for mistake, count in sorted(mistake_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # 分析最差时间
        time_stats = defaultdict(list)
        for decision in failed_decisions:
            time_cat = decision.get("features", {}).get("time_of_day", "unknown")
            time_stats[time_cat].append(decision.get("pnl", 0))
            
        if time_stats:
            worst_time = min(time_stats.items(), key=lambda x: np.mean(x[1]) if x[1] else 0)
            analysis["worst_time"] = worst_time[0]
            
        # 识别危险信号
        signal_failure_rates = defaultdict(lambda: {"total": 0, "failures": 0})
        
        for decision in self.decisions.values():
            for signal in decision.get("signals_used", []):
                signal_failure_rates[signal]["total"] += 1
                if decision["status"] == "failure":
                    signal_failure_rates[signal]["failures"] += 1
                    
        dangerous_signals = []
        for signal, stats in signal_failure_rates.items():
            if stats["total"] >= 5:  # 至少5次使用
                failure_rate = stats["failures"] / stats["total"]
                if failure_rate > 0.6:
                    dangerous_signals.append({
                        "signal": signal,
                        "failure_rate": failure_rate
                    })
                    
        analysis["dangerous_signals"] = sorted(dangerous_signals, key=lambda x: x["failure_rate"], reverse=True)[:5]
        
        return analysis
        
    def get_performance_metrics(self, period_days: int = 30) -> Dict:
        """
        获取性能指标
        
        Args:
            period_days: 统计周期（天）
            
        Returns:
            性能指标
        """
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        recent_decisions = [
            d for d in self.decisions.values()
            if datetime.fromisoformat(d["timestamp"]) >= cutoff_date
        ]
        
        if not recent_decisions:
            return {"message": f"最近{period_days}天无决策记录"}
            
        metrics = {
            "period_days": period_days,
            "total_decisions": len(recent_decisions),
            "success_count": 0,
            "failure_count": 0,
            "neutral_count": 0,
            "success_rate": 0,
            "total_pnl": 0,
            "average_pnl": 0,
            "best_trade": None,
            "worst_trade": None,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "win_loss_ratio": 0,
            "average_win": 0,
            "average_loss": 0
        }
        
        # 统计成功/失败
        pnls = []
        wins = []
        losses = []
        
        for decision in recent_decisions:
            status = decision.get("status", "pending")
            if status == "success":
                metrics["success_count"] += 1
                if decision.get("pnl"):
                    wins.append(decision["pnl"])
            elif status == "failure":
                metrics["failure_count"] += 1
                if decision.get("pnl"):
                    losses.append(decision["pnl"])
            else:
                metrics["neutral_count"] += 1
                
            if decision.get("pnl"):
                pnls.append(decision["pnl"])
                
        # 计算指标
        if pnls:
            metrics["total_pnl"] = sum(pnls)
            metrics["average_pnl"] = np.mean(pnls)
            
            # 最佳/最差交易
            best_pnl = max(pnls)
            worst_pnl = min(pnls)
            
            for decision in recent_decisions:
                if decision.get("pnl") == best_pnl:
                    metrics["best_trade"] = {
                        "id": decision["id"],
                        "symbol": decision["symbol"],
                        "pnl": best_pnl,
                        "confidence": decision["confidence"]
                    }
                if decision.get("pnl") == worst_pnl:
                    metrics["worst_trade"] = {
                        "id": decision["id"],
                        "symbol": decision["symbol"],
                        "pnl": worst_pnl,
                        "confidence": decision["confidence"]
                    }
                    
            # 计算夏普比率
            if len(pnls) > 1:
                returns_std = np.std(pnls)
                if returns_std > 0:
                    metrics["sharpe_ratio"] = np.mean(pnls) / returns_std
                    
            # 计算最大回撤
            cumulative_returns = np.cumsum(pnls)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = cumulative_returns - running_max
            metrics["max_drawdown"] = np.min(drawdown) if len(drawdown) > 0 else 0
            
        # 成功率
        total_evaluated = metrics["success_count"] + metrics["failure_count"]
        if total_evaluated > 0:
            metrics["success_rate"] = metrics["success_count"] / total_evaluated
            
        # 盈亏比
        if wins:
            metrics["average_win"] = np.mean(wins)
        if losses:
            metrics["average_loss"] = np.mean(losses)
            
        if metrics["average_loss"] != 0:
            metrics["win_loss_ratio"] = abs(metrics["average_win"] / metrics["average_loss"])
            
        return metrics
        
    def _save_decisions(self):
        """保存决策数据"""
        with open(self.decisions_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.decisions, f, ensure_ascii=False, indent=2)
            
    def _save_patterns(self):
        """保存模式数据"""
        with open(self.patterns_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试代码
    tracker = DecisionTracker()
    
    # 模拟记录决策
    test_decision = {
        "symbol": "BTC/USDT",
        "action": "BUY",
        "confidence": 0.85,
        "position_size": 0.1,
        "entry_price": 45000,
        "stop_loss": 43000,
        "take_profit": 48000,
        "reasoning": {
            "technical": "突破关键阻力位",
            "volume": "成交量放大",
            "sentiment": "市场情绪积极"
        },
        "market_conditions": {
            "trend": "strong_up",
            "volatility": "normal",
            "volume": "high"
        },
        "signals_used": ["技术突破", "量价配合", "情绪指标"]
    }
    
    decision_id = tracker.record_decision(test_decision)
    print(f"✅ 决策已记录: {decision_id}")
    
    # 模拟更新结果
    result = {
        "result": "success",
        "exit_price": 47500,
        "exit_time": datetime.now().isoformat()
    }
    
    updated_decision = tracker.update_decision_result(decision_id, result)
    print(f"\n📊 决策结果:")
    print(f"  - 状态: {updated_decision['status']}")
    print(f"  - 盈亏: {updated_decision.get('pnl', 0):.2%}")
    print(f"  - 持续时间: {updated_decision.get('duration_hours', 0):.1f} 小时")
    
    # 分析成功模式
    success_analysis = tracker.analyze_success_patterns()
    print(f"\n✨ 成功模式分析:")
    print(f"  - 总成功次数: {success_analysis.get('total_successes', 0)}")
    print(f"  - 平均收益: {success_analysis.get('average_pnl', 0):.2%}")
    print(f"  - 平均信心度: {success_analysis.get('average_confidence', 0):.2f}")
    print(f"  - 最佳时段: {success_analysis.get('best_time', 'N/A')}")
    
    # 获取性能指标
    metrics = tracker.get_performance_metrics(30)
    print(f"\n📈 最近30天性能指标:")
    print(f"  - 总决策数: {metrics['total_decisions']}")
    print(f"  - 成功率: {metrics['success_rate']:.1%}")
    print(f"  - 总盈亏: {metrics['total_pnl']:.2%}")
    print(f"  - 夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"  - 最大回撤: {metrics['max_drawdown']:.2%}")