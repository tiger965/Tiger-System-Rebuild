"""
策略优化器
负责优化策略参数、调整权重、进行A/B测试
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from skopt import BayesSearchCV
from skopt.space import Real, Integer, Categorical
import warnings
warnings.filterwarnings('ignore')

from ..config.config import OPTIMIZATION_CONFIG, DATABASE_CONFIG, LOG_DIR
from ..records.trade_recorder import TradeRecorder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'strategy_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """策略优化器"""
    
    def __init__(self, trade_recorder: TradeRecorder):
        self.trade_recorder = trade_recorder
        self.optimization_config = OPTIMIZATION_CONFIG
        
        # 初始化数据库
        self.db_path = DATABASE_CONFIG["patterns"]["path"].parent / "optimizer.db"
        self._init_database()
        
        # 策略权重缓存
        self.strategy_weights = {}
        
        logger.info("StrategyOptimizer initialized")
    
    def _init_database(self):
        """初始化优化器数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 策略权重表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_weights (
                strategy_id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                weight REAL NOT NULL,
                performance_score REAL,
                market_condition TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 参数优化结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                parameters TEXT NOT NULL,
                performance_metrics TEXT NOT NULL,
                optimization_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # A/B测试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                control_strategy TEXT NOT NULL,
                test_strategy TEXT NOT NULL,
                control_performance TEXT,
                test_performance TEXT,
                sample_size INTEGER,
                p_value REAL,
                is_significant BOOLEAN,
                winner TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def evaluate_strategy(self, 
                         strategy_id: str,
                         days: int = 30) -> Dict[str, float]:
        """评估策略表现"""
        # 获取该策略的交易记录
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        # 筛选特定策略的交易（假设交易记录中有strategy_id字段）
        strategy_trades = [t for t in trades if t.get('strategy_id') == strategy_id]
        
        if not strategy_trades:
            logger.warning(f"No trades found for strategy {strategy_id}")
            return {
                "win_rate": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "recovery_factor": 0
            }
        
        # 计算胜率
        wins = sum(1 for t in strategy_trades if t.get('exit_pnl', 0) > 0)
        win_rate = wins / len(strategy_trades)
        
        # 计算盈亏比
        profits = [t['exit_pnl'] for t in strategy_trades if t.get('exit_pnl', 0) > 0]
        losses = [abs(t['exit_pnl']) for t in strategy_trades if t.get('exit_pnl', 0) < 0]
        
        profit_factor = sum(profits) / sum(losses) if losses else float('inf')
        
        # 计算夏普比率
        returns = [t.get('exit_pnl', 0) for t in strategy_trades]
        if len(returns) > 1:
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
        else:
            sharpe_ratio = 0
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(returns)
        
        # 计算恢复系数
        recovery_factor = self._calculate_recovery_factor(returns, max_drawdown)
        
        metrics = {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "recovery_factor": recovery_factor
        }
        
        # 保存评估结果
        self._save_evaluation_metrics(strategy_id, metrics)
        
        return metrics
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """计算夏普比率"""
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        
        if len(excess_returns) < 2:
            return 0
        
        mean_excess_return = np.mean(excess_returns)
        std_excess_return = np.std(excess_returns)
        
        if std_excess_return == 0:
            return 0
        
        # 年化夏普比率（假设每天交易）
        sharpe_ratio = (mean_excess_return / std_excess_return) * np.sqrt(365)
        
        return sharpe_ratio
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """计算最大回撤"""
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / (running_max + 1e-8)
        
        return abs(np.min(drawdown))
    
    def _calculate_recovery_factor(self, returns: List[float], max_drawdown: float) -> float:
        """计算恢复系数"""
        total_profit = sum(returns)
        
        if max_drawdown == 0:
            return float('inf')
        
        return total_profit / max_drawdown
    
    def adjust_weights_performance(self, strategies: List[str], days: int = 30) -> Dict[str, float]:
        """根据表现调整策略权重"""
        weights = {}
        performances = {}
        
        # 评估每个策略
        for strategy_id in strategies:
            metrics = self.evaluate_strategy(strategy_id, days)
            # 综合评分
            score = (
                metrics["win_rate"] * 0.3 +
                min(metrics["profit_factor"] / 3, 1) * 0.3 +
                min(metrics["sharpe_ratio"] / 2, 1) * 0.2 +
                (1 - metrics["max_drawdown"]) * 0.2
            )
            performances[strategy_id] = score
        
        # 归一化权重
        total_score = sum(performances.values())
        if total_score > 0:
            for strategy_id, score in performances.items():
                weights[strategy_id] = score / total_score
        else:
            # 平均分配权重
            for strategy_id in strategies:
                weights[strategy_id] = 1 / len(strategies)
        
        # 保存权重
        for strategy_id, weight in weights.items():
            self._save_strategy_weight(strategy_id, weight, performances[strategy_id])
        
        return weights
    
    def adjust_weights_market_adaptive(self, 
                                      strategies: List[str],
                                      market_condition: str) -> Dict[str, float]:
        """根据市场条件调整权重"""
        weights = {}
        
        # 预定义的市场条件权重配置
        market_weights = {
            "trending": {
                "trend_following": 0.4,
                "momentum": 0.3,
                "mean_reversion": 0.1,
                "arbitrage": 0.2
            },
            "ranging": {
                "trend_following": 0.1,
                "momentum": 0.2,
                "mean_reversion": 0.4,
                "arbitrage": 0.3
            },
            "volatile": {
                "trend_following": 0.2,
                "momentum": 0.2,
                "mean_reversion": 0.2,
                "arbitrage": 0.4
            }
        }
        
        # 获取对应市场条件的权重
        condition_weights = market_weights.get(market_condition, {})
        
        for strategy_id in strategies:
            # 提取策略类型
            strategy_type = self._get_strategy_type(strategy_id)
            weight = condition_weights.get(strategy_type, 1 / len(strategies))
            weights[strategy_id] = weight
        
        # 归一化
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        # 保存权重
        for strategy_id, weight in weights.items():
            self._save_strategy_weight(strategy_id, weight, market_condition=market_condition)
        
        return weights
    
    def _get_strategy_type(self, strategy_id: str) -> str:
        """获取策略类型"""
        # 从策略ID推断类型
        if "trend" in strategy_id.lower():
            return "trend_following"
        elif "momentum" in strategy_id.lower():
            return "momentum"
        elif "mean" in strategy_id.lower() or "reversion" in strategy_id.lower():
            return "mean_reversion"
        elif "arb" in strategy_id.lower():
            return "arbitrage"
        else:
            return "general"
    
    def optimize_parameters_grid(self,
                                strategy_id: str,
                                param_grid: Dict[str, List],
                                scoring_func: callable) -> Dict[str, Any]:
        """网格搜索优化参数"""
        if not self.optimization_config["methods"]["grid_search"]["enabled"]:
            logger.info("Grid search is disabled")
            return {}
        
        logger.info(f"Starting grid search for {strategy_id}")
        
        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_grid)
        
        best_score = float('-inf')
        best_params = {}
        
        for params in param_combinations:
            score = scoring_func(params)
            if score > best_score:
                best_score = score
                best_params = params
        
        # 保存优化结果
        self._save_optimization_result(
            strategy_id,
            best_params,
            {"score": best_score},
            "grid_search"
        )
        
        logger.info(f"Grid search completed. Best params: {best_params}, Score: {best_score}")
        
        return best_params
    
    def optimize_parameters_bayesian(self,
                                   strategy_id: str,
                                   search_space: Dict[str, Any],
                                   scoring_func: callable,
                                   n_calls: int = 50) -> Dict[str, Any]:
        """贝叶斯优化参数"""
        if not self.optimization_config["methods"]["bayesian"]["enabled"]:
            logger.info("Bayesian optimization is disabled")
            return {}
        
        logger.info(f"Starting Bayesian optimization for {strategy_id}")
        
        # 转换搜索空间
        dimensions = []
        param_names = []
        
        for param_name, param_range in search_space.items():
            param_names.append(param_name)
            if isinstance(param_range, tuple) and len(param_range) == 2:
                if isinstance(param_range[0], float):
                    dimensions.append(Real(param_range[0], param_range[1]))
                else:
                    dimensions.append(Integer(param_range[0], param_range[1]))
            elif isinstance(param_range, list):
                dimensions.append(Categorical(param_range))
        
        # 执行优化
        from skopt import gp_minimize
        
        def objective(params):
            param_dict = dict(zip(param_names, params))
            return -scoring_func(param_dict)  # 最小化负分数
        
        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_calls=n_calls,
            n_initial_points=self.optimization_config["methods"]["bayesian"]["n_initial_points"],
            random_state=42
        )
        
        best_params = dict(zip(param_names, result.x))
        best_score = -result.fun
        
        # 保存优化结果
        self._save_optimization_result(
            strategy_id,
            best_params,
            {"score": best_score},
            "bayesian"
        )
        
        logger.info(f"Bayesian optimization completed. Best params: {best_params}, Score: {best_score}")
        
        return best_params
    
    def _generate_param_combinations(self, param_grid: Dict[str, List]) -> List[Dict]:
        """生成参数组合"""
        import itertools
        
        keys = param_grid.keys()
        values = param_grid.values()
        
        combinations = []
        for combination in itertools.product(*values):
            combinations.append(dict(zip(keys, combination)))
        
        return combinations
    
    def run_ab_test(self,
                   test_name: str,
                   control_strategy: str,
                   test_strategy: str,
                   days: int = 30) -> Dict[str, Any]:
        """运行A/B测试"""
        logger.info(f"Starting A/B test: {test_name}")
        
        # 获取控制组和测试组的交易记录
        control_trades = self._get_strategy_trades(control_strategy, days)
        test_trades = self._get_strategy_trades(test_strategy, days)
        
        # 检查样本量
        min_sample_size = self.optimization_config["ab_testing"]["min_sample_size"]
        if len(control_trades) < min_sample_size or len(test_trades) < min_sample_size:
            logger.warning(f"Insufficient sample size for A/B test")
            return {
                "test_name": test_name,
                "is_significant": False,
                "winner": None,
                "message": "Insufficient sample size"
            }
        
        # 计算性能指标
        control_metrics = self._calculate_ab_metrics(control_trades)
        test_metrics = self._calculate_ab_metrics(test_trades)
        
        # 统计检验
        control_returns = [t.get('exit_pnl', 0) for t in control_trades]
        test_returns = [t.get('exit_pnl', 0) for t in test_trades]
        
        # T检验
        t_stat, p_value = stats.ttest_ind(test_returns, control_returns)
        
        # 判断显著性
        confidence_level = self.optimization_config["ab_testing"]["confidence_level"]
        is_significant = p_value < (1 - confidence_level)
        
        # 确定获胜者
        winner = None
        if is_significant:
            if np.mean(test_returns) > np.mean(control_returns):
                winner = test_strategy
            else:
                winner = control_strategy
        
        result = {
            "test_name": test_name,
            "control_strategy": control_strategy,
            "test_strategy": test_strategy,
            "control_metrics": control_metrics,
            "test_metrics": test_metrics,
            "sample_size": {
                "control": len(control_trades),
                "test": len(test_trades)
            },
            "t_statistic": t_stat,
            "p_value": p_value,
            "is_significant": is_significant,
            "winner": winner,
            "confidence_level": confidence_level
        }
        
        # 保存A/B测试结果
        self._save_ab_test_result(result)
        
        logger.info(f"A/B test completed. Winner: {winner}, P-value: {p_value:.4f}")
        
        return result
    
    def _get_strategy_trades(self, strategy_id: str, days: int) -> List[Dict]:
        """获取策略的交易记录"""
        all_trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        return [t for t in all_trades if t.get('strategy_id') == strategy_id]
    
    def _calculate_ab_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """计算A/B测试指标"""
        if not trades:
            return {
                "avg_return": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "total_pnl": 0
            }
        
        returns = [t.get('exit_pnl', 0) for t in trades]
        wins = sum(1 for r in returns if r > 0)
        
        return {
            "avg_return": np.mean(returns),
            "std_return": np.std(returns),
            "win_rate": wins / len(trades),
            "sharpe_ratio": self._calculate_sharpe_ratio(returns),
            "total_pnl": sum(returns),
            "trade_count": len(trades)
        }
    
    def apply_time_decay(self, 
                        strategy_id: str,
                        current_weight: float,
                        decay_rate: float = 0.95,
                        min_weight: float = 0.1) -> float:
        """应用时间衰减"""
        # 获取策略最后更新时间
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_updated FROM strategy_weights
            WHERE strategy_id = ?
        ''', (strategy_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return current_weight
        
        # 计算天数差
        last_updated = datetime.fromisoformat(result[0])
        days_passed = (datetime.now() - last_updated).days
        
        # 应用衰减
        new_weight = current_weight * (decay_rate ** days_passed)
        
        # 确保不低于最小权重
        new_weight = max(new_weight, min_weight)
        
        # 更新权重
        self._save_strategy_weight(strategy_id, new_weight)
        
        return new_weight
    
    def get_optimal_weights(self, strategies: List[str]) -> Dict[str, float]:
        """获取最优权重组合"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        weights = {}
        
        for strategy_id in strategies:
            cursor.execute('''
                SELECT weight, performance_score FROM strategy_weights
                WHERE strategy_id = ?
                ORDER BY last_updated DESC
                LIMIT 1
            ''', (strategy_id,))
            
            result = cursor.fetchone()
            
            if result:
                weights[strategy_id] = result['weight']
            else:
                # 默认权重
                weights[strategy_id] = 1 / len(strategies)
        
        conn.close()
        
        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _save_strategy_weight(self, 
                            strategy_id: str,
                            weight: float,
                            performance_score: Optional[float] = None,
                            market_condition: Optional[str] = None):
        """保存策略权重"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO strategy_weights
            (strategy_id, strategy_name, weight, performance_score, 
             market_condition, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            strategy_id,
            strategy_id,  # 使用ID作为名称
            weight,
            performance_score,
            market_condition,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _save_evaluation_metrics(self, strategy_id: str, metrics: Dict[str, float]):
        """保存评估指标"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO optimization_results
            (strategy_id, parameters, performance_metrics, optimization_method)
            VALUES (?, ?, ?, ?)
        ''', (
            strategy_id,
            json.dumps({}),  # 空参数
            json.dumps(metrics),
            "evaluation"
        ))
        
        conn.commit()
        conn.close()
    
    def _save_optimization_result(self,
                                 strategy_id: str,
                                 parameters: Dict,
                                 metrics: Dict,
                                 method: str):
        """保存优化结果"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO optimization_results
            (strategy_id, parameters, performance_metrics, optimization_method)
            VALUES (?, ?, ?, ?)
        ''', (
            strategy_id,
            json.dumps(parameters),
            json.dumps(metrics),
            method
        ))
        
        conn.commit()
        conn.close()
    
    def _save_ab_test_result(self, result: Dict):
        """保存A/B测试结果"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ab_test_results
            (test_name, control_strategy, test_strategy,
             control_performance, test_performance,
             sample_size, p_value, is_significant, winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result["test_name"],
            result["control_strategy"],
            result["test_strategy"],
            json.dumps(result["control_metrics"]),
            json.dumps(result["test_metrics"]),
            result["sample_size"]["test"],
            result["p_value"],
            result["is_significant"],
            result["winner"]
        ))
        
        conn.commit()
        conn.close()
    
    def cleanup(self):
        """清理资源"""
        self.strategy_weights.clear()
        logger.info("StrategyOptimizer cleanup completed")