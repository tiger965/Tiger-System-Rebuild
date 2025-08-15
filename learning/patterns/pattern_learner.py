"""
模式识别引擎
识别成功和失败的交易模式，包括机会识别学习
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from mlxtend.frequent_patterns import apriori, association_rules
import sqlite3

from ..config.config import DATABASE_CONFIG, PATTERN_CONFIG, LOG_DIR
from ..records.trade_recorder import TradeRecorder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'pattern_learner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PatternLearner:
    """模式学习器"""
    
    def __init__(self, trade_recorder: TradeRecorder):
        self.trade_recorder = trade_recorder
        self.db_path = DATABASE_CONFIG["patterns"]["path"]
        self.cache_size = DATABASE_CONFIG["patterns"]["cache_size"]
        
        # 模式识别配置
        self.clustering_config = PATTERN_CONFIG["clustering"]
        self.association_config = PATTERN_CONFIG["association"]
        self.success_threshold = PATTERN_CONFIG["success_threshold"]
        self.failure_threshold = PATTERN_CONFIG["failure_threshold"]
        
        # 初始化数据库
        self._init_database()
        
        # 缓存
        self.pattern_cache = {}
        
        logger.info("PatternLearner initialized")
    
    def _init_database(self):
        """初始化模式数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 成功模式表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS success_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                conditions TEXT NOT NULL,
                success_rate REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                confidence REAL NOT NULL,
                metadata TEXT,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 失败模式表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failure_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                conditions TEXT NOT NULL,
                failure_rate REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                risk_level TEXT,
                metadata TEXT,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 机会识别模式表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunity_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_type TEXT NOT NULL,
                trigger_conditions TEXT NOT NULL,
                success_rate REAL NOT NULL,
                avg_return REAL,
                risk_reward_ratio REAL,
                optimal_position_size REAL,
                timing_window TEXT,
                sample_size INTEGER NOT NULL,
                metadata TEXT,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_success_rate ON success_patterns(success_rate)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_failure_rate ON failure_patterns(failure_rate)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_opportunity_success ON opportunity_patterns(success_rate)')
        
        conn.commit()
        conn.close()
    
    def analyze_entry_conditions(self, days: int = 30) -> Dict[str, Any]:
        """分析入场条件的成功率"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        if not trades:
            logger.warning("No closed trades found for analysis")
            return {}
        
        # 按入场原因分组
        entry_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "total_pnl": 0})
        
        for trade in trades:
            entry_reason = trade.get('entry_reason', 'unknown')
            pnl = trade.get('exit_pnl', 0)
            
            if pnl > 0:
                entry_stats[entry_reason]["wins"] += 1
            else:
                entry_stats[entry_reason]["losses"] += 1
            
            entry_stats[entry_reason]["total_pnl"] += pnl
        
        # 计算成功率
        patterns = {}
        for reason, stats in entry_stats.items():
            total = stats["wins"] + stats["losses"]
            success_rate = stats["wins"] / total if total > 0 else 0
            
            patterns[reason] = {
                "success_rate": success_rate,
                "total_trades": total,
                "total_pnl": stats["total_pnl"],
                "avg_pnl": stats["total_pnl"] / total if total > 0 else 0
            }
            
            # 保存成功模式
            if success_rate >= self.success_threshold and total >= 10:
                self._save_success_pattern(
                    pattern_type="entry_condition",
                    pattern_name=reason,
                    conditions={"entry_reason": reason},
                    success_rate=success_rate,
                    sample_size=total
                )
            
            # 保存失败模式
            elif success_rate <= self.failure_threshold and total >= 10:
                self._save_failure_pattern(
                    pattern_type="entry_condition",
                    pattern_name=reason,
                    conditions={"entry_reason": reason},
                    failure_rate=1 - success_rate,
                    sample_size=total
                )
        
        return patterns
    
    def analyze_indicator_combinations(self, days: int = 30) -> Dict[str, Any]:
        """分析指标组合的效果"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        if not trades:
            return {}
        
        # 提取指标数据
        indicator_data = []
        labels = []
        
        for trade in trades:
            indicators_str = trade.get('entry_indicators', '{}')
            try:
                indicators = json.loads(indicators_str)
                if indicators:
                    indicator_data.append(indicators)
                    labels.append(1 if trade.get('exit_pnl', 0) > 0 else 0)
            except json.JSONDecodeError:
                continue
        
        if len(indicator_data) < 10:
            logger.warning("Not enough indicator data for analysis")
            return {}
        
        # 转换为DataFrame
        df = pd.DataFrame(indicator_data)
        
        # 标准化数据
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df.fillna(0))
        
        # K-means聚类
        n_clusters = min(self.clustering_config["n_clusters"], len(scaled_data) // 5)
        kmeans = KMeans(
            n_clusters=n_clusters,
            max_iter=self.clustering_config["max_iter"],
            random_state=42
        )
        clusters = kmeans.fit_predict(scaled_data)
        
        # 分析每个聚类的成功率
        cluster_stats = defaultdict(lambda: {"wins": 0, "total": 0})
        
        for cluster, label in zip(clusters, labels):
            cluster_stats[cluster]["total"] += 1
            if label == 1:
                cluster_stats[cluster]["wins"] += 1
        
        # 找出成功的指标组合
        successful_combos = {}
        for cluster_id, stats in cluster_stats.items():
            success_rate = stats["wins"] / stats["total"] if stats["total"] > 0 else 0
            
            if success_rate >= self.success_threshold and stats["total"] >= 5:
                # 获取该聚类的中心点特征
                center = scaler.inverse_transform([kmeans.cluster_centers_[cluster_id]])[0]
                feature_importance = dict(zip(df.columns, center))
                
                successful_combos[f"combo_{cluster_id}"] = {
                    "success_rate": success_rate,
                    "sample_size": stats["total"],
                    "key_indicators": feature_importance
                }
                
                # 保存成功模式
                self._save_success_pattern(
                    pattern_type="indicator_combo",
                    pattern_name=f"combo_{cluster_id}",
                    conditions=feature_importance,
                    success_rate=success_rate,
                    sample_size=stats["total"]
                )
        
        return successful_combos
    
    def analyze_market_states(self, days: int = 30) -> Dict[str, Any]:
        """分析不同市场状态下的表现"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        if not trades:
            return {}
        
        # 按市场状态分组
        market_stats = defaultdict(lambda: {
            "wins": 0, 
            "losses": 0, 
            "total_pnl": 0,
            "durations": []
        })
        
        for trade in trades:
            market_state = trade.get('entry_market_state', 'unknown')
            pnl = trade.get('exit_pnl', 0)
            duration = trade.get('exit_duration', 0)
            
            if pnl > 0:
                market_stats[market_state]["wins"] += 1
            else:
                market_stats[market_state]["losses"] += 1
            
            market_stats[market_state]["total_pnl"] += pnl
            market_stats[market_state]["durations"].append(duration)
        
        # 分析结果
        patterns = {}
        for state, stats in market_stats.items():
            total = stats["wins"] + stats["losses"]
            if total == 0:
                continue
            
            success_rate = stats["wins"] / total
            avg_duration = np.mean(stats["durations"]) if stats["durations"] else 0
            
            patterns[state] = {
                "success_rate": success_rate,
                "total_trades": total,
                "total_pnl": stats["total_pnl"],
                "avg_pnl": stats["total_pnl"] / total,
                "avg_duration": avg_duration
            }
            
            # 保存有意义的模式
            if total >= 10:
                if success_rate >= self.success_threshold:
                    self._save_success_pattern(
                        pattern_type="market_state",
                        pattern_name=state,
                        conditions={"market_state": state},
                        success_rate=success_rate,
                        sample_size=total
                    )
                elif success_rate <= self.failure_threshold:
                    self._save_failure_pattern(
                        pattern_type="market_state",
                        pattern_name=state,
                        conditions={"market_state": state},
                        failure_rate=1 - success_rate,
                        sample_size=total
                    )
        
        return patterns
    
    def analyze_time_patterns(self, days: int = 30) -> Dict[str, Any]:
        """分析时间模式"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        if not trades:
            return {}
        
        # 按时间段分组
        time_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "total_pnl": 0})
        
        for trade in trades:
            timestamp_str = trade.get('entry_timestamp', '')
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                hour = timestamp.hour
                day_of_week = timestamp.weekday()
                
                # 按小时分组
                hour_key = f"hour_{hour:02d}"
                # 按星期分组
                dow_key = f"dow_{day_of_week}"
                # 按时段分组
                if 0 <= hour < 6:
                    period_key = "night"
                elif 6 <= hour < 12:
                    period_key = "morning"
                elif 12 <= hour < 18:
                    period_key = "afternoon"
                else:
                    period_key = "evening"
                
                pnl = trade.get('exit_pnl', 0)
                
                for key in [hour_key, dow_key, period_key]:
                    if pnl > 0:
                        time_stats[key]["wins"] += 1
                    else:
                        time_stats[key]["losses"] += 1
                    time_stats[key]["total_pnl"] += pnl
            
            except (ValueError, AttributeError):
                continue
        
        # 分析结果
        patterns = {}
        for time_key, stats in time_stats.items():
            total = stats["wins"] + stats["losses"]
            if total < 5:  # 样本太少
                continue
            
            success_rate = stats["wins"] / total
            
            patterns[time_key] = {
                "success_rate": success_rate,
                "total_trades": total,
                "total_pnl": stats["total_pnl"],
                "avg_pnl": stats["total_pnl"] / total
            }
            
            # 保存显著的时间模式
            if total >= 20:
                if success_rate >= self.success_threshold:
                    self._save_success_pattern(
                        pattern_type="time_pattern",
                        pattern_name=time_key,
                        conditions={"time": time_key},
                        success_rate=success_rate,
                        sample_size=total
                    )
        
        return patterns
    
    def analyze_opportunity_patterns(self, days: int = 30) -> Dict[str, Any]:
        """分析机会识别模式"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        if not trades:
            return {}
        
        opportunity_stats = defaultdict(lambda: {
            "successful": [],
            "failed": [],
            "returns": [],
            "risk_rewards": []
        })
        
        for trade in trades:
            # 提取机会相关信息
            entry_reason = trade.get('entry_reason', '')
            pnl = trade.get('exit_pnl', 0)
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            
            if not entry_price:
                continue
            
            # 计算收益率
            return_rate = (exit_price - entry_price) / entry_price if entry_price > 0 else 0
            
            # 识别机会类型
            opportunity_type = self._identify_opportunity_type(trade)
            
            if pnl > 0:
                opportunity_stats[opportunity_type]["successful"].append(trade)
            else:
                opportunity_stats[opportunity_type]["failed"].append(trade)
            
            opportunity_stats[opportunity_type]["returns"].append(return_rate)
            
            # 计算风险收益比
            if 'stop_loss' in trade and 'take_profit' in trade:
                risk = abs(entry_price - trade['stop_loss'])
                reward = abs(trade['take_profit'] - entry_price)
                if risk > 0:
                    opportunity_stats[opportunity_type]["risk_rewards"].append(reward / risk)
        
        # 分析并保存机会模式
        patterns = {}
        for opp_type, stats in opportunity_stats.items():
            total = len(stats["successful"]) + len(stats["failed"])
            if total < 5:
                continue
            
            success_rate = len(stats["successful"]) / total
            avg_return = np.mean(stats["returns"]) if stats["returns"] else 0
            avg_risk_reward = np.mean(stats["risk_rewards"]) if stats["risk_rewards"] else 0
            
            patterns[opp_type] = {
                "success_rate": success_rate,
                "total_opportunities": total,
                "avg_return": avg_return,
                "avg_risk_reward": avg_risk_reward,
                "successful_examples": len(stats["successful"]),
                "failed_examples": len(stats["failed"])
            }
            
            # 保存有价值的机会模式
            if total >= 10 and success_rate >= 0.5:
                self._save_opportunity_pattern(
                    opportunity_type=opp_type,
                    trigger_conditions=self._extract_trigger_conditions(stats["successful"]),
                    success_rate=success_rate,
                    avg_return=avg_return,
                    risk_reward_ratio=avg_risk_reward,
                    sample_size=total
                )
        
        return patterns
    
    def _identify_opportunity_type(self, trade: Dict) -> str:
        """识别机会类型"""
        entry_reason = trade.get('entry_reason', '').lower()
        market_state = trade.get('entry_market_state', '').lower()
        
        if 'breakout' in entry_reason:
            return 'breakout'
        elif 'reversal' in entry_reason:
            return 'reversal'
        elif 'momentum' in entry_reason:
            return 'momentum'
        elif 'dip' in entry_reason:
            return 'dip_buy'
        elif 'trend' in market_state:
            return 'trend_following'
        else:
            return 'general'
    
    def _extract_trigger_conditions(self, successful_trades: List[Dict]) -> Dict:
        """提取成功交易的触发条件"""
        if not successful_trades:
            return {}
        
        # 提取共同特征
        common_indicators = defaultdict(list)
        
        for trade in successful_trades:
            indicators_str = trade.get('entry_indicators', '{}')
            try:
                indicators = json.loads(indicators_str)
                for key, value in indicators.items():
                    if isinstance(value, (int, float)):
                        common_indicators[key].append(value)
            except json.JSONDecodeError:
                continue
        
        # 计算平均值和范围
        trigger_conditions = {}
        for key, values in common_indicators.items():
            if values:
                trigger_conditions[key] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }
        
        return trigger_conditions
    
    def identify_common_mistakes(self, days: int = 30) -> List[Dict]:
        """识别常见错误"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        # 筛选亏损交易
        losing_trades = [t for t in trades if t.get('exit_pnl', 0) < 0]
        
        if not losing_trades:
            return []
        
        mistakes = []
        
        # 分析止损过早
        early_stops = [t for t in losing_trades if t.get('exit_reason', '') == 'stop_loss']
        if len(early_stops) > len(losing_trades) * 0.5:
            mistakes.append({
                "type": "early_stop_loss",
                "frequency": len(early_stops) / len(losing_trades),
                "avg_loss": np.mean([t['exit_pnl'] for t in early_stops]),
                "suggestion": "Consider wider stop loss or better entry timing"
            })
        
        # 分析追高
        high_entries = []
        for trade in losing_trades:
            indicators_str = trade.get('entry_indicators', '{}')
            try:
                indicators = json.loads(indicators_str)
                if indicators.get('rsi', 0) > 70:  # RSI超买
                    high_entries.append(trade)
            except json.JSONDecodeError:
                continue
        
        if len(high_entries) > len(losing_trades) * 0.3:
            mistakes.append({
                "type": "chasing_highs",
                "frequency": len(high_entries) / len(losing_trades),
                "avg_loss": np.mean([t['exit_pnl'] for t in high_entries]),
                "suggestion": "Avoid entering when RSI > 70"
            })
        
        # 保存失败模式
        for mistake in mistakes:
            self._save_failure_pattern(
                pattern_type="common_mistake",
                pattern_name=mistake["type"],
                conditions={"mistake_type": mistake["type"]},
                failure_rate=mistake["frequency"],
                sample_size=len(losing_trades),
                risk_level="high" if mistake["frequency"] > 0.5 else "medium"
            )
        
        return mistakes
    
    def mine_association_rules(self, days: int = 30) -> List[Dict]:
        """挖掘关联规则"""
        trades = self.trade_recorder.get_recent_trades(days=days, status='closed')
        
        if len(trades) < 20:
            logger.warning("Not enough trades for association rule mining")
            return []
        
        # 准备数据
        transactions = []
        for trade in trades:
            transaction = []
            
            # 添加成功/失败标签
            if trade.get('exit_pnl', 0) > 0:
                transaction.append('profitable')
            else:
                transaction.append('loss')
            
            # 添加市场状态
            market_state = trade.get('entry_market_state', '')
            if market_state:
                transaction.append(f"market_{market_state}")
            
            # 添加入场原因
            entry_reason = trade.get('entry_reason', '')
            if entry_reason:
                transaction.append(f"reason_{entry_reason}")
            
            # 添加时间特征
            timestamp_str = trade.get('entry_timestamp', '')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    transaction.append(f"hour_{timestamp.hour // 6}")  # 分成4个时段
                except ValueError:
                    pass
            
            transactions.append(transaction)
        
        # 转换为适合关联规则挖掘的格式
        unique_items = set(item for transaction in transactions for item in transaction)
        encoded_transactions = []
        
        for transaction in transactions:
            encoded_transaction = {item: (item in transaction) for item in unique_items}
            encoded_transactions.append(encoded_transaction)
        
        df = pd.DataFrame(encoded_transactions)
        
        # 使用Apriori算法
        try:
            frequent_itemsets = apriori(
                df, 
                min_support=self.association_config["min_support"],
                use_colnames=True
            )
            
            if not frequent_itemsets.empty:
                rules = association_rules(
                    frequent_itemsets,
                    metric="confidence",
                    min_threshold=self.association_config["min_confidence"]
                )
                
                # 筛选有价值的规则
                valuable_rules = []
                for _, rule in rules.iterrows():
                    if 'profitable' in rule['consequents']:
                        valuable_rules.append({
                            "conditions": list(rule['antecedents']),
                            "result": list(rule['consequents']),
                            "confidence": rule['confidence'],
                            "support": rule['support'],
                            "lift": rule['lift']
                        })
                
                return valuable_rules
        
        except Exception as e:
            logger.error(f"Association rule mining failed: {e}")
        
        return []
    
    def _save_success_pattern(self, 
                             pattern_type: str,
                             pattern_name: str,
                             conditions: Dict,
                             success_rate: float,
                             sample_size: int,
                             confidence: float = 0.95):
        """保存成功模式"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO success_patterns 
            (pattern_type, pattern_name, conditions, success_rate, 
             sample_size, confidence, metadata, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern_type,
            pattern_name,
            json.dumps(conditions),
            success_rate,
            sample_size,
            confidence,
            json.dumps({"discovered": datetime.now().isoformat()}),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved success pattern: {pattern_name} (success_rate: {success_rate:.2%})")
    
    def _save_failure_pattern(self,
                            pattern_type: str,
                            pattern_name: str,
                            conditions: Dict,
                            failure_rate: float,
                            sample_size: int,
                            risk_level: str = "medium"):
        """保存失败模式"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO failure_patterns
            (pattern_type, pattern_name, conditions, failure_rate,
             sample_size, risk_level, metadata, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern_type,
            pattern_name,
            json.dumps(conditions),
            failure_rate,
            sample_size,
            risk_level,
            json.dumps({"discovered": datetime.now().isoformat()}),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved failure pattern: {pattern_name} (failure_rate: {failure_rate:.2%})")
    
    def _save_opportunity_pattern(self,
                                 opportunity_type: str,
                                 trigger_conditions: Dict,
                                 success_rate: float,
                                 avg_return: float,
                                 risk_reward_ratio: float,
                                 sample_size: int):
        """保存机会识别模式"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO opportunity_patterns
            (opportunity_type, trigger_conditions, success_rate,
             avg_return, risk_reward_ratio, optimal_position_size,
             timing_window, sample_size, metadata, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            opportunity_type,
            json.dumps(trigger_conditions),
            success_rate,
            avg_return,
            risk_reward_ratio,
            min(1.0, success_rate * risk_reward_ratio / 2),  # 简单的仓位计算
            "24h",  # 默认时间窗口
            sample_size,
            json.dumps({"discovered": datetime.now().isoformat()}),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved opportunity pattern: {opportunity_type} (success: {success_rate:.2%}, return: {avg_return:.2%})")
    
    def get_best_patterns(self, pattern_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """获取最佳模式"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute('''
                SELECT * FROM success_patterns
                WHERE pattern_type = ?
                ORDER BY success_rate DESC
                LIMIT ?
            ''', (pattern_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM success_patterns
                ORDER BY success_rate DESC
                LIMIT ?
            ''', (limit,))
        
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 解析JSON字段
        for pattern in patterns:
            pattern['conditions'] = json.loads(pattern['conditions'])
            if pattern['metadata']:
                pattern['metadata'] = json.loads(pattern['metadata'])
        
        return patterns
    
    def get_risk_patterns(self, limit: int = 10) -> List[Dict]:
        """获取风险模式"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM failure_patterns
            ORDER BY failure_rate DESC
            LIMIT ?
        ''', (limit,))
        
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 解析JSON字段
        for pattern in patterns:
            pattern['conditions'] = json.loads(pattern['conditions'])
            if pattern['metadata']:
                pattern['metadata'] = json.loads(pattern['metadata'])
        
        return patterns
    
    def cleanup(self):
        """清理资源"""
        self.pattern_cache.clear()
        logger.info("PatternLearner cleanup completed")