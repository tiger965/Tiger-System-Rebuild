"""
币Coin广场数据爬虫
抓取交易员动态、观点和交易信号
"""

import json
import time
import random
from datetime import datetime
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


class SquareCrawler:
    """币Coin广场爬虫"""
    
    def __init__(self, auth: BiCoinAuth):
        """
        初始化爬虫
        
        Args:
            auth: BiCoinAuth实例
        """
        self.auth = auth
        self.driver = auth.get_driver()
        self.url = "https://i.bicoin.com.cn/web/modules/square.html"
        self.data_path = "data/square/"
        
        # 创建数据目录
        os.makedirs(self.data_path, exist_ok=True)
        
    def _scroll_page(self, scroll_times: int = 3):
        """
        滚动页面加载更多内容
        
        Args:
            scroll_times: 滚动次数
        """
        for i in range(scroll_times):
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 随机等待
            time.sleep(2 + random.random() * 2)
            
            # 稍微向上滚动一点（模拟真实用户行为）
            self.driver.execute_script("window.scrollBy(0, -200);")
            time.sleep(0.5 + random.random())
    
    def _parse_post(self, post_element) -> Optional[Dict[str, Any]]:
        """
        解析单个动态帖子
        
        Args:
            post_element: 帖子元素
            
        Returns:
            Dict: 帖子数据
        """
        try:
            post_data = {}
            
            # 交易员信息
            try:
                trader_name = post_element.find_element(By.CLASS_NAME, "trader-name").text
                post_data["trader_name"] = trader_name
            except:
                post_data["trader_name"] = "Unknown"
            
            # 发布时间
            try:
                time_text = post_element.find_element(By.CLASS_NAME, "post-time").text
                post_data["post_time"] = time_text
                post_data["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except:
                post_data["post_time"] = ""
                post_data["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 内容
            try:
                content = post_element.find_element(By.CLASS_NAME, "post-content").text
                post_data["content"] = content
                
                # 分析内容中的交易信号
                post_data["signals"] = self._extract_signals(content)
            except:
                post_data["content"] = ""
                post_data["signals"] = {}
            
            # 互动数据
            try:
                likes = post_element.find_element(By.CLASS_NAME, "like-count").text
                post_data["likes"] = int(likes) if likes.isdigit() else 0
            except:
                post_data["likes"] = 0
            
            try:
                comments = post_element.find_element(By.CLASS_NAME, "comment-count").text
                post_data["comments"] = int(comments) if comments.isdigit() else 0
            except:
                post_data["comments"] = 0
            
            # 标签
            try:
                tags = post_element.find_elements(By.CLASS_NAME, "post-tag")
                post_data["tags"] = [tag.text for tag in tags]
            except:
                post_data["tags"] = []
            
            # 交易操作（如果有）
            try:
                action_element = post_element.find_element(By.CLASS_NAME, "trade-action")
                action_text = action_element.text
                
                if "开多" in action_text or "做多" in action_text:
                    post_data["action"] = "LONG"
                elif "开空" in action_text or "做空" in action_text:
                    post_data["action"] = "SHORT"
                elif "平仓" in action_text:
                    post_data["action"] = "CLOSE"
                else:
                    post_data["action"] = "NEUTRAL"
            except:
                post_data["action"] = "NEUTRAL"
            
            # 关联币种
            post_data["symbols"] = self._extract_symbols(post_data.get("content", ""))
            
            return post_data
            
        except Exception as e:
            logger.error(f"解析帖子失败: {e}")
            return None
    
    def _extract_signals(self, content: str) -> Dict[str, Any]:
        """
        从内容中提取交易信号
        
        Args:
            content: 帖子内容
            
        Returns:
            Dict: 交易信号
        """
        signals = {
            "direction": None,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "confidence": None
        }
        
        # 方向判断
        if any(word in content for word in ["做多", "开多", "看涨", "买入", "LONG"]):
            signals["direction"] = "LONG"
        elif any(word in content for word in ["做空", "开空", "看跌", "卖出", "SHORT"]):
            signals["direction"] = "SHORT"
        
        # 价格提取（简单正则）
        import re
        
        # 入场价格
        price_pattern = r'[入进]场[：:]\s*(\d+\.?\d*)'
        match = re.search(price_pattern, content)
        if match:
            signals["entry_price"] = float(match.group(1))
        
        # 止损价格
        sl_pattern = r'止损[：:]\s*(\d+\.?\d*)'
        match = re.search(sl_pattern, content)
        if match:
            signals["stop_loss"] = float(match.group(1))
        
        # 止盈价格
        tp_pattern = r'止盈[：:]\s*(\d+\.?\d*)'
        match = re.search(tp_pattern, content)
        if match:
            signals["take_profit"] = float(match.group(1))
        
        # 信心程度（基于关键词）
        if any(word in content for word in ["强烈", "必须", "重仓", "all in"]):
            signals["confidence"] = "HIGH"
        elif any(word in content for word in ["可能", "也许", "小仓", "试探"]):
            signals["confidence"] = "LOW"
        else:
            signals["confidence"] = "MEDIUM"
        
        return signals
    
    def _extract_symbols(self, content: str) -> List[str]:
        """
        从内容中提取币种符号
        
        Args:
            content: 帖子内容
            
        Returns:
            List: 币种列表
        """
        symbols = []
        
        # 常见币种列表
        common_symbols = [
            "BTC", "ETH", "BNB", "SOL", "ADA", "DOGE", "AVAX", "DOT",
            "MATIC", "LINK", "UNI", "ATOM", "LTC", "ETC", "XRP", "BCH",
            "NEAR", "FIL", "ICP", "TRX", "SHIB", "APT", "ARB", "OP"
        ]
        
        content_upper = content.upper()
        for symbol in common_symbols:
            if symbol in content_upper:
                symbols.append(symbol)
        
        return list(set(symbols))  # 去重
    
    def crawl_square(self, max_posts: int = 50, scroll_times: int = 5) -> List[Dict[str, Any]]:
        """
        爬取广场数据
        
        Args:
            max_posts: 最大爬取帖子数
            scroll_times: 页面滚动次数
            
        Returns:
            List: 帖子数据列表
        """
        posts_data = []
        
        try:
            # 访问广场页面
            logger.info(f"访问币Coin广场: {self.url}")
            self.driver.get(self.url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "square-container")))
            
            # 初始等待
            time.sleep(3)
            
            # 滚动加载更多内容
            self._scroll_page(scroll_times)
            
            # 获取所有帖子
            posts = self.driver.find_elements(By.CLASS_NAME, "post-item")
            logger.info(f"找到 {len(posts)} 个帖子")
            
            # 解析帖子
            for i, post in enumerate(posts[:max_posts]):
                if i % 10 == 0:
                    logger.info(f"正在解析第 {i+1} 个帖子")
                
                post_data = self._parse_post(post)
                if post_data:
                    posts_data.append(post_data)
                
                # 随机延迟
                time.sleep(0.1 + random.random() * 0.3)
            
            logger.info(f"成功爬取 {len(posts_data)} 个帖子")
            
            # 保存数据
            self._save_data(posts_data)
            
            return posts_data
            
        except TimeoutException:
            logger.error("页面加载超时")
            return posts_data
        except Exception as e:
            logger.error(f"爬取失败: {e}")
            return posts_data
    
    def _save_data(self, data: List[Dict[str, Any]]):
        """
        保存数据到文件
        
        Args:
            data: 数据列表
        """
        if not data:
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_path}square_{timestamp}.json"
        
        # 保存JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到: {filename}")
    
    def analyze_trends(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析广场趋势
        
        Args:
            posts: 帖子列表
            
        Returns:
            Dict: 趋势分析结果
        """
        analysis = {
            "total_posts": len(posts),
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "top_symbols": {},
            "active_traders": {},
            "high_engagement_posts": []
        }
        
        for post in posts:
            # 统计多空情绪
            action = post.get("action", "NEUTRAL")
            if action == "LONG":
                analysis["bullish_count"] += 1
            elif action == "SHORT":
                analysis["bearish_count"] += 1
            else:
                analysis["neutral_count"] += 1
            
            # 统计币种提及
            for symbol in post.get("symbols", []):
                analysis["top_symbols"][symbol] = analysis["top_symbols"].get(symbol, 0) + 1
            
            # 统计活跃交易员
            trader = post.get("trader_name", "Unknown")
            if trader != "Unknown":
                if trader not in analysis["active_traders"]:
                    analysis["active_traders"][trader] = {
                        "posts": 0,
                        "total_likes": 0,
                        "total_comments": 0
                    }
                analysis["active_traders"][trader]["posts"] += 1
                analysis["active_traders"][trader]["total_likes"] += post.get("likes", 0)
                analysis["active_traders"][trader]["total_comments"] += post.get("comments", 0)
            
            # 高互动帖子
            engagement = post.get("likes", 0) + post.get("comments", 0) * 2
            if engagement > 50:  # 阈值可调整
                analysis["high_engagement_posts"].append({
                    "trader": trader,
                    "content": post.get("content", "")[:100],
                    "engagement": engagement,
                    "action": action
                })
        
        # 计算情绪指数
        total_directional = analysis["bullish_count"] + analysis["bearish_count"]
        if total_directional > 0:
            analysis["sentiment_index"] = (analysis["bullish_count"] / total_directional) * 100
        else:
            analysis["sentiment_index"] = 50
        
        # 排序热门币种
        analysis["top_symbols"] = dict(
            sorted(analysis["top_symbols"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # 排序高互动帖子
        analysis["high_engagement_posts"] = sorted(
            analysis["high_engagement_posts"], 
            key=lambda x: x["engagement"], 
            reverse=True
        )[:10]
        
        return analysis
    
    def monitor_realtime(self, interval: int = 600, duration: int = 3600):
        """
        实时监控广场动态
        
        Args:
            interval: 更新间隔（秒）
            duration: 监控持续时间（秒）
        """
        start_time = time.time()
        
        logger.info(f"开始实时监控，间隔{interval}秒，持续{duration/3600}小时")
        
        while time.time() - start_time < duration:
            try:
                # 爬取数据
                posts = self.crawl_square(max_posts=30, scroll_times=2)
                
                # 分析趋势
                if posts:
                    analysis = self.analyze_trends(posts)
                    
                    # 输出分析结果
                    logger.info(f"情绪指数: {analysis['sentiment_index']:.1f}% (多头)")
                    logger.info(f"多空比: {analysis['bullish_count']}:{analysis['bearish_count']}")
                    logger.info(f"热门币种: {list(analysis['top_symbols'].keys())[:5]}")
                    
                    # 保存分析结果
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    analysis_file = f"{self.data_path}analysis_{timestamp}.json"
                    with open(analysis_file, 'w', encoding='utf-8') as f:
                        json.dump(analysis, f, ensure_ascii=False, indent=2)
                
                # 等待下次更新
                if time.time() - start_time < duration:
                    logger.info(f"等待{interval}秒后继续...")
                    time.sleep(interval)
                    
            except Exception as e:
                logger.error(f"监控出错: {e}")
                time.sleep(60)  # 出错后等待1分钟
        
        logger.info("监控结束")


# 测试代码
if __name__ == "__main__":
    # 初始化认证
    auth = BiCoinAuth()
    
    # 登录
    if auth.login():
        # 创建爬虫
        crawler = SquareCrawler(auth)
        
        # 爬取广场数据
        posts = crawler.crawl_square(max_posts=20, scroll_times=2)
        
        if posts:
            # 分析趋势
            analysis = crawler.analyze_trends(posts)
            print(f"\n分析结果:")
            print(f"总帖子数: {analysis['total_posts']}")
            print(f"情绪指数: {analysis['sentiment_index']:.1f}% (多头)")
            print(f"多空比: {analysis['bullish_count']}:{analysis['bearish_count']}")
            print(f"热门币种: {list(analysis['top_symbols'].keys())[:5]}")
            print(f"活跃交易员数: {len(analysis['active_traders'])}")
        
        # 关闭
        auth.close()
    else:
        print("登录失败")