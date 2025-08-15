"""
黑天鹅事件学习工具 - Window 9组件
从历史黑天鹅事件中学习，识别相似模式
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from collections import defaultdict


class BlackSwanLearning:
    """从历史黑天鹅事件中学习"""
    
    def __init__(self, base_path: str = "learning_data"):
        """
        初始化黑天鹅学习器
        
        Args:
            base_path: 学习数据存储基础路径
        """
        self.base_path = Path(base_path)
        self.patterns_path = self.base_path / "patterns"
        self.patterns_path.mkdir(parents=True, exist_ok=True)
        
        # 历史黑天鹅事件数据库
        self.historical_events = self._init_historical_events()
        
        # 模式识别阈值
        self.similarity_threshold = 0.65
        
        # 当前市场警告级别
        self.warning_levels = {
            "LOW": 0.3,
            "MEDIUM": 0.5,
            "HIGH": 0.7,
            "CRITICAL": 0.9
        }
        
    def _init_historical_events(self) -> Dict:
        """初始化历史黑天鹅事件数据"""
        return {
            "FTX_2022": {
                "date": "2022-11-08",
                "duration_days": 6,
                "max_drawdown": -0.98,
                "early_signals": [
                    "Alameda资产负债表泄露",
                    "FTT代币大量抛售",
                    "币安CEO发推质疑",
                    "用户提现激增",
                    "链上大额转移异常"
                ],
                "cascade_speed": "6天归零",
                "affected_assets": ["FTT", "SOL", "SRM"],
                "lessons": [
                    "流动性危机信号要立即响应",
                    "中心化交易所风险需要持续监控",
                    "关联资产会产生连锁反应"
                ],
                "opportunity": "做空FTT获利500%+",
                "pattern_features": {
                    "liquidity_crisis": 1.0,
                    "regulatory_risk": 0.3,
                    "technical_failure": 0.1,
                    "market_manipulation": 0.6,
                    "cascade_effect": 0.9
                }
            },
            "LUNA_2022": {
                "date": "2022-05-07",
                "duration_days": 3,
                "max_drawdown": -0.999,
                "early_signals": [
                    "UST轻微脱锚",
                    "Curve池失衡",
                    "LFG储备耗尽",
                    "恐慌性抛售开始",
                    "死亡螺旋形成"
                ],
                "cascade_speed": "3天归零",
                "affected_assets": ["LUNA", "UST", "ANC", "MIR"],
                "lessons": [
                    "算法稳定币脱锚风险极高",
                    "死亡螺旋一旦开始难以逆转",
                    "早期脱锚信号必须重视"
                ],
                "opportunity": "做空LUNA获利1000%+",
                "pattern_features": {
                    "liquidity_crisis": 0.7,
                    "regulatory_risk": 0.2,
                    "technical_failure": 0.9,
                    "market_manipulation": 0.4,
                    "cascade_effect": 1.0
                }
            },
            "312_2020": {
                "date": "2020-03-12",
                "duration_days": 1,
                "max_drawdown": -0.50,
                "early_signals": [
                    "传统市场恐慌",
                    "原油价格战",
                    "COVID-19全球蔓延",
                    "流动性枯竭",
                    "连环爆仓"
                ],
                "cascade_speed": "24小时跌50%",
                "affected_assets": ["BTC", "ETH", "全市场"],
                "lessons": [
                    "外部黑天鹅会传导到加密市场",
                    "流动性危机导致无差别抛售",
                    "极端恐慌是抄底良机"
                ],
                "opportunity": "3850美元抄底BTC",
                "pattern_features": {
                    "liquidity_crisis": 1.0,
                    "regulatory_risk": 0.0,
                    "technical_failure": 0.2,
                    "market_manipulation": 0.1,
                    "cascade_effect": 0.8
                }
            },
            "SVB_2023": {
                "date": "2023-03-10",
                "duration_days": 3,
                "max_drawdown": -0.25,
                "early_signals": [
                    "硅谷银行挤兑",
                    "USDC脱锚",
                    "银行业危机蔓延",
                    "监管介入",
                    "稳定币信任危机"
                ],
                "cascade_speed": "3天恢复",
                "affected_assets": ["USDC", "DAI", "FRAX"],
                "lessons": [
                    "传统银行风险会影响稳定币",
                    "监管介入可快速稳定市场",
                    "脱锚可能是暂时的"
                ],
                "opportunity": "USDC 0.87美元抄底",
                "pattern_features": {
                    "liquidity_crisis": 0.6,
                    "regulatory_risk": 0.8,
                    "technical_failure": 0.0,
                    "market_manipulation": 0.2,
                    "cascade_effect": 0.5
                }
            },
            "CELSIUS_2022": {
                "date": "2022-06-12",
                "duration_days": 30,
                "max_drawdown": -0.95,
                "early_signals": [
                    "提现暂停",
                    "流动性问题传闻",
                    "CEL代币异常波动",
                    "大户撤资",
                    "死亡螺旋风险"
                ],
                "cascade_speed": "30天破产",
                "affected_assets": ["CEL", "借贷市场"],
                "lessons": [
                    "CeFi平台风险不容忽视",
                    "高收益背后往往是高风险",
                    "提现限制是重大危险信号"
                ],
                "opportunity": "提前撤出资金",
                "pattern_features": {
                    "liquidity_crisis": 0.9,
                    "regulatory_risk": 0.4,
                    "technical_failure": 0.1,
                    "market_manipulation": 0.3,
                    "cascade_effect": 0.6
                }
            }
        }
        
    def analyze_current_vs_historical(self, current_signals: List[str]) -> List[Dict]:
        """
        对比当前信号与历史事件
        
        Args:
            current_signals: 当前市场信号列表
            
        Returns:
            相似度分析结果
        """
        similarities = []
        
        for event_name, event_data in self.historical_events.items():
            similarity_score = self._calculate_similarity(current_signals, event_data)
            
            if similarity_score > self.similarity_threshold:
                similarities.append({
                    "event": event_name,
                    "date": event_data["date"],
                    "similarity": similarity_score,
                    "matched_signals": self._find_matched_signals(current_signals, event_data["early_signals"]),
                    "suggested_action": event_data.get("opportunity", ""),
                    "lessons": event_data["lessons"],
                    "risk_level": self._calculate_risk_level(similarity_score),
                    "cascade_speed": event_data["cascade_speed"],
                    "max_drawdown": event_data["max_drawdown"]
                })
                
        # 按相似度排序
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities
        
    def _calculate_similarity(self, current_signals: List[str], event_data: Dict) -> float:
        """
        计算信号相似度
        
        Args:
            current_signals: 当前信号
            event_data: 历史事件数据
            
        Returns:
            相似度分数(0-1)
        """
        if not current_signals:
            return 0.0
            
        historical_signals = event_data.get("early_signals", [])
        
        # 基于关键词匹配
        matched_count = 0
        for current in current_signals:
            current_lower = current.lower()
            for historical in historical_signals:
                historical_lower = historical.lower()
                
                # 检查关键词匹配
                if self._check_keyword_match(current_lower, historical_lower):
                    matched_count += 1
                    break
                    
        # 计算基础相似度
        base_similarity = matched_count / max(len(historical_signals), len(current_signals))
        
        # 考虑模式特征加权
        pattern_similarity = self._calculate_pattern_similarity(current_signals, event_data.get("pattern_features", {}))
        
        # 综合相似度
        final_similarity = base_similarity * 0.6 + pattern_similarity * 0.4
        
        return min(final_similarity, 1.0)
        
    def _check_keyword_match(self, signal1: str, signal2: str) -> bool:
        """检查关键词匹配"""
        keywords = [
            "流动性", "liquidity",
            "脱锚", "depeg",
            "爆仓", "liquidation",
            "挤兑", "bank run",
            "破产", "bankruptcy",
            "监管", "regulatory",
            "黑客", "hack",
            "漏洞", "exploit",
            "恐慌", "panic",
            "抛售", "sell-off",
            "提现", "withdrawal",
            "死亡螺旋", "death spiral"
        ]
        
        for keyword in keywords:
            if keyword in signal1 and keyword in signal2:
                return True
                
        # 模糊匹配
        words1 = set(signal1.split())
        words2 = set(signal2.split())
        
        # 如果有超过30%的词匹配，认为相似
        if len(words1) > 0 and len(words2) > 0:
            intersection = words1.intersection(words2)
            match_ratio = len(intersection) / min(len(words1), len(words2))
            if match_ratio > 0.3:
                return True
                
        return False
        
    def _calculate_pattern_similarity(self, current_signals: List[str], pattern_features: Dict) -> float:
        """计算模式特征相似度"""
        current_features = self._extract_pattern_features(current_signals)
        
        if not pattern_features or not current_features:
            return 0.0
            
        # 计算特征向量的余弦相似度
        similarity = 0.0
        total_weight = 0.0
        
        for feature, weight in pattern_features.items():
            if feature in current_features:
                similarity += weight * current_features[feature]
                total_weight += weight
                
        if total_weight > 0:
            return similarity / total_weight
            
        return 0.0
        
    def _extract_pattern_features(self, signals: List[str]) -> Dict:
        """从信号中提取模式特征"""
        features = {
            "liquidity_crisis": 0.0,
            "regulatory_risk": 0.0,
            "technical_failure": 0.0,
            "market_manipulation": 0.0,
            "cascade_effect": 0.0
        }
        
        signal_text = " ".join(signals).lower()
        
        # 流动性危机特征
        if any(word in signal_text for word in ["流动性", "liquidity", "提现", "withdrawal", "挤兑"]):
            features["liquidity_crisis"] = 0.8
            
        # 监管风险特征
        if any(word in signal_text for word in ["监管", "regulatory", "SEC", "政策", "禁令"]):
            features["regulatory_risk"] = 0.7
            
        # 技术故障特征
        if any(word in signal_text for word in ["黑客", "hack", "漏洞", "exploit", "故障", "bug"]):
            features["technical_failure"] = 0.8
            
        # 市场操纵特征
        if any(word in signal_text for word in ["操纵", "manipulation", "巨鲸", "whale", "砸盘"]):
            features["market_manipulation"] = 0.6
            
        # 级联效应特征
        if any(word in signal_text for word in ["连锁", "cascade", "传染", "蔓延", "螺旋"]):
            features["cascade_effect"] = 0.7
            
        return features
        
    def _find_matched_signals(self, current_signals: List[str], historical_signals: List[str]) -> List[str]:
        """找出匹配的信号"""
        matched = []
        
        for current in current_signals:
            for historical in historical_signals:
                if self._check_keyword_match(current.lower(), historical.lower()):
                    matched.append(f"{current} ≈ {historical}")
                    break
                    
        return matched
        
    def _calculate_risk_level(self, similarity: float) -> str:
        """计算风险级别"""
        if similarity >= 0.9:
            return "CRITICAL"
        elif similarity >= 0.7:
            return "HIGH"
        elif similarity >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
            
    def has_similar_pattern(self, current_signal: Dict, historical_data: Dict) -> bool:
        """
        检查是否有相似模式
        
        Args:
            current_signal: 当前信号
            historical_data: 历史数据
            
        Returns:
            是否相似
        """
        # 提取当前信号的特征
        current_features = []
        
        if "signals" in current_signal:
            current_features = current_signal["signals"]
        elif "description" in current_signal:
            current_features = [current_signal["description"]]
            
        if not current_features:
            return False
            
        # 计算相似度
        similarity = self._calculate_similarity(current_features, historical_data)
        
        return similarity > self.similarity_threshold
        
    def learn_from_new_event(self, event_data: Dict) -> bool:
        """
        从新的黑天鹅事件中学习
        
        Args:
            event_data: 新事件数据
            
        Returns:
            是否成功添加
        """
        event_name = event_data.get("name", f"Event_{datetime.now().strftime('%Y%m%d')}")
        
        # 验证必要字段
        required_fields = ["date", "early_signals", "lessons", "max_drawdown"]
        for field in required_fields:
            if field not in event_data:
                print(f"缺少必要字段: {field}")
                return False
                
        # 添加到历史事件库
        self.historical_events[event_name] = event_data
        
        # 保存到文件
        self._save_events_database()
        
        return True
        
    def _save_events_database(self):
        """保存事件数据库"""
        db_path = self.patterns_path / "black_swan_events.json"
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(self.historical_events, f, ensure_ascii=False, indent=2)
            
    def generate_risk_report(self, current_signals: List[str]) -> Dict:
        """
        生成风险报告
        
        Args:
            current_signals: 当前市场信号
            
        Returns:
            风险报告
        """
        similarities = self.analyze_current_vs_historical(current_signals)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_signals": current_signals,
            "risk_assessment": {
                "overall_risk": "LOW",
                "confidence": 0.0,
                "similar_events": [],
                "recommended_actions": []
            },
            "historical_matches": similarities[:3]  # 最相似的3个事件
        }
        
        if similarities:
            # 计算总体风险
            max_similarity = similarities[0]["similarity"]
            
            if max_similarity >= 0.9:
                report["risk_assessment"]["overall_risk"] = "CRITICAL"
            elif max_similarity >= 0.7:
                report["risk_assessment"]["overall_risk"] = "HIGH"
            elif max_similarity >= 0.5:
                report["risk_assessment"]["overall_risk"] = "MEDIUM"
                
            report["risk_assessment"]["confidence"] = max_similarity
            
            # 提取行动建议
            for event in similarities[:2]:
                if event["suggested_action"]:
                    report["risk_assessment"]["recommended_actions"].append(event["suggested_action"])
                    
                report["risk_assessment"]["similar_events"].append({
                    "event": event["event"],
                    "similarity": event["similarity"],
                    "lessons": event["lessons"]
                })
                
        return report


if __name__ == "__main__":
    # 测试代码
    learner = BlackSwanLearning()
    
    # 模拟当前市场信号
    current_signals = [
        "大型交易所提现延迟",
        "稳定币出现轻微脱锚",
        "链上大额转移激增",
        "市场恐慌情绪上升",
        "流动性指标恶化"
    ]
    
    print("🦢 黑天鹅模式分析")
    print(f"当前信号: {current_signals}")
    
    # 分析相似度
    similarities = learner.analyze_current_vs_historical(current_signals)
    
    if similarities:
        print(f"\n⚠️ 发现相似历史事件:")
        for sim in similarities[:3]:
            print(f"\n事件: {sim['event']}")
            print(f"相似度: {sim['similarity']:.1%}")
            print(f"风险级别: {sim['risk_level']}")
            print(f"级联速度: {sim['cascade_speed']}")
            print(f"最大回撤: {sim['max_drawdown']:.1%}")
            print(f"建议行动: {sim['suggested_action']}")
            print(f"经验教训:")
            for lesson in sim['lessons']:
                print(f"  - {lesson}")
    else:
        print("\n✅ 未发现高相似度历史事件")
        
    # 生成风险报告
    report = learner.generate_risk_report(current_signals)
    print(f"\n📊 风险评估报告:")
    print(f"总体风险: {report['risk_assessment']['overall_risk']}")
    print(f"置信度: {report['risk_assessment']['confidence']:.1%}")
    if report['risk_assessment']['recommended_actions']:
        print(f"建议行动:")
        for action in report['risk_assessment']['recommended_actions']:
            print(f"  - {action}")