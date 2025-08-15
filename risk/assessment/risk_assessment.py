"""
Tiger系统 - 风险评估引擎
窗口：7号
功能：全方位风险评估与预警
作者：Window-7 Risk Control Officer
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    price: float
    volume: float
    volatility: float
    liquidity: float
    correlation_matrix: Dict[str, float]
    funding_rate: float
    open_interest: float


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: float  # 95%置信度的VaR
    var_99: float  # 99%置信度的VaR
    expected_shortfall: float
    max_drawdown: float
    sharpe_ratio: float
    beta: float


class RiskAssessment:
    """风险评估引擎 - 360度风险扫描"""
    
    def __init__(self):
        self.risk_scores = {}
        self.risk_history = []
        self.alert_thresholds = {
            "low": 10,
            "medium": 20,
            "high": 25,
            "critical": 30
        }
        
        # 风险权重配置
        self.risk_weights = {
            "market_risk": 0.35,
            "position_risk": 0.30,
            "timing_risk": 0.20,
            "liquidity_risk": 0.15
        }
        
    def calculate_market_risk(self, market_data: MarketData) -> Tuple[float, Dict]:
        """
        计算市场风险
        
        Args:
            market_data: 市场数据
            
        Returns:
            (风险分数, 详细信息)
        """
        risk_components = {}
        
        # 波动率风险 (0-10分)
        volatility_score = self._calculate_volatility_risk(market_data.volatility)
        risk_components["volatility"] = {
            "score": volatility_score,
            "value": market_data.volatility,
            "level": self._get_risk_level(volatility_score)
        }
        
        # 流动性风险 (0-10分)
        liquidity_score = self._calculate_liquidity_risk(market_data.liquidity, market_data.volume)
        risk_components["liquidity"] = {
            "score": liquidity_score,
            "depth": market_data.liquidity,
            "volume": market_data.volume,
            "level": self._get_risk_level(liquidity_score)
        }
        
        # 相关性风险 (0-10分)
        correlation_score = self._calculate_correlation_risk(market_data.correlation_matrix)
        risk_components["correlation"] = {
            "score": correlation_score,
            "matrix": market_data.correlation_matrix,
            "level": self._get_risk_level(correlation_score)
        }
        
        # 系统性风险 (0-10分)
        systemic_score = self._calculate_systemic_risk(market_data)
        risk_components["systemic"] = {
            "score": systemic_score,
            "funding_rate": market_data.funding_rate,
            "open_interest": market_data.open_interest,
            "level": self._get_risk_level(systemic_score)
        }
        
        # 计算综合市场风险
        total_score = (
            volatility_score * 0.3 +
            liquidity_score * 0.25 +
            correlation_score * 0.25 +
            systemic_score * 0.2
        )
        
        return total_score, risk_components
    
    def calculate_position_risk(self, position: Dict) -> Tuple[float, Dict]:
        """
        计算仓位风险
        
        Args:
            position: 仓位信息
            
        Returns:
            (风险分数, 详细信息)
        """
        risk_components = {}
        
        # 仓位集中度风险
        concentration_score = self._calculate_concentration_risk(position)
        risk_components["concentration"] = {
            "score": concentration_score,
            "positions": position.get("positions", {}),
            "level": self._get_risk_level(concentration_score)
        }
        
        # 杠杆风险
        leverage_score = self._calculate_leverage_risk(position.get("leverage", 1))
        risk_components["leverage"] = {
            "score": leverage_score,
            "leverage": position.get("leverage", 1),
            "level": self._get_risk_level(leverage_score)
        }
        
        # 未实现盈亏风险
        unrealized_pnl_score = self._calculate_unrealized_pnl_risk(position.get("unrealized_pnl", 0))
        risk_components["unrealized_pnl"] = {
            "score": unrealized_pnl_score,
            "pnl": position.get("unrealized_pnl", 0),
            "level": self._get_risk_level(unrealized_pnl_score)
        }
        
        # 计算综合仓位风险
        total_score = (
            concentration_score * 0.4 +
            leverage_score * 0.35 +
            unrealized_pnl_score * 0.25
        )
        
        return total_score, risk_components
    
    def calculate_timing_risk(self, timing_factors: Dict) -> Tuple[float, Dict]:
        """
        计算时机风险
        
        Args:
            timing_factors: 时机因素
            
        Returns:
            (风险分数, 详细信息)
        """
        risk_components = {}
        
        # 市场时机风险
        market_timing_score = self._calculate_market_timing_risk(timing_factors)
        risk_components["market_timing"] = {
            "score": market_timing_score,
            "trend": timing_factors.get("trend"),
            "momentum": timing_factors.get("momentum"),
            "level": self._get_risk_level(market_timing_score)
        }
        
        # 事件风险
        event_score = self._calculate_event_risk(timing_factors.get("events", []))
        risk_components["events"] = {
            "score": event_score,
            "upcoming_events": timing_factors.get("events", []),
            "level": self._get_risk_level(event_score)
        }
        
        # 时区风险
        timezone_score = self._calculate_timezone_risk(datetime.now())
        risk_components["timezone"] = {
            "score": timezone_score,
            "current_session": self._get_trading_session(),
            "level": self._get_risk_level(timezone_score)
        }
        
        # 计算综合时机风险
        total_score = (
            market_timing_score * 0.5 +
            event_score * 0.3 +
            timezone_score * 0.2
        )
        
        return total_score, risk_components
    
    def calculate_specific_risks(self, symbol: str, exchange: str) -> Tuple[float, Dict]:
        """
        计算特定风险
        
        Args:
            symbol: 币种
            exchange: 交易所
            
        Returns:
            (风险分数, 详细信息)
        """
        risk_components = {}
        
        # 币种特定风险
        coin_score = self._calculate_coin_specific_risk(symbol)
        risk_components["coin_risk"] = {
            "score": coin_score,
            "symbol": symbol,
            "level": self._get_risk_level(coin_score)
        }
        
        # 交易所风险
        exchange_score = self._calculate_exchange_risk(exchange)
        risk_components["exchange_risk"] = {
            "score": exchange_score,
            "exchange": exchange,
            "level": self._get_risk_level(exchange_score)
        }
        
        # 技术风险
        technical_score = self._calculate_technical_risk()
        risk_components["technical_risk"] = {
            "score": technical_score,
            "level": self._get_risk_level(technical_score)
        }
        
        # 监管风险
        regulatory_score = self._calculate_regulatory_risk(symbol)
        risk_components["regulatory_risk"] = {
            "score": regulatory_score,
            "symbol": symbol,
            "level": self._get_risk_level(regulatory_score)
        }
        
        # 计算综合特定风险
        total_score = (
            coin_score * 0.3 +
            exchange_score * 0.3 +
            technical_score * 0.2 +
            regulatory_score * 0.2
        )
        
        return total_score, risk_components
    
    def calculate_var(self, portfolio_value: float, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        计算VaR (Value at Risk)
        
        Args:
            portfolio_value: 组合价值
            returns: 历史收益率
            confidence_level: 置信水平
            
        Returns:
            VaR值
        """
        if not returns:
            return 0
        
        # 使用历史模拟法
        returns_array = np.array(returns)
        var_percentile = (1 - confidence_level) * 100
        var_return = np.percentile(returns_array, var_percentile)
        var_value = portfolio_value * abs(var_return)
        
        logger.info(f"VaR计算: {confidence_level*100}%置信度, VaR={var_value:.2f}")
        
        return var_value
    
    def calculate_expected_shortfall(self, portfolio_value: float, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        计算预期短缺 (Expected Shortfall / CVaR)
        
        Args:
            portfolio_value: 组合价值
            returns: 历史收益率
            confidence_level: 置信水平
            
        Returns:
            ES值
        """
        if not returns:
            return 0
        
        returns_array = np.array(returns)
        var_percentile = (1 - confidence_level) * 100
        var_threshold = np.percentile(returns_array, var_percentile)
        
        # 计算超过VaR阈值的平均损失
        tail_losses = returns_array[returns_array <= var_threshold]
        if len(tail_losses) > 0:
            es_return = np.mean(tail_losses)
            es_value = portfolio_value * abs(es_return)
        else:
            es_value = 0
        
        logger.info(f"ES计算: {confidence_level*100}%置信度, ES={es_value:.2f}")
        
        return es_value
    
    def get_comprehensive_risk_score(self, 
                                    market_data: MarketData,
                                    position: Dict,
                                    timing_factors: Dict,
                                    symbol: str,
                                    exchange: str) -> Dict:
        """
        获取综合风险评分
        
        Args:
            market_data: 市场数据
            position: 仓位信息
            timing_factors: 时机因素
            symbol: 币种
            exchange: 交易所
            
        Returns:
            综合风险评估结果
        """
        # 计算各类风险
        market_risk, market_details = self.calculate_market_risk(market_data)
        position_risk, position_details = self.calculate_position_risk(position)
        timing_risk, timing_details = self.calculate_timing_risk(timing_factors)
        specific_risk, specific_details = self.calculate_specific_risks(symbol, exchange)
        
        # 计算总分
        total_score = (
            market_risk * self.risk_weights["market_risk"] +
            position_risk * self.risk_weights["position_risk"] +
            timing_risk * self.risk_weights["timing_risk"] +
            specific_risk * self.risk_weights["liquidity_risk"]
        )
        
        # 确定风险等级
        risk_level = "LOW"
        for level, threshold in sorted(self.alert_thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                risk_level = level.upper()
                break
        
        # 生成风险报告
        risk_report = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "total_score": round(total_score, 2),
            "risk_level": risk_level,
            "components": {
                "market_risk": {
                    "score": round(market_risk, 2),
                    "weight": self.risk_weights["market_risk"],
                    "details": market_details
                },
                "position_risk": {
                    "score": round(position_risk, 2),
                    "weight": self.risk_weights["position_risk"],
                    "details": position_details
                },
                "timing_risk": {
                    "score": round(timing_risk, 2),
                    "weight": self.risk_weights["timing_risk"],
                    "details": timing_details
                },
                "specific_risk": {
                    "score": round(specific_risk, 2),
                    "weight": self.risk_weights["liquidity_risk"],
                    "details": specific_details
                }
            },
            "alerts": self._generate_alerts(total_score, risk_level),
            "recommendations": self._generate_recommendations(risk_level, market_details, position_details)
        }
        
        # 记录到历史
        self.risk_history.append(risk_report)
        
        return risk_report
    
    def _calculate_volatility_risk(self, volatility: float) -> float:
        """计算波动率风险"""
        if volatility < 0.2:
            return 2
        elif volatility < 0.5:
            return 5
        elif volatility < 1.0:
            return 7
        else:
            return 9
    
    def _calculate_liquidity_risk(self, liquidity: float, volume: float) -> float:
        """计算流动性风险"""
        if volume > 1000000 and liquidity > 0.8:
            return 2
        elif volume > 500000 and liquidity > 0.5:
            return 5
        elif volume > 100000 and liquidity > 0.3:
            return 7
        else:
            return 9
    
    def _calculate_correlation_risk(self, correlation_matrix: Dict) -> float:
        """计算相关性风险"""
        if not correlation_matrix:
            return 5
        
        high_correlations = sum(1 for v in correlation_matrix.values() if abs(v) > 0.7)
        if high_correlations == 0:
            return 3
        elif high_correlations < 3:
            return 5
        elif high_correlations < 5:
            return 7
        else:
            return 9
    
    def _calculate_systemic_risk(self, market_data: MarketData) -> float:
        """计算系统性风险"""
        risk_score = 5  # 基础分
        
        # 资金费率异常
        if abs(market_data.funding_rate) > 0.001:
            risk_score += 2
        
        # 持仓量异常
        if market_data.open_interest > 1000000000:  # 10亿美元
            risk_score += 2
        
        return min(risk_score, 10)
    
    def _calculate_concentration_risk(self, position: Dict) -> float:
        """计算集中度风险"""
        positions = position.get("positions", {})
        if not positions:
            return 0
        
        total_value = sum(positions.values())
        if total_value == 0:
            return 0
        
        # 计算HHI指数
        hhi = sum((v/total_value)**2 for v in positions.values())
        
        if hhi < 0.15:
            return 3
        elif hhi < 0.25:
            return 5
        elif hhi < 0.35:
            return 7
        else:
            return 9
    
    def _calculate_leverage_risk(self, leverage: float) -> float:
        """计算杠杆风险"""
        if leverage <= 1:
            return 1
        elif leverage <= 3:
            return 3
        elif leverage <= 5:
            return 5
        elif leverage <= 10:
            return 7
        else:
            return 10
    
    def _calculate_unrealized_pnl_risk(self, unrealized_pnl: float) -> float:
        """计算未实现盈亏风险"""
        if unrealized_pnl > 0:
            return 2  # 有盈利，风险较低
        elif unrealized_pnl > -1000:
            return 5
        elif unrealized_pnl > -5000:
            return 7
        else:
            return 9
    
    def _calculate_market_timing_risk(self, timing_factors: Dict) -> float:
        """计算市场时机风险"""
        trend = timing_factors.get("trend", "neutral")
        momentum = timing_factors.get("momentum", 0)
        
        if trend == "strong_uptrend" and momentum > 0:
            return 3
        elif trend == "uptrend":
            return 5
        elif trend == "neutral":
            return 6
        elif trend == "downtrend":
            return 7
        else:  # strong_downtrend
            return 9
    
    def _calculate_event_risk(self, events: List) -> float:
        """计算事件风险"""
        if not events:
            return 3
        
        high_impact_events = sum(1 for e in events if e.get("impact") == "high")
        if high_impact_events == 0:
            return 4
        elif high_impact_events == 1:
            return 6
        elif high_impact_events == 2:
            return 8
        else:
            return 10
    
    def _calculate_timezone_risk(self, current_time: datetime) -> float:
        """计算时区风险"""
        hour = current_time.hour
        
        # 亚洲时段 (相对安全)
        if 0 <= hour < 8:
            return 4
        # 欧洲时段
        elif 8 <= hour < 16:
            return 5
        # 美国时段 (波动较大)
        elif 16 <= hour < 24:
            return 6
        else:
            return 5
    
    def _calculate_coin_specific_risk(self, symbol: str) -> float:
        """计算币种特定风险"""
        # 主流币风险较低
        if symbol in ["BTC", "ETH"]:
            return 3
        elif symbol in ["BNB", "SOL", "ADA"]:
            return 5
        elif symbol in ["DOGE", "SHIB"]:
            return 7
        else:
            return 8
    
    def _calculate_exchange_risk(self, exchange: str) -> float:
        """计算交易所风险"""
        # 顶级交易所
        if exchange in ["Binance", "Coinbase", "OKX"]:
            return 3
        elif exchange in ["Bybit", "Gate", "Kucoin"]:
            return 5
        else:
            return 7
    
    def _calculate_technical_risk(self) -> float:
        """计算技术风险"""
        # 简化：返回固定值，实际应检查系统状态
        return 4
    
    def _calculate_regulatory_risk(self, symbol: str) -> float:
        """计算监管风险"""
        # 简化：稳定币和隐私币风险较高
        if symbol in ["USDT", "USDC"]:
            return 6
        elif symbol in ["XMR", "ZEC"]:
            return 8
        else:
            return 4
    
    def _get_risk_level(self, score: float) -> str:
        """获取风险等级"""
        if score < 3:
            return "LOW"
        elif score < 6:
            return "MEDIUM"
        elif score < 8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _get_trading_session(self) -> str:
        """获取当前交易时段"""
        hour = datetime.now().hour
        if 0 <= hour < 8:
            return "ASIA"
        elif 8 <= hour < 16:
            return "EUROPE"
        else:
            return "US"
    
    def _generate_alerts(self, total_score: float, risk_level: str) -> List[str]:
        """生成风险警报"""
        alerts = []
        
        if risk_level == "CRITICAL":
            alerts.append("⚠️ 风险极高，建议立即减仓或平仓")
        elif risk_level == "HIGH":
            alerts.append("⚠️ 风险较高，密切监控并准备减仓")
        elif risk_level == "MEDIUM":
            alerts.append("ℹ️ 风险适中，保持警惕")
        
        if total_score > 25:
            alerts.append("🚨 总风险分超过25，触发风控预警")
        
        return alerts
    
    def _generate_recommendations(self, risk_level: str, market_details: Dict, position_details: Dict) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        if risk_level in ["HIGH", "CRITICAL"]:
            recommendations.append("减少仓位至安全水平")
            recommendations.append("设置更严格的止损")
            recommendations.append("避免新开仓位")
        
        if market_details.get("volatility", {}).get("level") == "HIGH":
            recommendations.append("降低杠杆倍数")
        
        if position_details.get("concentration", {}).get("level") == "HIGH":
            recommendations.append("分散投资，降低集中度")
        
        return recommendations


if __name__ == "__main__":
    # 测试代码
    ra = RiskAssessment()
    
    # 创建测试数据
    test_market = MarketData(
        symbol="BTC",
        price=70000,
        volume=1500000,
        volatility=0.6,
        liquidity=0.7,
        correlation_matrix={"ETH": 0.8, "SOL": 0.6},
        funding_rate=0.0008,
        open_interest=800000000
    )
    
    test_position = {
        "positions": {"BTC": 50000, "ETH": 30000},
        "leverage": 3,
        "unrealized_pnl": -2000
    }
    
    test_timing = {
        "trend": "uptrend",
        "momentum": 0.5,
        "events": [{"name": "FOMC", "impact": "high"}]
    }
    
    # 计算综合风险
    risk_report = ra.get_comprehensive_risk_score(
        test_market,
        test_position,
        test_timing,
        "BTC",
        "Binance"
    )
    
    print(f"风险评估报告:")
    print(f"总分: {risk_report['total_score']}")
    print(f"等级: {risk_report['risk_level']}")
    print(f"警报: {risk_report['alerts']}")
    print(f"建议: {risk_report['recommendations']}")