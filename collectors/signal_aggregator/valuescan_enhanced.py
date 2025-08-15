"""
ValueScan.io 增强版爬虫
包含自动重连、Cookie管理、登录状态检测
确保能够长时间稳定运行
"""

import os
import sys
import json
import time
import pickle
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValueScanEnhanced:
    """增强版ValueScan爬虫，支持自动重连和会话保持"""
    
    def __init__(self):
        """初始化"""
        self.url = "https://www.valuescan.io"
        self.username = "3205381503@qq.com"
        self.password = "Yzh198796&"
        
        # 路径配置
        self.data_path = Path("data/valuescan")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.cookie_path = self.data_path / "cookies.pkl"
        self.state_path = self.data_path / "state.json"
        
        # 驱动和会话
        self.driver = None
        self.logged_in = False
        self.last_login_time = None
        self.login_retry_count = 0
        self.max_login_retries = 3
        
        # 监控配置
        self.check_interval = 60  # 每分钟检查一次登录状态
        self.session_timeout = 1800  # 30分钟后重新登录
        
        # 加载保存的状态
        self.load_state()
    
    def setup_driver(self, headless: bool = False):
        """设置Chrome驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        options = uc.ChromeOptions()
        
        # 使用Windows的Chrome（Edge也可以）
        # 尝试找到Chrome或Edge的路径
        import platform
        if platform.system() == "Linux" and "microsoft" in platform.uname().release.lower():
            # 在WSL中使用Windows的Chrome
            chrome_paths = [
                "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe",
                "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    logger.info(f"使用浏览器: {path}")
                    break
        
        # 基础设置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 是否无头模式
        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
        
        # 禁用自动化提示
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 设置窗口大小
        options.add_argument('--window-size=1920,1080')
        
        # 创建driver
        self.driver = uc.Chrome(options=options)
        
        # 执行反检测脚本
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        logger.info("Chrome驱动已初始化")
        return self.driver
    
    def save_cookies(self):
        """保存Cookies到文件"""
        if self.driver and self.logged_in:
            cookies = self.driver.get_cookies()
            with open(self.cookie_path, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info("Cookies已保存")
    
    def load_cookies(self) -> bool:
        """加载Cookies"""
        if not self.cookie_path.exists():
            return False
        
        try:
            with open(self.cookie_path, 'rb') as f:
                cookies = pickle.load(f)
            
            # 先访问网站
            self.driver.get(self.url)
            time.sleep(2)
            
            # 添加cookies
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            # 刷新页面
            self.driver.refresh()
            time.sleep(2)
            
            logger.info("Cookies已加载")
            return True
            
        except Exception as e:
            logger.error(f"加载Cookies失败: {e}")
            return False
    
    def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查URL
            current_url = self.driver.current_url
            
            # 已登录的标志
            if any(path in current_url for path in ['/dashboard', '/home', '/alerts', '/tracking']):
                return True
            
            # 检查是否有登录后才有的元素
            try:
                self.driver.find_element(By.CLASS_NAME, "user-menu")
                return True
            except:
                pass
            
            # 检查是否被重定向到登录页
            if '/login' in current_url:
                return False
            
            # 尝试访问需要登录的页面
            self.driver.get(f"{self.url}/alerts")
            time.sleep(2)
            
            if '/login' in self.driver.current_url:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def login_with_retry(self) -> bool:
        """带重试的登录"""
        for attempt in range(self.max_login_retries):
            logger.info(f"登录尝试 {attempt + 1}/{self.max_login_retries}")
            
            if self.do_login():
                self.login_retry_count = 0
                return True
            
            if attempt < self.max_login_retries - 1:
                wait_time = (attempt + 1) * 5
                logger.info(f"等待{wait_time}秒后重试...")
                time.sleep(wait_time)
        
        logger.error("登录失败，已达最大重试次数")
        return False
    
    def do_login(self) -> bool:
        """执行登录"""
        try:
            logger.info("正在登录ValueScan.io...")
            
            # 确保driver存在
            if not self.driver:
                self.setup_driver()
            
            # 先尝试使用cookies
            if self.load_cookies():
                if self.check_login_status():
                    logger.info("使用Cookies登录成功")
                    self.logged_in = True
                    self.last_login_time = datetime.now()
                    return True
            
            # Cookie登录失败，使用账号密码
            logger.info("使用账号密码登录...")
            
            # 访问登录页面
            self.driver.get(f"{self.url}/login")
            time.sleep(3)
            
            # 等待登录表单
            wait = WebDriverWait(self.driver, 20)
            
            # 查找邮箱输入框（尝试多种选择器）
            email_input = None
            for selector in [
                (By.NAME, "email"),
                (By.ID, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='email']"),
                (By.XPATH, "//input[@type='email']")
            ]:
                try:
                    email_input = wait.until(EC.presence_of_element_located(selector))
                    break
                except:
                    continue
            
            if not email_input:
                logger.error("找不到邮箱输入框")
                return False
            
            # 清空并输入邮箱
            email_input.clear()
            for char in self.username:
                email_input.send_keys(char)
                time.sleep(0.1 + random.random() * 0.1)
            
            # 查找密码输入框
            password_input = None
            for selector in [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@type='password']")
            ]:
                try:
                    password_input = self.driver.find_element(*selector)
                    break
                except:
                    continue
            
            if not password_input:
                logger.error("找不到密码输入框")
                return False
            
            # 清空并输入密码
            password_input.clear()
            for char in self.password:
                password_input.send_keys(char)
                time.sleep(0.1 + random.random() * 0.1)
            
            # 等待一下
            time.sleep(1 + random.random())
            
            # 查找登录按钮
            login_button = None
            for selector in [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), '登录')]"),
                (By.CLASS_NAME, "login-button"),
                (By.ID, "login-button")
            ]:
                try:
                    login_button = self.driver.find_element(*selector)
                    break
                except:
                    continue
            
            if not login_button:
                logger.error("找不到登录按钮")
                return False
            
            # 点击登录
            login_button.click()
            
            # 等待登录完成
            time.sleep(5)
            
            # 检查登录结果
            if self.check_login_status():
                logger.info("登录成功！")
                self.logged_in = True
                self.last_login_time = datetime.now()
                self.save_cookies()
                self.save_state()
                return True
            else:
                logger.error("登录失败：可能是账号密码错误或需要验证码")
                return False
                
        except TimeoutException:
            logger.error("登录超时")
            return False
        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            # 保存截图用于调试
            try:
                screenshot_path = self.data_path / f"login_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(str(screenshot_path))
                logger.info(f"错误截图已保存: {screenshot_path}")
            except:
                pass
            return False
    
    def ensure_logged_in(self) -> bool:
        """确保已登录"""
        # 检查是否需要重新登录
        if self.last_login_time:
            elapsed = (datetime.now() - self.last_login_time).total_seconds()
            if elapsed > self.session_timeout:
                logger.info("会话超时，需要重新登录")
                self.logged_in = False
        
        # 如果未登录或需要重新登录
        if not self.logged_in or not self.check_login_status():
            return self.login_with_retry()
        
        return True
    
    def get_page_with_login_check(self, url: str) -> bool:
        """访问页面并检查登录状态"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # 如果被重定向到登录页
            if '/login' in self.driver.current_url:
                logger.info("需要重新登录")
                if self.ensure_logged_in():
                    self.driver.get(url)
                    time.sleep(2)
                    return True
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"访问页面失败: {e}")
            return False
    
    def crawl_with_auto_reconnect(self):
        """带自动重连的爬取"""
        logger.info("🚀 启动增强版ValueScan监控...")
        
        # 初始化driver
        self.setup_driver()
        
        # 确保登录
        if not self.ensure_logged_in():
            logger.error("初始登录失败")
            return
        
        # 主循环
        error_count = 0
        max_errors = 5
        
        while True:
            try:
                # 定期检查登录状态
                if not self.ensure_logged_in():
                    logger.error("无法保持登录状态")
                    error_count += 1
                    if error_count >= max_errors:
                        logger.error("错误次数过多，停止监控")
                        break
                    time.sleep(60)
                    continue
                
                # 重置错误计数
                error_count = 0
                
                # 执行爬取任务
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 开始爬取...")
                
                # 爬取风险警告
                if self.get_page_with_login_check(f"{self.url}/alerts/risk"):
                    self.parse_risk_alerts()
                
                # 爬取机会信号
                if self.get_page_with_login_check(f"{self.url}/opportunities"):
                    self.parse_opportunities()
                
                # 爬取跟踪列表
                if self.get_page_with_login_check(f"{self.url}/tracking"):
                    self.parse_tracking()
                
                # 保存状态
                self.save_state()
                
                # 休眠
                logger.info(f"等待{self.check_interval}秒...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("用户中断")
                break
            except Exception as e:
                logger.error(f"爬取循环错误: {e}")
                error_count += 1
                
                # 尝试重启driver
                if error_count >= 3:
                    logger.info("尝试重启浏览器...")
                    self.setup_driver()
                    self.logged_in = False
                
                time.sleep(30)
    
    def parse_risk_alerts(self):
        """解析风险警告（简化版）"""
        try:
            # 等待内容加载
            wait = WebDriverWait(self.driver, 10)
            
            # 查找警告元素
            alerts = self.driver.find_elements(By.CSS_SELECTOR, "[class*='alert'], [class*='risk'], [class*='warning']")
            
            logger.info(f"找到 {len(alerts)} 条风险警告")
            
            # 解析并保存
            for alert in alerts[:10]:  # 限制数量
                try:
                    text = alert.text
                    if text:
                        logger.warning(f"风险警告: {text[:100]}...")
                except:
                    pass
                    
        except TimeoutException:
            logger.info("风险警告页面加载超时")
        except Exception as e:
            logger.error(f"解析风险警告失败: {e}")
    
    def parse_opportunities(self):
        """解析机会信号（简化版）"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # 查找机会元素
            opportunities = self.driver.find_elements(By.CSS_SELECTOR, "[class*='opportunity'], [class*='signal'], [class*='alert']")
            
            logger.info(f"找到 {len(opportunities)} 个机会信号")
            
            # 解析并保存
            for opp in opportunities[:10]:
                try:
                    text = opp.text
                    if text:
                        logger.info(f"机会信号: {text[:100]}...")
                except:
                    pass
                    
        except TimeoutException:
            logger.info("机会页面加载超时")
        except Exception as e:
            logger.error(f"解析机会信号失败: {e}")
    
    def parse_tracking(self):
        """解析跟踪列表（简化版）"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # 查找跟踪元素
            tracking_items = self.driver.find_elements(By.CSS_SELECTOR, "table tr, [class*='track'], [class*='coin']")
            
            logger.info(f"跟踪列表包含 {len(tracking_items)} 项")
            
        except TimeoutException:
            logger.info("跟踪页面加载超时")
        except Exception as e:
            logger.error(f"解析跟踪列表失败: {e}")
    
    def save_state(self):
        """保存状态"""
        state = {
            "last_login_time": self.last_login_time.isoformat() if self.last_login_time else None,
            "logged_in": self.logged_in,
            "last_update": datetime.now().isoformat()
        }
        
        with open(self.state_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """加载状态"""
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    state = json.load(f)
                    
                if state.get("last_login_time"):
                    self.last_login_time = datetime.fromisoformat(state["last_login_time"])
                    
            except Exception as e:
                logger.error(f"加载状态失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        logger.info("爬虫已停止")


# 添加必要的导入
import random

# 主函数
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ValueScan增强版爬虫")
    parser.add_argument("--mode", choices=["monitor", "test", "login"], default="test",
                       help="运行模式: monitor(监控), test(测试), login(仅登录)")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    
    args = parser.parse_args()
    
    # 创建爬虫
    crawler = ValueScanEnhanced()
    
    try:
        if args.mode == "login":
            # 仅测试登录
            crawler.setup_driver(headless=args.headless)
            if crawler.login_with_retry():
                logger.info("✅ 登录测试成功！")
                
                # 测试访问各个页面
                test_urls = [
                    f"{crawler.url}/alerts",
                    f"{crawler.url}/opportunities",
                    f"{crawler.url}/tracking"
                ]
                
                for url in test_urls:
                    logger.info(f"测试访问: {url}")
                    if crawler.get_page_with_login_check(url):
                        logger.info(f"✅ 访问成功")
                    else:
                        logger.error(f"❌ 访问失败")
                    time.sleep(2)
            else:
                logger.error("❌ 登录测试失败")
                
        elif args.mode == "test":
            # 完整测试
            crawler.setup_driver(headless=args.headless)
            if crawler.ensure_logged_in():
                logger.info("✅ 登录成功，开始测试爬取...")
                
                # 测试各个爬取功能
                if crawler.get_page_with_login_check(f"{crawler.url}/alerts/risk"):
                    crawler.parse_risk_alerts()
                    
                if crawler.get_page_with_login_check(f"{crawler.url}/opportunities"):
                    crawler.parse_opportunities()
                    
                if crawler.get_page_with_login_check(f"{crawler.url}/tracking"):
                    crawler.parse_tracking()
                    
                logger.info("✅ 测试完成！")
            else:
                logger.error("❌ 登录失败")
                
        else:
            # 监控模式
            crawler.crawl_with_auto_reconnect()
            
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"程序错误: {e}", exc_info=True)
    finally:
        crawler.cleanup()