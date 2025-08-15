# -*- coding: utf-8 -*-
"""
复合指标监控系统 - 窗口3核心功能
专门为窗口6提供大资金入场信号分析

核心逻辑：资金费率↑ + Gas费用↑ + 稳定币涨价 = 大资金准备入场
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
try:
    from .window2_interface import Window2Interface
except ImportError:
    # 用于直接运行时的导入
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from window2_interface import Window2Interface

@dataclass
class CompositeSignalData:
    """复合信号数据结构"""
    timestamp: datetime
    # 资金费率数据
    funding_rate_btc: float
    funding_rate_eth: float
    funding_rate_trend: str  # "rising", "falling", "stable"
    
    # Gas费用数据
    gas_price_gwei: float
    gas_price_usd: float
    gas_trend: str  # "rising", "falling", "stable"
    
    # 稳定币数据
    usdt_price: float
    usdc_price: float
    stablecoin_premium: float  # 稳定币溢价率
    stablecoin_trend: str  # "rising", "falling", "stable"
    
    # 复合信号
    composite_score: float  # 0-100的综合得分
    signal_strength: str  # "weak", "medium", "strong", "critical"
    big_money_signal: bool  # 是否是大资金入场信号
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，供窗口6使用"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class CompositeSignalMonitor:
    """复合指标监控器 - 窗口3专用"""
    
    def __init__(self):
        self.etherscan_api_key = "2S23UTJZVZYZHS9V5347C4CKJJC8UGJY7T"
        self.session = None
        
        # 窗口2接口
        self.window2_interface = Window2Interface()
        
        # 历史数据存储（用于趋势分析）
        self.funding_rate_history: List[float] = []
        self.gas_price_history: List[float] = []
        self.stablecoin_history: List[float] = []
        
        # 阈值配置
        self.thresholds = {
            "funding_rate_positive": 0.01,  # 资金费率为正的阈值
            "gas_surge_multiplier": 1.5,    # Gas费用激增倍数
            "stablecoin_premium": 1.002,    # 稳定币溢价阈值
            "composite_signal": 70           # 复合信号阈值
        }
        
        print("🎯 复合指标监控系统已初始化")
        print("📊 监控指标：资金费率 + Gas费用 + 稳定币价格")
        print("🚨 目标：识别大资金入场信号")
        print("🔗 集成窗口2实时数据")

    async def initialize(self):
        """初始化异步会话"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Tiger-Trading-System/1.0'}
        )
        # 初始化窗口2接口
        await self.window2_interface.initialize()
        print("✅ 网络会话已初始化")
        print("✅ 窗口2接口已连接")

    async def get_funding_rate_data(self) -> Dict[str, Any]:
        """从窗口2获取实时资金费率数据"""
        try:
            # 从窗口2接口获取实时数据
            funding_data = await self.window2_interface.get_combined_funding_rates()
            
            summary = funding_data.get('summary', {})
            
            # 提取关键数据
            result = {
                'btc_funding_rate': summary.get('btc_avg_funding', 0.0),
                'eth_funding_rate': summary.get('eth_avg_funding', 0.0),
                'overall_sentiment': summary.get('overall_sentiment', 'neutral'),
                'positive_funding_ratio': summary.get('positive_funding_ratio', 0.0),
                'strong_positive_count': summary.get('strong_positive_count', 0),
                'raw_data': funding_data  # 保留原始数据
            }
            
            print(f"✅ 窗口2资金费率获取成功 - BTC: {result['btc_funding_rate']:.4f}%, ETH: {result['eth_funding_rate']:.4f}%")
            return result
                    
        except Exception as e:
            print(f"❌ 从窗口2获取资金费率失败: {e}")
            
        # 返回默认值
        return {
            'btc_funding_rate': 0.0, 
            'eth_funding_rate': 0.0,
            'overall_sentiment': 'neutral',
            'positive_funding_ratio': 0.0,
            'strong_positive_count': 0
        }

    async def get_gas_price_data(self) -> Dict[str, float]:
        """从Etherscan获取Gas费用数据"""
        try:
            # 获取当前Gas价格
            gas_url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={self.etherscan_api_key}"
            
            async with self.session.get(gas_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == '1':
                        fast_gas = float(data['result']['FastGasPrice'])
                        
                        # 获取ETH价格来计算Gas费用的美元价值
                        eth_price = await self.get_eth_price()
                        gas_usd = (fast_gas * 21000 * eth_price) / (10**9)  # 标准转账的Gas费用
                        
                        return {
                            'gas_price_gwei': fast_gas,
                            'gas_price_usd': gas_usd
                        }
                        
        except Exception as e:
            print(f"❌ 获取Gas费用失败: {e}")
            
        return {'gas_price_gwei': 20.0, 'gas_price_usd': 5.0}

    async def get_eth_price(self) -> float:
        """获取ETH价格"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data['ethereum']['usd'])
        except:
            pass
        return 3000.0  # 默认值

    async def get_stablecoin_data(self) -> Dict[str, float]:
        """从DeFiLlama获取稳定币价格数据"""
        try:
            # 获取USDT和USDC价格
            url = "https://coins.llama.fi/prices/current/coingecko:tether,coingecko:usd-coin"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    coins = data.get('coins', {})
                    
                    usdt_price = coins.get('coingecko:tether', {}).get('price', 1.0)
                    usdc_price = coins.get('coingecko:usd-coin', {}).get('price', 1.0)
                    
                    # 计算稳定币溢价率
                    avg_premium = (usdt_price + usdc_price) / 2
                    
                    return {
                        'usdt_price': usdt_price,
                        'usdc_price': usdc_price,
                        'stablecoin_premium': avg_premium
                    }
                    
        except Exception as e:
            print(f"❌ 获取稳定币数据失败: {e}")
            
        return {'usdt_price': 1.0, 'usdc_price': 1.0, 'stablecoin_premium': 1.0}

    def analyze_trend(self, current_value: float, history: List[float], periods: int = 5) -> str:
        """分析趋势方向"""
        if len(history) < periods:
            return "stable"
            
        recent_avg = sum(history[-periods:]) / periods
        older_avg = sum(history[-periods*2:-periods]) / periods if len(history) >= periods*2 else recent_avg
        
        if recent_avg > older_avg * 1.1:
            return "rising"
        elif recent_avg < older_avg * 0.9:
            return "falling"
        else:
            return "stable"

    def calculate_composite_score(self, funding_data: Dict[str, Any], 
                                gas_trend: str, stablecoin_premium: float) -> float:
        """计算复合信号得分 (0-100)"""
        score = 0
        
        funding_btc = funding_data.get('btc_funding_rate', 0)
        funding_eth = funding_data.get('eth_funding_rate', 0)
        overall_sentiment = funding_data.get('overall_sentiment', 'neutral')
        positive_ratio = funding_data.get('positive_funding_ratio', 0)
        
        # 资金费率得分 (0-45分) - 增强权重
        if funding_btc > 0 and funding_eth > 0:
            score += 25  # 双币种都为正
            score += min(funding_btc * 800, 10)  # BTC资金费率贡献
            score += min(funding_eth * 800, 10)  # ETH资金费率贡献
        
        # 整体情绪加分
        sentiment_scores = {
            'very_bullish': 15,
            'bullish': 8,
            'neutral': 0,
            'bearish': -5
        }
        score += sentiment_scores.get(overall_sentiment, 0)
        
        # 正资金费率比例加分
        if positive_ratio > 0.7:
            score += 10
        elif positive_ratio > 0.5:
            score += 5
        
        # Gas费用得分 (0-30分)
        if gas_trend == "rising":
            score += 30
        elif gas_trend == "stable":
            score += 15
            
        # 稳定币溢价得分 (0-25分)
        if stablecoin_premium > self.thresholds["stablecoin_premium"]:
            premium_score = (stablecoin_premium - 1) * 8000  # 放大溢价
            score += min(premium_score, 25)
        
        return min(max(score, 0), 100)  # 确保在0-100范围内

    def determine_signal_strength(self, score: float) -> tuple[str, bool]:
        """确定信号强度和是否为大资金信号"""
        if score >= 80:
            return "critical", True
        elif score >= 70:
            return "strong", True
        elif score >= 50:
            return "medium", False
        else:
            return "weak", False

    async def collect_composite_signal(self) -> CompositeSignalData:
        """收集复合信号数据"""
        print("📊 开始收集复合指标数据...")
        
        # 并行获取所有数据
        funding_task = self.get_funding_rate_data()
        gas_task = self.get_gas_price_data()
        stablecoin_task = self.get_stablecoin_data()
        
        funding_data, gas_data, stablecoin_data = await asyncio.gather(
            funding_task, gas_task, stablecoin_task
        )
        
        # 更新历史数据
        self.funding_rate_history.append(funding_data['btc_funding_rate'])
        self.gas_price_history.append(gas_data['gas_price_gwei'])
        self.stablecoin_history.append(stablecoin_data['stablecoin_premium'])
        
        # 保持历史数据长度
        max_history = 50
        if len(self.funding_rate_history) > max_history:
            self.funding_rate_history = self.funding_rate_history[-max_history:]
        if len(self.gas_price_history) > max_history:
            self.gas_price_history = self.gas_price_history[-max_history:]
        if len(self.stablecoin_history) > max_history:
            self.stablecoin_history = self.stablecoin_history[-max_history:]
        
        # 分析趋势
        funding_trend = self.analyze_trend(funding_data['btc_funding_rate'], self.funding_rate_history)
        gas_trend = self.analyze_trend(gas_data['gas_price_gwei'], self.gas_price_history)
        stablecoin_trend = self.analyze_trend(stablecoin_data['stablecoin_premium'], self.stablecoin_history)
        
        # 计算复合得分 - 传入完整的funding_data
        composite_score = self.calculate_composite_score(
            funding_data,  # 传入完整数据
            gas_trend,
            stablecoin_data['stablecoin_premium']
        )
        
        # 确定信号强度
        signal_strength, big_money_signal = self.determine_signal_strength(composite_score)
        
        # 构建结果
        signal_data = CompositeSignalData(
            timestamp=datetime.now(),
            funding_rate_btc=funding_data['btc_funding_rate'],
            funding_rate_eth=funding_data['eth_funding_rate'],
            funding_rate_trend=funding_trend,
            gas_price_gwei=gas_data['gas_price_gwei'],
            gas_price_usd=gas_data['gas_price_usd'],
            gas_trend=gas_trend,
            usdt_price=stablecoin_data['usdt_price'],
            usdc_price=stablecoin_data['usdc_price'],
            stablecoin_premium=stablecoin_data['stablecoin_premium'],
            stablecoin_trend=stablecoin_trend,
            composite_score=composite_score,
            signal_strength=signal_strength,
            big_money_signal=big_money_signal
        )
        
        # 添加窗口2详细数据到signal_data
        signal_data.window2_data = funding_data.get('raw_data', {})
        
        print(f"✅ 复合信号收集完成 - 得分: {composite_score:.1f}, 强度: {signal_strength}")
        
        return signal_data

    def format_for_window6(self, signal_data: CompositeSignalData) -> Dict[str, Any]:
        """为窗口6格式化数据 - 包含组合逻辑分析"""
        
        # 生成组合分析
        combo_analysis = self.generate_combo_analysis(signal_data)
        
        return {
            "data_source": "window3_composite_signal",
            "timestamp": signal_data.timestamp.isoformat(),
            
            # 窗口3核心价值：组合逻辑分析
            "combo_logic_analysis": combo_analysis,
            
            # 快速决策摘要
            "quick_decision_summary": {
                "strongest_signal": combo_analysis["combo_analysis_summary"]["strongest_signal"],
                "market_phase": combo_analysis["combo_analysis_summary"]["market_phase"],
                "confidence": combo_analysis["combo_analysis_summary"]["confidence_level"],
                "immediate_action": self.get_immediate_action(combo_analysis),
                "reason_explanation": self.get_action_reason(combo_analysis)
            },
            
            "big_money_analysis": {
                "is_big_money_signal": signal_data.big_money_signal,
                "composite_score": signal_data.composite_score,
                "signal_strength": signal_data.signal_strength,
                "confidence_level": "high" if signal_data.composite_score > 70 else "medium",
                "detected_combos": len(combo_analysis["big_money_signals"])
            },
            "funding_rate_analysis": {
                "btc_funding_rate": signal_data.funding_rate_btc,
                "eth_funding_rate": signal_data.funding_rate_eth,
                "trend": signal_data.funding_rate_trend,
                "interpretation": "多头情绪" if signal_data.funding_rate_btc > 0 else "空头情绪",
                "window2_raw_data": getattr(signal_data, 'window2_data', {}),
                "overall_sentiment": getattr(signal_data, 'window2_data', {}).get('summary', {}).get('overall_sentiment', 'neutral'),
                "positive_funding_ratio": getattr(signal_data, 'window2_data', {}).get('summary', {}).get('positive_funding_ratio', 0)
            },
            "gas_analysis": {
                "gas_price_gwei": signal_data.gas_price_gwei,
                "gas_price_usd": signal_data.gas_price_usd,
                "trend": signal_data.gas_trend,
                "interpretation": "链上活跃度激增" if signal_data.gas_trend == "rising" else "链上活动平稳"
            },
            "stablecoin_analysis": {
                "usdt_price": signal_data.usdt_price,
                "usdc_price": signal_data.usdc_price,
                "premium_rate": (signal_data.stablecoin_premium - 1) * 100,
                "trend": signal_data.stablecoin_trend,
                "interpretation": "资金涌入" if signal_data.stablecoin_premium > 1.001 else "资金流出"
            },
            "trading_suggestion": {
                "action": "积极买入" if signal_data.big_money_signal else "观望",
                "reason": self.get_trading_reason(signal_data),
                "risk_level": "低风险" if signal_data.composite_score > 80 else "中等风险"
            },
            
            # 窗口3预处理说明
            "preprocessing_info": {
                "analysis_type": "组合逻辑预处理",
                "value": "减少AI计算时间，提供结构化决策依据",
                "combo_rules_applied": self.get_applied_rules_count(combo_analysis),
                "processing_time_saved": "估计节省60%AI分析时间"
            }
        }
    
    def get_immediate_action(self, combo_analysis: Dict) -> str:
        """获取立即行动建议"""
        big_money_signals = combo_analysis["big_money_signals"]
        risk_warnings = combo_analysis["risk_warnings"]
        
        if big_money_signals:
            strongest = max(big_money_signals, key=lambda x: {"critical": 4, "very_high": 3, "high": 2, "medium": 1}.get(x["strength"], 0))
            return strongest["action"]
        elif risk_warnings:
            return risk_warnings[0]["action"]
        else:
            return "持有观望"
    
    def get_action_reason(self, combo_analysis: Dict) -> str:
        """获取行动原因"""
        strongest = combo_analysis["combo_analysis_summary"]["strongest_signal"]
        if strongest["combo_name"] != "无明显信号":
            return strongest.get("logic", "组合信号触发")
        else:
            return "暂无明确组合信号，建议继续观察"
    
    def get_applied_rules_count(self, combo_analysis: Dict) -> int:
        """获取应用的规则数量"""
        return len(combo_analysis["big_money_signals"]) + len(combo_analysis["risk_warnings"]) + len(combo_analysis["turning_points"]) + len(combo_analysis["arbitrage_opportunities"])

    def get_trading_reason(self, signal_data: CompositeSignalData) -> str:
        """获取交易建议原因"""
        if signal_data.big_money_signal:
            reasons = []
            if signal_data.funding_rate_btc > 0:
                reasons.append("资金费率转正显示多头意愿")
            if signal_data.gas_trend == "rising":
                reasons.append("Gas费用上涨表明链上活动激增")
            if signal_data.stablecoin_premium > 1.001:
                reasons.append("稳定币溢价显示大量资金准备入场")
            return "；".join(reasons)
        else:
            return "复合指标未达到大资金入场阈值，建议继续观察"

    async def run_monitoring(self, interval: int = 300):
        """运行监控循环"""
        print(f"🚀 开始复合指标监控，间隔: {interval}秒")
        
        while True:
            try:
                # 收集数据
                signal_data = await self.collect_composite_signal()
                
                # 格式化给窗口6
                window6_data = self.format_for_window6(signal_data)
                
                # 打印重要信号
                if signal_data.big_money_signal:
                    print("🚨" + "="*60)
                    print("🚨 大资金入场信号检测！")
                    print(f"🚨 复合得分: {signal_data.composite_score:.1f}/100")
                    print(f"🚨 信号强度: {signal_data.signal_strength}")
                    print("🚨" + "="*60)
                
                # 保存数据（供窗口6调用）
                await self.save_for_window6(window6_data)
                
                print(f"📊 监控数据已更新 - {datetime.now().strftime('%H:%M:%S')}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
                await asyncio.sleep(60)  # 错误时等待1分钟

    async def save_for_window6(self, data: Dict[str, Any]):
        """保存数据供窗口6使用"""
        try:
            # 保存到文件
            with open('/tmp/window3_composite_signal.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 也保存到项目目录
            output_path = "/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/data/composite_signals.json"
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")

    def generate_combo_analysis(self, signal_data: CompositeSignalData) -> Dict[str, Any]:
        """生成组合逻辑分析 - 窗口3的核心价值"""
        
        # 1. 大资金入场信号组合
        big_money_combos = []
        
        # 组合1: 资金费率转正 + 稳定币溢价
        if signal_data.funding_rate_btc > 0 and signal_data.stablecoin_premium > 1.002:
            big_money_combos.append({
                "combo_name": "多头+资金涌入",
                "logic": "资金费率转正表明多头意愿强烈，稳定币溢价显示大量资金准备入场",
                "strength": "high",
                "prediction": "大概率上涨",
                "action": "积极买入"
            })
        
        # 组合2: Gas费暴涨 + 资金费率高
        if signal_data.gas_trend == "rising" and signal_data.funding_rate_btc > 0.01:
            big_money_combos.append({
                "combo_name": "链上活跃+多头爆发",
                "logic": "Gas费用暴涨说明链上大量交易，高资金费率确认多头力量",
                "strength": "very_high",
                "prediction": "短期强势上涨",
                "action": "立即买入"
            })
        
        # 组合3: 三重确认信号
        if (signal_data.funding_rate_btc > 0 and 
            signal_data.gas_trend == "rising" and 
            signal_data.stablecoin_premium > 1.001):
            big_money_combos.append({
                "combo_name": "三重大资金信号",
                "logic": "资金费率+Gas费+稳定币同时异常，机构资金大举入场",
                "strength": "critical",
                "prediction": "强烈看涨",
                "action": "重仓买入"
            })
        
        # 2. 风险警告组合
        risk_combos = []
        
        # 组合4: 资金费率负值 + Gas费下降
        if signal_data.funding_rate_btc < -0.005 and signal_data.gas_trend == "falling":
            risk_combos.append({
                "combo_name": "双重看空信号",
                "logic": "负资金费率显示空头力量，Gas费下降说明链上活动减少",
                "strength": "high",
                "prediction": "可能下跌",
                "action": "减仓观望"
            })
        
        # 3. 市场转折组合
        turning_combos = []
        
        # 组合5: 资金费率反转
        if (len(self.funding_rate_history) >= 3 and 
            self.funding_rate_history[-3] < 0 and signal_data.funding_rate_btc > 0):
            turning_combos.append({
                "combo_name": "空转多信号",
                "logic": "资金费率从负转正，市场情绪发生根本性转变",
                "strength": "high",
                "prediction": "趋势反转",
                "action": "抄底买入"
            })
        
        # 4. 套利机会组合
        arbitrage_combos = []
        
        # 组合6: 稳定币脱锚
        if signal_data.usdt_price > 1.005 or signal_data.usdc_price > 1.005:
            arbitrage_combos.append({
                "combo_name": "稳定币脱锚套利",
                "logic": "稳定币严重溢价，存在套利空间",
                "strength": "medium",
                "prediction": "短期套利机会",
                "action": "套利交易"
            })
        
        return {
            "timestamp": signal_data.timestamp.isoformat(),
            "combo_analysis_summary": {
                "total_combos_detected": len(big_money_combos) + len(risk_combos) + len(turning_combos) + len(arbitrage_combos),
                "strongest_signal": self.get_strongest_combo(big_money_combos + risk_combos + turning_combos),
                "market_phase": self.determine_market_phase(signal_data),
                "confidence_level": self.calculate_combo_confidence(big_money_combos, risk_combos)
            },
            "big_money_signals": big_money_combos,
            "risk_warnings": risk_combos,
            "turning_points": turning_combos,
            "arbitrage_opportunities": arbitrage_combos,
            "ai_preprocessing_note": "窗口3已完成数据组合分析，减少AI计算负担，提高决策速度"
        }
    
    def get_strongest_combo(self, combos: List[Dict]) -> Dict[str, Any]:
        """获取最强信号组合"""
        if not combos:
            return {"combo_name": "无明显信号", "strength": "none"}
        
        strength_map = {"critical": 4, "very_high": 3, "high": 2, "medium": 1, "none": 0}
        strongest = max(combos, key=lambda x: strength_map.get(x["strength"], 0))
        return strongest
    
    def determine_market_phase(self, signal_data: CompositeSignalData) -> str:
        """判断市场阶段"""
        score = signal_data.composite_score
        
        if score >= 80:
            return "牛市爆发期"
        elif score >= 60:
            return "牛市积累期"  
        elif score >= 40:
            return "震荡整理期"
        elif score >= 20:
            return "熊市反弹期"
        else:
            return "熊市下跌期"
    
    def calculate_combo_confidence(self, big_money_combos: List, risk_combos: List) -> str:
        """计算组合信号置信度"""
        if len(big_money_combos) >= 2:
            return "极高"
        elif len(big_money_combos) >= 1:
            return "高"
        elif len(risk_combos) >= 1:
            return "中等"
        else:
            return "低"

    async def close(self):
        """清理资源"""
        if self.session:
            await self.session.close()
        await self.window2_interface.close()
        print("✅ 复合指标监控系统已关闭")

async def main():
    """主函数 - 测试复合指标系统"""
    monitor = CompositeSignalMonitor()
    
    try:
        await monitor.initialize()
        
        # 运行一次测试
        print("🧪 开始测试复合指标收集...")
        signal_data = await monitor.collect_composite_signal()
        
        # 显示结果
        print("\n" + "="*60)
        print("📊 复合指标分析结果")
        print("="*60)
        print(f"⏰ 时间: {signal_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 BTC资金费率: {signal_data.funding_rate_btc:.4f}% ({signal_data.funding_rate_trend})")
        print(f"💰 ETH资金费率: {signal_data.funding_rate_eth:.4f}% ({signal_data.funding_rate_trend})")
        print(f"⛽ Gas价格: {signal_data.gas_price_gwei:.1f} Gwei (${signal_data.gas_price_usd:.2f}) ({signal_data.gas_trend})")
        print(f"🔸 USDT价格: ${signal_data.usdt_price:.4f} ({signal_data.stablecoin_trend})")
        print(f"🔸 USDC价格: ${signal_data.usdc_price:.4f}")
        print(f"📈 稳定币溢价: {(signal_data.stablecoin_premium-1)*100:.3f}%")
        print(f"🎯 复合得分: {signal_data.composite_score:.1f}/100")
        print(f"🚨 信号强度: {signal_data.signal_strength}")
        print(f"💎 大资金信号: {'是' if signal_data.big_money_signal else '否'}")
        
        # 格式化给窗口6的数据
        window6_data = monitor.format_for_window6(signal_data)
        print("\n" + "="*60)
        print("📡 给窗口6的数据格式:")
        print("="*60)
        print(json.dumps(window6_data, ensure_ascii=False, indent=2))
        
    finally:
        await monitor.close()

if __name__ == "__main__":
    asyncio.run(main())