"""
币Coin爆仓统计爬虫
实时监控全网爆仓数据，分析市场极端情况
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
import requests

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bicoin_auth import BiCoinAuth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiquidationCrawler:
    """爆仓数据爬虫"""
    
    def __init__(self, auth: BiCoinAuth):
        """
        初始化爬虫
        
        Args:
            auth: BiCoinAuth实例
        """
        self.auth = auth
        self.driver = auth.get_driver()
        self.api_url = "https://test1.bicoin.info/place-mgr/stock/state"
        self.web_url = "https://i.bicoin.com.cn/web/modules/liquidation.html"
        self.data_path = "data/liquidation/"
        
        # 创建数据目录
        os.makedirs(self.data_path, exist_ok=True)
        
        # 爆仓阈值设置
        self.thresholds = {
            "large_amount": 100000,  # 大额爆仓阈值（USDT）
            "alert_rate": 1000000,   # 警报级别爆仓总额（USDT/小时）
            "cascade_threshold": 5   # 连续爆仓次数阈值
        }
        
    def get_api_data(self) -> Optional[Dict[str, Any]]:
        """
        通过API获取爆仓数据
        
        Returns:
            Dict: API返回的数据
        """
        try:
            # 从driver获取cookies
            cookies = self.driver.get_cookies()
            session = requests.Session()
            
            # 设置cookies
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # 设置请求头
            headers = {
                'User-Agent': self.driver.execute_script("return navigator.userAgent"),
                'Referer': 'https://i.bicoin.com.cn',
                'Accept': 'application/json, text/plain, */*'
            }
            
            # 发送请求
            response = session.get(self.api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取API数据失败: {e}")
            return None
    
    def crawl_web_data(self) -> Dict[str, Any]:
        """
        从网页爬取爆仓数据
        
        Returns:
            Dict: 爆仓数据
        """
        liquidation_data = {
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {},
            "recent_liquidations": [],
            "statistics": {}
        }
        
        try:
            # 访问爆仓页面
            logger.info(f"访问爆仓统计页面: {self.web_url}")
            self.driver.get(self.web_url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "liquidation-container")))
            
            time.sleep(3)
            
            # 获取汇总数据
            liquidation_data["summary"] = self._get_summary_data()
            
            # 获取最近爆仓列表
            liquidation_data["recent_liquidations"] = self._get_recent_liquidations()
            
            # 获取统计数据
            liquidation_data["statistics"] = self._get_statistics()
            
            # 分析爆仓趋势
            liquidation_data["analysis"] = self._analyze_liquidations(liquidation_data)
            
            return liquidation_data
            
        except TimeoutException:
            logger.error("页面加载超时")
            return liquidation_data
        except Exception as e:
            logger.error(f"爬取网页数据失败: {e}")
            return liquidation_data
    
    def _get_summary_data(self) -> Dict[str, Any]:
        """获取爆仓汇总数据"""
        summary = {
            "total_24h": 0,
            "total_1h": 0,
            "long_liquidations": 0,
            "short_liquidations": 0,
            "long_percentage": 0,
            "short_percentage": 0,
            "largest_single": 0
        }
        
        try:
            # 24小时爆仓总额
            try:
                total_24h = self.driver.find_element(By.CLASS_NAME, "total-24h").text
                summary["total_24h"] = self._parse_amount(total_24h)
            except:
                pass
            
            # 1小时爆仓总额
            try:
                total_1h = self.driver.find_element(By.CLASS_NAME, "total-1h").text
                summary["total_1h"] = self._parse_amount(total_1h)
            except:
                pass
            
            # 多空爆仓数据
            try:
                long_amount = self.driver.find_element(By.CLASS_NAME, "long-liquidation").text
                summary["long_liquidations"] = self._parse_amount(long_amount)
                
                short_amount = self.driver.find_element(By.CLASS_NAME, "short-liquidation").text
                summary["short_liquidations"] = self._parse_amount(short_amount)
                
                # 计算百分比
                total = summary["long_liquidations"] + summary["short_liquidations"]
                if total > 0:
                    summary["long_percentage"] = (summary["long_liquidations"] / total) * 100
                    summary["short_percentage"] = (summary["short_liquidations"] / total) * 100
            except:
                pass
            
            # 最大单笔爆仓
            try:
                largest = self.driver.find_element(By.CLASS_NAME, "largest-liquidation").text
                summary["largest_single"] = self._parse_amount(largest)
            except:
                pass
            
        except Exception as e:
            logger.error(f"获取汇总数据失败: {e}")
        
        return summary
    
    def _get_recent_liquidations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的爆仓记录"""
        liquidations = []
        
        try:
            # 获取爆仓列表
            items = self.driver.find_elements(By.CLASS_NAME, "liquidation-item")[:limit]
            
            for item in items:
                try:
                    liq_data = {}
                    
                    # 交易所
                    try:
                        exchange = item.find_element(By.CLASS_NAME, "exchange").text
                        liq_data["exchange"] = exchange
                    except:
                        liq_data["exchange"] = "Unknown"
                    
                    # 交易对
                    try:
                        symbol = item.find_element(By.CLASS_NAME, "symbol").text
                        liq_data["symbol"] = symbol
                    except:
                        liq_data["symbol"] = "Unknown"
                    
                    # 方向
                    try:
                        direction = item.find_element(By.CLASS_NAME, "direction").text
                        liq_data["direction"] = "LONG" if "多" in direction else "SHORT"
                    except:
                        liq_data["direction"] = "Unknown"
                    
                    # 爆仓金额
                    try:
                        amount = item.find_element(By.CLASS_NAME, "amount").text
                        liq_data["amount"] = self._parse_amount(amount)
                    except:
                        liq_data["amount"] = 0
                    
                    # 爆仓价格
                    try:
                        price = item.find_element(By.CLASS_NAME, "price").text
                        liq_data["price"] = float(price.replace(",", "").replace("$", ""))
                    except:
                        liq_data["price"] = 0
                    
                    # 时间
                    try:
                        time_text = item.find_element(By.CLASS_NAME, "time").text
                        liq_data["time"] = time_text
                    except:
                        liq_data["time"] = ""
                    
                    if liq_data["amount"] > 0:
                        liquidations.append(liq_data)
                    
                except Exception as e:
                    logger.debug(f"解析爆仓记录失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"获取爆仓列表失败: {e}")
        
        return liquidations
    
    def _get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        stats = {
            "by_exchange": {},
            "by_symbol": {},
            "by_time": {},
            "trends": {}
        }
        
        try:
            # 交易所分布
            exchange_items = self.driver.find_elements(By.CLASS_NAME, "exchange-stat")
            for item in exchange_items[:10]:
                try:
                    name = item.find_element(By.CLASS_NAME, "name").text
                    value = item.find_element(By.CLASS_NAME, "value").text
                    stats["by_exchange"][name] = self._parse_amount(value)
                except:
                    continue
            
            # 币种分布
            symbol_items = self.driver.find_elements(By.CLASS_NAME, "symbol-stat")
            for item in symbol_items[:10]:
                try:
                    name = item.find_element(By.CLASS_NAME, "name").text
                    value = item.find_element(By.CLASS_NAME, "value").text
                    stats["by_symbol"][name] = self._parse_amount(value)
                except:
                    continue
            
        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
        
        return stats
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        解析金额字符串
        
        Args:
            amount_str: 金额字符串（可能包含K, M, B等单位）
            
        Returns:
            float: 金额数值
        """
        try:
            # 清理字符串
            amount_str = amount_str.replace(",", "").replace("$", "").replace("USDT", "").strip()
            
            # 处理单位
            if "K" in amount_str or "k" in amount_str:
                return float(amount_str.replace("K", "").replace("k", "")) * 1000
            elif "M" in amount_str or "m" in amount_str:
                return float(amount_str.replace("M", "").replace("m", "")) * 1000000
            elif "B" in amount_str or "b" in amount_str:
                return float(amount_str.replace("B", "").replace("b", "")) * 1000000000
            else:
                return float(amount_str)
        except:
            return 0
    
    def _analyze_liquidations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析爆仓数据
        
        Args:
            data: 爆仓数据
            
        Returns:
            Dict: 分析结果
        """
        analysis = {
            "market_status": "NORMAL",
            "risk_level": "LOW",
            "dominant_direction": "NEUTRAL",
            "large_liquidations": [],
            "warnings": [],
            "signals": []
        }
        
        summary = data.get("summary", {})
        recent = data.get("recent_liquidations", [])
        
        # 判断市场状态
        total_1h = summary.get("total_1h", 0)
        if total_1h > self.thresholds["alert_rate"]:
            analysis["market_status"] = "EXTREME"
            analysis["risk_level"] = "HIGH"
            analysis["warnings"].append(f"爆仓速率异常: {total_1h/1000000:.2f}M USDT/小时")
        elif total_1h > self.thresholds["alert_rate"] / 2:
            analysis["market_status"] = "VOLATILE"
            analysis["risk_level"] = "MEDIUM"
        
        # 判断爆仓方向
        long_pct = summary.get("long_percentage", 50)
        if long_pct > 70:
            analysis["dominant_direction"] = "SHORT_SQUEEZE"
            analysis["signals"].append("空头主导，可能见底")
        elif long_pct < 30:
            analysis["dominant_direction"] = "LONG_SQUEEZE"
            analysis["signals"].append("多头主导，可能见顶")
        
        # 识别大额爆仓
        for liq in recent:
            if liq.get("amount", 0) > self.thresholds["large_amount"]:
                analysis["large_liquidations"].append({
                    "exchange": liq.get("exchange"),
                    "symbol": liq.get("symbol"),
                    "amount": liq.get("amount"),
                    "direction": liq.get("direction")
                })
        
        # 检测连续爆仓（cascade)
        if len(recent) >= self.thresholds["cascade_threshold"]:
            same_direction = all(
                liq.get("direction") == recent[0].get("direction") 
                for liq in recent[:self.thresholds["cascade_threshold"]]
            )
            if same_direction:
                direction = recent[0].get("direction")
                analysis["warnings"].append(f"检测到{direction}连续爆仓，可能出现踩踏")
        
        # 生成交易信号
        if analysis["risk_level"] == "HIGH":
            if analysis["dominant_direction"] == "LONG_SQUEEZE":
                analysis["signals"].append("考虑减仓或做空")
            elif analysis["dominant_direction"] == "SHORT_SQUEEZE":
                analysis["signals"].append("考虑逢低买入")
        
        return analysis
    
    def monitor_realtime(self, interval: int = 60, duration: int = 3600):
        """
        实时监控爆仓数据
        
        Args:
            interval: 更新间隔（秒）
            duration: 监控持续时间（秒）
        """
        start_time = time.time()
        historical_data = []
        
        logger.info(f"开始实时监控爆仓，间隔{interval}秒，持续{duration/3600}小时")
        
        while time.time() - start_time < duration:
            try:
                # 获取数据（优先API，备用网页）
                api_data = self.get_api_data()
                
                if api_data:
                    logger.info("使用API数据")
                    current_data = self._process_api_data(api_data)
                else:
                    logger.info("使用网页数据")
                    current_data = self.crawl_web_data()
                
                # 添加到历史数据
                historical_data.append(current_data)
                
                # 保存数据
                self._save_data(current_data)
                
                # 分析并输出
                analysis = current_data.get("analysis", {})
                summary = current_data.get("summary", {})
                
                logger.info(f"\n===== 爆仓监控 =====")
                logger.info(f"1小时爆仓: {summary.get('total_1h', 0)/1000000:.2f}M USDT")
                logger.info(f"24小时爆仓: {summary.get('total_24h', 0)/1000000:.2f}M USDT")
                logger.info(f"多空比: {summary.get('long_percentage', 0):.1f}% : {summary.get('short_percentage', 0):.1f}%")
                logger.info(f"市场状态: {analysis.get('market_status', 'UNKNOWN')}")
                logger.info(f"风险等级: {analysis.get('risk_level', 'UNKNOWN')}")
                
                # 输出警告
                for warning in analysis.get("warnings", []):
                    logger.warning(f"⚠️ {warning}")
                
                # 输出信号
                for signal in analysis.get("signals", []):
                    logger.info(f"📊 {signal}")
                
                # 检查是否需要报警
                if analysis.get("risk_level") == "HIGH":
                    self._send_alert(current_data)
                
                # 等待下次更新
                if time.time() - start_time < duration:
                    time.sleep(interval)
                    
            except Exception as e:
                logger.error(f"监控出错: {e}")
                time.sleep(30)
        
        logger.info("监控结束")
        
        # 生成监控报告
        self._generate_report(historical_data)
    
    def _process_api_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API数据格式"""
        # 根据实际API返回格式进行处理
        processed = {
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {},
            "recent_liquidations": [],
            "statistics": {}
        }
        
        # TODO: 根据实际API格式解析数据
        
        return processed
    
    def _save_data(self, data: Dict[str, Any]):
        """保存数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_path}liquidation_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"数据已保存: {filename}")
    
    def _send_alert(self, data: Dict[str, Any]):
        """发送警报（这里只是日志，实际可接入通知系统）"""
        logger.critical("🚨 爆仓警报 🚨")
        logger.critical(f"风险等级: {data['analysis']['risk_level']}")
        logger.critical(f"1小时爆仓: {data['summary']['total_1h']/1000000:.2f}M USDT")
        
    def _generate_report(self, historical_data: List[Dict[str, Any]]):
        """生成监控报告"""
        if not historical_data:
            return
        
        report = {
            "monitoring_period": {
                "start": historical_data[0]["crawl_time"],
                "end": historical_data[-1]["crawl_time"],
                "data_points": len(historical_data)
            },
            "summary": {
                "total_liquidations": sum(d["summary"].get("total_1h", 0) for d in historical_data),
                "avg_hourly": sum(d["summary"].get("total_1h", 0) for d in historical_data) / len(historical_data),
                "max_hourly": max(d["summary"].get("total_1h", 0) for d in historical_data),
                "high_risk_periods": sum(1 for d in historical_data if d["analysis"].get("risk_level") == "HIGH")
            }
        }
        
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
        crawler = LiquidationCrawler(auth)
        
        # 爬取爆仓数据
        data = crawler.crawl_web_data()
        
        if data:
            print(f"\n爆仓数据:")
            print(f"1小时爆仓: {data['summary'].get('total_1h', 0)/1000000:.2f}M USDT")
            print(f"24小时爆仓: {data['summary'].get('total_24h', 0)/1000000:.2f}M USDT")
            print(f"多空比: {data['summary'].get('long_percentage', 0):.1f}% : {data['summary'].get('short_percentage', 0):.1f}%")
            print(f"市场状态: {data['analysis'].get('market_status')}")
            print(f"风险等级: {data['analysis'].get('risk_level')}")
        
        # 关闭
        auth.close()
    else:
        print("登录失败")