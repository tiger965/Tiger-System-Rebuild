"""
ValueScan.io AI信号爬虫模块
高优先级：这是一个准确率很高的AI分析网站
作者：5号窗口
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import undetected_chromedriver as uc

# 添加父目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bicoin'))

from bicoin.anti_detection import AntiDetection, RequestManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValueScanCrawler:
    """
    ValueScan.io AI信号爬虫
    这是一个玩家做的AI网站，准确率很高！
    网站每几分钟就更新，必须高频爬取！
    """
    
    def __init__(self):
        """初始化爬虫"""
        self.url = "https://www.valuescan.io"
        self.username = "3205381503@qq.com"
        self.password = "Yzh198796&"
        
        # 爬取频率配置（分钟）
        self.crawl_schedule = {
            "risk_alerts": 2,      # 2分钟 - 风险提示最重要
            "opportunities": 3,    # 3分钟 - 机会信号
            "tracking_list": 5,    # 5分钟 - 跟踪列表
            "end_tracking": 3      # 3分钟 - 结束跟踪（重要）
        }
        
        # 信号类型
        self.signal_categories = {
            "HIGH_RISK": "风险警告 - 立即处理",
            "OPPORTUNITY": "机会提示 - 可能上涨",
            "START_TRACK": "上榜跟踪 - 值得关注",
            "IN_TRACKING": "跟踪中 - 持续监控",
            "END_TRACK": "结束跟踪 - 注意风险！"
        }
        
        # 数据存储路径
        self.data_path = Path("data/valuescan")
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 反检测
        self.anti_detection = AntiDetection()
        self.driver = None
        
        # 缓存
        self.processed_signals = set()
        self.tracking_pool = {}  # 当前跟踪池
        
        # 上次爬取时间
        self.last_crawl = {
            "risk_alerts": 0,
            "opportunities": 0,
            "tracking_list": 0,
            "end_tracking": 0
        }
    
    def setup_driver(self):
        """设置Chrome驱动"""
        if self.driver:
            return self.driver
        
        options = uc.ChromeOptions()
        
        # 基础设置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 随机User-Agent
        options.add_argument(f'user-agent={self.anti_detection.get_random_user_agent()}')
        
        # 禁用自动化提示
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 创建driver
        self.driver = uc.Chrome(options=options)
        
        # 注入反检测脚本
        self.anti_detection.inject_stealth_scripts(self.driver)
        
        return self.driver
    
    def login(self) -> bool:
        """登录ValueScan网站"""
        try:
            logger.info("正在登录ValueScan.io...")
            
            # 设置driver
            if not self.driver:
                self.setup_driver()
            
            # 访问登录页面
            self.driver.get(f"{self.url}/login")
            
            # 等待登录表单
            wait = WebDriverWait(self.driver, 20)
            
            # 输入邮箱
            email_input = wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            self.anti_detection.simulate_human_typing(email_input, self.username)
            
            # 输入密码
            password_input = self.driver.find_element(By.NAME, "password")
            self.anti_detection.simulate_human_typing(password_input, self.password)
            
            # 随机等待
            time.sleep(1 + self.anti_detection.random.random() * 2)
            
            # 点击登录按钮
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # 等待登录成功
            time.sleep(3)
            
            # 检查是否登录成功
            if "/dashboard" in self.driver.current_url or "/home" in self.driver.current_url:
                logger.info("登录成功！")
                return True
            else:
                logger.error("登录失败")
                return False
                
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    def get_risk_alerts(self) -> List[Dict[str, Any]]:
        """
        获取风险警告信号
        最高优先级 - 立即处理
        """
        signals = []
        
        try:
            logger.info("爬取风险警告...")
            
            # 访问风险提示页面
            self.driver.get(f"{self.url}/alerts/risk")
            time.sleep(2)
            
            # 等待数据加载
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-item")))
            
            # 解析风险警告
            alert_elements = self.driver.find_elements(By.CLASS_NAME, "risk-alert")
            
            for element in alert_elements:
                try:
                    signal = {
                        "type": "HIGH_RISK",
                        "coin": element.find_element(By.CLASS_NAME, "coin-name").text,
                        "reason": element.find_element(By.CLASS_NAME, "risk-reason").text,
                        "severity": element.find_element(By.CLASS_NAME, "severity").text,
                        "confidence": self._extract_confidence(element),
                        "suggested_action": "SELL_OR_AVOID",
                        "time": datetime.now().isoformat(),
                        "source": "valuescan_risk"
                    }
                    
                    # 生成唯一ID
                    signal_id = self._generate_signal_id(signal)
                    if signal_id not in self.processed_signals:
                        signals.append(signal)
                        self.processed_signals.add(signal_id)
                        logger.warning(f"🔴 风险警告: {signal['coin']} - {signal['reason']}")
                        
                except Exception as e:
                    logger.debug(f"解析风险警告失败: {e}")
                    continue
                    
        except TimeoutException:
            logger.info("暂无风险警告")
        except Exception as e:
            logger.error(f"获取风险警告失败: {e}")
        
        return signals
    
    def get_opportunities(self) -> List[Dict[str, Any]]:
        """
        获取机会信号
        可能上涨的币种
        """
        signals = []
        
        try:
            logger.info("爬取机会信号...")
            
            # 访问机会页面
            self.driver.get(f"{self.url}/opportunities")
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "opportunity-card")))
            
            # 解析机会信号
            opp_elements = self.driver.find_elements(By.CLASS_NAME, "opportunity-item")
            
            for element in opp_elements:
                try:
                    signal = {
                        "type": "OPPORTUNITY",
                        "coin": element.find_element(By.CLASS_NAME, "coin-symbol").text,
                        "potential": element.find_element(By.CLASS_NAME, "potential-gain").text,
                        "analysis": element.find_element(By.CLASS_NAME, "analysis-summary").text,
                        "confidence": self._extract_confidence(element),
                        "entry_zone": element.find_element(By.CLASS_NAME, "entry-price").text,
                        "target": element.find_element(By.CLASS_NAME, "target-price").text,
                        "suggested_action": "BUY_ZONE",
                        "time": datetime.now().isoformat(),
                        "source": "valuescan_opportunity"
                    }
                    
                    signal_id = self._generate_signal_id(signal)
                    if signal_id not in self.processed_signals:
                        signals.append(signal)
                        self.processed_signals.add(signal_id)
                        logger.info(f"💎 机会信号: {signal['coin']} - 潜力{signal['potential']}")
                        
                except Exception as e:
                    logger.debug(f"解析机会信号失败: {e}")
                    continue
                    
        except TimeoutException:
            logger.info("暂无新机会")
        except Exception as e:
            logger.error(f"获取机会信号失败: {e}")
        
        return signals
    
    def get_tracking_list(self) -> List[Dict[str, Any]]:
        """
        获取跟踪列表
        正在跟踪的币种
        """
        tracking_list = []
        
        try:
            logger.info("更新跟踪列表...")
            
            # 访问跟踪页面
            self.driver.get(f"{self.url}/tracking")
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tracking-table")))
            
            # 解析跟踪列表
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".tracking-table tbody tr")
            
            for row in rows:
                try:
                    coin = row.find_element(By.CLASS_NAME, "coin-name").text
                    status = row.find_element(By.CLASS_NAME, "track-status").text
                    entry_time = row.find_element(By.CLASS_NAME, "entry-time").text
                    current_pnl = row.find_element(By.CLASS_NAME, "current-pnl").text
                    
                    track_data = {
                        "coin": coin,
                        "status": status,
                        "entry_time": entry_time,
                        "current_pnl": current_pnl,
                        "update_time": datetime.now().isoformat()
                    }
                    
                    # 更新跟踪池
                    if status == "TRACKING":
                        self.tracking_pool[coin] = track_data
                        
                        # 检查是否是新上榜
                        if coin not in self.tracking_pool:
                            signal = {
                                "type": "START_TRACK",
                                "coin": coin,
                                "message": "新币上榜跟踪",
                                "suggested_action": "WATCH",
                                "time": datetime.now().isoformat(),
                                "source": "valuescan_tracking"
                            }
                            tracking_list.append(signal)
                            logger.info(f"📊 新上榜: {coin}")
                    
                except Exception as e:
                    logger.debug(f"解析跟踪项失败: {e}")
                    continue
                    
        except TimeoutException:
            logger.info("跟踪列表暂无更新")
        except Exception as e:
            logger.error(f"获取跟踪列表失败: {e}")
        
        return tracking_list
    
    def get_ended_tracking(self) -> List[Dict[str, Any]]:
        """
        获取结束跟踪的币种
        非常重要 - 可能需要止损
        """
        ended_signals = []
        
        try:
            logger.info("检查结束跟踪...")
            
            # 访问历史页面或检查状态变化
            self.driver.get(f"{self.url}/tracking/ended")
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ended-list")))
            
            # 解析结束跟踪
            ended_items = self.driver.find_elements(By.CLASS_NAME, "ended-item")
            
            for item in ended_items:
                try:
                    coin = item.find_element(By.CLASS_NAME, "coin-name").text
                    end_reason = item.find_element(By.CLASS_NAME, "end-reason").text
                    final_pnl = item.find_element(By.CLASS_NAME, "final-pnl").text
                    
                    # 检查是否刚结束
                    if coin in self.tracking_pool:
                        signal = {
                            "type": "END_TRACK",
                            "coin": coin,
                            "reason": end_reason,
                            "final_pnl": final_pnl,
                            "suggested_action": "EXIT_POSITION",
                            "urgency": "HIGH",
                            "time": datetime.now().isoformat(),
                            "source": "valuescan_ended"
                        }
                        
                        ended_signals.append(signal)
                        del self.tracking_pool[coin]  # 从跟踪池移除
                        logger.warning(f"⚠️ 结束跟踪: {coin} - {end_reason}")
                        
                except Exception as e:
                    logger.debug(f"解析结束项失败: {e}")
                    continue
                    
        except TimeoutException:
            logger.info("暂无结束跟踪")
        except Exception as e:
            logger.error(f"获取结束跟踪失败: {e}")
        
        return ended_signals
    
    def crawl_realtime(self):
        """
        实时爬取 - 必须稳定运行
        根据不同类型的爬取频率执行
        """
        logger.info("🚀 启动ValueScan实时监控...")
        
        # 首先登录
        if not self.login():
            logger.error("登录失败，停止监控")
            return
        
        # 主循环
        while True:
            try:
                current_time = time.time()
                
                # 风险警告（2分钟）
                if current_time - self.last_crawl["risk_alerts"] > self.crawl_schedule["risk_alerts"] * 60:
                    risk_signals = self.get_risk_alerts()
                    if risk_signals:
                        self.send_to_analysis_system(risk_signals, priority="URGENT")
                    self.last_crawl["risk_alerts"] = current_time
                
                # 机会信号（3分钟）
                if current_time - self.last_crawl["opportunities"] > self.crawl_schedule["opportunities"] * 60:
                    opportunities = self.get_opportunities()
                    if opportunities:
                        self.send_to_analysis_system(opportunities, priority="HIGH")
                    self.last_crawl["opportunities"] = current_time
                
                # 跟踪列表（5分钟）
                if current_time - self.last_crawl["tracking_list"] > self.crawl_schedule["tracking_list"] * 60:
                    tracking = self.get_tracking_list()
                    self.update_tracking_pool(tracking)
                    self.last_crawl["tracking_list"] = current_time
                
                # 结束跟踪（3分钟）
                if current_time - self.last_crawl["end_tracking"] > self.crawl_schedule["end_tracking"] * 60:
                    ended = self.get_ended_tracking()
                    if ended:
                        self.alert_position_exit(ended)
                    self.last_crawl["end_tracking"] = current_time
                
                # 保存当前状态
                self.save_state()
                
                # 休眠30秒
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(10)  # 出错后等10秒重试
    
    def parse_signal_strength(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析信号强度
        网站的信号通常是综合多个指标的
        """
        strength_data = {
            "coin": signal.get("coin", ""),
            "type": signal.get("type", ""),
            "strength": signal.get("confidence", 50),  # 置信度
            "reasons": signal.get("analysis", signal.get("reason", "")),  # 分析原因
            "suggested_action": signal.get("suggested_action", "HOLD"),
            "time": signal.get("time", datetime.now().isoformat()),
            "urgency": self._calculate_urgency(signal)
        }
        
        return strength_data
    
    def _calculate_urgency(self, signal: Dict[str, Any]) -> str:
        """计算信号紧急程度"""
        signal_type = signal.get("type", "")
        
        if signal_type == "HIGH_RISK" or signal_type == "END_TRACK":
            return "CRITICAL"
        elif signal_type == "OPPORTUNITY" and signal.get("confidence", 0) > 80:
            return "HIGH"
        elif signal_type == "START_TRACK":
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_confidence(self, element) -> float:
        """提取置信度"""
        try:
            # 尝试多种可能的类名
            for class_name in ["confidence", "score", "rating", "strength"]:
                try:
                    conf_elem = element.find_element(By.CLASS_NAME, class_name)
                    conf_text = conf_elem.text
                    # 提取数字
                    import re
                    numbers = re.findall(r'\d+\.?\d*', conf_text)
                    if numbers:
                        return float(numbers[0])
                except:
                    continue
        except:
            pass
        return 50.0  # 默认置信度
    
    def _generate_signal_id(self, signal: Dict[str, Any]) -> str:
        """生成信号唯一ID"""
        key_parts = [
            signal.get("coin", ""),
            signal.get("type", ""),
            signal.get("reason", signal.get("analysis", ""))[:50]
        ]
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def send_to_analysis_system(self, signals: List[Dict[str, Any]], priority: str = "NORMAL"):
        """
        发送信号到分析系统
        这里应该对接6号窗口的AI分析
        """
        for signal in signals:
            parsed = self.parse_signal_strength(signal)
            
            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_path / f"signal_{priority}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "priority": priority,
                    "signal": parsed,
                    "raw": signal
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"信号已保存: {filename}")
    
    def update_tracking_pool(self, tracking_updates: List[Dict[str, Any]]):
        """更新跟踪池"""
        for update in tracking_updates:
            coin = update.get("coin")
            if coin:
                self.tracking_pool[coin] = update
        
        # 保存跟踪池状态
        pool_file = self.data_path / "tracking_pool.json"
        with open(pool_file, 'w', encoding='utf-8') as f:
            json.dump(self.tracking_pool, f, ensure_ascii=False, indent=2)
    
    def alert_position_exit(self, ended_signals: List[Dict[str, Any]]):
        """
        发出平仓警报
        对接7号窗口的风控系统
        """
        for signal in ended_signals:
            logger.critical(f"🚨 平仓警报: {signal['coin']} - {signal['reason']}")
            
            # 保存紧急警报
            alert_file = self.data_path / f"URGENT_EXIT_{signal['coin']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(signal, f, ensure_ascii=False, indent=2)
    
    def save_state(self):
        """保存爬虫状态"""
        state = {
            "last_crawl": self.last_crawl,
            "tracking_pool": self.tracking_pool,
            "processed_count": len(self.processed_signals),
            "last_update": datetime.now().isoformat()
        }
        
        state_file = self.data_path / "crawler_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        logger.info("ValueScan爬虫已停止")


# 测试和主函数
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ValueScan.io AI信号爬虫")
    parser.add_argument("--mode", choices=["realtime", "test", "once"], default="realtime",
                       help="运行模式: realtime(实时监控), test(测试), once(单次)")
    
    args = parser.parse_args()
    
    # 创建爬虫
    crawler = ValueScanCrawler()
    
    try:
        if args.mode == "test":
            # 测试模式 - 只登录并获取一次数据
            if crawler.login():
                logger.info("登录测试成功")
                
                # 测试各个功能
                logger.info("\n测试风险警告...")
                risks = crawler.get_risk_alerts()
                logger.info(f"获取 {len(risks)} 条风险警告")
                
                logger.info("\n测试机会信号...")
                opps = crawler.get_opportunities()
                logger.info(f"获取 {len(opps)} 条机会信号")
                
                logger.info("\n测试跟踪列表...")
                tracking = crawler.get_tracking_list()
                logger.info(f"跟踪池中有 {len(crawler.tracking_pool)} 个币种")
                
                logger.info("\n测试完成！")
            else:
                logger.error("登录测试失败")
                
        elif args.mode == "once":
            # 单次模式 - 执行一轮完整爬取
            if crawler.login():
                crawler.get_risk_alerts()
                crawler.get_opportunities()
                crawler.get_tracking_list()
                crawler.get_ended_tracking()
                crawler.save_state()
                logger.info("单次爬取完成")
                
        else:
            # 实时监控模式
            crawler.crawl_realtime()
            
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"程序错误: {e}")
    finally:
        crawler.cleanup()