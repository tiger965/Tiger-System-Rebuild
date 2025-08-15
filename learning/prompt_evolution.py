"""
提示词权重进化工具 - Window 9组件
自动进化提示词权重，优化AI决策质量
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np


class PromptEvolution:
    """自动进化提示词权重"""
    
    def __init__(self, base_path: str = "learning_data"):
        """
        初始化提示词进化器
        
        Args:
            base_path: 学习数据存储基础路径
        """
        self.base_path = Path(base_path)
        self.weights_path = self.base_path / "weights"
        self.weights_path.mkdir(parents=True, exist_ok=True)
        
        # 当前权重配置
        self.current_weights = self._load_or_init_weights()
        
        # 性能历史记录
        self.performance_history_path = self.weights_path / "performance_history.json"
        self.performance_history = self._load_performance_history()
        
        # 基础提示词模板路径
        self.base_prompt_path = self.base_path / "prompts" / "base_prompt.txt"
        self.base_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 进化参数
        self.evolution_rate = 0.05  # 每次调整的幅度
        self.min_samples = 10  # 最少样本数才进行调整
        self.success_threshold = 0.7  # 成功率阈值
        self.failure_threshold = 0.4  # 失败率阈值
        
    def _load_or_init_weights(self) -> Dict:
        """加载或初始化权重"""
        weights_file = self.weights_path / "current_weights.json"
        
        if weights_file.exists():
            with open(weights_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始权重配置
            initial_weights = {
                "trend_following": 0.7,
                "mean_reversion": 0.3,
                "news_impact": 0.5,
                "whale_movement": 0.8,
                "external_ai_signal": 0.3,
                "technical_analysis": 0.6,
                "on_chain_data": 0.7,
                "sentiment_analysis": 0.4,
                "volume_analysis": 0.5,
                "volatility_factor": 0.6,
                "risk_aversion": 0.5,
                "time_horizon": 0.5,  # 0=短期, 1=长期
                "market_regime": {
                    "bull": 0.7,
                    "bear": 0.3,
                    "sideways": 0.5
                }
            }
            
            # 保存初始权重
            self._save_weights(initial_weights)
            return initial_weights
            
    def _load_performance_history(self) -> List:
        """加载性能历史"""
        if self.performance_history_path.exists():
            with open(self.performance_history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
        
    def evolve_weights(self, performance_data: Dict) -> Dict:
        """
        根据表现自动调整权重
        
        Args:
            performance_data: 各策略的表现数据
            
        Returns:
            调整后的权重
        """
        adjustments = {}
        
        for strategy, performance in performance_data.items():
            if strategy not in self.current_weights:
                continue
                
            # 需要足够的样本才进行调整
            if performance.get('sample_count', 0) < self.min_samples:
                continue
                
            success_rate = performance.get('success_rate', 0.5)
            current_weight = self.current_weights[strategy]
            
            # 根据成功率调整权重
            if success_rate > self.success_threshold:
                # 表现好，增加权重
                new_weight = min(1.0, current_weight + self.evolution_rate)
                adjustments[strategy] = {
                    "old": current_weight,
                    "new": new_weight,
                    "reason": f"高成功率 {success_rate:.1%}"
                }
                self.current_weights[strategy] = new_weight
                
            elif success_rate < self.failure_threshold:
                # 表现差，降低权重
                new_weight = max(0.1, current_weight - self.evolution_rate)
                adjustments[strategy] = {
                    "old": current_weight,
                    "new": new_weight,
                    "reason": f"低成功率 {success_rate:.1%}"
                }
                self.current_weights[strategy] = new_weight
                
        # 记录调整历史
        if adjustments:
            self._record_evolution(adjustments, performance_data)
            
        # 保存新权重
        self._save_weights(self.current_weights)
        
        return {
            "new_weights": self.current_weights,
            "adjustments": adjustments
        }
        
    def _record_evolution(self, adjustments: Dict, performance_data: Dict):
        """记录进化历史"""
        evolution_record = {
            "timestamp": datetime.now().isoformat(),
            "adjustments": adjustments,
            "performance_basis": performance_data,
            "weights_snapshot": self.current_weights.copy()
        }
        
        self.performance_history.append(evolution_record)
        
        # 只保留最近100条记录
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
            
        # 保存历史
        with open(self.performance_history_path, 'w', encoding='utf-8') as f:
            json.dump(self.performance_history, f, ensure_ascii=False, indent=2)
            
    def generate_evolved_prompt(self) -> str:
        """
        生成进化后的提示词
        
        Returns:
            包含最新权重的提示词
        """
        # 加载基础提示词
        base_prompt = self.load_base_prompt()
        
        # 注入最新权重
        evolved_prompt = base_prompt + f"""

## 当前策略权重配置（基于机器学习优化）

### 核心策略权重
- 趋势跟踪权重: {self.current_weights['trend_following']:.2f}
- 均值回归权重: {self.current_weights['mean_reversion']:.2f}
- 新闻影响权重: {self.current_weights['news_impact']:.2f}
- 巨鲸动向权重: {self.current_weights['whale_movement']:.2f}
- 外部AI信号权重: {self.current_weights['external_ai_signal']:.2f}

### 分析维度权重
- 技术分析: {self.current_weights['technical_analysis']:.2f}
- 链上数据: {self.current_weights['on_chain_data']:.2f}
- 情绪分析: {self.current_weights['sentiment_analysis']:.2f}
- 成交量分析: {self.current_weights['volume_analysis']:.2f}
- 波动率因子: {self.current_weights['volatility_factor']:.2f}

### 风险与时间偏好
- 风险厌恶程度: {self.current_weights['risk_aversion']:.2f}
- 时间视野: {self.current_weights['time_horizon']:.2f} (0=短期, 1=长期)

### 市场状态权重
- 牛市权重: {self.current_weights['market_regime']['bull']:.2f}
- 熊市权重: {self.current_weights['market_regime']['bear']:.2f}
- 横盘权重: {self.current_weights['market_regime']['sideways']:.2f}

请根据这些权重调整你的决策偏好。权重越高的策略应该在决策中占据更重要的地位。

## 决策指导原则
1. 当多个高权重策略产生一致信号时，提高决策信心度
2. 低权重策略仅作为辅助参考，不应主导决策
3. 在不同市场状态下，动态调整策略组合
4. 持续学习和优化，根据实际表现调整权重
"""
        
        return evolved_prompt
        
    def load_base_prompt(self) -> str:
        """加载基础提示词"""
        if self.base_prompt_path.exists():
            with open(self.base_prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 创建默认基础提示词
            default_prompt = """# AI交易决策系统提示词

## 角色定义
你是一个专业的加密货币交易AI系统，负责分析市场数据并提供交易决策建议。

## 决策流程
1. 收集和整合多维度数据
2. 识别市场异常和机会
3. 评估风险和收益
4. 生成具体交易建议
5. 提供执行计划

## 数据源优先级
- 实时市场数据
- 链上数据分析
- 新闻和社交情绪
- 技术指标信号
- 外部AI预测

## 风险管理原则
- 永远不要忽视风险
- 设置明确的止损点
- 控制仓位大小
- 考虑市场流动性
- 预留应急方案
"""
            # 保存默认提示词
            with open(self.base_prompt_path, 'w', encoding='utf-8') as f:
                f.write(default_prompt)
                
            return default_prompt
            
    def update_base_prompt(self, new_prompt: str):
        """更新基础提示词"""
        with open(self.base_prompt_path, 'w', encoding='utf-8') as f:
            f.write(new_prompt)
            
    def get_weight_recommendations(self, market_condition: str = "normal") -> Dict:
        """
        获取权重建议
        
        Args:
            market_condition: 市场状况(bull/bear/sideways/volatile)
            
        Returns:
            权重建议
        """
        recommendations = {
            "current_weights": self.current_weights.copy(),
            "suggested_adjustments": [],
            "market_specific": {}
        }
        
        # 根据市场状况调整建议
        if market_condition == "bull":
            recommendations["suggested_adjustments"].append({
                "strategy": "trend_following",
                "suggestion": "增加权重到0.8+",
                "reason": "牛市中趋势策略表现最佳"
            })
            recommendations["market_specific"] = {
                "trend_following": 0.85,
                "mean_reversion": 0.15,
                "risk_aversion": 0.3
            }
            
        elif market_condition == "bear":
            recommendations["suggested_adjustments"].append({
                "strategy": "risk_aversion",
                "suggestion": "增加权重到0.8+",
                "reason": "熊市需要更保守的策略"
            })
            recommendations["market_specific"] = {
                "trend_following": 0.3,
                "mean_reversion": 0.5,
                "risk_aversion": 0.8
            }
            
        elif market_condition == "sideways":
            recommendations["suggested_adjustments"].append({
                "strategy": "mean_reversion",
                "suggestion": "增加权重到0.7+",
                "reason": "横盘市场适合均值回归"
            })
            recommendations["market_specific"] = {
                "trend_following": 0.2,
                "mean_reversion": 0.75,
                "volatility_factor": 0.8
            }
            
        elif market_condition == "volatile":
            recommendations["suggested_adjustments"].append({
                "strategy": "volatility_factor",
                "suggestion": "增加权重到0.8+",
                "reason": "高波动需要特殊策略"
            })
            recommendations["market_specific"] = {
                "volatility_factor": 0.85,
                "risk_aversion": 0.7,
                "time_horizon": 0.2  # 短期为主
            }
            
        return recommendations
        
    def analyze_weight_performance(self) -> Dict:
        """分析权重表现"""
        if not self.performance_history:
            return {"message": "暂无历史数据"}
            
        analysis = {
            "total_evolutions": len(self.performance_history),
            "last_evolution": None,
            "weight_trends": {},
            "most_improved": None,
            "most_declined": None
        }
        
        # 最近一次进化
        if self.performance_history:
            analysis["last_evolution"] = self.performance_history[-1]["timestamp"]
            
        # 分析权重趋势
        for strategy in self.current_weights:
            if isinstance(self.current_weights[strategy], (int, float)):
                trend = self._calculate_weight_trend(strategy)
                analysis["weight_trends"][strategy] = trend
                
        # 找出改进最大和下降最大的策略
        if analysis["weight_trends"]:
            sorted_trends = sorted(analysis["weight_trends"].items(), key=lambda x: x[1]["change"])
            
            if sorted_trends:
                analysis["most_declined"] = {
                    "strategy": sorted_trends[0][0],
                    "change": sorted_trends[0][1]["change"]
                }
                analysis["most_improved"] = {
                    "strategy": sorted_trends[-1][0],
                    "change": sorted_trends[-1][1]["change"]
                }
                
        return analysis
        
    def _calculate_weight_trend(self, strategy: str) -> Dict:
        """计算权重趋势"""
        if not self.performance_history:
            return {"initial": self.current_weights.get(strategy, 0), "current": self.current_weights.get(strategy, 0), "change": 0}
            
        # 获取初始权重
        initial_weight = None
        for record in self.performance_history:
            if "weights_snapshot" in record and strategy in record["weights_snapshot"]:
                initial_weight = record["weights_snapshot"][strategy]
                break
                
        if initial_weight is None:
            initial_weight = self.current_weights.get(strategy, 0.5)
            
        current_weight = self.current_weights.get(strategy, 0.5)
        
        return {
            "initial": initial_weight,
            "current": current_weight,
            "change": current_weight - initial_weight
        }
        
    def _save_weights(self, weights: Dict):
        """保存权重"""
        weights_file = self.weights_path / "current_weights.json"
        with open(weights_file, 'w', encoding='utf-8') as f:
            json.dump(weights, f, ensure_ascii=False, indent=2)
            
    def reset_weights(self):
        """重置权重到初始值"""
        self.current_weights = {
            "trend_following": 0.7,
            "mean_reversion": 0.3,
            "news_impact": 0.5,
            "whale_movement": 0.8,
            "external_ai_signal": 0.3,
            "technical_analysis": 0.6,
            "on_chain_data": 0.7,
            "sentiment_analysis": 0.4,
            "volume_analysis": 0.5,
            "volatility_factor": 0.6,
            "risk_aversion": 0.5,
            "time_horizon": 0.5,
            "market_regime": {
                "bull": 0.7,
                "bear": 0.3,
                "sideways": 0.5
            }
        }
        self._save_weights(self.current_weights)
        return self.current_weights


if __name__ == "__main__":
    # 测试代码
    evolver = PromptEvolution()
    
    print("🧬 提示词权重进化系统")
    print(f"\n当前权重配置:")
    for strategy, weight in evolver.current_weights.items():
        if isinstance(weight, (int, float)):
            print(f"  - {strategy}: {weight:.2f}")
            
    # 模拟性能数据
    performance_data = {
        "trend_following": {"success_rate": 0.75, "sample_count": 50},
        "mean_reversion": {"success_rate": 0.35, "sample_count": 30},
        "whale_movement": {"success_rate": 0.82, "sample_count": 25},
        "external_ai_signal": {"success_rate": 0.45, "sample_count": 15}
    }
    
    print(f"\n📊 模拟性能数据:")
    for strategy, perf in performance_data.items():
        print(f"  - {strategy}: 成功率 {perf['success_rate']:.1%} (样本数: {perf['sample_count']})")
        
    # 进化权重
    result = evolver.evolve_weights(performance_data)
    
    if result["adjustments"]:
        print(f"\n⚡ 权重调整:")
        for strategy, adj in result["adjustments"].items():
            print(f"  - {strategy}: {adj['old']:.2f} -> {adj['new']:.2f} ({adj['reason']})")
    else:
        print(f"\n✅ 权重保持不变")
        
    # 生成进化后的提示词
    evolved_prompt = evolver.generate_evolved_prompt()
    print(f"\n📝 已生成进化后的提示词 (长度: {len(evolved_prompt)} 字符)")
    
    # 获取市场特定建议
    market_recommendations = evolver.get_weight_recommendations("volatile")
    print(f"\n🎯 高波动市场权重建议:")
    for adj in market_recommendations["suggested_adjustments"]:
        print(f"  - {adj['strategy']}: {adj['suggestion']} - {adj['reason']}")