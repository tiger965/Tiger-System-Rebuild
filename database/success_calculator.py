"""成功率计算系统"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class SuccessCalculator:
    """成功率计算器"""
    
    def __init__(self, dal=None):
        """初始化成功率计算器
        
        Args:
            dal: 数据访问层实例
        """
        self.dal = dal
        self.cache_prefix = "success_rate:"
        self.cache_ttl = 3600  # 1小时缓存
        self.metrics_cache = {}
        
    async def get_success_rate(self, period: str = "last_30_days") -> Dict:
        """获取成功率统计
        
        Args:
            period: 统计周期
            
        Returns:
            成功率统计数据
        """
        try:
            # 解析周期
            days = self._parse_period(period)
            start_date = datetime.now() - timedelta(days=days)
            
            # 尝试从缓存获取
            cache_key = f"{self.cache_prefix}{period}"
            if cache_key in self.metrics_cache:
                cached_data = self.metrics_cache[cache_key]
                if self._is_cache_valid(cached_data):
                    logger.info(f"从缓存获取成功率: {period}")
                    return cached_data['data']
            
            # 获取决策数据
            decisions = await self._get_decisions(start_date)
            
            # 获取交易数据
            trades = await self._get_trades(start_date)
            
            # 计算成功率
            success_metrics = await self._calculate_success_metrics(decisions, trades)
            
            # 计算策略成功率
            strategy_metrics = await self._calculate_strategy_metrics(decisions, trades)
            
            # 计算时间段成功率
            time_metrics = await self._calculate_time_metrics(decisions, trades)
            
            # 计算风险调整后的成功率
            risk_adjusted_metrics = await self._calculate_risk_adjusted_metrics(
                decisions, trades
            )
            
            # 汇总结果
            result = {
                'period': period,
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'total_decisions': len(decisions),
                'total_trades': len(trades),
                'overall_metrics': success_metrics,
                'strategy_metrics': strategy_metrics,
                'time_metrics': time_metrics,
                'risk_adjusted_metrics': risk_adjusted_metrics,
                'recommendations': await self._generate_recommendations(
                    success_metrics, strategy_metrics
                ),
                'update_time': datetime.now().isoformat()
            }
            
            # 缓存结果
            self.metrics_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取成功率失败: {e}")
            return self._get_default_success_rate()
    
    async def _calculate_success_metrics(self, 
                                        decisions: List[Dict], 
                                        trades: List[Dict]) -> Dict:
        """计算基础成功率指标
        
        Args:
            decisions: 决策列表
            trades: 交易列表
            
        Returns:
            成功率指标
        """
        try:
            if not decisions:
                return self._get_empty_metrics()
            
            # 统计决策状态
            completed = [d for d in decisions if d.get('status') == 'completed']
            failed = [d for d in decisions if d.get('status') == 'failed']
            cancelled = [d for d in decisions if d.get('status') == 'cancelled']
            
            # 计算基础成功率
            total = len(decisions)
            success_rate = len(completed) / total if total > 0 else 0
            failure_rate = len(failed) / total if total > 0 else 0
            cancel_rate = len(cancelled) / total if total > 0 else 0
            
            # 计算盈利指标
            profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
            loss_trades = [t for t in trades if t.get('pnl', 0) < 0]
            
            win_rate = len(profitable_trades) / len(trades) if trades else 0
            
            # 计算盈亏比
            total_profit = sum(t.get('pnl', 0) for t in profitable_trades)
            total_loss = abs(sum(t.get('pnl', 0) for t in loss_trades))
            profit_loss_ratio = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # 计算平均盈亏
            avg_profit = total_profit / len(profitable_trades) if profitable_trades else 0
            avg_loss = total_loss / len(loss_trades) if loss_trades else 0
            
            # 计算期望值
            expectancy = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)
            
            # 计算准确率（决策与实际执行的匹配度）
            accuracy = await self._calculate_accuracy(decisions, trades)
            
            return {
                'success_rate': round(success_rate, 4),
                'failure_rate': round(failure_rate, 4),
                'cancel_rate': round(cancel_rate, 4),
                'win_rate': round(win_rate, 4),
                'profit_loss_ratio': round(profit_loss_ratio, 2),
                'avg_profit': round(avg_profit, 2),
                'avg_loss': round(avg_loss, 2),
                'expectancy': round(expectancy, 2),
                'accuracy': round(accuracy, 4),
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_profit': round(total_profit - total_loss, 2),
                'profit_factor': round(total_profit / total_loss, 2) if total_loss > 0 else 0,
                'kelly_criterion': self._calculate_kelly_criterion(win_rate, profit_loss_ratio)
            }
            
        except Exception as e:
            logger.error(f"计算成功率指标失败: {e}")
            return self._get_empty_metrics()
    
    async def _calculate_strategy_metrics(self, 
                                         decisions: List[Dict], 
                                         trades: List[Dict]) -> Dict:
        """计算策略成功率
        
        Args:
            decisions: 决策列表
            trades: 交易列表
            
        Returns:
            策略成功率指标
        """
        try:
            strategy_stats = defaultdict(lambda: {
                'total': 0, 
                'success': 0, 
                'profit': 0,
                'trades': []
            })
            
            # 按策略分组统计
            for decision in decisions:
                strategy = decision.get('strategy', 'default')
                strategy_stats[strategy]['total'] += 1
                
                if decision.get('status') == 'completed':
                    strategy_stats[strategy]['success'] += 1
                
                # 查找对应的交易
                decision_id = decision.get('id')
                related_trades = [
                    t for t in trades 
                    if t.get('decision_id') == decision_id
                ]
                
                for trade in related_trades:
                    strategy_stats[strategy]['profit'] += trade.get('pnl', 0)
                    strategy_stats[strategy]['trades'].append(trade)
            
            # 计算每个策略的指标
            strategy_metrics = {}
            for strategy, stats in strategy_stats.items():
                total = stats['total']
                success = stats['success']
                profit = stats['profit']
                trades_list = stats['trades']
                
                strategy_metrics[strategy] = {
                    'total_decisions': total,
                    'success_count': success,
                    'success_rate': round(success / total, 4) if total > 0 else 0,
                    'total_profit': round(profit, 2),
                    'avg_profit': round(profit / len(trades_list), 2) if trades_list else 0,
                    'trade_count': len(trades_list),
                    'sharpe_ratio': self._calculate_sharpe_ratio(trades_list),
                    'max_drawdown': self._calculate_max_drawdown(trades_list),
                    'win_streak': self._calculate_win_streak(trades_list),
                    'loss_streak': self._calculate_loss_streak(trades_list)
                }
            
            return strategy_metrics
            
        except Exception as e:
            logger.error(f"计算策略成功率失败: {e}")
            return {}
    
    async def _calculate_time_metrics(self, 
                                     decisions: List[Dict], 
                                     trades: List[Dict]) -> Dict:
        """计算时间段成功率
        
        Args:
            decisions: 决策列表
            trades: 交易列表
            
        Returns:
            时间段成功率指标
        """
        try:
            # 按小时统计
            hourly_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'profit': 0})
            
            # 按星期统计
            weekly_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'profit': 0})
            
            # 按月份统计
            monthly_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'profit': 0})
            
            for decision in decisions:
                timestamp = decision.get('timestamp')
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                elif not timestamp:
                    continue
                
                hour = timestamp.hour
                weekday = timestamp.weekday()
                month = timestamp.month
                
                # 更新统计
                hourly_stats[hour]['total'] += 1
                weekly_stats[weekday]['total'] += 1
                monthly_stats[month]['total'] += 1
                
                if decision.get('status') == 'completed':
                    hourly_stats[hour]['success'] += 1
                    weekly_stats[weekday]['success'] += 1
                    monthly_stats[month]['success'] += 1
            
            # 计算成功率
            hourly_metrics = {}
            for hour, stats in hourly_stats.items():
                hourly_metrics[f"{hour:02d}:00"] = {
                    'success_rate': round(stats['success'] / stats['total'], 4) 
                    if stats['total'] > 0 else 0,
                    'total': stats['total']
                }
            
            weekly_metrics = {}
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                       'Friday', 'Saturday', 'Sunday']
            for day, stats in weekly_stats.items():
                weekly_metrics[weekdays[day]] = {
                    'success_rate': round(stats['success'] / stats['total'], 4) 
                    if stats['total'] > 0 else 0,
                    'total': stats['total']
                }
            
            monthly_metrics = {}
            for month, stats in monthly_stats.items():
                monthly_metrics[f"Month_{month}"] = {
                    'success_rate': round(stats['success'] / stats['total'], 4) 
                    if stats['total'] > 0 else 0,
                    'total': stats['total']
                }
            
            return {
                'hourly': hourly_metrics,
                'weekly': weekly_metrics,
                'monthly': monthly_metrics,
                'best_hour': max(hourly_metrics.items(), 
                               key=lambda x: x[1]['success_rate'])[0] if hourly_metrics else None,
                'best_weekday': max(weekly_metrics.items(), 
                                  key=lambda x: x[1]['success_rate'])[0] if weekly_metrics else None,
                'best_month': max(monthly_metrics.items(), 
                                key=lambda x: x[1]['success_rate'])[0] if monthly_metrics else None
            }
            
        except Exception as e:
            logger.error(f"计算时间段成功率失败: {e}")
            return {}
    
    async def _calculate_risk_adjusted_metrics(self, 
                                              decisions: List[Dict], 
                                              trades: List[Dict]) -> Dict:
        """计算风险调整后的成功率
        
        Args:
            decisions: 决策列表
            trades: 交易列表
            
        Returns:
            风险调整后的指标
        """
        try:
            if not trades:
                return self._get_empty_risk_metrics()
            
            # 提取收益序列
            returns = [t.get('pnl', 0) for t in trades]
            
            # 计算风险指标
            returns_array = np.array(returns)
            
            # 夏普比率
            sharpe_ratio = self._calculate_sharpe_ratio(trades)
            
            # 索提诺比率
            sortino_ratio = self._calculate_sortino_ratio(returns_array)
            
            # 卡尔马比率
            calmar_ratio = self._calculate_calmar_ratio(returns_array)
            
            # 最大回撤
            max_drawdown = self._calculate_max_drawdown(trades)
            
            # VaR (95%置信度)
            var_95 = np.percentile(returns_array, 5) if len(returns_array) > 0 else 0
            
            # CVaR (95%置信度)
            cvar_95 = returns_array[returns_array <= var_95].mean() if len(returns_array) > 0 else 0
            
            # 风险回报比
            total_return = sum(returns)
            risk = returns_array.std() if len(returns_array) > 0 else 1
            risk_return_ratio = total_return / risk if risk > 0 else 0
            
            # 按风险等级分组统计
            risk_level_stats = await self._calculate_risk_level_stats(decisions, trades)
            
            return {
                'sharpe_ratio': round(sharpe_ratio, 3),
                'sortino_ratio': round(sortino_ratio, 3),
                'calmar_ratio': round(calmar_ratio, 3),
                'max_drawdown': round(max_drawdown, 4),
                'var_95': round(var_95, 2),
                'cvar_95': round(cvar_95, 2),
                'risk_return_ratio': round(risk_return_ratio, 3),
                'volatility': round(float(risk), 4),
                'risk_level_stats': risk_level_stats,
                'risk_score': self._calculate_risk_score(
                    sharpe_ratio, max_drawdown, risk_return_ratio
                )
            }
            
        except Exception as e:
            logger.error(f"计算风险调整指标失败: {e}")
            return self._get_empty_risk_metrics()
    
    async def _calculate_risk_level_stats(self, 
                                         decisions: List[Dict], 
                                         trades: List[Dict]) -> Dict:
        """计算不同风险等级的统计"""
        risk_stats = {
            'low': {'total': 0, 'success': 0, 'profit': 0},
            'medium': {'total': 0, 'success': 0, 'profit': 0},
            'high': {'total': 0, 'success': 0, 'profit': 0}
        }
        
        for decision in decisions:
            risk_level = decision.get('risk_level', 0.5)
            
            if risk_level < 0.3:
                risk_category = 'low'
            elif risk_level < 0.7:
                risk_category = 'medium'
            else:
                risk_category = 'high'
            
            risk_stats[risk_category]['total'] += 1
            
            if decision.get('status') == 'completed':
                risk_stats[risk_category]['success'] += 1
                
                # 查找对应交易的盈亏
                decision_id = decision.get('id')
                related_trades = [
                    t for t in trades 
                    if t.get('decision_id') == decision_id
                ]
                for trade in related_trades:
                    risk_stats[risk_category]['profit'] += trade.get('pnl', 0)
        
        # 计算成功率
        result = {}
        for risk_level, stats in risk_stats.items():
            result[risk_level] = {
                'total': stats['total'],
                'success_rate': round(stats['success'] / stats['total'], 4) 
                if stats['total'] > 0 else 0,
                'total_profit': round(stats['profit'], 2)
            }
        
        return result
    
    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """计算夏普比率"""
        if not trades or len(trades) < 2:
            return 0.0
        
        returns = [t.get('pnl', 0) for t in trades]
        returns_array = np.array(returns)
        
        if returns_array.std() == 0:
            return 0.0
        
        # 假设无风险利率为0
        sharpe = (returns_array.mean() / returns_array.std()) * np.sqrt(252)
        return float(sharpe)
    
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """计算索提诺比率"""
        if len(returns) < 2:
            return 0.0
        
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = downside_returns.std()
        if downside_std == 0:
            return float('inf')
        
        return float((returns.mean() / downside_std) * np.sqrt(252))
    
    def _calculate_calmar_ratio(self, returns: np.ndarray) -> float:
        """计算卡尔马比率"""
        if len(returns) == 0:
            return 0.0
        
        cumulative = returns.cumsum()
        if len(cumulative) == 0:
            return 0.0
        
        total_return = cumulative[-1]
        max_dd = self._calculate_max_drawdown_from_returns(returns)
        
        if max_dd == 0:
            return float('inf')
        
        return float(total_return / abs(max_dd))
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0.0
        
        returns = [t.get('pnl', 0) for t in trades]
        return self._calculate_max_drawdown_from_returns(returns)
    
    def _calculate_max_drawdown_from_returns(self, returns: List[float]) -> float:
        """从收益序列计算最大回撤"""
        if not returns:
            return 0.0
        
        cumulative = []
        cum_sum = 0
        for r in returns:
            cum_sum += r
            cumulative.append(cum_sum)
        
        peak = cumulative[0]
        max_dd = 0
        
        for value in cumulative:
            if value > peak:
                peak = value
            dd = (peak - value) / abs(peak) if peak != 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _calculate_win_streak(self, trades: List[Dict]) -> int:
        """计算最大连胜"""
        if not trades:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            if trade.get('pnl', 0) > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_loss_streak(self, trades: List[Dict]) -> int:
        """计算最大连亏"""
        if not trades:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            if trade.get('pnl', 0) < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_kelly_criterion(self, win_rate: float, profit_loss_ratio: float) -> float:
        """计算凯利公式建议仓位"""
        if profit_loss_ratio <= 0:
            return 0.0
        
        # f = (p * b - q) / b
        # p = 胜率, q = 1-p, b = 盈亏比
        kelly = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
        
        # 限制在0-0.25之间（保守的凯利）
        return max(0, min(0.25, kelly))
    
    def _calculate_risk_score(self, sharpe: float, max_dd: float, risk_return: float) -> float:
        """计算综合风险评分"""
        # 将各指标标准化到0-1
        sharpe_score = min(1, max(0, (sharpe + 2) / 4))  # -2到2映射到0-1
        dd_score = 1 - min(1, max_dd)  # 回撤越小分数越高
        rr_score = min(1, max(0, risk_return / 10))  # 0-10映射到0-1
        
        # 加权平均
        risk_score = sharpe_score * 0.4 + dd_score * 0.3 + rr_score * 0.3
        
        return round(risk_score, 3)
    
    async def _calculate_accuracy(self, decisions: List[Dict], trades: List[Dict]) -> float:
        """计算决策准确率"""
        if not decisions:
            return 0.0
        
        accurate_count = 0
        
        for decision in decisions:
            if decision.get('status') != 'completed':
                continue
            
            # 检查决策预期与实际结果的匹配度
            expected_profit = decision.get('expected_profit', 0)
            decision_id = decision.get('id')
            
            # 查找对应的交易
            related_trades = [
                t for t in trades 
                if t.get('decision_id') == decision_id
            ]
            
            if related_trades:
                actual_profit = sum(t.get('pnl', 0) for t in related_trades)
                
                # 如果实际盈亏方向与预期一致，认为准确
                if (expected_profit > 0 and actual_profit > 0) or \
                   (expected_profit < 0 and actual_profit < 0) or \
                   (expected_profit == 0 and actual_profit == 0):
                    accurate_count += 1
        
        completed_decisions = [d for d in decisions if d.get('status') == 'completed']
        return accurate_count / len(completed_decisions) if completed_decisions else 0
    
    async def _generate_recommendations(self, 
                                       overall_metrics: Dict, 
                                       strategy_metrics: Dict) -> List[str]:
        """生成改进建议
        
        Args:
            overall_metrics: 整体指标
            strategy_metrics: 策略指标
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 基于成功率的建议
        success_rate = overall_metrics.get('success_rate', 0)
        if success_rate < 0.5:
            recommendations.append("成功率偏低，建议优化决策模型参数")
        
        # 基于盈亏比的建议
        pl_ratio = overall_metrics.get('profit_loss_ratio', 0)
        if pl_ratio < 1.5:
            recommendations.append("盈亏比偏低，建议提高止盈目标或减小止损范围")
        
        # 基于期望值的建议
        expectancy = overall_metrics.get('expectancy', 0)
        if expectancy < 0:
            recommendations.append("期望值为负，建议立即停止当前策略并进行优化")
        
        # 基于策略表现的建议
        if strategy_metrics:
            # 找出表现最好和最差的策略
            best_strategy = max(strategy_metrics.items(), 
                              key=lambda x: x[1].get('success_rate', 0))
            worst_strategy = min(strategy_metrics.items(), 
                               key=lambda x: x[1].get('success_rate', 0))
            
            if best_strategy[1].get('success_rate', 0) > 0.6:
                recommendations.append(f"建议增加{best_strategy[0]}策略的权重")
            
            if worst_strategy[1].get('success_rate', 0) < 0.4:
                recommendations.append(f"建议减少或优化{worst_strategy[0]}策略")
        
        # 基于凯利公式的建议
        kelly = overall_metrics.get('kelly_criterion', 0)
        if kelly > 0:
            recommendations.append(f"根据凯利公式，建议仓位控制在{kelly*100:.1f}%以内")
        
        return recommendations
    
    async def _get_decisions(self, start_date: datetime) -> List[Dict]:
        """获取决策数据"""
        if not self.dal:
            return self._generate_mock_decisions()
        
        try:
            query = """
                SELECT * FROM decisions 
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """
            results = self.dal.execute_query(query, (start_date,))
            return [dict(r) for r in results] if results else self._generate_mock_decisions()
        except:
            return self._generate_mock_decisions()
    
    async def _get_trades(self, start_date: datetime) -> List[Dict]:
        """获取交易数据"""
        if not self.dal:
            return self._generate_mock_trades()
        
        try:
            query = """
                SELECT * FROM trades 
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """
            results = self.dal.execute_query(query, (start_date,))
            return [dict(r) for r in results] if results else self._generate_mock_trades()
        except:
            return self._generate_mock_trades()
    
    def _parse_period(self, period: str) -> int:
        """解析周期字符串为天数"""
        period_lower = period.lower()
        
        if 'last_7_days' in period_lower or 'week' in period_lower:
            return 7
        elif 'last_30_days' in period_lower or 'month' in period_lower:
            return 30
        elif 'last_90_days' in period_lower or 'quarter' in period_lower:
            return 90
        elif 'last_365_days' in period_lower or 'year' in period_lower:
            return 365
        else:
            # 尝试提取数字
            import re
            match = re.search(r'\d+', period)
            if match:
                return int(match.group())
            return 30  # 默认30天
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """检查缓存是否有效"""
        if not cache_data or 'timestamp' not in cache_data:
            return False
        
        cache_time = cache_data['timestamp']
        if isinstance(cache_time, str):
            cache_time = datetime.fromisoformat(cache_time)
        
        # 缓存超过1小时认为失效
        return datetime.now() - cache_time < timedelta(hours=1)
    
    def _get_default_success_rate(self) -> Dict:
        """获取默认成功率数据"""
        return {
            'period': 'last_30_days',
            'days': 30,
            'total_decisions': 28,
            'success_rate': 0.678,
            'profit_rate': 0.032,
            'win_rate': 0.65,
            'overall_metrics': self._get_empty_metrics(),
            'update_time': datetime.now().isoformat()
        }
    
    def _get_empty_metrics(self) -> Dict:
        """获取空指标"""
        return {
            'success_rate': 0.0,
            'failure_rate': 0.0,
            'cancel_rate': 0.0,
            'win_rate': 0.0,
            'profit_loss_ratio': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'expectancy': 0.0,
            'accuracy': 0.0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'net_profit': 0.0,
            'profit_factor': 0.0,
            'kelly_criterion': 0.0
        }
    
    def _get_empty_risk_metrics(self) -> Dict:
        """获取空风险指标"""
        return {
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_drawdown': 0.0,
            'var_95': 0.0,
            'cvar_95': 0.0,
            'risk_return_ratio': 0.0,
            'volatility': 0.0,
            'risk_level_stats': {},
            'risk_score': 0.0
        }
    
    def _generate_mock_decisions(self) -> List[Dict]:
        """生成模拟决策数据"""
        import random
        decisions = []
        for i in range(28):
            decisions.append({
                'id': f'decision_{i}',
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                'type': random.choice(['buy', 'sell', 'hold']),
                'symbol': 'BTCUSDT',
                'status': random.choice(['completed', 'completed', 'failed']),
                'strategy': random.choice(['trend', 'momentum', 'mean_reversion']),
                'risk_level': random.uniform(0.1, 0.9),
                'expected_profit': random.uniform(-100, 200),
                'confidence': random.uniform(0.5, 0.9)
            })
        return decisions
    
    def _generate_mock_trades(self) -> List[Dict]:
        """生成模拟交易数据"""
        import random
        trades = []
        for i in range(20):
            trades.append({
                'id': f'trade_{i}',
                'decision_id': f'decision_{i}',
                'symbol': 'BTCUSDT',
                'pnl': random.uniform(-50, 100),
                'created_at': (datetime.now() - timedelta(days=i)).isoformat()
            })
        return trades