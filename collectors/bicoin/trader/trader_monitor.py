"""
顶级交易员监控模块
实时追踪顶级交易员的操作和持仓变化
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import sys
import os
from dataclasses import dataclass, asdict

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bicoin_auth import BiCoinAuth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TraderPosition:
    """交易员持仓数据结构"""
    symbol: str
    direction: str  # LONG or SHORT
    entry_price: float
    current_price: float
    position_size: float  # 仓位百分比
    pnl_percentage: float  # 盈亏百分比
    entry_time: str
    hold_duration: str
    status: str  # OPEN, CLOSED, PARTIAL_CLOSE


@dataclass
class TraderInfo:
    """交易员信息数据结构"""
    trader_id: str
    trader_name: str
    total_followers: int
    win_rate: float
    total_pnl: float
    avg_hold_time: str
    trading_style: str  # SCALPER, DAY_TRADER, SWING_TRADER, POSITION_TRADER
    risk_level: str  # LOW, MEDIUM, HIGH
    last_update: str


class TraderMonitor:
    """顶级交易员监控器"""
    
    def __init__(self, auth: BiCoinAuth):
        """
        初始化监控器
        
        Args:
            auth: BiCoinAuth实例
        """
        self.auth = auth
        self.driver = auth.get_driver()
        self.data_path = "data/traders/"
        
        # 创建数据目录
        os.makedirs(self.data_path, exist_ok=True)
        
        # 顶级交易员列表（需要根据实际ID更新）
        self.top_traders = [
            {"name": "如果我不懂", "id": "trader_001", "url": ""},
            {"name": "熬鹰", "id": "trader_002", "url": ""},
            {"name": "以予", "id": "trader_003", "url": ""},
            {"name": "币圈狙击手", "id": "trader_004", "url": ""},
            {"name": "老韭菜", "id": "trader_005", "url": ""},
        ]
        
        # 监控数据缓存
        self.traders_cache: Dict[str, TraderInfo] = {}
        self.positions_cache: Dict[str, List[TraderPosition]] = {}
        self.historical_positions: Dict[str, List[TraderPosition]] = {}
        
    def discover_top_traders(self, min_win_rate: float = 60, min_followers: int = 1000) -> List[Dict[str, Any]]:
        """
        发现顶级交易员
        
        Args:
            min_win_rate: 最低胜率要求
            min_followers: 最低粉丝数要求
            
        Returns:
            List: 符合条件的交易员列表
        """
        discovered_traders = []
        
        try:
            # 访问交易员排行榜页面
            ranking_url = "https://i.bicoin.com.cn/web/modules/trader_ranking.html"
            logger.info(f"访问交易员排行榜: {ranking_url}")
            self.driver.get(ranking_url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "trader-list")))
            
            time.sleep(3)
            
            # 获取交易员列表
            traders = self.driver.find_elements(By.CLASS_NAME, "trader-item")
            
            for trader in traders[:50]:  # 检查前50名
                try:
                    trader_data = self._parse_trader_card(trader)
                    
                    # 筛选条件
                    if (trader_data.get("win_rate", 0) >= min_win_rate and 
                        trader_data.get("followers", 0) >= min_followers):
                        
                        discovered_traders.append(trader_data)
                        logger.info(f"发现优质交易员: {trader_data['name']} - 胜率:{trader_data['win_rate']}%")
                        
                except Exception as e:
                    logger.debug(f"解析交易员失败: {e}")
                    continue
            
            # 更新顶级交易员列表
            if discovered_traders:
                self._update_top_traders(discovered_traders)
            
        except Exception as e:
            logger.error(f"发现交易员失败: {e}")
        
        return discovered_traders
    
    def _parse_trader_card(self, trader_element) -> Dict[str, Any]:
        """解析交易员卡片信息"""
        trader_data = {}
        
        try:
            # 交易员名称
            trader_data["name"] = trader_element.find_element(By.CLASS_NAME, "trader-name").text
            
            # 交易员ID和主页链接
            profile_link = trader_element.find_element(By.CLASS_NAME, "profile-link")
            trader_data["url"] = profile_link.get_attribute("href")
            trader_data["id"] = self._extract_trader_id(trader_data["url"])
            
            # 胜率
            win_rate_text = trader_element.find_element(By.CLASS_NAME, "win-rate").text
            trader_data["win_rate"] = float(win_rate_text.replace("%", ""))
            
            # 粉丝数
            followers_text = trader_element.find_element(By.CLASS_NAME, "followers").text
            trader_data["followers"] = self._parse_number(followers_text)
            
            # 总收益
            pnl_text = trader_element.find_element(By.CLASS_NAME, "total-pnl").text
            trader_data["total_pnl"] = float(pnl_text.replace("%", "").replace("+", ""))
            
            # 平均持仓时间
            try:
                hold_time = trader_element.find_element(By.CLASS_NAME, "avg-hold").text
                trader_data["avg_hold_time"] = hold_time
            except:
                trader_data["avg_hold_time"] = "未知"
            
        except Exception as e:
            logger.debug(f"解析交易员卡片失败: {e}")
        
        return trader_data
    
    def monitor_trader(self, trader: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        监控单个交易员
        
        Args:
            trader: 交易员信息字典
            
        Returns:
            Dict: 交易员完整数据
        """
        trader_data = {
            "info": None,
            "positions": [],
            "recent_trades": [],
            "analysis": {}
        }
        
        try:
            # 访问交易员主页
            if trader.get("url"):
                logger.info(f"监控交易员: {trader['name']}")
                self.driver.get(trader["url"])
            else:
                # 构造URL
                trader_url = f"https://i.bicoin.com.cn/web/trader/{trader['id']}"
                self.driver.get(trader_url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "trader-profile")))
            
            time.sleep(2)
            
            # 获取交易员信息
            trader_data["info"] = self._get_trader_info(trader["id"], trader["name"])
            
            # 获取当前持仓
            trader_data["positions"] = self._get_current_positions()
            
            # 获取最近交易
            trader_data["recent_trades"] = self._get_recent_trades()
            
            # 分析交易员
            trader_data["analysis"] = self._analyze_trader(trader_data)
            
            # 缓存数据
            if trader_data["info"]:
                self.traders_cache[trader["id"]] = trader_data["info"]
            if trader_data["positions"]:
                self.positions_cache[trader["id"]] = trader_data["positions"]
            
            return trader_data
            
        except TimeoutException:
            logger.error(f"监控交易员超时: {trader['name']}")
            return None
        except Exception as e:
            logger.error(f"监控交易员失败: {trader['name']} - {e}")
            return None
    
    def _get_trader_info(self, trader_id: str, trader_name: str) -> TraderInfo:
        """获取交易员详细信息"""
        info = TraderInfo(
            trader_id=trader_id,
            trader_name=trader_name,
            total_followers=0,
            win_rate=0,
            total_pnl=0,
            avg_hold_time="",
            trading_style="UNKNOWN",
            risk_level="MEDIUM",
            last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        try:
            # 粉丝数
            try:
                followers = self.driver.find_element(By.CLASS_NAME, "followers-count").text
                info.total_followers = self._parse_number(followers)
            except:
                pass
            
            # 胜率
            try:
                win_rate = self.driver.find_element(By.CLASS_NAME, "win-rate-value").text
                info.win_rate = float(win_rate.replace("%", ""))
            except:
                pass
            
            # 总收益
            try:
                total_pnl = self.driver.find_element(By.CLASS_NAME, "total-pnl-value").text
                info.total_pnl = float(total_pnl.replace("%", "").replace("+", ""))
            except:
                pass
            
            # 平均持仓时间
            try:
                avg_hold = self.driver.find_element(By.CLASS_NAME, "avg-hold-value").text
                info.avg_hold_time = avg_hold
                
                # 判断交易风格
                if "分钟" in avg_hold or "小时" in avg_hold:
                    if "分钟" in avg_hold:
                        info.trading_style = "SCALPER"
                    else:
                        info.trading_style = "DAY_TRADER"
                elif "天" in avg_hold:
                    days = int(avg_hold.split("天")[0]) if "天" in avg_hold else 1
                    if days <= 3:
                        info.trading_style = "SWING_TRADER"
                    else:
                        info.trading_style = "POSITION_TRADER"
            except:
                pass
            
            # 判断风险等级
            if info.win_rate > 70:
                info.risk_level = "LOW"
            elif info.win_rate < 50:
                info.risk_level = "HIGH"
            
        except Exception as e:
            logger.error(f"获取交易员信息失败: {e}")
        
        return info
    
    def _get_current_positions(self) -> List[TraderPosition]:
        """获取当前持仓"""
        positions = []
        
        try:
            # 获取持仓列表
            position_items = self.driver.find_elements(By.CLASS_NAME, "position-item")
            
            for item in position_items:
                try:
                    position = self._parse_position(item)
                    if position:
                        positions.append(position)
                except Exception as e:
                    logger.debug(f"解析持仓失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
        
        return positions
    
    def _parse_position(self, position_element) -> Optional[TraderPosition]:
        """解析持仓信息"""
        try:
            # 币种
            symbol = position_element.find_element(By.CLASS_NAME, "position-symbol").text
            
            # 方向
            direction_elem = position_element.find_element(By.CLASS_NAME, "position-direction")
            direction = "LONG" if "多" in direction_elem.text or "Long" in direction_elem.text else "SHORT"
            
            # 入场价格
            entry_price = float(position_element.find_element(By.CLASS_NAME, "entry-price").text.replace(",", ""))
            
            # 当前价格
            current_price = float(position_element.find_element(By.CLASS_NAME, "current-price").text.replace(",", ""))
            
            # 仓位大小
            position_size_text = position_element.find_element(By.CLASS_NAME, "position-size").text
            position_size = float(position_size_text.replace("%", ""))
            
            # 盈亏
            pnl_text = position_element.find_element(By.CLASS_NAME, "position-pnl").text
            pnl_percentage = float(pnl_text.replace("%", "").replace("+", ""))
            
            # 入场时间
            entry_time = position_element.find_element(By.CLASS_NAME, "entry-time").text
            
            # 持仓时长
            hold_duration = position_element.find_element(By.CLASS_NAME, "hold-duration").text
            
            return TraderPosition(
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                current_price=current_price,
                position_size=position_size,
                pnl_percentage=pnl_percentage,
                entry_time=entry_time,
                hold_duration=hold_duration,
                status="OPEN"
            )
            
        except Exception as e:
            logger.debug(f"解析持仓信息失败: {e}")
            return None
    
    def _get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近交易记录"""
        trades = []
        
        try:
            # 切换到历史交易标签
            try:
                history_tab = self.driver.find_element(By.CLASS_NAME, "history-tab")
                history_tab.click()
                time.sleep(2)
            except:
                pass
            
            # 获取交易记录
            trade_items = self.driver.find_elements(By.CLASS_NAME, "trade-item")[:limit]
            
            for item in trade_items:
                try:
                    trade = {
                        "symbol": item.find_element(By.CLASS_NAME, "trade-symbol").text,
                        "action": item.find_element(By.CLASS_NAME, "trade-action").text,
                        "price": float(item.find_element(By.CLASS_NAME, "trade-price").text.replace(",", "")),
                        "time": item.find_element(By.CLASS_NAME, "trade-time").text,
                        "pnl": item.find_element(By.CLASS_NAME, "trade-pnl").text
                    }
                    trades.append(trade)
                except:
                    continue
            
        except Exception as e:
            logger.error(f"获取交易记录失败: {e}")
        
        return trades
    
    def _analyze_trader(self, trader_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析交易员
        
        Args:
            trader_data: 交易员数据
            
        Returns:
            Dict: 分析结果
        """
        analysis = {
            "trading_frequency": "UNKNOWN",
            "preferred_symbols": [],
            "risk_management": {},
            "performance_trend": "STABLE",
            "follow_signal": "NEUTRAL",
            "key_insights": []
        }
        
        info = trader_data.get("info")
        positions = trader_data.get("positions", [])
        recent_trades = trader_data.get("recent_trades", [])
        
        if not info:
            return analysis
        
        # 分析交易频率
        if info.trading_style == "SCALPER":
            analysis["trading_frequency"] = "VERY_HIGH"
        elif info.trading_style == "DAY_TRADER":
            analysis["trading_frequency"] = "HIGH"
        elif info.trading_style == "SWING_TRADER":
            analysis["trading_frequency"] = "MEDIUM"
        else:
            analysis["trading_frequency"] = "LOW"
        
        # 分析偏好币种
        if positions:
            symbols = [p.symbol for p in positions]
            analysis["preferred_symbols"] = list(set(symbols))
        
        # 风险管理分析
        if positions:
            avg_position_size = sum(p.position_size for p in positions) / len(positions)
            max_position_size = max(p.position_size for p in positions)
            
            analysis["risk_management"] = {
                "avg_position_size": avg_position_size,
                "max_position_size": max_position_size,
                "diversification": len(set(p.symbol for p in positions)),
                "risk_level": "HIGH" if max_position_size > 50 else "MEDIUM" if max_position_size > 30 else "LOW"
            }
        
        # 判断是否值得跟随
        if info.win_rate > 65 and info.total_pnl > 100:
            analysis["follow_signal"] = "STRONG_BUY"
            analysis["key_insights"].append(f"高胜率({info.win_rate}%)且收益稳定")
        elif info.win_rate > 60 and info.total_pnl > 50:
            analysis["follow_signal"] = "BUY"
            analysis["key_insights"].append("表现良好，可适度跟随")
        elif info.win_rate < 45:
            analysis["follow_signal"] = "AVOID"
            analysis["key_insights"].append("近期表现不佳，暂不建议跟随")
        
        # 检查当前持仓状态
        if positions:
            total_pnl = sum(p.pnl_percentage for p in positions)
            if total_pnl > 20:
                analysis["key_insights"].append("当前持仓盈利良好")
            elif total_pnl < -10:
                analysis["key_insights"].append("当前持仓亏损，需谨慎")
            
            # 检查是否有一致性操作
            directions = [p.direction for p in positions]
            if len(set(directions)) == 1:
                direction = directions[0]
                analysis["key_insights"].append(f"全仓{direction}，方向明确")
        
        return analysis
    
    def monitor_all_traders(self, interval: int = 600):
        """
        监控所有顶级交易员
        
        Args:
            interval: 监控间隔（秒）
        """
        logger.info(f"开始监控{len(self.top_traders)}个顶级交易员")
        
        all_data = []
        
        for trader in self.top_traders:
            logger.info(f"正在监控: {trader['name']}")
            
            # 监控交易员
            trader_data = self.monitor_trader(trader)
            
            if trader_data:
                all_data.append(trader_data)
                
                # 检测重要变化
                self._detect_important_changes(trader["id"], trader_data)
                
                # 随机延迟（避免被检测）
                time.sleep(5 + random.random() * 5)
            else:
                logger.warning(f"监控失败: {trader['name']}")
        
        # 分析集体行为
        collective_analysis = self._analyze_collective_behavior(all_data)
        
        # 保存数据
        self._save_monitoring_data(all_data, collective_analysis)
        
        # 生成报告
        self._generate_monitoring_report(all_data, collective_analysis)
        
        return all_data
    
    def _detect_important_changes(self, trader_id: str, current_data: Dict[str, Any]):
        """检测重要变化"""
        # 获取历史持仓
        historical = self.positions_cache.get(trader_id, [])
        current = current_data.get("positions", [])
        
        if not historical:
            return
        
        # 检测新开仓
        historical_symbols = {(p.symbol, p.direction) for p in historical}
        current_symbols = {(p.symbol, p.direction) for p in current}
        
        new_positions = current_symbols - historical_symbols
        closed_positions = historical_symbols - current_symbols
        
        trader_name = current_data["info"].trader_name if current_data.get("info") else trader_id
        
        for symbol, direction in new_positions:
            logger.warning(f"🔔 {trader_name} 新开仓: {symbol} {direction}")
        
        for symbol, direction in closed_positions:
            logger.warning(f"🔔 {trader_name} 平仓: {symbol} {direction}")
    
    def _analyze_collective_behavior(self, all_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析集体行为"""
        collective = {
            "consensus_level": 0,
            "dominant_direction": "NEUTRAL",
            "hot_symbols": {},
            "collective_signals": [],
            "divergence": []
        }
        
        if not all_data:
            return collective
        
        # 统计所有持仓
        all_positions = []
        for trader_data in all_data:
            all_positions.extend(trader_data.get("positions", []))
        
        if not all_positions:
            return collective
        
        # 统计方向一致性
        long_count = sum(1 for p in all_positions if p.direction == "LONG")
        short_count = sum(1 for p in all_positions if p.direction == "SHORT")
        
        total = long_count + short_count
        if total > 0:
            consensus = abs(long_count - short_count) / total
            collective["consensus_level"] = consensus * 100
            
            if long_count > short_count * 1.5:
                collective["dominant_direction"] = "LONG"
                collective["collective_signals"].append("多数交易员看多")
            elif short_count > long_count * 1.5:
                collective["dominant_direction"] = "SHORT"
                collective["collective_signals"].append("多数交易员看空")
        
        # 统计热门币种
        symbol_counts = {}
        for p in all_positions:
            symbol_counts[p.symbol] = symbol_counts.get(p.symbol, 0) + 1
        
        collective["hot_symbols"] = dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # 检测分歧
        if collective["consensus_level"] < 30:
            collective["divergence"].append("交易员观点分歧较大")
        
        return collective
    
    def _save_monitoring_data(self, all_data: List[Dict[str, Any]], collective: Dict[str, Any]):
        """保存监控数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存完整数据
        full_data = {
            "timestamp": timestamp,
            "traders": all_data,
            "collective_analysis": collective
        }
        
        filename = f"{self.data_path}monitoring_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            # 转换dataclass为dict
            for trader_data in full_data["traders"]:
                if trader_data.get("info"):
                    trader_data["info"] = asdict(trader_data["info"])
                if trader_data.get("positions"):
                    trader_data["positions"] = [asdict(p) for p in trader_data["positions"]]
            
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"监控数据已保存: {filename}")
    
    def _generate_monitoring_report(self, all_data: List[Dict[str, Any]], collective: Dict[str, Any]):
        """生成监控报告"""
        logger.info("\n" + "="*50)
        logger.info("顶级交易员监控报告")
        logger.info("="*50)
        
        # 输出每个交易员摘要
        for trader_data in all_data:
            if not trader_data.get("info"):
                continue
            
            info = trader_data["info"]
            positions = trader_data.get("positions", [])
            analysis = trader_data.get("analysis", {})
            
            logger.info(f"\n交易员: {info.trader_name}")
            logger.info(f"  胜率: {info.win_rate}%")
            logger.info(f"  总收益: {info.total_pnl}%")
            logger.info(f"  当前持仓: {len(positions)}个")
            logger.info(f"  跟随信号: {analysis.get('follow_signal', 'UNKNOWN')}")
            
            for insight in analysis.get("key_insights", [])[:2]:
                logger.info(f"  💡 {insight}")
        
        # 输出集体行为分析
        logger.info(f"\n集体行为分析:")
        logger.info(f"  一致性: {collective['consensus_level']:.1f}%")
        logger.info(f"  主导方向: {collective['dominant_direction']}")
        logger.info(f"  热门币种: {list(collective['hot_symbols'].keys())[:3]}")
        
        for signal in collective.get("collective_signals", []):
            logger.info(f"  📊 {signal}")
    
    def _parse_number(self, text: str) -> int:
        """解析数字文本"""
        try:
            text = text.replace(",", "").strip()
            if "K" in text or "k" in text:
                return int(float(text.replace("K", "").replace("k", "")) * 1000)
            elif "M" in text or "m" in text:
                return int(float(text.replace("M", "").replace("m", "")) * 1000000)
            else:
                return int(float(text))
        except:
            return 0
    
    def _extract_trader_id(self, url: str) -> str:
        """从URL提取交易员ID"""
        try:
            # 假设URL格式: https://i.bicoin.com.cn/web/trader/12345
            parts = url.split("/")
            return parts[-1] if parts else ""
        except:
            return ""
    
    def _update_top_traders(self, discovered_traders: List[Dict[str, Any]]):
        """更新顶级交易员列表"""
        # 合并新发现的交易员
        existing_ids = {t["id"] for t in self.top_traders}
        
        for trader in discovered_traders[:10]:  # 限制前10个
            if trader.get("id") and trader["id"] not in existing_ids:
                self.top_traders.append({
                    "name": trader["name"],
                    "id": trader["id"],
                    "url": trader.get("url", "")
                })
                logger.info(f"添加新交易员到监控列表: {trader['name']}")


# 测试代码
if __name__ == "__main__":
    # 初始化认证
    auth = BiCoinAuth()
    
    # 登录
    if auth.login():
        # 创建监控器
        monitor = TraderMonitor(auth)
        
        # 发现顶级交易员
        logger.info("发现顶级交易员...")
        top_traders = monitor.discover_top_traders(min_win_rate=60, min_followers=500)
        
        if top_traders:
            logger.info(f"发现 {len(top_traders)} 个优质交易员")
            
            # 监控所有交易员
            logger.info("\n开始监控交易员...")
            monitor.monitor_all_traders()
        else:
            logger.info("未发现符合条件的交易员")
        
        # 关闭
        auth.close()
    else:
        print("登录失败")