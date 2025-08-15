"""
窗口指挥官 - 协调控制其他窗口
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class WindowCommander:
    """窗口指挥官 - AI大脑控制其他窗口的中枢"""
    
    def __init__(self):
        """初始化窗口指挥官"""
        # 窗口状态跟踪
        self.window_status = {
            1: {"name": "数据库", "status": "ready", "last_call": None},
            2: {"name": "交易所", "status": "ready", "last_call": None},
            3: {"name": "数据采集", "status": "ready", "last_call": None},
            4: {"name": "计算工具", "status": "ready", "last_call": None},
            7: {"name": "风控执行", "status": "ready", "last_call": None},
            8: {"name": "通知工具", "status": "ready", "last_call": None},
            9: {"name": "学习工具", "status": "ready", "last_call": None}
        }
        
        # 命令队列
        self.command_queue = asyncio.Queue()
        self.command_history = []
        self.max_history = 1000
        
        # 性能统计
        self.call_stats = {}
        self.error_stats = {}
        
        logger.info("窗口指挥官初始化完成")
    
    async def execute_workflow(self, workflow_name: str, params: Dict = None) -> Dict:
        """
        执行预定义的工作流
        """
        workflows = {
            "market_scan": self._workflow_market_scan,
            "risk_assessment": self._workflow_risk_assessment,
            "opportunity_analysis": self._workflow_opportunity_analysis,
            "emergency_response": self._workflow_emergency_response,
            "daily_report": self._workflow_daily_report
        }
        
        if workflow_name not in workflows:
            logger.error(f"未知的工作流: {workflow_name}")
            return {"error": f"Unknown workflow: {workflow_name}"}
        
        logger.info(f"执行工作流: {workflow_name}")
        
        try:
            result = await workflows[workflow_name](params or {})
            return {
                "workflow": workflow_name,
                "status": "success",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"工作流执行失败: {workflow_name} - {e}")
            return {
                "workflow": workflow_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _workflow_market_scan(self, params: Dict) -> Dict:
        """市场扫描工作流"""
        results = {}
        
        # 1. 获取热门币种
        hot_coins = await self.call_window(2, "get_hot_ranking", {
            "exchange": params.get("exchange", "binance"),
            "top": params.get("top", 15)
        })
        results["hot_coins"] = hot_coins
        
        # 2. 获取成交量异动
        volume_surge = await self.call_window(2, "get_volume_surge", {
            "threshold": params.get("volume_threshold", 50),
            "timeframe": params.get("timeframe", "1h")
        })
        results["volume_surge"] = volume_surge
        
        # 3. 获取社交媒体热度
        social_heat = await self.call_window(3, "crawl_twitter", {
            "keyword": "crypto surge",
            "time_range_minutes": 60,
            "get_sentiment": True,
            "min_followers": 10000
        })
        results["social_heat"] = social_heat
        
        # 4. 获取鲸鱼动向
        whale_activity = await self.call_window(3, "track_whale_transfers", {
            "min_amount_usd": 5000000,
            "chains": ["ETH", "BSC", "SOL"],
            "direction": "all"
        })
        results["whale_activity"] = whale_activity
        
        return results
    
    async def _workflow_risk_assessment(self, params: Dict) -> Dict:
        """风险评估工作流"""
        results = {}
        
        # 1. 获取账户状态
        account = await self.call_window(1, "get_account_cache", {
            "user_id": params.get("user_id", "default")
        })
        results["account"] = account
        
        # 2. 计算技术指标
        symbol = params.get("symbol", "BTCUSDT")
        prices = params.get("prices", [])
        
        if prices:
            # RSI
            rsi = await self.call_window(4, "calculate_rsi", {
                "prices": prices,
                "period": 14
            })
            results["rsi"] = rsi
            
            # MACD
            macd = await self.call_window(4, "calculate_macd", {
                "prices": prices,
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            })
            results["macd"] = macd
        
        # 3. 计算凯利仓位
        kelly = await self.call_window(7, "calculate_kelly_position", {
            "win_probability": params.get("win_probability", 0.55),
            "odds": params.get("odds", 2),
            "max_risk": params.get("max_risk", 0.02),
            "account_balance": account.get("balance", 100000) if account else 100000
        })
        results["kelly_position"] = kelly
        
        return results
    
    async def _workflow_opportunity_analysis(self, params: Dict) -> Dict:
        """机会分析工作流"""
        results = {}
        
        # 1. 扫描ValueScan信号
        valuescan = await self.call_window(3, "crawl_valuescan", {
            "signal_type": "opportunities",
            "min_confidence": params.get("min_confidence", 0.7)
        })
        results["valuescan_signals"] = valuescan
        
        # 2. 查找相似历史模式
        if params.get("symbol") and params.get("current_pattern"):
            patterns = await self.call_window(4, "find_similar_patterns", {
                "symbol": params["symbol"],
                "current_pattern": params["current_pattern"],
                "min_similarity": 0.8
            })
            results["similar_patterns"] = patterns
        
        # 3. 获取成功率统计
        success_rate = await self.call_window(1, "get_success_rate", {
            "period": params.get("period", "7d")
        })
        results["success_rate"] = success_rate
        
        return results
    
    async def _workflow_emergency_response(self, params: Dict) -> Dict:
        """紧急响应工作流"""
        results = {}
        
        # 1. 立即发送警报
        alert = await self.call_window(8, "send_emergency_alert", {
            "level": "critical",
            "message": params.get("message", "紧急市场异动"),
            "data": params.get("data", {})
        })
        results["alert_sent"] = alert
        
        # 2. 评估风险
        risk = await self._workflow_risk_assessment(params)
        results["risk_assessment"] = risk
        
        # 3. 执行保护性操作
        if params.get("auto_protect", False):
            # 这里可以执行止损或对冲操作
            protection = await self.call_window(7, "execute_trade", {
                "action": "hedge",
                "symbol": params.get("symbol", "BTCUSDT"),
                "amount": risk.get("kelly_position", 0),
                "order_type": "market"
            })
            results["protection"] = protection
        
        return results
    
    async def _workflow_daily_report(self, params: Dict) -> Dict:
        """每日报告工作流"""
        results = {}
        
        # 1. 获取账户状态
        account = await self.call_window(1, "get_account_cache", {
            "user_id": "default"
        })
        results["account_status"] = account
        
        # 2. 获取今日交易统计
        success_rate = await self.call_window(1, "get_success_rate", {
            "period": "24h"
        })
        results["today_performance"] = success_rate
        
        # 3. 市场概览
        market = await self._workflow_market_scan({})
        results["market_overview"] = market
        
        # 4. 生成报告
        report = self._generate_report(results)
        
        # 5. 发送报告
        await self.call_window(8, "send_daily_report", {
            "report": report
        })
        
        return results
    
    def _generate_report(self, data: Dict) -> str:
        """生成报告文本"""
        report = f"""
=== AI决策系统日报 ===
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

账户状态:
- 总资产: ${data.get('account_status', {}).get('balance', 0):,.2f}
- 今日盈亏: {data.get('today_performance', {}).get('pnl', 0):+.2f}%
- 成功率: {data.get('today_performance', {}).get('success_rate', 0):.1f}%

市场概览:
- 热门币种: {len(data.get('market_overview', {}).get('hot_coins', []))}个
- 成交量异动: {len(data.get('market_overview', {}).get('volume_surge', []))}个
- 鲸鱼活动: {len(data.get('market_overview', {}).get('whale_activity', []))}笔

窗口调用统计:
{self._format_call_stats()}

=== 报告结束 ===
"""
        return report
    
    def _format_call_stats(self) -> str:
        """格式化调用统计"""
        lines = []
        for window_id, stats in self.call_stats.items():
            window_name = self.window_status[window_id]["name"]
            lines.append(f"- Window {window_id} ({window_name}): {stats.get('calls', 0)}次")
        return "\n".join(lines) if lines else "- 无调用记录"
    
    async def call_window(self, window_id: int, function: str, params: Dict) -> Any:
        """
        调用指定窗口的函数
        """
        # 检查窗口是否存在
        if window_id not in self.window_status:
            logger.error(f"无效的窗口ID: {window_id}")
            return None
        
        # 构建命令
        command = {
            "window": window_id,
            "function": function,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录调用
        self._record_call(window_id, function)
        
        # 执行命令（这里应该调用实际的command_interface）
        # 暂时返回模拟数据
        logger.info(f"调用Window {window_id} ({self.window_status[window_id]['name']}): "
                   f"{function}({params})")
        
        # 更新窗口状态
        self.window_status[window_id]["last_call"] = datetime.now()
        
        # 模拟返回
        return self._simulate_window_response(window_id, function, params)
    
    def _record_call(self, window_id: int, function: str):
        """记录调用统计"""
        if window_id not in self.call_stats:
            self.call_stats[window_id] = {"calls": 0, "functions": {}}
        
        self.call_stats[window_id]["calls"] += 1
        
        if function not in self.call_stats[window_id]["functions"]:
            self.call_stats[window_id]["functions"][function] = 0
        self.call_stats[window_id]["functions"][function] += 1
        
        # 添加到历史
        self.command_history.append({
            "window": window_id,
            "function": function,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录数量
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
    
    def _simulate_window_response(self, window_id: int, function: str, params: Dict) -> Any:
        """模拟窗口响应（测试用）"""
        simulated_responses = {
            1: {
                "get_account_cache": {"balance": 100000, "positions": [], "risk": 0.3},
                "record_decision": {"status": "success"},
                "get_success_rate": {"success_rate": 65.5, "total_trades": 100}
            },
            2: {
                "get_hot_ranking": [
                    {"symbol": "BTCUSDT", "price": 67500, "change_24h": 2.5},
                    {"symbol": "ETHUSDT", "price": 3800, "change_24h": 3.2}
                ],
                "get_realtime_price": {"symbol": "BTCUSDT", "price": 67500},
                "get_volume_surge": []
            },
            3: {
                "crawl_twitter": [{"text": "BTC to the moon!", "sentiment": 0.8}],
                "track_whale_transfers": [],
                "crawl_valuescan": []
            },
            4: {
                "calculate_rsi": 55.5,
                "calculate_macd": {"macd": 150, "signal": 140, "histogram": 10},
                "find_similar_patterns": []
            },
            7: {
                "calculate_kelly_position": 0.025,
                "execute_trade": {"order_id": "123456", "status": "filled"}
            },
            8: {
                "send_emergency_alert": {"status": "sent"},
                "send_daily_report": {"status": "sent"}
            }
        }
        
        window_responses = simulated_responses.get(window_id, {})
        return window_responses.get(function, {"status": "simulated"})
    
    def get_window_status(self) -> Dict:
        """获取所有窗口状态"""
        return self.window_status
    
    def get_call_statistics(self) -> Dict:
        """获取调用统计"""
        return {
            "total_calls": sum(s.get("calls", 0) for s in self.call_stats.values()),
            "by_window": self.call_stats,
            "recent_calls": self.command_history[-10:] if self.command_history else []
        }
    
    async def health_check(self) -> Dict:
        """健康检查"""
        health = {
            "status": "healthy",
            "windows": {},
            "issues": []
        }
        
        for window_id, status in self.window_status.items():
            window_health = {
                "name": status["name"],
                "status": status["status"],
                "last_call": status["last_call"].isoformat() if status["last_call"] else None
            }
            
            # 检查是否长时间未调用
            if status["last_call"]:
                time_since_call = datetime.now() - status["last_call"]
                if time_since_call.total_seconds() > 3600:  # 1小时
                    window_health["warning"] = "长时间未调用"
                    health["issues"].append(f"Window {window_id} 超过1小时未调用")
            
            health["windows"][window_id] = window_health
        
        if health["issues"]:
            health["status"] = "warning"
        
        return health