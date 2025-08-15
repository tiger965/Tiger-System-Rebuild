"""
Window 3 - 数据链整合器
负责整合来自Window 2的交易所数据、链上数据、社交数据
发现联动关系并打包成情报包给Window 6
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Window3-Integrator] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataChainIntegrator:
    """
    数据链整合器 - Window 3的核心组件
    整合多源数据，发现关联关系，生成情报包
    """
    
    def __init__(self):
        # 数据缓存
        self.window2_data_cache = {}
        self.chain_data_cache = {}
        self.social_data_cache = {}
        self.news_data_cache = {}
        
        # 数据时效性配置（秒）
        self.data_freshness = {
            "window2": 30,      # Window 2数据30秒内有效
            "chain": 60,        # 链上数据60秒内有效
            "social": 120,      # 社交数据2分钟内有效
            "news": 300         # 新闻数据5分钟内有效
        }
        
        # 关联模式定义
        self.correlation_patterns = {
            "pump_preparation": {
                "required_signals": ["funding_positive", "reserve_increase", "whale_accumulation"],
                "confidence_threshold": 0.7
            },
            "dump_warning": {
                "required_signals": ["funding_negative", "reserve_decrease", "whale_distribution"],
                "confidence_threshold": 0.7
            },
            "fomo_building": {
                "required_signals": ["social_sentiment_high", "volume_surge", "price_breakout"],
                "confidence_threshold": 0.6
            },
            "manipulation_detected": {
                "required_signals": ["unusual_flow", "coordinated_orders", "fake_volume"],
                "confidence_threshold": 0.8
            }
        }

    def receive_window2_data(self, data: Dict) -> bool:
        """
        接收Window 2的数据
        包括：实时价格、资金费率、交易所储备、套利机会等
        """
        try:
            self.window2_data_cache = {
                "timestamp": time.time(),
                "data": data
            }
            logger.info(f"接收Window 2数据: {len(data)} 个数据点")
            return True
        except Exception as e:
            logger.error(f"接收Window 2数据失败: {e}")
            return False

    def receive_chain_data(self, data: Dict) -> bool:
        """
        接收链上数据
        包括：巨鲸转账、Gas费用、DeFi活动等
        """
        try:
            self.chain_data_cache = {
                "timestamp": time.time(),
                "data": data
            }
            logger.info(f"接收链上数据: {len(data)} 个数据点")
            return True
        except Exception as e:
            logger.error(f"接收链上数据失败: {e}")
            return False

    def receive_social_data(self, data: Dict) -> bool:
        """
        接收社交媒体数据
        包括：Twitter情绪、Reddit讨论、KOL动态等
        """
        try:
            self.social_data_cache = {
                "timestamp": time.time(),
                "data": data
            }
            logger.info(f"接收社交数据: {len(data)} 个数据点")
            return True
        except Exception as e:
            logger.error(f"接收社交数据失败: {e}")
            return False

    def receive_news_data(self, data: Dict) -> bool:
        """
        接收新闻数据
        包括：重要公告、监管消息、项目更新等
        """
        try:
            self.news_data_cache = {
                "timestamp": time.time(),
                "data": data
            }
            logger.info(f"接收新闻数据: {len(data)} 个数据点")
            return True
        except Exception as e:
            logger.error(f"接收新闻数据失败: {e}")
            return False

    def analyze_pump_signals(self) -> Optional[Dict]:
        """
        分析拉盘信号
        整合多源数据发现拉盘准备迹象
        """
        signals = []
        confidence = 0
        evidence = []
        
        # 检查Window 2数据
        if self.is_data_fresh("window2"):
            w2_data = self.window2_data_cache["data"]
            
            # 资金费率转正
            if w2_data.get("funding_rates", {}).get("market_sentiment") == "bullish":
                signals.append("funding_positive")
                confidence += 0.3
                evidence.append(f"资金费率转正: {w2_data['funding_rates']}")
            
            # 交易所储备增加
            reserve_change = w2_data.get("exchange_reserves", {}).get("reserve_changes", "")
            if "+" in reserve_change and "BTC" in reserve_change:
                signals.append("reserve_increase")
                confidence += 0.3
                evidence.append(f"BTC储备增加: {reserve_change}")
            
            # 套利机会收窄
            arb_opportunities = w2_data.get("arbitrage_opportunities", [])
            if arb_opportunities and all(opp["percentage"] < 0.05 for opp in arb_opportunities):
                confidence += 0.1
                evidence.append("套利差价收窄，市场趋于一致")
        
        # 检查链上数据
        if self.is_data_fresh("chain"):
            chain_data = self.chain_data_cache["data"]
            
            # 巨鲸吸筹
            if chain_data.get("whale_activity") == "accumulating":
                signals.append("whale_accumulation")
                confidence += 0.3
                evidence.append(f"巨鲸地址增持: {chain_data.get('whale_accumulation', 'N/A')} BTC")
            
            # 交易所流出
            if chain_data.get("exchange_netflow", 0) < -100:  # 净流出超过100 BTC
                confidence += 0.1
                evidence.append(f"交易所净流出: {abs(chain_data['exchange_netflow'])} BTC")
        
        # 检查社交情绪
        if self.is_data_fresh("social"):
            social_data = self.social_data_cache["data"]
            
            # 社交情绪高涨
            if social_data.get("sentiment_score", 0) > 0.7:
                signals.append("social_sentiment_high")
                confidence += 0.2
                evidence.append(f"社交情绪积极: {social_data['sentiment_score']:.2f}")
        
        # 判断是否满足拉盘准备模式
        pattern = self.correlation_patterns["pump_preparation"]
        matched_signals = [s for s in signals if s in pattern["required_signals"]]
        
        if len(matched_signals) >= 2 and confidence >= pattern["confidence_threshold"]:
            return {
                "type": "PUMP_PREPARATION",
                "confidence": min(confidence, 1.0),
                "matched_signals": matched_signals,
                "evidence": evidence,
                "recommendation": "准备做多，建议设置止损，目标价位+3-5%",
                "timestamp": datetime.now().isoformat()
            }
        
        return None

    def analyze_dump_signals(self) -> Optional[Dict]:
        """
        分析砸盘信号
        整合多源数据发现砸盘预警
        """
        signals = []
        confidence = 0
        evidence = []
        
        # 检查Window 2数据
        if self.is_data_fresh("window2"):
            w2_data = self.window2_data_cache["data"]
            
            # 资金费率转负
            if w2_data.get("funding_rates", {}).get("market_sentiment") == "bearish":
                signals.append("funding_negative")
                confidence += 0.3
                evidence.append(f"资金费率转负: {w2_data['funding_rates']}")
            
            # 交易所储备减少
            reserve_change = w2_data.get("exchange_reserves", {}).get("reserve_changes", "")
            if "-" in reserve_change and "BTC" in reserve_change:
                signals.append("reserve_decrease")
                confidence += 0.3
                evidence.append(f"BTC储备减少: {reserve_change}")
        
        # 检查链上数据
        if self.is_data_fresh("chain"):
            chain_data = self.chain_data_cache["data"]
            
            # 巨鲸派发
            if chain_data.get("whale_activity") == "distributing":
                signals.append("whale_distribution")
                confidence += 0.3
                evidence.append(f"巨鲸地址减持: {chain_data.get('whale_distribution', 'N/A')} BTC")
            
            # 交易所流入
            if chain_data.get("exchange_netflow", 0) > 100:  # 净流入超过100 BTC
                confidence += 0.1
                evidence.append(f"交易所净流入: {chain_data['exchange_netflow']} BTC")
        
        # 判断是否满足砸盘预警模式
        pattern = self.correlation_patterns["dump_warning"]
        matched_signals = [s for s in signals if s in pattern["required_signals"]]
        
        if len(matched_signals) >= 2 and confidence >= pattern["confidence_threshold"]:
            return {
                "type": "DUMP_WARNING",
                "confidence": min(confidence, 1.0),
                "matched_signals": matched_signals,
                "evidence": evidence,
                "recommendation": "风险预警，建议减仓或做空，设置止损",
                "timestamp": datetime.now().isoformat()
            }
        
        return None

    def detect_market_manipulation(self) -> Optional[Dict]:
        """
        检测市场操控迹象
        通过异常数据模式发现潜在的市场操控
        """
        manipulation_signs = []
        confidence = 0
        
        # 检查异常资金流动
        if self.is_data_fresh("window2") and self.is_data_fresh("chain"):
            w2_data = self.window2_data_cache["data"]
            chain_data = self.chain_data_cache["data"]
            
            # 检查是否有协同的大额订单
            if w2_data.get("unusual_order_activity", False):
                manipulation_signs.append("协同下单行为")
                confidence += 0.3
            
            # 检查虚假成交量
            real_volume = w2_data.get("real_volume", 0)
            reported_volume = w2_data.get("reported_volume", 1)
            if reported_volume > 0 and real_volume / reported_volume < 0.5:
                manipulation_signs.append("疑似虚假成交量")
                confidence += 0.4
            
            # 检查价格与成交量不匹配
            price_change = w2_data.get("price_change_1h", 0)
            volume_change = w2_data.get("volume_change_1h", 0)
            if abs(price_change) > 2 and volume_change < 10:  # 价格大幅变动但成交量很小
                manipulation_signs.append("价量背离")
                confidence += 0.3
        
        if confidence >= 0.6 and manipulation_signs:
            return {
                "type": "MARKET_MANIPULATION",
                "confidence": min(confidence, 1.0),
                "signs": manipulation_signs,
                "recommendation": "谨慎交易，可能存在市场操控",
                "timestamp": datetime.now().isoformat()
            }
        
        return None

    def generate_intelligence_package(self, symbol: str = "BTC") -> Dict:
        """
        生成综合情报包
        整合所有数据源，提供给Window 6进行AI决策
        """
        package = {
            "window": 3,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "data_sources": {
                "window2": self.get_fresh_data("window2"),
                "chain": self.get_fresh_data("chain"),
                "social": self.get_fresh_data("social"),
                "news": self.get_fresh_data("news")
            },
            "analysis": {},
            "alerts": []
        }
        
        # 添加拉盘信号分析
        pump_analysis = self.analyze_pump_signals()
        if pump_analysis:
            package["analysis"]["pump_signals"] = pump_analysis
            package["alerts"].append({
                "level": "high",
                "type": "pump_preparation",
                "message": pump_analysis["recommendation"]
            })
        
        # 添加砸盘信号分析
        dump_analysis = self.analyze_dump_signals()
        if dump_analysis:
            package["analysis"]["dump_signals"] = dump_analysis
            package["alerts"].append({
                "level": "high",
                "type": "dump_warning",
                "message": dump_analysis["recommendation"]
            })
        
        # 添加市场操控检测
        manipulation = self.detect_market_manipulation()
        if manipulation:
            package["analysis"]["manipulation"] = manipulation
            package["alerts"].append({
                "level": "medium",
                "type": "manipulation_detected",
                "message": manipulation["recommendation"]
            })
        
        # 添加数据质量指标
        package["data_quality"] = {
            "window2_freshness": self.is_data_fresh("window2"),
            "chain_freshness": self.is_data_fresh("chain"),
            "social_freshness": self.is_data_fresh("social"),
            "news_freshness": self.is_data_fresh("news"),
            "overall_confidence": self.calculate_overall_confidence()
        }
        
        return package

    def is_data_fresh(self, source: str) -> bool:
        """检查数据是否新鲜"""
        cache_map = {
            "window2": self.window2_data_cache,
            "chain": self.chain_data_cache,
            "social": self.social_data_cache,
            "news": self.news_data_cache
        }
        
        cache = cache_map.get(source)
        if not cache or "timestamp" not in cache:
            return False
        
        age = time.time() - cache["timestamp"]
        return age <= self.data_freshness.get(source, 60)

    def get_fresh_data(self, source: str) -> Optional[Dict]:
        """获取新鲜数据"""
        if self.is_data_fresh(source):
            cache_map = {
                "window2": self.window2_data_cache,
                "chain": self.chain_data_cache,
                "social": self.social_data_cache,
                "news": self.news_data_cache
            }
            return cache_map.get(source, {}).get("data")
        return None

    def calculate_overall_confidence(self) -> float:
        """计算整体数据置信度"""
        fresh_sources = sum([
            self.is_data_fresh("window2"),
            self.is_data_fresh("chain"),
            self.is_data_fresh("social"),
            self.is_data_fresh("news")
        ])
        return fresh_sources / 4.0

    def clear_old_data(self):
        """清理过期数据"""
        current_time = time.time()
        
        # 清理各个缓存中的过期数据
        for source, max_age in self.data_freshness.items():
            cache_map = {
                "window2": self.window2_data_cache,
                "chain": self.chain_data_cache,
                "social": self.social_data_cache,
                "news": self.news_data_cache
            }
            
            cache = cache_map.get(source)
            if cache and "timestamp" in cache:
                if current_time - cache["timestamp"] > max_age * 2:  # 超过2倍时效性则清理
                    cache.clear()
                    logger.info(f"清理过期的{source}数据")


# 信号关联分析器
class SignalCorrelator:
    """
    信号关联分析器
    发现不同数据源之间的关联关系
    """
    
    def __init__(self):
        self.correlation_history = []
        self.pattern_library = {
            "whale_leads_price": {
                "description": "巨鲸动作领先价格变动",
                "time_window": 3600,  # 1小时内
                "confidence_boost": 0.2
            },
            "social_confirms_onchain": {
                "description": "社交情绪验证链上活动",
                "time_window": 7200,  # 2小时内
                "confidence_boost": 0.15
            },
            "funding_follows_reserve": {
                "description": "资金费率跟随储备变化",
                "time_window": 1800,  # 30分钟内
                "confidence_boost": 0.25
            }
        }

    def find_correlations(self, data_points: List[Dict]) -> List[Dict]:
        """
        发现数据点之间的关联关系
        """
        correlations = []
        
        # 按时间排序数据点
        sorted_data = sorted(data_points, key=lambda x: x.get("timestamp", 0))
        
        # 寻找时间相关的模式
        for i, point1 in enumerate(sorted_data):
            for point2 in sorted_data[i+1:]:
                time_diff = point2["timestamp"] - point1["timestamp"]
                
                # 检查是否匹配已知模式
                for pattern_name, pattern in self.pattern_library.items():
                    if time_diff <= pattern["time_window"]:
                        if self.matches_pattern(point1, point2, pattern_name):
                            correlations.append({
                                "pattern": pattern_name,
                                "description": pattern["description"],
                                "confidence_boost": pattern["confidence_boost"],
                                "data_points": [point1, point2],
                                "time_correlation": time_diff
                            })
        
        return correlations

    def matches_pattern(self, point1: Dict, point2: Dict, pattern_name: str) -> bool:
        """
        检查两个数据点是否匹配特定模式
        """
        if pattern_name == "whale_leads_price":
            # 巨鲸转账后价格变动
            return (point1.get("type") == "whale_transfer" and 
                   point2.get("type") == "price_change")
        
        elif pattern_name == "social_confirms_onchain":
            # 社交情绪与链上活动一致
            return (point1.get("type") == "social_sentiment" and 
                   point2.get("type") == "chain_activity")
        
        elif pattern_name == "funding_follows_reserve":
            # 储备变化后资金费率调整
            return (point1.get("type") == "reserve_change" and 
                   point2.get("type") == "funding_rate")
        
        return False


# 情报包装器
class IntelligencePackager:
    """
    情报包装器
    将原始数据和分析结果打包成结构化的情报包
    """
    
    def __init__(self):
        self.package_version = "1.0"
        self.package_counter = 0

    def create_package(self, 
                       raw_data: Dict,
                       analysis: Dict,
                       correlations: List[Dict],
                       priority: str = "normal") -> Dict:
        """
        创建标准化的情报包
        """
        self.package_counter += 1
        
        package = {
            "package_id": f"W3_PKG_{self.package_counter}_{int(time.time())}",
            "version": self.package_version,
            "source": "window3_data_collector",
            "created_at": datetime.now().isoformat(),
            "priority": priority,
            "summary": self.generate_summary(analysis),
            "raw_data": raw_data,
            "analysis": analysis,
            "correlations": correlations,
            "actionable_insights": self.extract_actionable_insights(analysis, correlations),
            "metadata": {
                "data_sources": list(raw_data.keys()),
                "analysis_modules": list(analysis.keys()),
                "correlation_count": len(correlations),
                "confidence_score": self.calculate_confidence(analysis, correlations)
            }
        }
        
        return package

    def generate_summary(self, analysis: Dict) -> str:
        """
        生成分析摘要
        """
        summaries = []
        
        if "pump_signals" in analysis:
            summaries.append(f"检测到拉盘准备信号 (置信度: {analysis['pump_signals']['confidence']:.1%})")
        
        if "dump_signals" in analysis:
            summaries.append(f"检测到砸盘风险信号 (置信度: {analysis['dump_signals']['confidence']:.1%})")
        
        if "manipulation" in analysis:
            summaries.append(f"发现市场操控迹象 (置信度: {analysis['manipulation']['confidence']:.1%})")
        
        if not summaries:
            summaries.append("市场状态正常，无特殊信号")
        
        return " | ".join(summaries)

    def extract_actionable_insights(self, analysis: Dict, correlations: List[Dict]) -> List[Dict]:
        """
        提取可执行的洞察
        """
        insights = []
        
        # 从分析中提取洞察
        for key, value in analysis.items():
            if isinstance(value, dict) and "recommendation" in value:
                insights.append({
                    "type": key,
                    "action": value["recommendation"],
                    "confidence": value.get("confidence", 0.5),
                    "evidence": value.get("evidence", [])
                })
        
        # 从关联中提取洞察
        for correlation in correlations:
            if correlation["confidence_boost"] >= 0.2:
                insights.append({
                    "type": "correlation",
                    "action": f"注意: {correlation['description']}",
                    "confidence": correlation["confidence_boost"],
                    "pattern": correlation["pattern"]
                })
        
        # 按置信度排序
        insights.sort(key=lambda x: x["confidence"], reverse=True)
        
        return insights[:5]  # 返回前5个最重要的洞察

    def calculate_confidence(self, analysis: Dict, correlations: List[Dict]) -> float:
        """
        计算整体置信度分数
        """
        confidence_scores = []
        
        # 收集所有分析的置信度
        for value in analysis.values():
            if isinstance(value, dict) and "confidence" in value:
                confidence_scores.append(value["confidence"])
        
        # 添加关联带来的置信度提升
        for correlation in correlations:
            confidence_scores.append(correlation["confidence_boost"])
        
        if confidence_scores:
            # 加权平均，较高的置信度权重更大
            weighted_sum = sum(score ** 2 for score in confidence_scores)
            weight_total = sum(score for score in confidence_scores)
            if weight_total > 0:
                return min(weighted_sum / weight_total, 1.0)
        
        return 0.5  # 默认置信度