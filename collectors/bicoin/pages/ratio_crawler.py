"""
全网多空比数据爬虫
监控市场整体情绪和大户持仓动向
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bicoin_auth import BiCoinAuth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RatioCrawler:
    """全网多空比爬虫"""
    
    def __init__(self, auth: BiCoinAuth):
        """
        初始化爬虫
        
        Args:
            auth: BiCoinAuth实例
        """
        self.auth = auth
        self.driver = auth.get_driver()
        self.url = "https://mapp.bicoin.info/bcoin-web/other/index.html"
        self.data_path = "data/ratio/"
        
        # 创建数据目录
        os.makedirs(self.data_path, exist_ok=True)
        
        # 情绪阈值
        self.sentiment_thresholds = {
            "extreme_greed": 80,     # 极度贪婪
            "greed": 65,             # 贪婪
            "neutral_high": 55,      # 中性偏多
            "neutral_low": 45,       # 中性偏空
            "fear": 35,              # 恐惧
            "extreme_fear": 20       # 极度恐惧
        }
    
    def crawl_ratio_data(self) -> Dict[str, Any]:
        """
        爬取多空比数据
        
        Returns:
            Dict: 多空比数据
        """
        ratio_data = {
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "global_ratio": {},
            "exchange_ratios": {},
            "whale_positions": {},
            "retail_positions": {},
            "historical_data": [],
            "sentiment_analysis": {}
        }
        
        try:
            # 访问多空比页面
            logger.info(f"访问多空比页面: {self.url}")
            self.driver.get(self.url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ratio-container")))
            
            time.sleep(3)
            
            # 获取全网多空比
            ratio_data["global_ratio"] = self._get_global_ratio()
            
            # 获取各交易所多空比
            ratio_data["exchange_ratios"] = self._get_exchange_ratios()
            
            # 获取大户持仓
            ratio_data["whale_positions"] = self._get_whale_positions()
            
            # 获取散户持仓
            ratio_data["retail_positions"] = self._get_retail_positions()
            
            # 获取历史数据
            ratio_data["historical_data"] = self._get_historical_data()
            
            # 情绪分析
            ratio_data["sentiment_analysis"] = self._analyze_sentiment(ratio_data)
            
            # 生成交易建议
            ratio_data["trading_suggestions"] = self._generate_suggestions(ratio_data)
            
            return ratio_data
            
        except TimeoutException:
            logger.error("页面加载超时")
            return ratio_data
        except Exception as e:
            logger.error(f"爬取多空比数据失败: {e}")
            return ratio_data
    
    def _get_global_ratio(self) -> Dict[str, Any]:
        """获取全网多空比"""
        global_ratio = {
            "long_percentage": 50,
            "short_percentage": 50,
            "total_positions": 0,
            "long_positions": 0,
            "short_positions": 0,
            "ratio": 1.0,
            "24h_change": 0
        }
        
        try:
            # 多头百分比
            try:
                long_pct = self.driver.find_element(By.CLASS_NAME, "long-percentage").text
                global_ratio["long_percentage"] = float(long_pct.replace("%", ""))
            except:
                pass
            
            # 空头百分比
            try:
                short_pct = self.driver.find_element(By.CLASS_NAME, "short-percentage").text
                global_ratio["short_percentage"] = float(short_pct.replace("%", ""))
            except:
                global_ratio["short_percentage"] = 100 - global_ratio["long_percentage"]
            
            # 持仓量
            try:
                total_pos = self.driver.find_element(By.CLASS_NAME, "total-positions").text
                global_ratio["total_positions"] = self._parse_position_value(total_pos)
                
                global_ratio["long_positions"] = global_ratio["total_positions"] * global_ratio["long_percentage"] / 100
                global_ratio["short_positions"] = global_ratio["total_positions"] * global_ratio["short_percentage"] / 100
            except:
                pass
            
            # 计算比率
            if global_ratio["short_percentage"] > 0:
                global_ratio["ratio"] = global_ratio["long_percentage"] / global_ratio["short_percentage"]
            
            # 24小时变化
            try:
                change_24h = self.driver.find_element(By.CLASS_NAME, "change-24h").text
                global_ratio["24h_change"] = float(change_24h.replace("%", "").replace("+", ""))
            except:
                pass
            
        except Exception as e:
            logger.error(f"获取全网多空比失败: {e}")
        
        return global_ratio
    
    def _get_exchange_ratios(self) -> Dict[str, Dict[str, Any]]:
        """获取各交易所多空比"""
        exchange_ratios = {}
        
        try:
            # 获取交易所列表
            exchanges = self.driver.find_elements(By.CLASS_NAME, "exchange-item")
            
            for exchange in exchanges[:10]:  # 限制前10个交易所
                try:
                    # 交易所名称
                    name = exchange.find_element(By.CLASS_NAME, "exchange-name").text
                    
                    # 多空数据
                    long_pct = exchange.find_element(By.CLASS_NAME, "exchange-long").text
                    short_pct = exchange.find_element(By.CLASS_NAME, "exchange-short").text
                    
                    exchange_ratios[name] = {
                        "long_percentage": float(long_pct.replace("%", "")),
                        "short_percentage": float(short_pct.replace("%", "")),
                        "ratio": 0
                    }
                    
                    # 计算比率
                    if exchange_ratios[name]["short_percentage"] > 0:
                        exchange_ratios[name]["ratio"] = (
                            exchange_ratios[name]["long_percentage"] / 
                            exchange_ratios[name]["short_percentage"]
                        )
                    
                except Exception as e:
                    logger.debug(f"解析交易所数据失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"获取交易所多空比失败: {e}")
        
        return exchange_ratios
    
    def _get_whale_positions(self) -> Dict[str, Any]:
        """获取大户持仓数据"""
        whale_data = {
            "long_percentage": 50,
            "short_percentage": 50,
            "position_change": 0,
            "top_traders_count": 0,
            "average_position_size": 0,
            "concentration": "LOW"  # LOW, MEDIUM, HIGH
        }
        
        try:
            # 大户多空比
            try:
                whale_long = self.driver.find_element(By.CLASS_NAME, "whale-long").text
                whale_data["long_percentage"] = float(whale_long.replace("%", ""))
                
                whale_short = self.driver.find_element(By.CLASS_NAME, "whale-short").text
                whale_data["short_percentage"] = float(whale_short.replace("%", ""))
            except:
                pass
            
            # 持仓变化
            try:
                position_change = self.driver.find_element(By.CLASS_NAME, "whale-change").text
                whale_data["position_change"] = float(position_change.replace("%", "").replace("+", ""))
            except:
                pass
            
            # 大户数量
            try:
                trader_count = self.driver.find_element(By.CLASS_NAME, "whale-count").text
                whale_data["top_traders_count"] = int(trader_count.replace(",", ""))
            except:
                pass
            
            # 判断集中度
            if whale_data["long_percentage"] > 70 or whale_data["short_percentage"] > 70:
                whale_data["concentration"] = "HIGH"
            elif whale_data["long_percentage"] > 60 or whale_data["short_percentage"] > 60:
                whale_data["concentration"] = "MEDIUM"
            
        except Exception as e:
            logger.error(f"获取大户持仓失败: {e}")
        
        return whale_data
    
    def _get_retail_positions(self) -> Dict[str, Any]:
        """获取散户持仓数据"""
        retail_data = {
            "long_percentage": 50,
            "short_percentage": 50,
            "account_ratio": 0,  # 多空账户比
            "sentiment": "NEUTRAL"
        }
        
        try:
            # 散户多空比
            try:
                retail_long = self.driver.find_element(By.CLASS_NAME, "retail-long").text
                retail_data["long_percentage"] = float(retail_long.replace("%", ""))
                
                retail_short = self.driver.find_element(By.CLASS_NAME, "retail-short").text
                retail_data["short_percentage"] = float(retail_short.replace("%", ""))
            except:
                pass
            
            # 账户比
            try:
                account_ratio = self.driver.find_element(By.CLASS_NAME, "account-ratio").text
                retail_data["account_ratio"] = float(account_ratio)
            except:
                pass
            
            # 判断散户情绪
            if retail_data["long_percentage"] > 65:
                retail_data["sentiment"] = "BULLISH"
            elif retail_data["long_percentage"] < 35:
                retail_data["sentiment"] = "BEARISH"
            else:
                retail_data["sentiment"] = "NEUTRAL"
            
        except Exception as e:
            logger.error(f"获取散户持仓失败: {e}")
        
        return retail_data
    
    def _get_historical_data(self) -> List[Dict[str, Any]]:
        """获取历史数据（如果页面提供）"""
        historical = []
        
        try:
            # 尝试获取图表数据
            chart_points = self.driver.find_elements(By.CLASS_NAME, "chart-point")
            
            for point in chart_points[-24:]:  # 最近24小时
                try:
                    time_str = point.get_attribute("data-time")
                    long_value = point.get_attribute("data-long")
                    
                    if time_str and long_value:
                        historical.append({
                            "time": time_str,
                            "long_percentage": float(long_value),
                            "short_percentage": 100 - float(long_value)
                        })
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"获取历史数据失败: {e}")
        
        return historical
    
    def _parse_position_value(self, value_str: str) -> float:
        """解析持仓量字符串"""
        try:
            value_str = value_str.replace(",", "").replace("$", "").strip()
            
            if "B" in value_str or "b" in value_str:
                return float(value_str.replace("B", "").replace("b", "")) * 1000000000
            elif "M" in value_str or "m" in value_str:
                return float(value_str.replace("M", "").replace("m", "")) * 1000000
            elif "K" in value_str or "k" in value_str:
                return float(value_str.replace("K", "").replace("k", "")) * 1000
            else:
                return float(value_str)
        except:
            return 0
    
    def _analyze_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场情绪
        
        Args:
            data: 多空比数据
            
        Returns:
            Dict: 情绪分析结果
        """
        analysis = {
            "overall_sentiment": "NEUTRAL",
            "sentiment_score": 50,
            "market_phase": "BALANCED",
            "divergence": [],
            "warnings": [],
            "opportunities": []
        }
        
        global_ratio = data.get("global_ratio", {})
        whale_data = data.get("whale_positions", {})
        retail_data = data.get("retail_positions", {})
        
        # 计算综合情绪分数
        long_pct = global_ratio.get("long_percentage", 50)
        analysis["sentiment_score"] = long_pct
        
        # 判断整体情绪
        if long_pct >= self.sentiment_thresholds["extreme_greed"]:
            analysis["overall_sentiment"] = "EXTREME_GREED"
            analysis["warnings"].append("市场极度贪婪，注意回调风险")
        elif long_pct >= self.sentiment_thresholds["greed"]:
            analysis["overall_sentiment"] = "GREED"
            analysis["warnings"].append("市场贪婪，谨慎追高")
        elif long_pct >= self.sentiment_thresholds["neutral_high"]:
            analysis["overall_sentiment"] = "NEUTRAL_BULLISH"
        elif long_pct >= self.sentiment_thresholds["neutral_low"]:
            analysis["overall_sentiment"] = "NEUTRAL_BEARISH"
        elif long_pct >= self.sentiment_thresholds["fear"]:
            analysis["overall_sentiment"] = "FEAR"
            analysis["opportunities"].append("市场恐惧，可能存在抄底机会")
        else:
            analysis["overall_sentiment"] = "EXTREME_FEAR"
            analysis["opportunities"].append("市场极度恐惧，优质资产超卖")
        
        # 检测大户与散户分歧
        whale_long = whale_data.get("long_percentage", 50)
        retail_long = retail_data.get("long_percentage", 50)
        
        divergence = abs(whale_long - retail_long)
        if divergence > 20:
            if whale_long > retail_long:
                analysis["divergence"].append("大户看多，散户看空 - 跟随大户")
                analysis["opportunities"].append("大户建仓信号")
            else:
                analysis["divergence"].append("散户看多，大户看空 - 警惕风险")
                analysis["warnings"].append("大户可能在出货")
        
        # 判断市场阶段
        if whale_data.get("concentration") == "HIGH":
            if whale_long > 65:
                analysis["market_phase"] = "ACCUMULATION"  # 吸筹阶段
            elif whale_long < 35:
                analysis["market_phase"] = "DISTRIBUTION"  # 派发阶段
        elif divergence > 30:
            analysis["market_phase"] = "DIVERGENCE"  # 分歧阶段
        else:
            analysis["market_phase"] = "BALANCED"  # 平衡阶段
        
        return analysis
    
    def _generate_suggestions(self, data: Dict[str, Any]) -> List[str]:
        """
        生成交易建议
        
        Args:
            data: 完整的多空比数据
            
        Returns:
            List: 交易建议列表
        """
        suggestions = []
        
        sentiment = data.get("sentiment_analysis", {})
        global_ratio = data.get("global_ratio", {})
        whale_data = data.get("whale_positions", {})
        
        # 根据情绪生成建议
        overall_sentiment = sentiment.get("overall_sentiment")
        
        if overall_sentiment == "EXTREME_GREED":
            suggestions.append("🔴 减仓或开空：市场过热，随时可能回调")
            suggestions.append("💡 设置止盈：保护已有利润")
        elif overall_sentiment == "EXTREME_FEAR":
            suggestions.append("🟢 分批建仓：市场超卖，逐步买入")
            suggestions.append("💡 关注优质标的：寻找错杀品种")
        elif overall_sentiment == "GREED":
            suggestions.append("🟡 谨慎做多：控制仓位，严格止损")
        elif overall_sentiment == "FEAR":
            suggestions.append("🟡 逢低布局：小仓位试探")
        
        # 根据大户动向生成建议
        whale_concentration = whale_data.get("concentration")
        whale_change = whale_data.get("position_change", 0)
        
        if whale_concentration == "HIGH" and whale_change > 5:
            suggestions.append("🐋 跟随大户：大户增仓明显")
        elif whale_concentration == "HIGH" and whale_change < -5:
            suggestions.append("⚠️ 注意风险：大户减仓中")
        
        # 根据分歧生成建议
        for divergence in sentiment.get("divergence", []):
            if "大户建仓" in divergence:
                suggestions.append("📈 看涨信号：大户悄然建仓")
            elif "大户可能在出货" in divergence:
                suggestions.append("📉 看跌信号：大户可能出货")
        
        # 根据市场阶段
        market_phase = sentiment.get("market_phase")
        if market_phase == "ACCUMULATION":
            suggestions.append("🔄 吸筹阶段：耐心持有，等待启动")
        elif market_phase == "DISTRIBUTION":
            suggestions.append("🔄 派发阶段：逐步减仓，落袋为安")
        
        return suggestions
    
    def monitor_realtime(self, interval: int = 300, duration: int = 3600):
        """
        实时监控多空比变化
        
        Args:
            interval: 更新间隔（秒）
            duration: 监控持续时间（秒）
        """
        start_time = time.time()
        historical_data = []
        
        logger.info(f"开始监控多空比，间隔{interval}秒，持续{duration/3600}小时")
        
        while time.time() - start_time < duration:
            try:
                # 爬取数据
                current_data = self.crawl_ratio_data()
                
                # 添加到历史
                historical_data.append(current_data)
                
                # 保存数据
                self._save_data(current_data)
                
                # 输出分析
                global_ratio = current_data.get("global_ratio", {})
                sentiment = current_data.get("sentiment_analysis", {})
                suggestions = current_data.get("trading_suggestions", [])
                
                logger.info(f"\n===== 多空比监控 =====")
                logger.info(f"全网多空比: {global_ratio.get('long_percentage', 0):.1f}% : {global_ratio.get('short_percentage', 0):.1f}%")
                logger.info(f"多空比率: {global_ratio.get('ratio', 1):.2f}")
                logger.info(f"市场情绪: {sentiment.get('overall_sentiment', 'UNKNOWN')}")
                logger.info(f"情绪分数: {sentiment.get('sentiment_score', 50):.1f}")
                logger.info(f"市场阶段: {sentiment.get('market_phase', 'UNKNOWN')}")
                
                # 输出警告
                for warning in sentiment.get("warnings", []):
                    logger.warning(f"⚠️ {warning}")
                
                # 输出机会
                for opportunity in sentiment.get("opportunities", []):
                    logger.info(f"💎 {opportunity}")
                
                # 输出建议
                logger.info("\n交易建议:")
                for suggestion in suggestions[:3]:  # 限制输出前3条
                    logger.info(f"  {suggestion}")
                
                # 检测急剧变化
                if len(historical_data) > 1:
                    self._detect_rapid_changes(historical_data[-2:])
                
                # 等待下次更新
                if time.time() - start_time < duration:
                    time.sleep(interval)
                    
            except Exception as e:
                logger.error(f"监控出错: {e}")
                time.sleep(30)
        
        logger.info("监控结束")
        
        # 生成报告
        self._generate_report(historical_data)
    
    def _detect_rapid_changes(self, recent_data: List[Dict[str, Any]]):
        """检测急剧变化"""
        if len(recent_data) < 2:
            return
        
        prev = recent_data[0]["global_ratio"]
        curr = recent_data[1]["global_ratio"]
        
        change = curr["long_percentage"] - prev["long_percentage"]
        
        if abs(change) > 5:
            if change > 0:
                logger.warning(f"🚀 多头急增 {change:.1f}%，可能有大资金进场")
            else:
                logger.warning(f"💥 空头急增 {abs(change):.1f}%，可能有大资金离场")
    
    def _save_data(self, data: Dict[str, Any]):
        """保存数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_path}ratio_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"数据已保存: {filename}")
    
    def _generate_report(self, historical_data: List[Dict[str, Any]]):
        """生成监控报告"""
        if not historical_data:
            return
        
        # 计算统计数据
        long_percentages = [d["global_ratio"]["long_percentage"] for d in historical_data]
        sentiment_scores = [d["sentiment_analysis"]["sentiment_score"] for d in historical_data]
        
        report = {
            "monitoring_period": {
                "start": historical_data[0]["crawl_time"],
                "end": historical_data[-1]["crawl_time"],
                "data_points": len(historical_data)
            },
            "statistics": {
                "avg_long_percentage": sum(long_percentages) / len(long_percentages),
                "max_long_percentage": max(long_percentages),
                "min_long_percentage": min(long_percentages),
                "avg_sentiment_score": sum(sentiment_scores) / len(sentiment_scores),
                "sentiment_changes": len([1 for i in range(1, len(historical_data)) 
                                         if historical_data[i]["sentiment_analysis"]["overall_sentiment"] != 
                                         historical_data[i-1]["sentiment_analysis"]["overall_sentiment"]])
            },
            "key_insights": []
        }
        
        # 添加关键洞察
        if report["statistics"]["max_long_percentage"] > 80:
            report["key_insights"].append("监控期间出现极度贪婪")
        if report["statistics"]["min_long_percentage"] < 20:
            report["key_insights"].append("监控期间出现极度恐惧")
        if report["statistics"]["sentiment_changes"] > 5:
            report["key_insights"].append("市场情绪频繁变化，波动较大")
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.data_path}report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"监控报告已生成: {report_file}")


# 测试代码
if __name__ == "__main__":
    # 初始化认证
    auth = BiCoinAuth()
    
    # 登录
    if auth.login():
        # 创建爬虫
        crawler = RatioCrawler(auth)
        
        # 爬取多空比数据
        data = crawler.crawl_ratio_data()
        
        if data:
            print(f"\n多空比数据:")
            print(f"全网多空: {data['global_ratio'].get('long_percentage', 0):.1f}% : {data['global_ratio'].get('short_percentage', 0):.1f}%")
            print(f"市场情绪: {data['sentiment_analysis'].get('overall_sentiment')}")
            print(f"市场阶段: {data['sentiment_analysis'].get('market_phase')}")
            
            print(f"\n交易建议:")
            for suggestion in data.get('trading_suggestions', [])[:3]:
                print(f"  {suggestion}")
        
        # 关闭
        auth.close()
    else:
        print("登录失败")