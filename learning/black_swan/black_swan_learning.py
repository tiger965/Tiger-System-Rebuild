"""
黑天鹅学习模块
从历史黑天鹅事件中学习，优化预警和响应策略
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from ..config.config import BLACK_SWAN_CONFIG, DATABASE_CONFIG, LOG_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'black_swan_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class BlackSwanEvent:
    """黑天鹅事件数据结构"""
    event_name: str
    event_date: str
    event_type: str  # crash/squeeze/hack/regulation
    early_signals: List[str]
    missed_signals: List[str]
    cascade_speed: str
    impact_duration: str
    max_drawdown: float
    recovery_time: str
    opportunity_type: str  # short/long/avoid
    potential_return: float
    lessons_learned: List[str]


@dataclass
class AlertRecord:
    """预警记录"""
    alert_id: str
    timestamp: str
    alert_level: int  # 1-3级
    alert_type: str
    trigger_conditions: Dict[str, Any]
    market_indicators: Dict[str, float]
    response_action: str
    actual_outcome: Optional[str]  # 实际结果
    was_correct: Optional[bool]  # 预警是否正确


class BlackSwanLearning:
    """黑天鹅学习系统"""
    
    def __init__(self):
        self.config = BLACK_SWAN_CONFIG
        self.db_path = DATABASE_CONFIG["patterns"]["path"].parent / "black_swan.db"
        
        # 初始化数据库
        self._init_database()
        
        # 加载历史事件
        self.historical_events = self._load_historical_events()
        
        # 初始化异常检测模型
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        
        # 预警阈值
        self.alert_thresholds = self.config["alert_levels"]
        
        logger.info("BlackSwanLearning initialized")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 历史事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_events (
                event_name TEXT PRIMARY KEY,
                event_date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                early_signals TEXT,
                missed_signals TEXT,
                cascade_speed TEXT,
                impact_duration TEXT,
                max_drawdown REAL,
                recovery_time TEXT,
                opportunity_type TEXT,
                potential_return REAL,
                lessons_learned TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 预警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_records (
                alert_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                alert_level INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                trigger_conditions TEXT,
                market_indicators TEXT,
                response_action TEXT,
                actual_outcome TEXT,
                was_correct BOOLEAN,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 模式识别表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crisis_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                indicators TEXT NOT NULL,
                confidence REAL,
                success_rate REAL,
                avg_warning_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 响应策略表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_strategies (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                alert_level INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                position_adjustment REAL,
                success_rate REAL,
                avg_loss_avoided REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_historical_events(self) -> Dict[str, BlackSwanEvent]:
        """加载历史黑天鹅事件"""
        events = {}
        
        # FTX崩溃事件
        events["FTX_2022"] = BlackSwanEvent(
            event_name="FTX_2022",
            event_date="2022-11-08",
            event_type="exchange_collapse",
            early_signals=[
                "Alameda资产负债表泄露",
                "FTT代币大额转移",
                "CZ推特发声",
                "用户提现延迟"
            ],
            missed_signals=[
                "SBF频繁辟谣",
                "内部人士抛售",
                "审计报告缺失"
            ],
            cascade_speed="6天",
            impact_duration="2周",
            max_drawdown=0.85,
            recovery_time="未完全恢复",
            opportunity_type="short",
            potential_return=10.0,  # 1000%
            lessons_learned=[
                "交易所代币风险极高",
                "关注链上大额转移",
                "重视社交媒体信号",
                "及时响应提现异常"
            ]
        )
        
        # LUNA崩盘事件
        events["LUNA_2022"] = BlackSwanEvent(
            event_name="LUNA_2022",
            event_date="2022-05-09",
            event_type="algorithmic_failure",
            early_signals=[
                "UST轻微脱锚",
                "Anchor协议TVL下降",
                "大额UST抛售",
                "LFG储备消耗"
            ],
            missed_signals=[
                "Do Kwon过度自信",
                "算法稳定币根本缺陷",
                "死亡螺旋风险"
            ],
            cascade_speed="3天",
            impact_duration="1周",
            max_drawdown=0.99,
            recovery_time="永不恢复",
            opportunity_type="short",
            potential_return=50.0,  # 5000%
            lessons_learned=[
                "算法稳定币存在根本缺陷",
                "关注脱锚程度和频率",
                "TVL快速下降是危险信号",
                "死亡螺旋一旦开始难以逆转"
            ]
        )
        
        # 312暴跌事件
        events["312_2020"] = BlackSwanEvent(
            event_name="312_2020",
            event_date="2020-03-12",
            event_type="market_crash",
            early_signals=[
                "传统市场恐慌",
                "原油价格战",
                "疫情全球扩散",
                "避险情绪上升"
            ],
            missed_signals=[
                "流动性危机征兆",
                "杠杆过高",
                "矿工抛售压力"
            ],
            cascade_speed="24小时",
            impact_duration="1个月",
            max_drawdown=0.50,
            recovery_time="2个月",
            opportunity_type="long",
            potential_return=3.0,  # 300%
            lessons_learned=[
                "传统市场联动性增强",
                "流动性危机传导快速",
                "极端恐慌产生抄底机会",
                "V型反转可能性"
            ]
        )
        
        # SVB银行危机
        events["SVB_2023"] = BlackSwanEvent(
            event_name="SVB_2023",
            event_date="2023-03-10",
            event_type="banking_crisis",
            early_signals=[
                "银行股下跌",
                "USDC脱锚",
                "存款挤兑",
                "监管介入"
            ],
            missed_signals=[
                "利率风险暴露",
                "资产负债期限错配",
                "科技行业资金链紧张"
            ],
            cascade_speed="2天",
            impact_duration="1周",
            max_drawdown=0.15,
            recovery_time="1周",
            opportunity_type="avoid",
            potential_return=0.2,  # 20%避损
            lessons_learned=[
                "稳定币也有脱锚风险",
                "传统金融风险会传导",
                "监管反应影响市场",
                "分散化资产更安全"
            ]
        )
        
        # 保存到数据库
        for event in events.values():
            self._save_historical_event(event)
        
        return events
    
    def analyze_historical_events(self) -> Dict[str, Any]:
        """分析历史黑天鹅事件"""
        analysis = {
            "event_types": {},
            "early_signals": {},
            "cascade_patterns": {},
            "recovery_patterns": {},
            "opportunity_analysis": {}
        }
        
        for event in self.historical_events.values():
            # 统计事件类型
            event_type = event.event_type
            if event_type not in analysis["event_types"]:
                analysis["event_types"][event_type] = {
                    "count": 0,
                    "avg_drawdown": [],
                    "avg_recovery_days": [],
                    "common_signals": []
                }
            
            analysis["event_types"][event_type]["count"] += 1
            analysis["event_types"][event_type]["avg_drawdown"].append(event.max_drawdown)
            
            # 统计早期信号
            for signal in event.early_signals:
                if signal not in analysis["early_signals"]:
                    analysis["early_signals"][signal] = 0
                analysis["early_signals"][signal] += 1
            
            # 分析级联速度
            analysis["cascade_patterns"][event.event_name] = {
                "speed": event.cascade_speed,
                "impact": event.max_drawdown,
                "duration": event.impact_duration
            }
            
            # 分析机会
            analysis["opportunity_analysis"][event.event_name] = {
                "type": event.opportunity_type,
                "potential_return": event.potential_return,
                "timing": event.cascade_speed
            }
        
        # 计算统计值
        for event_type, data in analysis["event_types"].items():
            if data["avg_drawdown"]:
                data["avg_drawdown"] = np.mean(data["avg_drawdown"])
        
        return analysis
    
    def record_alert(self, 
                    alert_level: int,
                    alert_type: str,
                    trigger_conditions: Dict[str, Any],
                    market_indicators: Dict[str, float],
                    response_action: str) -> str:
        """记录预警"""
        alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = AlertRecord(
            alert_id=alert_id,
            timestamp=datetime.now().isoformat(),
            alert_level=alert_level,
            alert_type=alert_type,
            trigger_conditions=trigger_conditions,
            market_indicators=market_indicators,
            response_action=response_action,
            actual_outcome=None,
            was_correct=None
        )
        
        # 保存到数据库
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alert_records
            (alert_id, timestamp, alert_level, alert_type,
             trigger_conditions, market_indicators, response_action)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert.alert_id,
            alert.timestamp,
            alert.alert_level,
            alert.alert_type,
            json.dumps(alert.trigger_conditions),
            json.dumps(alert.market_indicators),
            alert.response_action
        ))
        
        conn.commit()
        conn.close()
        
        logger.warning(f"Alert recorded: Level {alert_level} - {alert_type}")
        
        return alert_id
    
    def update_alert_outcome(self, 
                           alert_id: str,
                           actual_outcome: str,
                           was_correct: bool):
        """更新预警结果"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alert_records
            SET actual_outcome = ?, was_correct = ?
            WHERE alert_id = ?
        ''', (actual_outcome, was_correct, alert_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Alert {alert_id} outcome updated: {actual_outcome}")
    
    def optimize_response_strategy(self) -> Dict[str, Any]:
        """优化响应策略"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有已验证的预警
        cursor.execute('''
            SELECT * FROM alert_records
            WHERE was_correct IS NOT NULL
        ''')
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not alerts:
            logger.warning("No verified alerts for optimization")
            return {}
        
        # 分析预警效果
        optimization_results = {
            "alert_accuracy": {},
            "response_effectiveness": {},
            "threshold_adjustments": {}
        }
        
        # 按预警级别分析
        for level in [1, 2, 3]:
            level_alerts = [a for a in alerts if a['alert_level'] == level]
            if level_alerts:
                correct = sum(1 for a in level_alerts if a['was_correct'])
                accuracy = correct / len(level_alerts)
                
                optimization_results["alert_accuracy"][f"level_{level}"] = {
                    "accuracy": accuracy,
                    "total_alerts": len(level_alerts),
                    "correct_alerts": correct
                }
                
                # 建议阈值调整
                if accuracy < 0.5:  # 准确率太低
                    optimization_results["threshold_adjustments"][f"level_{level}"] = {
                        "current_threshold": self.alert_thresholds[f"level_{level}"]["threshold"],
                        "suggested_threshold": self.alert_thresholds[f"level_{level}"]["threshold"] * 1.2,
                        "reason": "Too many false positives"
                    }
                elif accuracy > 0.9:  # 准确率很高，可以更敏感
                    optimization_results["threshold_adjustments"][f"level_{level}"] = {
                        "current_threshold": self.alert_thresholds[f"level_{level}"]["threshold"],
                        "suggested_threshold": self.alert_thresholds[f"level_{level}"]["threshold"] * 0.9,
                        "reason": "Can be more sensitive"
                    }
        
        # 按预警类型分析
        alert_types = set(a['alert_type'] for a in alerts)
        for alert_type in alert_types:
            type_alerts = [a for a in alerts if a['alert_type'] == alert_type]
            correct = sum(1 for a in type_alerts if a['was_correct'])
            
            optimization_results["response_effectiveness"][alert_type] = {
                "accuracy": correct / len(type_alerts),
                "sample_size": len(type_alerts)
            }
        
        return optimization_results
    
    def update_trigger_thresholds(self, adjustments: Dict[str, float]):
        """更新触发阈值"""
        for level, adjustment in adjustments.items():
            if level in self.alert_thresholds:
                old_threshold = self.alert_thresholds[level]["threshold"]
                new_threshold = old_threshold * adjustment
                self.alert_thresholds[level]["threshold"] = new_threshold
                
                logger.info(f"Updated {level} threshold: {old_threshold:.3f} -> {new_threshold:.3f}")
    
    def train_pattern_recognition(self, 
                                market_data: pd.DataFrame) -> Dict[str, Any]:
        """训练模式识别模型"""
        if market_data.empty:
            logger.warning("No market data for training")
            return {}
        
        # 特征工程
        features = self._extract_crisis_features(market_data)
        
        if features.shape[0] < 100:
            logger.warning("Insufficient data for training")
            return {}
        
        # 标准化
        scaled_features = self.scaler.fit_transform(features)
        
        # 训练异常检测模型
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # 假设10%的数据是异常
            random_state=42
        )
        self.anomaly_detector.fit(scaled_features)
        
        # 评估模型
        anomaly_scores = self.anomaly_detector.score_samples(scaled_features)
        predictions = self.anomaly_detector.predict(scaled_features)
        
        # 统计结果
        n_anomalies = sum(predictions == -1)
        anomaly_rate = n_anomalies / len(predictions)
        
        results = {
            "model_type": "IsolationForest",
            "training_samples": len(features),
            "anomaly_rate": anomaly_rate,
            "anomaly_count": n_anomalies,
            "score_threshold": np.percentile(anomaly_scores, 10)
        }
        
        logger.info(f"Pattern recognition model trained: {n_anomalies} anomalies detected")
        
        return results
    
    def _extract_crisis_features(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """提取危机特征"""
        features = pd.DataFrame()
        
        # 价格特征
        if 'close' in market_data.columns:
            features['price_change'] = market_data['close'].pct_change()
            features['price_volatility'] = market_data['close'].rolling(24).std()
            features['price_drawdown'] = (market_data['close'] / market_data['close'].rolling(24).max() - 1)
        
        # 成交量特征
        if 'volume' in market_data.columns:
            features['volume_spike'] = market_data['volume'] / market_data['volume'].rolling(24).mean()
            features['volume_change'] = market_data['volume'].pct_change()
        
        # 技术指标
        if 'close' in market_data.columns:
            # RSI
            delta = market_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # 移动平均偏离
            features['ma_deviation'] = (market_data['close'] / market_data['close'].rolling(50).mean() - 1)
        
        # 市场宽度指标
        if 'high' in market_data.columns and 'low' in market_data.columns:
            features['price_range'] = (market_data['high'] - market_data['low']) / market_data['close']
        
        return features.dropna()
    
    def predict_crisis_probability(self, 
                                  current_indicators: Dict[str, float]) -> float:
        """预测危机概率"""
        if self.anomaly_detector is None:
            logger.warning("Model not trained yet")
            return 0.0
        
        # 准备特征
        features = pd.DataFrame([current_indicators])
        
        # 确保特征顺序一致
        expected_features = self.scaler.feature_names_in_ if hasattr(self.scaler, 'feature_names_in_') else features.columns
        features = features.reindex(columns=expected_features, fill_value=0)
        
        # 标准化
        scaled_features = self.scaler.transform(features)
        
        # 预测
        anomaly_score = self.anomaly_detector.score_samples(scaled_features)[0]
        
        # 转换为概率（越低的分数表示越可能是异常）
        # 使用sigmoid函数将分数映射到0-1之间
        crisis_probability = 1 / (1 + np.exp(anomaly_score * 10))
        
        return crisis_probability
    
    def get_recommended_action(self, 
                              crisis_probability: float,
                              current_position: float) -> Dict[str, Any]:
        """获取推荐操作"""
        action = {
            "reduce_position": 0,
            "hedge_position": False,
            "stop_loss": None,
            "alert_level": 0,
            "action_type": "none"
        }
        
        # 根据危机概率确定警报级别
        if crisis_probability > self.alert_thresholds["level_3"]["threshold"]:
            action["alert_level"] = 3
            action["action_type"] = "exit"
            action["reduce_position"] = current_position  # 清仓
            action["stop_loss"] = "immediate"
            
        elif crisis_probability > self.alert_thresholds["level_2"]["threshold"]:
            action["alert_level"] = 2
            action["action_type"] = "reduce"
            action["reduce_position"] = current_position * 0.5  # 减仓50%
            action["hedge_position"] = True
            action["stop_loss"] = "tight"
            
        elif crisis_probability > self.alert_thresholds["level_1"]["threshold"]:
            action["alert_level"] = 1
            action["action_type"] = "monitor"
            action["reduce_position"] = current_position * 0.2  # 减仓20%
            action["stop_loss"] = "normal"
        
        return action
    
    def learn_from_new_event(self, 
                            event_name: str,
                            event_data: Dict[str, Any]):
        """从新事件中学习"""
        # 创建事件对象
        new_event = BlackSwanEvent(
            event_name=event_name,
            event_date=event_data.get("date", datetime.now().isoformat()),
            event_type=event_data.get("type", "unknown"),
            early_signals=event_data.get("early_signals", []),
            missed_signals=event_data.get("missed_signals", []),
            cascade_speed=event_data.get("cascade_speed", "unknown"),
            impact_duration=event_data.get("impact_duration", "unknown"),
            max_drawdown=event_data.get("max_drawdown", 0),
            recovery_time=event_data.get("recovery_time", "unknown"),
            opportunity_type=event_data.get("opportunity_type", "avoid"),
            potential_return=event_data.get("potential_return", 0),
            lessons_learned=event_data.get("lessons_learned", [])
        )
        
        # 保存到数据库
        self._save_historical_event(new_event)
        
        # 更新历史事件
        self.historical_events[event_name] = new_event
        
        # 提取新的模式
        self._extract_patterns_from_event(new_event)
        
        logger.info(f"Learned from new event: {event_name}")
    
    def _extract_patterns_from_event(self, event: BlackSwanEvent):
        """从事件中提取模式"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 提取信号模式
        for signal in event.early_signals:
            cursor.execute('''
                INSERT OR REPLACE INTO crisis_patterns
                (pattern_name, pattern_type, indicators, confidence, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                f"{event.event_type}_{signal}",
                "early_warning",
                json.dumps({"signal": signal, "event": event.event_name}),
                0.8,  # 初始置信度
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _save_historical_event(self, event: BlackSwanEvent):
        """保存历史事件"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO historical_events
            (event_name, event_date, event_type, early_signals,
             missed_signals, cascade_speed, impact_duration,
             max_drawdown, recovery_time, opportunity_type,
             potential_return, lessons_learned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_name,
            event.event_date,
            event.event_type,
            json.dumps(event.early_signals),
            json.dumps(event.missed_signals),
            event.cascade_speed,
            event.impact_duration,
            event.max_drawdown,
            event.recovery_time,
            event.opportunity_type,
            event.potential_return,
            json.dumps(event.lessons_learned)
        ))
        
        conn.commit()
        conn.close()
    
    def get_crisis_patterns(self) -> List[Dict]:
        """获取危机模式"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM crisis_patterns
            ORDER BY confidence DESC
        ''')
        
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 解析JSON字段
        for pattern in patterns:
            pattern['indicators'] = json.loads(pattern['indicators'])
        
        return patterns
    
    def generate_crisis_report(self) -> str:
        """生成危机学习报告"""
        analysis = self.analyze_historical_events()
        optimization = self.optimize_response_strategy()
        patterns = self.get_crisis_patterns()
        
        report = f"""
========== 黑天鹅学习报告 ==========
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. 历史事件分析
   - 已学习事件数：{len(self.historical_events)}
   - 事件类型分布：{json.dumps(list(analysis['event_types'].keys()), ensure_ascii=False)}
   - 常见早期信号：{json.dumps(list(analysis['early_signals'].keys())[:5], ensure_ascii=False)}

2. 预警准确率
"""
        
        if optimization.get("alert_accuracy"):
            for level, stats in optimization["alert_accuracy"].items():
                report += f"   - {level}: {stats['accuracy']:.2%} ({stats['correct_alerts']}/{stats['total_alerts']})\n"
        
        report += f"""
3. 识别模式数量：{len(patterns)}

4. 关键教训
"""
        
        for event_name, event in list(self.historical_events.items())[:3]:
            report += f"   【{event_name}】\n"
            for lesson in event.lessons_learned[:2]:
                report += f"   - {lesson}\n"
        
        report += """
5. 优化建议
"""
        
        if optimization.get("threshold_adjustments"):
            for level, adjustment in optimization["threshold_adjustments"].items():
                report += f"   - {level}: 建议调整阈值至 {adjustment['suggested_threshold']:.3f}\n"
        
        report += """
==========================================
"""
        
        return report
    
    def cleanup(self):
        """清理资源"""
        logger.info("BlackSwanLearning cleanup completed")