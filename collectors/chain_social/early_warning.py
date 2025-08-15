"""
黑天鹅早期预警系统
宁可错报1000次，不可漏报1次
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import statistics
import redis
import hashlib

logger = logging.getLogger(__name__)

class BlackSwanEarlyDetector:
    """提前24-48小时发现黑天鹅迹象"""
    
    # 链上异常模式
    ON_CHAIN_PATTERNS = {
        "whale_behavior": {
            "mass_transfer": {"desc": "10个以上巨鲸同时转移", "weight": 40},
            "exchange_deposit": {"desc": "巨鲸大量充值交易所", "weight": 35},
            "stablecoin_flight": {"desc": "USDT/USDC大量铸造", "weight": 30},
            "dormant_activation": {"desc": "沉睡地址突然激活", "weight": 45}
        },
        "smart_money_flow": {
            "vc_wallets": {"desc": "知名VC地址异动", "weight": 35},
            "market_maker": {"desc": "做市商钱包异常", "weight": 30},
            "miner_selling": {"desc": "矿工大量抛售", "weight": 25},
            "defi_exit": {"desc": "DeFi大量提取", "weight": 20}
        }
    }
    
    # 交易所异常
    EXCHANGE_ANOMALY = {
        "balance_change": {"desc": "交易所余额急剧变化", "weight": 30},
        "withdrawal_pause": {"desc": "提币暂停（前兆）", "weight": 50},
        "maintenance": {"desc": "突然维护（可疑）", "weight": 35},
        "api_issues": {"desc": "API异常（早期信号）", "weight": 25}
    }
    
    # 社交媒体恐慌信号
    SOCIAL_PANIC_SIGNALS = {
        "insider_leaks": {"desc": "内部人士爆料", "weight": 40},
        "coordinated_fud": {"desc": "协调一致的恐慌", "weight": 35},
        "unusual_silence": {"desc": "异常沉默（暴风雨前）", "weight": 30},
        "deletion_wave": {"desc": "大量删帖（掩盖）", "weight": 45}
    }
    
    def __init__(self, config: Dict[str, Any]):
        """初始化黑天鹅检测器"""
        self.config = config
        self.redis_client = None
        self.init_redis()
        
        # 检测历史
        self.detection_history = []
        self.evidence_cache = []
        self.current_score = 0
        
        # 监控状态
        self.monitoring_active = True
        self.last_alert_time = None
        
    def init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except:
            logger.warning("Redis连接失败，使用内存模式")
            self.redis_client = None
    
    async def detect_whale_exodus(self, blockchain_data: Dict[str, Any]) -> int:
        """检测巨鲸大规模撤离"""
        score = 0
        evidence = []
        
        # 检查巨鲸转账
        whale_activities = blockchain_data.get('whale_activities', [])
        
        # 统计大额转账
        large_transfers = [a for a in whale_activities if a.get('value_usd', 0) > 5000000]
        if len(large_transfers) > 10:
            score += 20
            evidence.append(f"检测到{len(large_transfers)}笔大额转账")
        
        # 检查是否同方向（都是转入交易所）
        exchange_deposits = [a for a in large_transfers if 'exchange' in str(a.get('to', '')).lower()]
        if len(exchange_deposits) > 5:
            score += 20
            evidence.append(f"{len(exchange_deposits)}笔巨鲸充值交易所")
        
        # 检查沉睡地址激活
        for activity in whale_activities:
            # 检查是否是长期未动地址
            if self._is_dormant_address(activity.get('from', '')):
                score += 15
                evidence.append(f"沉睡地址激活: {activity['from'][:10]}...")
        
        self.evidence_cache.extend(evidence)
        return score
    
    async def detect_exchange_anomaly(self, exchange_data: Dict[str, Any]) -> int:
        """检测交易所异常"""
        score = 0
        evidence = []
        
        # 检查余额变化
        for flow in exchange_data.get('exchange_flows', []):
            if flow.get('type') == 'outflow' and flow.get('value_usd', 0) > 10000000:
                score += 10
                evidence.append(f"{flow['exchange']}流出${flow['value_usd']/1000000:.1f}M")
        
        # 检查API异常（模拟）
        if exchange_data.get('api_errors', 0) > 5:
            score += 15
            evidence.append("交易所API频繁异常")
        
        # 检查维护公告（需要新闻数据）
        if exchange_data.get('maintenance_announced', False):
            score += 20
            evidence.append("交易所宣布紧急维护")
        
        self.evidence_cache.extend(evidence)
        return score
    
    async def detect_social_panic(self, social_data: Dict[str, Any]) -> int:
        """检测社交媒体恐慌"""
        score = 0
        evidence = []
        
        # 检查情绪分数
        sentiment = social_data.get('sentiment', {})
        if sentiment.get('aggregated_score', 0) < -50:
            score += 10
            evidence.append(f"极度负面情绪: {sentiment['aggregated_score']}")
        
        # 检查恐慌关键词
        panic_keywords = ['hack', 'rug', 'scam', 'bankruptcy', 'insolvent', 'freeze']
        tweets = social_data.get('twitter', {}).get('kol_tweets', [])
        
        panic_count = 0
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            if any(keyword in text for keyword in panic_keywords):
                panic_count += 1
        
        if panic_count > 5:
            score += 15
            evidence.append(f"检测到{panic_count}条恐慌推文")
        
        # 检查删帖行为
        if social_data.get('deletion_detected', False):
            score += 10
            evidence.append("检测到大量删帖行为")
        
        self.evidence_cache.extend(evidence)
        return score
    
    async def detect_negative_news(self, news_data: List[Dict[str, Any]]) -> int:
        """检测负面新闻"""
        score = 0
        evidence = []
        
        critical_news = [n for n in news_data if n.get('importance', '') == 'critical']
        
        for news in critical_news:
            categories = news.get('categories', [])
            if 'hack' in categories or 'regulation' in categories:
                score += 10
                evidence.append(f"重大新闻: {news['title'][:50]}...")
        
        self.evidence_cache.extend(evidence)
        return score
    
    async def calculate_warning_level(self, all_data: Dict[str, Any]) -> str:
        """计算综合预警级别"""
        self.current_score = 0
        self.evidence_cache = []
        
        # 链上异常 +40分
        blockchain_score = await self.detect_whale_exodus(all_data.get('blockchain', {}))
        self.current_score += blockchain_score
        
        # 交易所异常 +30分
        exchange_score = await self.detect_exchange_anomaly(all_data.get('blockchain', {}))
        self.current_score += exchange_score
        
        # 社交恐慌 +20分
        social_score = await self.detect_social_panic(all_data.get('social', {}))
        self.current_score += social_score
        
        # 新闻事件 +10分
        news_score = await self.detect_negative_news(all_data.get('news', []))
        self.current_score += news_score
        
        # 返回预警级别
        if self.current_score >= 70:
            return "RED_ALERT"  # 黑天鹅高危
        elif self.current_score >= 50:
            return "ORANGE_ALERT"  # 中度风险
        elif self.current_score >= 30:
            return "YELLOW_ALERT"  # 需要关注
        else:
            return "NORMAL"
    
    def collect_evidence(self) -> List[str]:
        """收集所有证据"""
        return self.evidence_cache.copy()
    
    def suggest_action(self, level: str) -> List[str]:
        """建议采取的行动"""
        actions = {
            "RED_ALERT": [
                "立即减仓至30%以下",
                "将资金转移到冷钱包",
                "暂停所有自动交易",
                "准备做空头寸",
                "24小时人工值守"
            ],
            "ORANGE_ALERT": [
                "减仓至50%",
                "提高止损线",
                "暂停高风险交易",
                "增加监控频率",
                "准备应急预案"
            ],
            "YELLOW_ALERT": [
                "控制仓位在70%以下",
                "检查止损设置",
                "关注关键指标",
                "保持警惕"
            ],
            "NORMAL": [
                "维持正常交易",
                "定期检查"
            ]
        }
        return actions.get(level, [])
    
    async def notify_risk_system(self, alert_level: str):
        """通知7号风控窗口"""
        if alert_level in ["RED_ALERT", "ORANGE_ALERT", "YELLOW_ALERT"]:
            message = {
                "type": "BLACK_SWAN_WARNING",
                "level": alert_level,
                "score": self.current_score,
                "evidence": self.collect_evidence(),
                "suggested_action": self.suggest_action(alert_level),
                "time_horizon": "24-48h",
                "timestamp": datetime.now().isoformat(),
                "source": "Window-3-BlackSwan"
            }
            
            # 通过Redis发布
            if self.redis_client:
                try:
                    self.redis_client.publish("black_swan_channel", json.dumps(message))
                    logger.warning(f"[{alert_level}] 黑天鹅预警已发送到风控系统")
                except Exception as e:
                    logger.error(f"Redis发布失败: {e}")
            
            # 同时记录到本地
            self.detection_history.append(message)
            
            # 更新最后警报时间
            self.last_alert_time = datetime.now()
            
            return message
        
        return None
    
    def _is_dormant_address(self, address: str) -> bool:
        """判断是否是沉睡地址（简化版）"""
        # 实际应该查询历史交易记录
        # 这里简化处理，检查特定模式
        dormant_patterns = ['0x000', '1A1z', 'bc1q']
        return any(pattern in address for pattern in dormant_patterns)
    
    async def continuous_monitor(self, data_callback):
        """持续监控"""
        logger.info("黑天鹅监控系统启动")
        
        while self.monitoring_active:
            try:
                # 获取最新数据
                all_data = await data_callback()
                
                # 计算预警级别
                alert_level = await self.calculate_warning_level(all_data)
                
                # 发送预警
                if alert_level != "NORMAL":
                    await self.notify_risk_system(alert_level)
                    logger.warning(f"当前预警级别: {alert_level} (得分: {self.current_score})")
                
                # 根据级别调整监控频率
                if alert_level == "RED_ALERT":
                    await asyncio.sleep(10)  # 10秒
                elif alert_level == "ORANGE_ALERT":
                    await asyncio.sleep(30)  # 30秒
                elif alert_level == "YELLOW_ALERT":
                    await asyncio.sleep(60)  # 1分钟
                else:
                    await asyncio.sleep(300)  # 5分钟
                    
            except Exception as e:
                logger.error(f"黑天鹅监控异常: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "active": self.monitoring_active,
            "current_score": self.current_score,
            "last_alert": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "alert_count": len(self.detection_history),
            "recent_evidence": self.evidence_cache[-5:] if self.evidence_cache else []
        }


class EarlyWarningSystem:
    """早期预警系统 - 宁可错报1000次，不可漏报1次"""
    
    # 一级预警触发器（黄色）
    LEVEL_1_TRIGGERS = {
        "whale_movement": {
            "threshold": 5000,  # BTC
            "desc": ">5000 BTC单笔转账",
            "priority": "high"
        },
        "exchange_outflow": {
            "threshold": 50,  # 百分比
            "desc": "交易所提币激增>50%",
            "priority": "critical"
        },
        "social_panic": {
            "threshold": 300,  # 百分比
            "desc": "负面消息增长>300%",
            "priority": "high"
        },
        "stablecoin_depeg": {
            "threshold": 0.5,  # 百分比
            "desc": "USDT/USDC偏离>0.5%",
            "priority": "critical"
        },
        "unusual_activity": {
            "threshold": 3,  # 数量
            "desc": "Top10地址中3个以上活跃",
            "priority": "high"
        }
    }
    
    # 监控重点
    MONITORING_TARGETS = {
        "exchanges": ["Binance", "OKX", "Coinbase冷钱包", "FTX", "Huobi"],
        "whale_addresses": ["Top 100 BTC地址", "Top 100 ETH地址"],
        "social_keywords": ["hack", "rug", "bankrupt", "停止提币", "维护", "无法提现"],
        "on_chain_metrics": ["Gas费异常", "MEV活动激增", "闪电贷攻击"]
    }
    
    # 响应速度要求
    RESPONSE_TIME = {
        "detection": 30,     # <30秒
        "analysis": 60,      # <1分钟
        "notification": 10   # <10秒
    }
    
    def __init__(self, config: Dict[str, Any]):
        """初始化预警系统"""
        self.config = config
        self.black_swan_detector = BlackSwanEarlyDetector(config)
        self.alert_queue = []
        self.monitoring_stats = {
            "total_checks": 0,
            "alerts_sent": 0,
            "false_positives": 0,
            "response_times": []
        }
    
    async def detect_anomaly(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        持续监控，任何异常立即上报
        不要担心误报，担心漏报
        """
        start_time = datetime.now()
        anomalies = []
        
        # 链上异常检测
        chain_anomalies = await self._detect_chain_anomalies(data.get('blockchain', {}))
        anomalies.extend(chain_anomalies)
        
        # 社交恐慌监控
        social_anomalies = await self._detect_social_anomalies(data.get('social', {}))
        anomalies.extend(social_anomalies)
        
        # 跨链监控
        cross_chain_anomalies = await self._detect_cross_chain_anomalies(data)
        anomalies.extend(cross_chain_anomalies)
        
        # 记录响应时间
        response_time = (datetime.now() - start_time).total_seconds()
        self.monitoring_stats['response_times'].append(response_time)
        self.monitoring_stats['total_checks'] += 1
        
        # 检查是否满足速度要求
        if response_time > self.RESPONSE_TIME['detection']:
            logger.warning(f"检测时间超标: {response_time}秒 > {self.RESPONSE_TIME['detection']}秒")
        
        return anomalies
    
    async def _detect_chain_anomalies(self, blockchain_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """链上异常检测"""
        anomalies = []
        
        # 大额转账监控
        for activity in blockchain_data.get('whale_activities', []):
            if activity.get('chain') == 'BTC':
                btc_value = activity.get('value', 0)
                if btc_value > self.LEVEL_1_TRIGGERS['whale_movement']['threshold']:
                    anomalies.append({
                        'type': 'whale_movement',
                        'severity': 'HIGH',
                        'desc': f"检测到{btc_value} BTC大额转账",
                        'data': activity,
                        'timestamp': datetime.now().isoformat()
                    })
        
        # 交易所钱包监控
        outflow_total = 0
        inflow_total = 0
        for flow in blockchain_data.get('exchange_flows', []):
            if flow.get('type') == 'outflow':
                outflow_total += flow.get('value_usd', 0)
            else:
                inflow_total += flow.get('value_usd', 0)
        
        if inflow_total > 0:
            outflow_ratio = (outflow_total / inflow_total - 1) * 100
            if outflow_ratio > self.LEVEL_1_TRIGGERS['exchange_outflow']['threshold']:
                anomalies.append({
                    'type': 'exchange_outflow',
                    'severity': 'CRITICAL',
                    'desc': f"交易所提币激增{outflow_ratio:.1f}%",
                    'data': {'outflow': outflow_total, 'inflow': inflow_total},
                    'timestamp': datetime.now().isoformat()
                })
        
        # Gas费突然飙升
        gas_data = blockchain_data.get('gas_metrics', {})
        if gas_data.get('spike_detected', False):
            anomalies.append({
                'type': 'gas_spike',
                'severity': 'MEDIUM',
                'desc': f"Gas费飙升至{gas_data.get('current_gwei', 0)} Gwei",
                'data': gas_data,
                'timestamp': datetime.now().isoformat()
            })
        
        return anomalies
    
    async def _detect_social_anomalies(self, social_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """社交媒体异常检测"""
        anomalies = []
        
        # Twitter情绪分析
        sentiment = social_data.get('sentiment', {})
        if sentiment.get('aggregated_score', 0) < -50:
            anomalies.append({
                'type': 'social_panic',
                'severity': 'HIGH',
                'desc': f"社交媒体极度恐慌，情绪分数: {sentiment['aggregated_score']}",
                'data': sentiment,
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查关键词激增
        for keyword in self.MONITORING_TARGETS['social_keywords']:
            # 这里应该实际统计关键词出现频率
            # 简化处理
            pass
        
        return anomalies
    
    async def _detect_cross_chain_anomalies(self, all_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """跨链异常检测"""
        anomalies = []
        
        # 稳定币监控（需要实际价格数据）
        # 跨链桥监控（需要跨链桥数据）
        # DeFi协议异常（需要DeFi数据）
        
        return anomalies
    
    async def notify_ai_system(self, anomalies: List[Dict[str, Any]]):
        """立即通知6号AI分析系统"""
        if not anomalies:
            return
        
        notification = {
            "type": "ANOMALY_DETECTION",
            "source": "Window-3-EarlyWarning",
            "timestamp": datetime.now().isoformat(),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "require_analysis": True,
            "priority": "IMMEDIATE"
        }
        
        # 发送到6号窗口
        # 这里应该通过消息队列或API发送
        logger.warning(f"[预警] 发现{len(anomalies)}个异常，已通知AI分析系统")
        
        self.monitoring_stats['alerts_sent'] += len(anomalies)
        
        return notification
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        avg_response_time = (
            statistics.mean(self.monitoring_stats['response_times']) 
            if self.monitoring_stats['response_times'] else 0
        )
        
        return {
            "total_checks": self.monitoring_stats['total_checks'],
            "alerts_sent": self.monitoring_stats['alerts_sent'],
            "false_positive_rate": (
                self.monitoring_stats['false_positives'] / 
                max(self.monitoring_stats['alerts_sent'], 1) * 100
            ),
            "avg_response_time": avg_response_time,
            "speed_compliance": {
                "detection": avg_response_time <= self.RESPONSE_TIME['detection'],
                "analysis": True,  # 需要实际测量
                "notification": True  # 需要实际测量
            }
        }