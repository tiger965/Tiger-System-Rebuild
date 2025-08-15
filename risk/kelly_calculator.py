"""
Tiger系统 - 凯利公式仓位计算器
窗口：7号
功能：使用凯利公式科学计算最优仓位大小
作者：Window-7 Risk Control Officer
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeStats:
    """交易统计数据"""
    win_rate: float  # 胜率
    avg_win: float   # 平均盈利
    avg_loss: float  # 平均亏损
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    trades_count: int  # 交易次数


class KellyCalculator:
    """
    凯利公式仓位计算器
    
    f = (p * b - q) / b
    其中：
    f = 应投注的资金比例
    p = 获胜概率
    b = 赔率（赢时的盈利/输时的亏损）
    q = 失败概率 (1-p)
    """
    
    def __init__(self, max_kelly_fraction: float = 0.25):
        """
        初始化
        
        Args:
            max_kelly_fraction: 最大凯利比例（安全起见通常使用1/4凯利）
        """
        self.max_kelly_fraction = max_kelly_fraction
        self.min_kelly_fraction = 0.01  # 最小1%
        self.trades_history = []
        self.kelly_history = []
        
    def calculate_kelly_fraction(self, win_rate: float, win_loss_ratio: float) -> float:
        """
        计算基础凯利公式
        
        Args:
            win_rate: 胜率 (0-1)
            win_loss_ratio: 盈亏比（平均盈利/平均亏损）
            
        Returns:
            凯利比例
        """
        if win_rate <= 0 or win_rate >= 1:
            logger.warning(f"无效胜率: {win_rate}")
            return 0
        
        if win_loss_ratio <= 0:
            logger.warning(f"无效盈亏比: {win_loss_ratio}")
            return 0
        
        # 凯利公式: f = (p * b - q) / b
        p = win_rate
        q = 1 - win_rate
        b = win_loss_ratio
        
        kelly = (p * b - q) / b
        
        # 限制凯利比例
        kelly = max(0, kelly)  # 不能为负
        kelly = min(kelly, self.max_kelly_fraction)  # 不超过最大值
        
        logger.info(f"凯利计算: 胜率={p:.2%}, 盈亏比={b:.2f}, 凯利={kelly:.2%}")
        
        return kelly
    
    def calculate_optimal_fraction(self, trades: List[Dict]) -> float:
        """
        基于历史交易计算最优仓位比例
        
        Args:
            trades: 历史交易列表
            
        Returns:
            最优仓位比例
        """
        if not trades or len(trades) < 10:
            logger.warning("交易历史不足，使用保守仓位")
            return self.min_kelly_fraction
        
        # 计算统计数据
        stats = self._calculate_trade_stats(trades)
        
        # 计算基础凯利
        if stats.avg_loss != 0:
            win_loss_ratio = abs(stats.avg_win / stats.avg_loss)
        else:
            win_loss_ratio = 0
        
        base_kelly = self.calculate_kelly_fraction(stats.win_rate, win_loss_ratio)
        
        # 根据市场条件调整
        adjusted_kelly = self._adjust_kelly_fraction(base_kelly, stats)
        
        return adjusted_kelly
    
    def calculate_position_size(self, capital: float, kelly_fraction: float, 
                               risk_per_trade: float = 0.02) -> Dict:
        """
        计算实际仓位大小
        
        Args:
            capital: 账户资金
            kelly_fraction: 凯利比例
            risk_per_trade: 单笔最大风险
            
        Returns:
            仓位信息
        """
        # 基础仓位
        base_position = capital * kelly_fraction
        
        # 风险限制
        max_position = capital * risk_per_trade * 3  # 假设33%止损
        
        # 实际仓位
        actual_position = min(base_position, max_position)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "capital": capital,
            "kelly_fraction": kelly_fraction,
            "base_position": base_position,
            "max_position": max_position,
            "actual_position": actual_position,
            "position_percent": actual_position / capital,
            "leverage_suggested": actual_position / (capital * 0.1)  # 假设10%保证金
        }
    
    def monte_carlo_kelly(self, trades: List[Dict], simulations: int = 1000) -> Dict:
        """
        蒙特卡洛模拟优化凯利比例
        
        Args:
            trades: 历史交易
            simulations: 模拟次数
            
        Returns:
            模拟结果
        """
        if not trades or len(trades) < 20:
            return {
                "optimal_kelly": self.min_kelly_fraction,
                "expected_return": 0,
                "risk_of_ruin": 1.0,
                "message": "数据不足"
            }
        
        # 提取收益率
        returns = [t.get('pnl_percent', 0) for t in trades]
        
        kelly_range = np.linspace(0.01, self.max_kelly_fraction, 50)
        results = []
        
        for kelly in kelly_range:
            final_values = []
            
            for _ in range(simulations):
                # 随机抽样构建交易序列
                sim_returns = np.random.choice(returns, size=len(returns), replace=True)
                
                # 计算最终资金
                capital = 100000
                for ret in sim_returns:
                    capital *= (1 + kelly * ret)
                    if capital <= 10000:  # 破产阈值
                        capital = 0
                        break
                
                final_values.append(capital)
            
            # 统计结果
            final_values = np.array(final_values)
            avg_return = np.mean(final_values) / 100000 - 1
            risk_of_ruin = np.sum(final_values == 0) / simulations
            sharpe = avg_return / (np.std(final_values) / 100000) if np.std(final_values) > 0 else 0
            
            results.append({
                'kelly': kelly,
                'expected_return': avg_return,
                'risk_of_ruin': risk_of_ruin,
                'sharpe': sharpe
            })
        
        # 找到最优凯利（最大化夏普比率，同时限制破产风险）
        valid_results = [r for r in results if r['risk_of_ruin'] < 0.05]  # 破产风险<5%
        
        if valid_results:
            optimal = max(valid_results, key=lambda x: x['sharpe'])
        else:
            optimal = min(results, key=lambda x: x['risk_of_ruin'])
        
        return {
            "optimal_kelly": optimal['kelly'],
            "expected_return": optimal['expected_return'],
            "risk_of_ruin": optimal['risk_of_ruin'],
            "sharpe_ratio": optimal['sharpe'],
            "simulations": simulations
        }
    
    def dynamic_kelly_adjustment(self, current_drawdown: float, 
                                volatility: float, market_regime: str) -> float:
        """
        动态调整凯利比例
        
        Args:
            current_drawdown: 当前回撤
            volatility: 市场波动率
            market_regime: 市场状态 (trending/ranging/volatile)
            
        Returns:
            调整系数
        """
        adjustment = 1.0
        
        # 回撤调整
        if current_drawdown > 0.20:
            adjustment *= 0.3  # 回撤>20%，大幅降低
        elif current_drawdown > 0.10:
            adjustment *= 0.5  # 回撤>10%，减半
        elif current_drawdown > 0.05:
            adjustment *= 0.75  # 回撤>5%，适度降低
        
        # 波动率调整
        if volatility > 0.30:  # 高波动
            adjustment *= 0.5
        elif volatility > 0.20:  # 中高波动
            adjustment *= 0.75
        elif volatility < 0.10:  # 低波动
            adjustment *= 1.25
        
        # 市场状态调整
        regime_adjustments = {
            "trending": 1.2,    # 趋势市场增加
            "ranging": 0.8,     # 震荡市场减少
            "volatile": 0.5,    # 剧烈波动大幅减少
            "uncertain": 0.6    # 不确定减少
        }
        adjustment *= regime_adjustments.get(market_regime, 1.0)
        
        # 限制调整范围
        adjustment = max(0.1, min(1.5, adjustment))
        
        logger.info(f"动态调整: 回撤={current_drawdown:.2%}, 波动={volatility:.2%}, "
                   f"市场={market_regime}, 调整系数={adjustment:.2f}")
        
        return adjustment
    
    def _calculate_trade_stats(self, trades: List[Dict]) -> TradeStats:
        """计算交易统计"""
        wins = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
        losses = [t['pnl'] for t in trades if t.get('pnl', 0) < 0]
        
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # 计算收益序列
        returns = [t.get('pnl_percent', 0) for t in trades]
        
        # 夏普比率
        if returns and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        cumulative = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        return TradeStats(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            trades_count=len(trades)
        )
    
    def _adjust_kelly_fraction(self, base_kelly: float, stats: TradeStats) -> float:
        """根据统计数据调整凯利比例"""
        adjusted = base_kelly
        
        # 根据夏普比率调整
        if stats.sharpe_ratio < 0.5:
            adjusted *= 0.5
        elif stats.sharpe_ratio < 1.0:
            adjusted *= 0.75
        elif stats.sharpe_ratio > 2.0:
            adjusted *= 1.25
        
        # 根据最大回撤调整
        if stats.max_drawdown > 0.30:
            adjusted *= 0.3
        elif stats.max_drawdown > 0.20:
            adjusted *= 0.5
        elif stats.max_drawdown > 0.10:
            adjusted *= 0.75
        
        # 根据样本数量调整
        if stats.trades_count < 30:
            adjusted *= 0.5
        elif stats.trades_count < 50:
            adjusted *= 0.75
        elif stats.trades_count > 100:
            adjusted *= 1.1
        
        # 确保在合理范围内
        adjusted = max(self.min_kelly_fraction, min(self.max_kelly_fraction, adjusted))
        
        logger.info(f"凯利调整: 基础={base_kelly:.2%}, 调整后={adjusted:.2%}")
        
        return adjusted
    
    def get_recommendation(self, capital: float, trades: List[Dict], 
                          market_conditions: Dict) -> Dict:
        """
        获取仓位建议
        
        Args:
            capital: 账户资金
            trades: 历史交易
            market_conditions: 市场条件
            
        Returns:
            完整的仓位建议
        """
        # 计算最优凯利
        optimal_kelly = self.calculate_optimal_fraction(trades)
        
        # 动态调整
        adjustment = self.dynamic_kelly_adjustment(
            market_conditions.get('drawdown', 0),
            market_conditions.get('volatility', 0.15),
            market_conditions.get('regime', 'uncertain')
        )
        
        # 调整后的凯利
        adjusted_kelly = optimal_kelly * adjustment
        
        # 计算仓位
        position_info = self.calculate_position_size(capital, adjusted_kelly)
        
        # 蒙特卡洛验证
        monte_carlo = self.monte_carlo_kelly(trades)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "capital": capital,
            "optimal_kelly": optimal_kelly,
            "adjustment_factor": adjustment,
            "final_kelly": adjusted_kelly,
            "position_size": position_info['actual_position'],
            "position_percent": position_info['position_percent'],
            "monte_carlo_validation": monte_carlo,
            "confidence_level": self._calculate_confidence(trades, adjusted_kelly),
            "recommendation": self._generate_recommendation(adjusted_kelly, market_conditions)
        }
    
    def _calculate_confidence(self, trades: List[Dict], kelly: float) -> str:
        """计算置信度"""
        if not trades or len(trades) < 20:
            return "LOW"
        
        stats = self._calculate_trade_stats(trades)
        
        if stats.sharpe_ratio > 1.5 and stats.win_rate > 0.55 and kelly > 0.05:
            return "HIGH"
        elif stats.sharpe_ratio > 1.0 and stats.win_rate > 0.50:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendation(self, kelly: float, conditions: Dict) -> str:
        """生成建议"""
        if kelly < 0.02:
            return "风险过高，建议观望或最小仓位"
        elif kelly < 0.05:
            return "谨慎交易，使用小仓位"
        elif kelly < 0.10:
            return "正常交易，标准仓位"
        elif kelly < 0.15:
            return "有利条件，可适度加仓"
        else:
            return "优势明显，但仍需控制风险"


if __name__ == "__main__":
    # 测试代码
    calculator = KellyCalculator(max_kelly_fraction=0.25)
    
    # 测试基础凯利计算
    kelly = calculator.calculate_kelly_fraction(win_rate=0.60, win_loss_ratio=1.5)
    print(f"基础凯利比例: {kelly:.2%}")
    
    # 模拟历史交易
    trades = [
        {"pnl": 1000, "pnl_percent": 0.01},
        {"pnl": -500, "pnl_percent": -0.005},
        {"pnl": 1500, "pnl_percent": 0.015},
        {"pnl": -300, "pnl_percent": -0.003},
        {"pnl": 800, "pnl_percent": 0.008},
    ] * 10  # 复制以获得足够样本
    
    # 获取完整建议
    recommendation = calculator.get_recommendation(
        capital=100000,
        trades=trades,
        market_conditions={
            "drawdown": 0.05,
            "volatility": 0.15,
            "regime": "trending"
        }
    )
    
    print(f"\n仓位建议:")
    print(f"最优凯利: {recommendation['optimal_kelly']:.2%}")
    print(f"调整系数: {recommendation['adjustment_factor']:.2f}")
    print(f"最终凯利: {recommendation['final_kelly']:.2%}")
    print(f"建议仓位: ${recommendation['position_size']:.2f}")
    print(f"置信度: {recommendation['confidence_level']}")
    print(f"建议: {recommendation['recommendation']}")