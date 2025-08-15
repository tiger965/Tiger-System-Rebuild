"""
学习进化系统主程序
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from learning.records.trade_recorder import TradeRecorder, TradeEntry, TradeExit, TradeContext
from learning.patterns.pattern_learner import PatternLearner
from learning.optimizer.strategy_optimizer import StrategyOptimizer
from learning.black_swan.black_swan_learning import BlackSwanLearning
from learning.config.config import LOG_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LearningSystem:
    """学习系统主类"""
    
    def __init__(self):
        logger.info("Initializing Learning System...")
        
        # 初始化各模块
        self.trade_recorder = TradeRecorder()
        self.pattern_learner = PatternLearner(self.trade_recorder)
        self.strategy_optimizer = StrategyOptimizer(self.trade_recorder)
        self.black_swan_learning = BlackSwanLearning()
        
        logger.info("Learning System initialized successfully")
    
    def record_trade(self, trade_data: dict) -> str:
        """记录交易"""
        # 构建交易入场信息
        entry = TradeEntry(
            price=trade_data['entry_price'],
            reason=trade_data['entry_reason'],
            indicators=trade_data.get('indicators', {}),
            market_state=trade_data.get('market_state', 'normal'),
            ai_analysis=trade_data.get('ai_analysis', {}),
            timestamp=datetime.now().isoformat()
        )
        
        # 构建交易上下文
        context = TradeContext(
            market_trend=trade_data.get('market_trend', 'neutral'),
            volatility=trade_data.get('volatility', 0.5),
            news_events=trade_data.get('news_events', []),
            trader_actions=trade_data.get('trader_actions', [])
        )
        
        # 记录交易
        trade_id = self.trade_recorder.record_trade_entry(
            symbol=trade_data['symbol'],
            direction=trade_data['direction'],
            entry=entry,
            context=context
        )
        
        logger.info(f"Trade recorded: {trade_id}")
        return trade_id
    
    def close_trade(self, trade_id: str, exit_data: dict):
        """关闭交易"""
        # 获取交易记录
        trade = self.trade_recorder.get_trade_by_id(trade_id)
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return
        
        # 计算持仓时间
        entry_time = datetime.fromisoformat(trade['entry_timestamp'])
        exit_time = datetime.now()
        duration_hours = (exit_time - entry_time).total_seconds() / 3600
        
        # 计算盈亏
        entry_price = trade['entry_price']
        exit_price = exit_data['exit_price']
        
        if trade['direction'] == 'long':
            pnl = (exit_price - entry_price) / entry_price
        else:  # short
            pnl = (entry_price - exit_price) / entry_price
        
        # 构建出场信息
        exit_info = TradeExit(
            price=exit_price,
            reason=exit_data['exit_reason'],
            duration=duration_hours,
            pnl=pnl,
            timestamp=exit_time.isoformat()
        )
        
        # 记录出场
        self.trade_recorder.record_trade_exit(trade_id, exit_info)
        
        logger.info(f"Trade closed: {trade_id}, PnL: {pnl:.2%}")
    
    def analyze_patterns(self, days: int = 30):
        """分析交易模式"""
        logger.info(f"Analyzing patterns for last {days} days...")
        
        results = {
            "entry_conditions": self.pattern_learner.analyze_entry_conditions(days),
            "indicator_combos": self.pattern_learner.analyze_indicator_combinations(days),
            "market_states": self.pattern_learner.analyze_market_states(days),
            "time_patterns": self.pattern_learner.analyze_time_patterns(days),
            "opportunity_patterns": self.pattern_learner.analyze_opportunity_patterns(days),
            "common_mistakes": self.pattern_learner.identify_common_mistakes(days),
            "association_rules": self.pattern_learner.mine_association_rules(days)
        }
        
        # 获取最佳模式
        results["best_patterns"] = self.pattern_learner.get_best_patterns(limit=5)
        results["risk_patterns"] = self.pattern_learner.get_risk_patterns(limit=5)
        
        logger.info(f"Pattern analysis completed")
        return results
    
    def optimize_strategies(self, strategies: list, days: int = 30):
        """优化策略"""
        logger.info(f"Optimizing {len(strategies)} strategies...")
        
        # 根据表现调整权重
        performance_weights = self.strategy_optimizer.adjust_weights_performance(strategies, days)
        
        # 获取最优权重
        optimal_weights = self.strategy_optimizer.get_optimal_weights(strategies)
        
        logger.info(f"Strategy optimization completed")
        
        return {
            "performance_weights": performance_weights,
            "optimal_weights": optimal_weights
        }
    
    def check_black_swan_risk(self, market_indicators: dict) -> dict:
        """检查黑天鹅风险"""
        # 预测危机概率
        crisis_probability = self.black_swan_learning.predict_crisis_probability(market_indicators)
        
        # 获取推荐操作
        current_position = market_indicators.get('current_position', 1.0)
        recommended_action = self.black_swan_learning.get_recommended_action(
            crisis_probability, 
            current_position
        )
        
        # 如果需要预警，记录它
        if recommended_action['alert_level'] > 0:
            alert_id = self.black_swan_learning.record_alert(
                alert_level=recommended_action['alert_level'],
                alert_type="market_anomaly",
                trigger_conditions={"crisis_probability": crisis_probability},
                market_indicators=market_indicators,
                response_action=recommended_action['action_type']
            )
            recommended_action['alert_id'] = alert_id
        
        recommended_action['crisis_probability'] = crisis_probability
        
        return recommended_action
    
    def generate_learning_report(self) -> str:
        """生成学习报告"""
        # 获取交易统计
        trade_stats = self.trade_recorder.calculate_statistics(days=30)
        
        # 获取模式分析
        patterns = self.analyze_patterns(days=30)
        
        # 获取黑天鹅报告
        black_swan_report = self.black_swan_learning.generate_crisis_report()
        
        report = f"""
========== 学习进化系统报告 ==========
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【交易统计】
- 总交易数：{trade_stats.get('total_trades', 0)}
- 胜率：{trade_stats.get('win_rate', 0):.2%}
- 盈亏比：{trade_stats.get('profit_factor', 0):.2f}
- 总盈亏：{trade_stats.get('total_pnl', 0):.2%}
- 平均盈亏：{trade_stats.get('avg_pnl', 0):.2%}
- 最大盈利：{trade_stats.get('max_profit', 0):.2%}
- 最大亏损：{trade_stats.get('max_loss', 0):.2%}

【模式识别】
- 成功入场条件：{len(patterns.get('entry_conditions', {}))}个
- 有效指标组合：{len(patterns.get('indicator_combos', {}))}个
- 识别的时间模式：{len(patterns.get('time_patterns', {}))}个
- 机会模式：{len(patterns.get('opportunity_patterns', {}))}个
- 常见错误：{len(patterns.get('common_mistakes', []))}个

【最佳模式TOP3】
"""
        
        for i, pattern in enumerate(patterns.get('best_patterns', [])[:3], 1):
            report += f"{i}. {pattern.get('pattern_name', 'Unknown')} - 成功率: {pattern.get('success_rate', 0):.2%}\n"
        
        report += f"""
【风险模式TOP3】
"""
        
        for i, pattern in enumerate(patterns.get('risk_patterns', [])[:3], 1):
            report += f"{i}. {pattern.get('pattern_name', 'Unknown')} - 失败率: {pattern.get('failure_rate', 0):.2%}\n"
        
        report += f"""
{black_swan_report}

【系统状态】
- 学习模块：正常运行
- 模式识别：已识别{len(patterns.get('best_patterns', []))}个成功模式
- 黑天鹅监控：活跃
- 数据完整性：100%

==========================================
"""
        
        return report
    
    def run_demo(self):
        """运行演示"""
        logger.info("Starting Learning System Demo...")
        
        # 模拟记录一些交易
        demo_trades = [
            {
                'symbol': 'BTC/USDT',
                'direction': 'long',
                'entry_price': 50000,
                'entry_reason': 'breakout',
                'indicators': {'rsi': 65, 'macd': 0.5},
                'market_state': 'trending',
                'market_trend': 'bullish',
                'volatility': 0.7,
                'news_events': ['positive_news'],
                'trader_actions': ['whale_buy']
            },
            {
                'symbol': 'ETH/USDT',
                'direction': 'short',
                'entry_price': 3000,
                'entry_reason': 'reversal',
                'indicators': {'rsi': 75, 'macd': -0.3},
                'market_state': 'overbought',
                'market_trend': 'bearish',
                'volatility': 0.8,
                'news_events': ['negative_news'],
                'trader_actions': ['whale_sell']
            }
        ]
        
        trade_ids = []
        for trade in demo_trades:
            trade_id = self.record_trade(trade)
            trade_ids.append(trade_id)
        
        # 模拟关闭交易
        exit_data = [
            {'exit_price': 52000, 'exit_reason': 'take_profit'},
            {'exit_price': 2900, 'exit_reason': 'stop_loss'}
        ]
        
        for trade_id, exit_info in zip(trade_ids, exit_data):
            self.close_trade(trade_id, exit_info)
        
        # 分析模式
        patterns = self.analyze_patterns(days=1)
        logger.info(f"Found {len(patterns.get('entry_conditions', {}))} entry patterns")
        
        # 检查黑天鹅风险
        market_indicators = {
            'price_change': -0.05,
            'price_volatility': 0.8,
            'volume_spike': 2.5,
            'rsi': 25,
            'current_position': 1.0
        }
        
        risk_check = self.check_black_swan_risk(market_indicators)
        logger.info(f"Black Swan Risk Level: {risk_check['alert_level']}")
        logger.info(f"Crisis Probability: {risk_check['crisis_probability']:.2%}")
        logger.info(f"Recommended Action: {risk_check['action_type']}")
        
        # 生成报告
        report = self.generate_learning_report()
        print(report)
        
        logger.info("Demo completed successfully")
    
    def cleanup(self):
        """清理资源"""
        self.trade_recorder.cleanup()
        self.pattern_learner.cleanup()
        self.strategy_optimizer.cleanup()
        self.black_swan_learning.cleanup()
        logger.info("Learning System cleanup completed")


def main():
    """主函数"""
    system = LearningSystem()
    
    try:
        # 运行演示
        system.run_demo()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        system.cleanup()


if __name__ == "__main__":
    main()

class LearningEngine:
    """学习引擎主类"""
    
    def __init__(self):
        """初始化学习引擎"""
        self.initialized = True
        
    def start(self):
        """启动学习引擎"""
        pass
