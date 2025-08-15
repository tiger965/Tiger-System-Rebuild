"""
集成监控系统
整合币Coin爬虫和AI预警网站爬虫，提供统一的数据采集和分析
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import threading
from queue import Queue

# 添加父目录
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bicoin_auth import BiCoinAuth
from pages.square_crawler import SquareCrawler
from pages.liquidation_crawler import LiquidationCrawler
from pages.ratio_crawler import RatioCrawler
from trader.trader_monitor import TraderMonitor
from ai_alert_crawler import AIAlertCrawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IntegratedMonitor:
    """集成监控系统"""
    
    def __init__(self, config_file: str = "config/integrated_config.json"):
        """
        初始化集成监控系统
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.data_queue = Queue()  # 数据队列
        self.alert_queue = Queue()  # 预警队列
        
        # 初始化各模块
        self.modules = {}
        self._init_modules()
        
        # 统计信息
        self.stats = {
            "start_time": None,
            "bicoin_crawls": 0,
            "ai_alerts": 0,
            "critical_alerts": 0,
            "data_points": 0
        }
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "bicoin": {
                "enabled": True,
                "intervals": {
                    "square": 600,      # 10分钟
                    "liquidation": 60,  # 1分钟
                    "ratio": 300,       # 5分钟
                    "traders": 1800     # 30分钟
                }
            },
            "ai_alert": {
                "enabled": True,
                "url": "",  # 需要配置
                "interval": 60,  # 1分钟
                "requires_login": False
            },
            "integration": {
                "correlation_window": 300,  # 5分钟相关性窗口
                "alert_threshold": {
                    "confidence": 70,  # 置信度阈值
                    "severity": "high"  # 严重程度阈值
                }
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # 深度合并配置
                return self._merge_configs(default_config, user_config)
        else:
            # 保存默认配置
            Path(config_file).parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """深度合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _init_modules(self):
        """初始化各模块"""
        # 币Coin模块
        if self.config["bicoin"]["enabled"]:
            try:
                auth = BiCoinAuth()
                self.modules["bicoin_auth"] = auth
                self.modules["square"] = SquareCrawler(auth)
                self.modules["liquidation"] = LiquidationCrawler(auth)
                self.modules["ratio"] = RatioCrawler(auth)
                self.modules["traders"] = TraderMonitor(auth)
                logger.info("币Coin模块初始化成功")
            except Exception as e:
                logger.error(f"币Coin模块初始化失败: {e}")
        
        # AI预警模块
        if self.config["ai_alert"]["enabled"]:
            try:
                ai_config = self.config["ai_alert"]
                if ai_config.get("url"):
                    self.modules["ai_alert"] = AIAlertCrawler(ai_config)
                    logger.info("AI预警模块初始化成功")
                else:
                    logger.warning("AI预警模块未配置URL，跳过初始化")
            except Exception as e:
                logger.error(f"AI预警模块初始化失败: {e}")
    
    def run_bicoin_module(self, module_name: str):
        """运行币Coin模块"""
        try:
            if module_name == "square" and "square" in self.modules:
                data = self.modules["square"].crawl_square(max_posts=30, scroll_times=3)
                if data:
                    analysis = self.modules["square"].analyze_trends(data)
                    self.data_queue.put({
                        "source": "bicoin_square",
                        "data": data,
                        "analysis": analysis,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.stats["bicoin_crawls"] += 1
                    logger.info(f"币Coin广场: 获取{len(data)}条动态")
            
            elif module_name == "liquidation" and "liquidation" in self.modules:
                data = self.modules["liquidation"].crawl_web_data()
                if data:
                    self.data_queue.put({
                        "source": "bicoin_liquidation",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.stats["bicoin_crawls"] += 1
                    
                    # 检查是否需要预警
                    if data.get("analysis", {}).get("risk_level") == "HIGH":
                        self.alert_queue.put({
                            "source": "liquidation",
                            "severity": "high",
                            "message": f"爆仓风险预警: {data['analysis'].get('market_status')}",
                            "data": data["summary"]
                        })
            
            elif module_name == "ratio" and "ratio" in self.modules:
                data = self.modules["ratio"].crawl_ratio_data()
                if data:
                    self.data_queue.put({
                        "source": "bicoin_ratio",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.stats["bicoin_crawls"] += 1
            
            elif module_name == "traders" and "traders" in self.modules:
                data = self.modules["traders"].monitor_all_traders()
                if data:
                    self.data_queue.put({
                        "source": "bicoin_traders",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.stats["bicoin_crawls"] += 1
                    
        except Exception as e:
            logger.error(f"运行币Coin模块{module_name}失败: {e}")
    
    def run_ai_alert_module(self):
        """运行AI预警模块"""
        try:
            if "ai_alert" in self.modules:
                alerts = self.modules["ai_alert"].crawl_alerts()
                if alerts:
                    analysis = self.modules["ai_alert"].analyze_alerts(alerts)
                    
                    self.data_queue.put({
                        "source": "ai_alerts",
                        "data": alerts,
                        "analysis": analysis,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    self.stats["ai_alerts"] += len(alerts)
                    
                    # 处理高优先级预警
                    for alert in alerts:
                        if self._should_forward_alert(alert):
                            self.alert_queue.put({
                                "source": "ai_alert",
                                "severity": alert.get("severity", "medium"),
                                "symbol": alert.get("symbol", ""),
                                "message": alert.get("title", ""),
                                "confidence": alert.get("confidence", 0),
                                "data": alert
                            })
                            
                            if alert.get("severity") == "critical":
                                self.stats["critical_alerts"] += 1
                    
                    logger.info(f"AI预警: 获取{len(alerts)}条预警")
                    
        except Exception as e:
            logger.error(f"运行AI预警模块失败: {e}")
    
    def _should_forward_alert(self, alert: Dict[str, Any]) -> bool:
        """判断是否需要转发预警"""
        thresholds = self.config["integration"]["alert_threshold"]
        
        # 检查置信度
        if alert.get("confidence", 0) < thresholds.get("confidence", 70):
            return False
        
        # 检查严重程度
        severity_levels = ["low", "medium", "high", "critical"]
        alert_severity = alert.get("severity", "medium")
        threshold_severity = thresholds.get("severity", "high")
        
        if severity_levels.index(alert_severity) < severity_levels.index(threshold_severity):
            return False
        
        return True
    
    def correlate_data(self):
        """关联分析不同来源的数据"""
        # 收集最近的数据
        recent_data = []
        while not self.data_queue.empty():
            recent_data.append(self.data_queue.get())
            self.stats["data_points"] += 1
        
        if len(recent_data) < 2:
            return
        
        # 按来源分组
        data_by_source = {}
        for item in recent_data:
            source = item["source"]
            if source not in data_by_source:
                data_by_source[source] = []
            data_by_source[source].append(item)
        
        # 关联分析
        correlations = []
        
        # 1. AI预警与爆仓数据关联
        if "ai_alerts" in data_by_source and "bicoin_liquidation" in data_by_source:
            ai_data = data_by_source["ai_alerts"][-1] if data_by_source["ai_alerts"] else None
            liq_data = data_by_source["bicoin_liquidation"][-1] if data_by_source["bicoin_liquidation"] else None
            
            if ai_data and liq_data:
                # 检查是否有相关性
                for alert in ai_data.get("data", []):
                    if alert.get("type") == "price" and alert.get("severity") in ["high", "critical"]:
                        if liq_data.get("data", {}).get("analysis", {}).get("risk_level") == "HIGH":
                            correlations.append({
                                "type": "ai_liquidation_correlation",
                                "message": f"AI预警与爆仓风险同时出现，需要特别关注{alert.get('symbol', '')}",
                                "severity": "critical"
                            })
        
        # 2. 交易员行为与市场情绪关联
        if "bicoin_traders" in data_by_source and "bicoin_ratio" in data_by_source:
            trader_data = data_by_source["bicoin_traders"][-1] if data_by_source["bicoin_traders"] else None
            ratio_data = data_by_source["bicoin_ratio"][-1] if data_by_source["bicoin_ratio"] else None
            
            if trader_data and ratio_data:
                # 检查交易员集体行为
                collective = trader_data.get("data", {}).get("collective_analysis", {})
                sentiment = ratio_data.get("data", {}).get("sentiment_analysis", {})
                
                if collective.get("consensus_level", 0) > 70 and sentiment.get("overall_sentiment") in ["EXTREME_GREED", "EXTREME_FEAR"]:
                    correlations.append({
                        "type": "trader_sentiment_correlation",
                        "message": f"顶级交易员一致行动且市场情绪极端({sentiment.get('overall_sentiment')})",
                        "severity": "high"
                    })
        
        # 输出关联分析结果
        for correlation in correlations:
            logger.warning(f"🔗 关联预警: {correlation['message']}")
            self.alert_queue.put(correlation)
    
    def process_alerts(self):
        """处理预警队列"""
        alerts = []
        while not self.alert_queue.empty():
            alerts.append(self.alert_queue.get())
        
        if not alerts:
            return
        
        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 2))
        
        # 输出预警
        logger.info(f"\n{'='*50}")
        logger.info("📢 综合预警报告")
        logger.info(f"{'='*50}")
        
        for alert in alerts[:10]:  # 最多显示10条
            severity = alert.get("severity", "medium")
            source = alert.get("source", "unknown")
            message = alert.get("message", "")
            
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            
            logger.info(f"{icon} [{severity.upper()}] {source}: {message}")
            
            # 如果有置信度，显示
            if "confidence" in alert:
                logger.info(f"   置信度: {alert['confidence']}%")
        
        logger.info(f"{'='*50}\n")
    
    def monitor(self, duration: int = 3600):
        """
        主监控循环
        
        Args:
            duration: 监控时长（秒）
        """
        self.stats["start_time"] = datetime.now()
        start_time = time.time()
        
        logger.info(f"开始集成监控，持续{duration/3600:.1f}小时")
        
        # 记录上次运行时间
        last_run = {
            "square": 0,
            "liquidation": 0,
            "ratio": 0,
            "traders": 0,
            "ai_alert": 0,
            "correlation": 0
        }
        
        try:
            while time.time() - start_time < duration:
                current_time = time.time()
                
                # 币Coin模块
                if self.config["bicoin"]["enabled"]:
                    intervals = self.config["bicoin"]["intervals"]
                    
                    # 爆仓监控（高频）
                    if current_time - last_run["liquidation"] > intervals["liquidation"]:
                        self.run_bicoin_module("liquidation")
                        last_run["liquidation"] = current_time
                    
                    # 多空比监控
                    if current_time - last_run["ratio"] > intervals["ratio"]:
                        self.run_bicoin_module("ratio")
                        last_run["ratio"] = current_time
                    
                    # 广场监控
                    if current_time - last_run["square"] > intervals["square"]:
                        self.run_bicoin_module("square")
                        last_run["square"] = current_time
                    
                    # 交易员监控（低频）
                    if current_time - last_run["traders"] > intervals["traders"]:
                        self.run_bicoin_module("traders")
                        last_run["traders"] = current_time
                
                # AI预警模块
                if self.config["ai_alert"]["enabled"] and "ai_alert" in self.modules:
                    if current_time - last_run["ai_alert"] > self.config["ai_alert"]["interval"]:
                        self.run_ai_alert_module()
                        last_run["ai_alert"] = current_time
                
                # 关联分析（每5分钟）
                if current_time - last_run["correlation"] > 300:
                    self.correlate_data()
                    last_run["correlation"] = current_time
                
                # 处理预警
                self.process_alerts()
                
                # 显示统计
                if int(current_time) % 600 == 0:  # 每10分钟
                    self._display_stats()
                
                # 短暂休眠
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("用户中断")
        except Exception as e:
            logger.error(f"监控出错: {e}")
        finally:
            self._cleanup()
    
    def _display_stats(self):
        """显示统计信息"""
        if not self.stats["start_time"]:
            return
        
        runtime = datetime.now() - self.stats["start_time"]
        hours = runtime.total_seconds() / 3600
        
        logger.info(f"\n[统计] 运行时间: {hours:.1f}小时 | "
                   f"币Coin爬取: {self.stats['bicoin_crawls']} | "
                   f"AI预警: {self.stats['ai_alerts']} | "
                   f"严重预警: {self.stats['critical_alerts']} | "
                   f"数据点: {self.stats['data_points']}")
    
    def _cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        
        # 关闭币Coin模块
        if "bicoin_auth" in self.modules:
            self.modules["bicoin_auth"].close()
        
        # 关闭AI预警模块
        if "ai_alert" in self.modules:
            self.modules["ai_alert"].cleanup()
        
        # 生成最终报告
        self._generate_report()
    
    def _generate_report(self):
        """生成监控报告"""
        if not self.stats["start_time"]:
            return
        
        runtime = datetime.now() - self.stats["start_time"]
        
        report = {
            "monitoring_session": {
                "start": self.stats["start_time"].isoformat(),
                "end": datetime.now().isoformat(),
                "duration_hours": runtime.total_seconds() / 3600
            },
            "statistics": self.stats,
            "configuration": self.config
        }
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/integrated_report_{timestamp}.json"
        
        Path("reports").mkdir(exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"监控报告已保存: {report_file}")


# 主函数
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="集成监控系统")
    parser.add_argument("--config", default="config/integrated_config.json", 
                       help="配置文件路径")
    parser.add_argument("--duration", type=int, default=3600, 
                       help="监控时长（秒）")
    parser.add_argument("--ai-url", help="AI预警网站URL")
    
    args = parser.parse_args()
    
    # 如果提供了AI URL，更新配置
    if args.ai_url:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        if "ai_alert" not in config:
            config["ai_alert"] = {}
        config["ai_alert"]["url"] = args.ai_url
        config["ai_alert"]["enabled"] = True
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"已更新AI预警网站URL: {args.ai_url}")
    
    # 创建监控系统
    monitor = IntegratedMonitor(args.config)
    
    # 开始监控
    monitor.monitor(duration=args.duration)


if __name__ == "__main__":
    main()