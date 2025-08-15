"""
VPN连接检查工具 - 防止币安封号
确保币安API调用前VPN连接正常
"""
import requests
import socket
import time
from loguru import logger


class VPNChecker:
    """VPN连接检查器 - 币安API必须通过VPN"""
    
    def __init__(self, proxy_host="127.0.0.1", proxy_port=1080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_url = f"http://{proxy_host}:{proxy_port}"
        self.proxies = {
            'http': self.proxy_url,
            'https': self.proxy_url
        }
    
    def check_proxy_available(self) -> bool:
        """检查代理端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.proxy_host, self.proxy_port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"代理端口检查失败: {e}")
            return False
    
    def check_binance_connection(self) -> bool:
        """检查通过代理访问币安API"""
        try:
            # 测试币安ping接口
            response = requests.get(
                'https://api.binance.com/api/v3/ping',
                proxies=self.proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ 币安VPN连接正常")
                return True
            else:
                logger.error(f"❌ 币安API返回错误: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 币安VPN连接失败: {e}")
            return False
    
    def check_ip_location(self) -> dict:
        """检查当前IP位置（通过代理）"""
        try:
            response = requests.get(
                'https://ipapi.co/json/',
                proxies=self.proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"当前IP位置: {data.get('country_name')} - {data.get('city')}")
                return data
            else:
                logger.warning("无法获取IP位置信息")
                return {}
                
        except Exception as e:
            logger.error(f"IP位置检查失败: {e}")
            return {}
    
    def force_vpn_check(self) -> bool:
        """强制VPN检查 - 币安必须通过"""
        logger.info("🔒 开始币安VPN强制检查...")
        
        # 1. 检查代理端口
        if not self.check_proxy_available():
            raise Exception("🚨 代理端口不可用！请启动Shadowsocks！")
        
        # 2. 检查币安连接
        if not self.check_binance_connection():
            raise Exception("🚨 币安VPN连接失败！继续使用会导致封号！")
        
        # 3. 检查IP位置
        ip_info = self.check_ip_location()
        country = ip_info.get('country_code', '')
        
        # 如果显示中国IP，警告
        if country == 'CN':
            logger.warning("⚠️ 警告：当前显示中国IP，请确认VPN正常工作")
        
        logger.info("✅ 币安VPN检查通过，可以安全访问")
        return True
    
    def auto_retry_check(self, max_retries=3, retry_delay=5) -> bool:
        """自动重试VPN检查"""
        for attempt in range(max_retries):
            try:
                return self.force_vpn_check()
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"VPN检查失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"等待{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"VPN检查最终失败: {e}")
                    raise e
        
        return False


# 全局VPN检查器实例
vpn_checker = VPNChecker()


def ensure_binance_vpn():
    """确保币安VPN连接 - 装饰器使用"""
    return vpn_checker.force_vpn_check()


def binance_vpn_required(func):
    """币安VPN必需装饰器"""
    def wrapper(*args, **kwargs):
        # 检查是否是币安相关调用
        if len(args) > 1 and isinstance(args[1], str) and 'binance' in args[1].lower():
            ensure_binance_vpn()
        return func(*args, **kwargs)
    return wrapper


if __name__ == "__main__":
    # 测试VPN检查
    checker = VPNChecker()
    try:
        checker.force_vpn_check()
        print("✅ VPN检查通过")
    except Exception as e:
        print(f"❌ VPN检查失败: {e}")