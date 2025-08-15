"""
AI预警网站爬虫模块
爬取第三方AI分析网站的预警信息，作为我们系统的参考数据
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bicoin_auth import BiCoinAuth
from anti_detection import AntiDetection, RequestManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIAlertCrawler:
    """AI预警网站爬虫"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化爬虫
        
        Args:
            config: 配置字典，包含网站URL、登录信息等
        """
        # 默认配置
        default_config = {
            "url": "",  # 需要用户提供
            "requires_login": False,
            "username": "",
            "password": "",
            "update_interval": 60,  # 更新间隔（秒）
            "data_path": "data/ai_alerts/",
            "alert_types": ["price", "volume", "news", "social", "technical"]
        }
        
        self.config = {**default_config, **(config or {})}
        self.data_path = Path(self.config["data_path"])
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化反检测
        self.anti_detection = AntiDetection()
        self.request_manager = RequestManager(self.anti_detection)
        
        # 初始化driver
        self.driver = None
        self.auth = BiCoinAuth()  # 复用认证模块的driver管理
        
        # 缓存已处理的预警
        self.processed_alerts = set()
        self._load_processed_alerts()
        
    def _load_processed_alerts(self):
        """加载已处理的预警ID"""
        cache_file = self.data_path / "processed_alerts.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.processed_alerts = set(data.get("alert_ids", []))
            except:
                pass
    
    def _save_processed_alerts(self):
        """保存已处理的预警ID"""
        cache_file = self.data_path / "processed_alerts.json"
        with open(cache_file, 'w') as f:
            json.dump({
                "alert_ids": list(self.processed_alerts)[-10000:],  # 只保留最近10000条
                "updated": datetime.now().isoformat()
            }, f)
    
    def setup_driver(self):
        """设置浏览器驱动"""
        if not self.driver:
            self.driver = self.auth._init_driver()
            # 注入反检测脚本
            self.anti_detection.inject_stealth_scripts(self.driver)
        return self.driver
    
    def login_if_needed(self) -> bool:
        """如果需要登录，执行登录操作"""
        if not self.config["requires_login"]:
            return True
        
        try:
            # 这里需要根据实际网站定制登录逻辑
            logger.info("尝试登录AI预警网站...")
            
            # 示例登录流程（需要根据实际网站修改）
            self.driver.get(self.config["url"] + "/login")
            
            # 等待登录表单
            wait = WebDriverWait(self.driver, 20)
            
            # 输入用户名密码
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            self.anti_detection.simulate_human_typing(
                username_input, 
                self.config["username"]
            )
            
            password_input = self.driver.find_element(By.NAME, "password")
            self.anti_detection.simulate_human_typing(
                password_input,
                self.config["password"]
            )
            
            # 点击登录
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # 等待登录成功
            time.sleep(3)
            
            # 检查是否登录成功
            if "login" not in self.driver.current_url.lower():
                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                return False
                
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    def crawl_alerts(self) -> List[Dict[str, Any]]:
        """
        爬取预警信息
        
        Returns:
            List: 预警列表
        """
        alerts = []
        
        try:
            # 设置driver
            if not self.driver:
                self.setup_driver()
            
            # 访问预警页面
            logger.info(f"访问AI预警网站: {self.config['url']}")
            self.driver.get(self.config['url'])
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-container")))
            
            # 模拟人类行为
            self.anti_detection.simulate_human_scrolling(self.driver, times=2)
            
            # 解析预警数据
            alerts = self._parse_alerts()
            
            # 过滤新预警
            new_alerts = self._filter_new_alerts(alerts)
            
            # 保存数据
            if new_alerts:
                self._save_alerts(new_alerts)
                logger.info(f"发现 {len(new_alerts)} 条新预警")
            
            return new_alerts
            
        except TimeoutException:
            logger.error("页面加载超时")
            return []
        except Exception as e:
            logger.error(f"爬取预警失败: {e}")
            return []
    
    def _parse_alerts(self) -> List[Dict[str, Any]]:
        """
        解析预警信息（需要根据实际网站结构定制）
        
        Returns:
            List: 预警数据列表
        """
        alerts = []
        
        try:
            # 查找所有预警项
            alert_elements = self.driver.find_elements(By.CLASS_NAME, "alert-item")
            
            for element in alert_elements:
                try:
                    alert = self._parse_single_alert(element)
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    logger.debug(f"解析单条预警失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"解析预警列表失败: {e}")
        
        return alerts
    
    def _parse_single_alert(self, element) -> Optional[Dict[str, Any]]:
        """
        解析单条预警（需要根据实际网站结构定制）
        
        Args:
            element: 预警元素
            
        Returns:
            Dict: 预警数据
        """
        try:
            alert = {
                "id": "",
                "type": "",
                "symbol": "",
                "title": "",
                "content": "",
                "severity": "",  # low, medium, high, critical
                "confidence": 0,  # 置信度 0-100
                "time": "",
                "source": "ai_alert_site",
                "metadata": {}
            }
            
            # 示例解析逻辑（需要根据实际网站修改）
            
            # 获取预警ID（可能需要从属性或文本中提取）
            alert_id = element.get_attribute("data-alert-id")
            if not alert_id:
                # 如果没有ID，生成一个基于内容的哈希
                content = element.text
                alert_id = hashlib.md5(content.encode()).hexdigest()[:16]
            alert["id"] = alert_id
            
            # 获取币种
            try:
                symbol = element.find_element(By.CLASS_NAME, "alert-symbol").text
                alert["symbol"] = symbol.upper()
            except:
                pass
            
            # 获取预警类型
            try:
                alert_type = element.find_element(By.CLASS_NAME, "alert-type").text
                alert["type"] = self._normalize_alert_type(alert_type)
            except:
                pass
            
            # 获取标题
            try:
                title = element.find_element(By.CLASS_NAME, "alert-title").text
                alert["title"] = title
            except:
                pass
            
            # 获取内容
            try:
                content = element.find_element(By.CLASS_NAME, "alert-content").text
                alert["content"] = content
            except:
                pass
            
            # 获取严重程度
            try:
                severity = element.find_element(By.CLASS_NAME, "alert-severity").text
                alert["severity"] = self._normalize_severity(severity)
            except:
                alert["severity"] = "medium"
            
            # 获取置信度
            try:
                confidence = element.find_element(By.CLASS_NAME, "confidence").text
                alert["confidence"] = float(confidence.replace("%", ""))
            except:
                alert["confidence"] = 50
            
            # 获取时间
            try:
                time_text = element.find_element(By.CLASS_NAME, "alert-time").text
                alert["time"] = self._parse_time(time_text)
            except:
                alert["time"] = datetime.now().isoformat()
            
            # 提取关键指标
            alert["metadata"] = self._extract_metadata(element)
            
            return alert
            
        except Exception as e:
            logger.debug(f"解析预警详情失败: {e}")
            return None
    
    def _normalize_alert_type(self, type_text: str) -> str:
        """标准化预警类型"""
        type_text = type_text.lower()
        
        if any(word in type_text for word in ["price", "价格", "pump", "dump"]):
            return "price"
        elif any(word in type_text for word in ["volume", "成交量", "量能"]):
            return "volume"
        elif any(word in type_text for word in ["news", "新闻", "消息"]):
            return "news"
        elif any(word in type_text for word in ["social", "社交", "热度"]):
            return "social"
        elif any(word in type_text for word in ["technical", "技术", "指标"]):
            return "technical"
        else:
            return "other"
    
    def _normalize_severity(self, severity_text: str) -> str:
        """标准化严重程度"""
        severity_text = severity_text.lower()
        
        if any(word in severity_text for word in ["critical", "紧急", "严重"]):
            return "critical"
        elif any(word in severity_text for word in ["high", "高", "重要"]):
            return "high"
        elif any(word in severity_text for word in ["medium", "中", "一般"]):
            return "medium"
        elif any(word in severity_text for word in ["low", "低", "轻微"]):
            return "low"
        else:
            return "medium"
    
    def _parse_time(self, time_text: str) -> str:
        """解析时间文本"""
        # 处理相对时间（如"5分钟前"）
        if "分钟前" in time_text or "minutes ago" in time_text:
            minutes = int(''.join(filter(str.isdigit, time_text)))
            return (datetime.now() - timedelta(minutes=minutes)).isoformat()
        elif "小时前" in time_text or "hours ago" in time_text:
            hours = int(''.join(filter(str.isdigit, time_text)))
            return (datetime.now() - timedelta(hours=hours)).isoformat()
        else:
            # 尝试直接解析
            return time_text
    
    def _extract_metadata(self, element) -> Dict[str, Any]:
        """提取额外的元数据"""
        metadata = {}
        
        try:
            # 提取数值指标（价格变化、成交量等）
            indicators = element.find_elements(By.CLASS_NAME, "indicator")
            for indicator in indicators:
                try:
                    key = indicator.find_element(By.CLASS_NAME, "key").text
                    value = indicator.find_element(By.CLASS_NAME, "value").text
                    metadata[key] = value
                except:
                    continue
        except:
            pass
        
        return metadata
    
    def _filter_new_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出新的预警"""
        new_alerts = []
        
        for alert in alerts:
            alert_id = alert.get("id")
            if alert_id and alert_id not in self.processed_alerts:
                new_alerts.append(alert)
                self.processed_alerts.add(alert_id)
        
        return new_alerts
    
    def _save_alerts(self, alerts: List[Dict[str, Any]]):
        """保存预警数据"""
        if not alerts:
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_path / f"alerts_{timestamp}.json"
        
        # 保存数据
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "count": len(alerts),
                "alerts": alerts
            }, f, ensure_ascii=False, indent=2)
        
        # 更新已处理列表
        self._save_processed_alerts()
        
        logger.info(f"预警数据已保存: {filename}")
    
    def analyze_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析预警信息，生成综合报告
        
        Args:
            alerts: 预警列表
            
        Returns:
            Dict: 分析报告
        """
        analysis = {
            "total_alerts": len(alerts),
            "by_type": {},
            "by_severity": {},
            "by_symbol": {},
            "high_confidence": [],
            "critical_alerts": [],
            "trending_symbols": [],
            "summary": ""
        }
        
        if not alerts:
            return analysis
        
        # 按类型统计
        for alert in alerts:
            alert_type = alert.get("type", "other")
            analysis["by_type"][alert_type] = analysis["by_type"].get(alert_type, 0) + 1
            
            # 按严重程度统计
            severity = alert.get("severity", "medium")
            analysis["by_severity"][severity] = analysis["by_severity"].get(severity, 0) + 1
            
            # 按币种统计
            symbol = alert.get("symbol", "UNKNOWN")
            if symbol != "UNKNOWN":
                analysis["by_symbol"][symbol] = analysis["by_symbol"].get(symbol, 0) + 1
            
            # 高置信度预警
            if alert.get("confidence", 0) >= 80:
                analysis["high_confidence"].append({
                    "symbol": symbol,
                    "type": alert_type,
                    "title": alert.get("title", ""),
                    "confidence": alert.get("confidence")
                })
            
            # 严重预警
            if severity == "critical":
                analysis["critical_alerts"].append({
                    "symbol": symbol,
                    "type": alert_type,
                    "title": alert.get("title", ""),
                    "content": alert.get("content", "")[:200]
                })
        
        # 热门币种（预警最多的）
        if analysis["by_symbol"]:
            sorted_symbols = sorted(
                analysis["by_symbol"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            analysis["trending_symbols"] = [
                {"symbol": sym, "count": count} 
                for sym, count in sorted_symbols[:5]
            ]
        
        # 生成摘要
        analysis["summary"] = self._generate_summary(analysis)
        
        return analysis
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        # 总体情况
        total = analysis["total_alerts"]
        summary_parts.append(f"共收到{total}条预警")
        
        # 严重预警
        critical_count = analysis["by_severity"].get("critical", 0)
        if critical_count > 0:
            summary_parts.append(f"其中{critical_count}条严重预警需要立即关注")
        
        # 热门币种
        if analysis["trending_symbols"]:
            top_symbol = analysis["trending_symbols"][0]
            summary_parts.append(f"{top_symbol['symbol']}最受关注({top_symbol['count']}条)")
        
        # 主要类型
        if analysis["by_type"]:
            main_type = max(analysis["by_type"].items(), key=lambda x: x[1])
            summary_parts.append(f"主要为{main_type[0]}类预警")
        
        return "，".join(summary_parts) + "。"
    
    def monitor_realtime(self, interval: int = None, duration: int = 3600):
        """
        实时监控预警
        
        Args:
            interval: 更新间隔（秒）
            duration: 监控持续时间（秒）
        """
        if interval is None:
            interval = self.config.get("update_interval", 60)
        
        start_time = time.time()
        
        logger.info(f"开始监控AI预警，间隔{interval}秒，持续{duration/3600:.1f}小时")
        
        try:
            # 初始化driver
            self.setup_driver()
            
            # 登录（如果需要）
            if self.config["requires_login"]:
                if not self.login_if_needed():
                    logger.error("登录失败，停止监控")
                    return
            
            while time.time() - start_time < duration:
                try:
                    # 爬取预警
                    alerts = self.crawl_alerts()
                    
                    if alerts:
                        # 分析预警
                        analysis = self.analyze_alerts(alerts)
                        
                        # 输出分析结果
                        logger.info(f"\n===== AI预警分析 =====")
                        logger.info(f"摘要: {analysis['summary']}")
                        
                        # 输出严重预警
                        for critical in analysis["critical_alerts"][:3]:
                            logger.warning(f"🔴 严重预警: {critical['symbol']} - {critical['title']}")
                        
                        # 输出高置信度预警
                        for high_conf in analysis["high_confidence"][:3]:
                            logger.info(f"⭐ 高置信度: {high_conf['symbol']} - {high_conf['title']} ({high_conf['confidence']}%)")
                    
                    # 等待下次更新
                    if time.time() - start_time < duration:
                        time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"监控循环出错: {e}")
                    time.sleep(30)
            
        finally:
            if self.driver:
                self.driver.quit()
        
        logger.info("监控结束")
    
    def get_latest_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最新的预警
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List: 最新预警列表
        """
        # 查找最新的预警文件
        alert_files = sorted(self.data_path.glob("alerts_*.json"), reverse=True)
        
        all_alerts = []
        for file in alert_files[:5]:  # 最多读取5个文件
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_alerts.extend(data.get("alerts", []))
                    
                if len(all_alerts) >= limit:
                    break
            except:
                continue
        
        return all_alerts[:limit]
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
            self.driver = None


# 配置示例
def create_config_template():
    """创建配置模板"""
    template = {
        "url": "https://example-ai-alert-site.com",  # 需要替换为实际URL
        "requires_login": False,  # 是否需要登录
        "username": "",  # 如果需要登录，填写用户名
        "password": "",  # 如果需要登录，填写密码
        "update_interval": 60,  # 更新间隔（秒）
        "alert_types": ["price", "volume", "news", "social", "technical"],
        
        # 页面元素选择器（需要根据实际网站调整）
        "selectors": {
            "alert_container": ".alert-container",
            "alert_item": ".alert-item",
            "alert_id": "[data-alert-id]",
            "alert_symbol": ".alert-symbol",
            "alert_type": ".alert-type",
            "alert_title": ".alert-title",
            "alert_content": ".alert-content",
            "alert_severity": ".alert-severity",
            "alert_confidence": ".confidence",
            "alert_time": ".alert-time"
        }
    }
    
    # 保存模板
    config_file = Path("config/ai_alert_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    logger.info(f"配置模板已创建: {config_file}")
    return template


# 测试代码
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI预警网站爬虫")
    parser.add_argument("--url", help="网站URL")
    parser.add_argument("--config", default="config/ai_alert_config.json", help="配置文件路径")
    parser.add_argument("--mode", choices=["once", "monitor", "setup"], default="once",
                       help="运行模式: once(单次), monitor(监控), setup(创建配置)")
    parser.add_argument("--duration", type=int, default=3600, help="监控时长（秒）")
    
    args = parser.parse_args()
    
    if args.mode == "setup":
        # 创建配置模板
        create_config_template()
        print("配置模板已创建，请编辑 config/ai_alert_config.json 文件")
    else:
        # 加载配置
        config = {}
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = json.load(f)
        
        # 如果提供了URL参数，覆盖配置
        if args.url:
            config["url"] = args.url
        
        if not config.get("url"):
            print("错误：请提供网站URL")
            print("使用 --url 参数或编辑配置文件")
            sys.exit(1)
        
        # 创建爬虫
        crawler = AIAlertCrawler(config)
        
        if args.mode == "once":
            # 单次爬取
            alerts = crawler.crawl_alerts()
            if alerts:
                analysis = crawler.analyze_alerts(alerts)
                print(f"\n发现 {len(alerts)} 条新预警")
                print(f"摘要: {analysis['summary']}")
            else:
                print("没有发现新预警")
            
            crawler.cleanup()
            
        elif args.mode == "monitor":
            # 实时监控
            crawler.monitor_realtime(duration=args.duration)