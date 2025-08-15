"""
币Coin自动登录模块
实现安全的登录凭证管理和自动登录功能
"""

import os
import json
import time
import pickle
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BiCoinAuth:
    """币Coin自动登录和Session管理"""
    
    def __init__(self, config_path: str = "config/bicoin_config.json"):
        """
        初始化认证管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.cookies_path = Path("data/cookies/bicoin_cookies.pkl")
        self.key_path = Path("config/.key")
        
        # 创建必要的目录
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化加密器
        self.cipher = self._init_cipher()
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化driver
        self.driver = None
        
    def _init_cipher(self) -> Fernet:
        """初始化加密器"""
        if not self.key_path.exists():
            # 生成新的加密密钥
            key = Fernet.generate_key()
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_path, 'wb') as f:
                f.write(key)
            # 设置权限为仅所有者可读写
            os.chmod(self.key_path, 0o600)
        
        with open(self.key_path, 'rb') as f:
            key = f.read()
        
        return Fernet(key)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            # 创建默认配置
            default_config = {
                "login_url": "https://i.bicoin.com.cn/web/login.html",
                "username": "",
                "password": "",
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                ],
                "login_retry_times": 3,
                "login_timeout": 30,
                "cookie_expire_hours": 24
            }
            
            # 如果有环境变量，使用环境变量
            if os.getenv("BICOIN_USERNAME"):
                default_config["username"] = self._encrypt_text(os.getenv("BICOIN_USERNAME"))
            if os.getenv("BICOIN_PASSWORD"):
                default_config["password"] = self._encrypt_text(os.getenv("BICOIN_PASSWORD"))
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"创建默认配置文件: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _encrypt_text(self, text: str) -> str:
        """加密文本"""
        return self.cipher.encrypt(text.encode()).decode()
    
    def _decrypt_text(self, encrypted_text: str) -> str:
        """解密文本"""
        if not encrypted_text:
            return ""
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except:
            # 如果解密失败，可能是明文，直接返回
            return encrypted_text
    
    def set_credentials(self, username: str, password: str):
        """
        设置登录凭证（加密存储）
        
        Args:
            username: 用户名
            password: 密码
        """
        self.config["username"] = self._encrypt_text(username)
        self.config["password"] = self._encrypt_text(password)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        logger.info("登录凭证已安全保存")
    
    def _init_driver(self) -> webdriver.Chrome:
        """初始化Chrome driver"""
        options = uc.ChromeOptions()
        
        # 基础设置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 随机User-Agent
        import random
        user_agent = random.choice(self.config.get("user_agents", []))
        if user_agent:
            options.add_argument(f'user-agent={user_agent}')
        
        # 禁用图片加载（提高速度）
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        # 使用undetected-chromedriver避免检测
        driver = uc.Chrome(options=options)
        
        # 执行反检测脚本
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return driver
    
    def _save_cookies(self):
        """保存cookies到文件"""
        if self.driver:
            cookies = self.driver.get_cookies()
            with open(self.cookies_path, 'wb') as f:
                pickle.dump({
                    'cookies': cookies,
                    'save_time': datetime.now()
                }, f)
            logger.info(f"Cookies已保存到: {self.cookies_path}")
    
    def _load_cookies(self) -> bool:
        """
        加载cookies
        
        Returns:
            bool: 是否成功加载有效的cookies
        """
        if not self.cookies_path.exists():
            return False
        
        try:
            with open(self.cookies_path, 'rb') as f:
                data = pickle.load(f)
            
            # 检查cookies是否过期
            save_time = data.get('save_time')
            expire_hours = self.config.get('cookie_expire_hours', 24)
            
            if datetime.now() - save_time > timedelta(hours=expire_hours):
                logger.info("Cookies已过期")
                return False
            
            # 加载cookies
            cookies = data.get('cookies', [])
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            logger.info("成功加载cookies")
            return True
            
        except Exception as e:
            logger.error(f"加载cookies失败: {e}")
            return False
    
    def _do_login(self) -> bool:
        """
        执行登录操作
        
        Returns:
            bool: 是否登录成功
        """
        try:
            username = self._decrypt_text(self.config.get("username", ""))
            password = self._decrypt_text(self.config.get("password", ""))
            
            if not username or not password:
                logger.error("未设置登录凭证，请先调用set_credentials设置")
                return False
            
            # 访问登录页面
            login_url = self.config.get("login_url")
            self.driver.get(login_url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, self.config.get("login_timeout", 30))
            
            # 输入用户名
            username_input = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input.clear()
            
            # 模拟人工输入
            for char in username:
                username_input.send_keys(char)
                time.sleep(0.1 + random.random() * 0.2)
            
            # 输入密码
            password_input = self.driver.find_element(By.ID, "password")
            password_input.clear()
            
            for char in password:
                password_input.send_keys(char)
                time.sleep(0.1 + random.random() * 0.2)
            
            # 随机等待
            time.sleep(1 + random.random() * 2)
            
            # 点击登录按钮
            login_button = self.driver.find_element(By.CLASS_NAME, "login-button")
            login_button.click()
            
            # 等待登录完成
            time.sleep(3)
            
            # 检查是否登录成功
            if self._check_login_status():
                self._save_cookies()
                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                return False
                
        except TimeoutException:
            logger.error("登录超时")
            return False
        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False
    
    def _check_login_status(self) -> bool:
        """
        检查登录状态
        
        Returns:
            bool: 是否已登录
        """
        try:
            # 检查URL是否已跳转
            current_url = self.driver.current_url
            if "login" not in current_url:
                return True
            
            # 检查是否有用户信息元素
            try:
                self.driver.find_element(By.CLASS_NAME, "user-info")
                return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def login(self) -> bool:
        """
        自动登录（优先使用cookies）
        
        Returns:
            bool: 是否登录成功
        """
        try:
            # 初始化driver
            if not self.driver:
                self.driver = self._init_driver()
            
            # 先访问主页
            self.driver.get("https://i.bicoin.com.cn")
            
            # 尝试加载cookies
            if self._load_cookies():
                # 刷新页面
                self.driver.refresh()
                time.sleep(2)
                
                # 检查是否登录成功
                if self._check_login_status():
                    logger.info("使用cookies登录成功")
                    return True
            
            # cookies登录失败，执行常规登录
            retry_times = self.config.get("login_retry_times", 3)
            for i in range(retry_times):
                logger.info(f"尝试登录 ({i+1}/{retry_times})")
                if self._do_login():
                    return True
                time.sleep(2)
            
            logger.error("多次尝试登录失败")
            return False
            
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """
        获取已登录的driver
        
        Returns:
            webdriver.Chrome: 已登录的driver实例
        """
        if not self.driver:
            if not self.login():
                return None
        
        return self.driver
    
    def close(self):
        """关闭driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Driver已关闭")
    
    def refresh_session(self):
        """刷新session"""
        if self.driver:
            self.driver.refresh()
            time.sleep(2)
            
            if self._check_login_status():
                self._save_cookies()
                logger.info("Session刷新成功")
            else:
                logger.info("Session已失效，重新登录")
                self.login()


# 测试代码
if __name__ == "__main__":
    auth = BiCoinAuth()
    
    # 设置登录凭证（首次使用）
    # auth.set_credentials("your_username", "your_password")
    
    # 执行登录
    if auth.login():
        print("登录成功！")
        driver = auth.get_driver()
        
        # 测试访问其他页面
        driver.get("https://i.bicoin.com.cn/web/modules/square.html")
        time.sleep(5)
        
        auth.close()
    else:
        print("登录失败！")