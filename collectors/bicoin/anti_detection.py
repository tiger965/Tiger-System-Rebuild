"""
反爬虫对策模块
实现各种反检测技术，确保爬虫稳定运行
"""

import time
import random
from typing import Any, Callable
from functools import wraps
import logging
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AntiDetection:
    """反检测策略类"""
    
    def __init__(self):
        """初始化反检测策略"""
        # User-Agent列表
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        # 请求间隔配置
        self.request_intervals = {
            "min": 1,      # 最小间隔（秒）
            "max": 5,      # 最大间隔（秒）
            "burst": 0.5   # 突发请求间隔（秒）
        }
        
        # 行为模拟配置
        self.behavior_config = {
            "scroll_speed": (100, 300),    # 滚动速度范围（像素/次）
            "typing_speed": (0.05, 0.2),   # 打字速度范围（秒/字符）
            "mouse_speed": (0.5, 2),       # 鼠标移动速度范围（秒）
            "read_time": (2, 5)            # 页面阅读时间范围（秒）
        }
        
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """
        随机延迟
        
        Args:
            min_seconds: 最小延迟时间
            max_seconds: 最大延迟时间
        """
        if min_seconds is None:
            min_seconds = self.request_intervals["min"]
        if max_seconds is None:
            max_seconds = self.request_intervals["max"]
        
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def simulate_human_scrolling(self, driver: webdriver.Chrome, times: int = 3):
        """
        模拟人类滚动行为
        
        Args:
            driver: WebDriver实例
            times: 滚动次数
        """
        for _ in range(times):
            # 随机滚动距离
            scroll_distance = random.randint(*self.behavior_config["scroll_speed"])
            
            # 执行滚动
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            
            # 随机停留
            self.random_delay(0.5, 1.5)
            
            # 偶尔向上滚动一点
            if random.random() < 0.3:
                up_distance = random.randint(50, 150)
                driver.execute_script(f"window.scrollBy(0, -{up_distance});")
                self.random_delay(0.3, 0.8)
    
    def simulate_human_typing(self, element, text: str):
        """
        模拟人类打字行为
        
        Args:
            element: 输入框元素
            text: 要输入的文本
        """
        element.clear()
        
        for char in text:
            element.send_keys(char)
            # 随机打字间隔
            delay = random.uniform(*self.behavior_config["typing_speed"])
            time.sleep(delay)
            
            # 偶尔停顿（思考）
            if random.random() < 0.1:
                time.sleep(random.uniform(0.5, 1.5))
    
    def simulate_mouse_movement(self, driver: webdriver.Chrome, element=None):
        """
        模拟鼠标移动
        
        Args:
            driver: WebDriver实例
            element: 目标元素（可选）
        """
        action = ActionChains(driver)
        
        if element:
            # 生成贝塞尔曲线路径
            points = self._generate_bezier_curve()
            
            # 移动鼠标
            for x, y in points:
                action.move_by_offset(x, y)
            
            action.move_to_element(element)
        else:
            # 随机移动
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                action.move_by_offset(x_offset, y_offset)
        
        action.perform()
        
        # 移动后停顿
        self.random_delay(0.2, 0.5)
    
    def _generate_bezier_curve(self, num_points: int = 10):
        """
        生成贝塞尔曲线路径（模拟真实鼠标轨迹）
        
        Args:
            num_points: 路径点数量
            
        Returns:
            List: 路径点列表
        """
        t = np.linspace(0, 1, num_points)
        
        # 控制点
        p0 = np.array([0, 0])
        p1 = np.array([random.randint(-50, 50), random.randint(-50, 50)])
        p2 = np.array([random.randint(-50, 50), random.randint(-50, 50)])
        p3 = np.array([0, 0])
        
        # 计算贝塞尔曲线
        points = []
        for ti in t:
            point = (
                (1 - ti)**3 * p0 +
                3 * (1 - ti)**2 * ti * p1 +
                3 * (1 - ti) * ti**2 * p2 +
                ti**3 * p3
            )
            points.append(point.astype(int).tolist())
        
        # 计算相对位移
        relative_points = []
        for i in range(1, len(points)):
            dx = points[i][0] - points[i-1][0]
            dy = points[i][1] - points[i-1][1]
            relative_points.append((dx, dy))
        
        return relative_points
    
    def handle_cloudflare(self, driver: webdriver.Chrome, max_wait: int = 30):
        """
        处理Cloudflare检测
        
        Args:
            driver: WebDriver实例
            max_wait: 最大等待时间（秒）
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # 检查是否有Cloudflare挑战
                if "Checking your browser" in driver.page_source:
                    logger.info("检测到Cloudflare，等待通过...")
                    time.sleep(5)
                else:
                    # 页面正常加载
                    return True
            except:
                pass
            
            time.sleep(1)
        
        logger.warning("Cloudflare检测超时")
        return False
    
    def check_for_captcha(self, driver: webdriver.Chrome) -> bool:
        """
        检查是否出现验证码
        
        Args:
            driver: WebDriver实例
            
        Returns:
            bool: 是否检测到验证码
        """
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "验证码",
            "verification",
            "robot",
            "滑块验证"
        ]
        
        page_source = driver.page_source.lower()
        
        for indicator in captcha_indicators:
            if indicator in page_source:
                logger.warning(f"检测到验证码: {indicator}")
                return True
        
        return False
    
    def rotate_ip(self, proxy_list: list = None):
        """
        IP轮换（需要代理池支持）
        
        Args:
            proxy_list: 代理IP列表
        """
        if not proxy_list:
            logger.debug("未配置代理池")
            return None
        
        proxy = random.choice(proxy_list)
        logger.info(f"切换到代理: {proxy}")
        return proxy
    
    def rate_limiter(self, func: Callable) -> Callable:
        """
        速率限制装饰器
        
        Args:
            func: 要限制的函数
            
        Returns:
            Callable: 包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 执行前延迟
            self.random_delay()
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 执行后延迟
            self.random_delay(0.5, 1.5)
            
            return result
        
        return wrapper
    
    def inject_stealth_scripts(self, driver: webdriver.Chrome):
        """
        注入隐身脚本
        
        Args:
            driver: WebDriver实例
        """
        # 隐藏webdriver特征
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        
        window.chrome = {
            runtime: {}
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' })
            })
        });
        """
        
        driver.execute_script(stealth_js)
    
    def adaptive_delay(self, success_count: int, fail_count: int):
        """
        自适应延迟（根据成功/失败率调整）
        
        Args:
            success_count: 成功次数
            fail_count: 失败次数
        """
        if fail_count == 0:
            # 全部成功，使用最小延迟
            delay_multiplier = 1
        else:
            # 根据失败率调整延迟
            fail_rate = fail_count / (success_count + fail_count)
            delay_multiplier = 1 + fail_rate * 3  # 失败率越高，延迟越长
        
        min_delay = self.request_intervals["min"] * delay_multiplier
        max_delay = self.request_intervals["max"] * delay_multiplier
        
        self.random_delay(min_delay, max_delay)
    
    def fingerprint_randomization(self) -> dict:
        """
        浏览器指纹随机化
        
        Returns:
            dict: 随机化的浏览器配置
        """
        config = {
            "screen_resolution": random.choice([
                (1920, 1080), (1366, 768), (1440, 900),
                (1536, 864), (1280, 720), (1600, 900)
            ]),
            "color_depth": random.choice([24, 32]),
            "timezone_offset": random.choice([-480, -420, -360, -300, -240, -180, -120, 0, 60, 120]),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "hardware_concurrency": random.choice([2, 4, 6, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16, 32])
        }
        
        return config
    
    def session_management(self, driver: webdriver.Chrome, max_requests: int = 100):
        """
        会话管理（定期刷新会话）
        
        Args:
            driver: WebDriver实例
            max_requests: 最大请求数
        """
        # 这里可以实现会话轮换逻辑
        pass


class RequestManager:
    """请求管理器"""
    
    def __init__(self, anti_detection: AntiDetection):
        """
        初始化请求管理器
        
        Args:
            anti_detection: 反检测实例
        """
        self.anti_detection = anti_detection
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_request_time = None
        
    def execute_with_retry(self, func: Callable, max_retries: int = 3, *args, **kwargs) -> Any:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            
        Returns:
            Any: 函数返回值
        """
        for attempt in range(max_retries):
            try:
                # 自适应延迟
                self.anti_detection.adaptive_delay(self.success_count, self.fail_count)
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 成功计数
                self.success_count += 1
                self.request_count += 1
                
                return result
                
            except Exception as e:
                self.fail_count += 1
                logger.warning(f"执行失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # 增加延迟时间
                    delay = (attempt + 1) * 5
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    raise e
        
        return None
    
    def get_statistics(self) -> dict:
        """获取请求统计信息"""
        return {
            "total_requests": self.request_count,
            "successful": self.success_count,
            "failed": self.fail_count,
            "success_rate": (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        }


# 测试代码
if __name__ == "__main__":
    # 创建反检测实例
    anti = AntiDetection()
    
    # 测试User-Agent
    print(f"Random User-Agent: {anti.get_random_user_agent()}")
    
    # 测试延迟
    print("Testing random delay...")
    anti.random_delay(1, 2)
    
    # 测试指纹随机化
    fingerprint = anti.fingerprint_randomization()
    print(f"Random fingerprint: {fingerprint}")
    
    # 创建请求管理器
    manager = RequestManager(anti)
    
    # 测试带重试的执行
    def test_function():
        if random.random() < 0.7:  # 70% 成功率
            return "Success"
        else:
            raise Exception("Random failure")
    
    try:
        result = manager.execute_with_retry(test_function)
        print(f"Result: {result}")
    except:
        print("Failed after retries")
    
    # 输出统计
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")