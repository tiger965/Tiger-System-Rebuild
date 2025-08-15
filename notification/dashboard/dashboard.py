"""
实时监控仪表板
终端UI实时显示系统状态
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque
import json

# 尝试导入rich库用于终端美化
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    last_update: datetime

@dataclass
class Position:
    """持仓数据"""
    symbol: str
    side: str
    entry_price: float
    current_price: float
    size: float
    pnl: float
    pnl_percent: float

@dataclass
class Signal:
    """信号数据"""
    timestamp: datetime
    symbol: str
    type: str
    confidence: int
    status: str

class Dashboard:
    """实时监控仪表板"""
    
    def __init__(self, refresh_rate: int = 1):
        """
        初始化仪表板
        
        Args:
            refresh_rate: 刷新频率（秒）
        """
        self.refresh_rate = refresh_rate
        self.running = False
        
        # 数据存储
        self.market_data = {}
        self.positions = []
        self.signals = deque(maxlen=20)
        self.alerts = deque(maxlen=10)
        self.system_status = {
            "status": "运行中",
            "uptime": timedelta(0),
            "start_time": datetime.now(),
            "cpu": 0,
            "memory": 0,
            "connections": 0
        }
        
        # 统计数据
        self.stats = {
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "daily_trades": 0,
            "risk_level": "低",
            "active_positions": 0
        }
        
        # 刷新控制
        self.refresh_rates = {
            "prices": 1,      # 价格刷新频率（秒）
            "positions": 5,   # 持仓刷新频率
            "signals": 10,    # 信号刷新频率
            "full": 30        # 完整刷新频率
        }
        
        self.last_refresh = {
            "prices": datetime.now(),
            "positions": datetime.now(),
            "signals": datetime.now(),
            "full": datetime.now()
        }
        
        # Rich终端支持
        if RICH_AVAILABLE:
            self.console = Console()
            self.use_rich = True
        else:
            self.use_rich = False
        
        # 更新线程
        self.update_thread = None
    
    def start(self):
        """启动仪表板"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._run_dashboard)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        print("仪表板已启动")
    
    def stop(self):
        """停止仪表板"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        print("\n仪表板已停止")
    
    def _run_dashboard(self):
        """运行仪表板主循环"""
        if self.use_rich:
            self._run_rich_dashboard()
        else:
            self._run_simple_dashboard()
    
    def _run_rich_dashboard(self):
        """运行Rich终端仪表板"""
        with Live(self._generate_rich_layout(), refresh_per_second=1, console=self.console) as live:
            while self.running:
                # 更新数据
                self._update_data()
                
                # 更新显示
                live.update(self._generate_rich_layout())
                
                time.sleep(self.refresh_rate)
    
    def _run_simple_dashboard(self):
        """运行简单终端仪表板"""
        while self.running:
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 更新数据
            self._update_data()
            
            # 显示仪表板
            self._display_simple_dashboard()
            
            time.sleep(self.refresh_rate)
    
    def _generate_rich_layout(self) -> Layout:
        """生成Rich布局"""
        layout = Layout()
        
        # 创建布局结构
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # 头部 - 系统状态
        layout["header"].update(self._create_header_panel())
        
        # 主体部分
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # 左侧 - 市场和持仓
        layout["body"]["left"].split_column(
            Layout(self._create_market_table(), name="market"),
            Layout(self._create_positions_table(), name="positions")
        )
        
        # 右侧 - 信号和警报
        layout["body"]["right"].split_column(
            Layout(self._create_signals_panel(), name="signals"),
            Layout(self._create_alerts_panel(), name="alerts")
        )
        
        # 底部 - 统计信息
        layout["footer"].update(self._create_stats_panel())
        
        return layout
    
    def _create_header_panel(self) -> Panel:
        """创建头部面板"""
        uptime = datetime.now() - self.system_status["start_time"]
        header_text = Text()
        header_text.append("🐅 Tiger System Monitor ", style="bold yellow")
        header_text.append(f"| 状态: {self.system_status['status']} ", 
                          style="green" if self.system_status['status'] == "运行中" else "red")
        header_text.append(f"| 运行时间: {str(uptime).split('.')[0]} ")
        header_text.append(f"| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return Panel(header_text, style="bold blue")
    
    def _create_market_table(self) -> Panel:
        """创建市场数据表格"""
        table = Table(title="📊 市场行情", show_header=True, header_style="bold magenta")
        table.add_column("币种", style="cyan", width=8)
        table.add_column("价格", justify="right", width=12)
        table.add_column("24h涨跌", justify="right", width=10)
        table.add_column("成交量", justify="right", width=12)
        
        # 添加市场数据
        for symbol, data in list(self.market_data.items())[:5]:
            price_str = f"${data.price:,.2f}"
            change_color = "green" if data.change_24h >= 0 else "red"
            change_str = f"{data.change_24h:+.2f}%"
            volume_str = f"${data.volume_24h/1e6:.1f}M"
            
            table.add_row(
                symbol,
                price_str,
                Text(change_str, style=change_color),
                volume_str
            )
        
        return Panel(table, border_style="blue")
    
    def _create_positions_table(self) -> Panel:
        """创建持仓表格"""
        table = Table(title="💼 当前持仓", show_header=True, header_style="bold magenta")
        table.add_column("币种", style="cyan", width=8)
        table.add_column("方向", width=6)
        table.add_column("入场价", justify="right", width=10)
        table.add_column("当前价", justify="right", width=10)
        table.add_column("盈亏", justify="right", width=12)
        
        # 添加持仓数据
        for pos in self.positions[:5]:
            side_color = "green" if pos.side == "LONG" else "red"
            pnl_color = "green" if pos.pnl >= 0 else "red"
            
            table.add_row(
                pos.symbol,
                Text(pos.side, style=side_color),
                f"${pos.entry_price:,.2f}",
                f"${pos.current_price:,.2f}",
                Text(f"${pos.pnl:+,.2f} ({pos.pnl_percent:+.1f}%)", style=pnl_color)
            )
        
        if not self.positions:
            table.add_row("无持仓", "-", "-", "-", "-")
        
        return Panel(table, border_style="blue")
    
    def _create_signals_panel(self) -> Panel:
        """创建信号面板"""
        signals_text = Text()
        signals_text.append("📡 最近信号\n", style="bold yellow")
        signals_text.append("─" * 40 + "\n", style="dim")
        
        for signal in list(self.signals)[:5]:
            time_str = signal.timestamp.strftime("%H:%M:%S")
            confidence_color = "green" if signal.confidence >= 7 else "yellow" if signal.confidence >= 5 else "red"
            status_icon = "✅" if signal.status == "执行" else "⏳" if signal.status == "待定" else "❌"
            
            signals_text.append(f"{time_str} ", style="dim")
            signals_text.append(f"{signal.symbol} ", style="cyan")
            signals_text.append(f"{signal.type} ", style="magenta")
            signals_text.append(f"[{signal.confidence}/10] ", style=confidence_color)
            signals_text.append(f"{status_icon}\n")
        
        if not self.signals:
            signals_text.append("暂无信号", style="dim")
        
        return Panel(signals_text, border_style="yellow")
    
    def _create_alerts_panel(self) -> Panel:
        """创建警报面板"""
        alerts_text = Text()
        alerts_text.append("⚠️ 风险警报\n", style="bold red")
        alerts_text.append("─" * 40 + "\n", style="dim")
        
        for alert in list(self.alerts)[:3]:
            alerts_text.append(f"• {alert}\n", style="yellow")
        
        if not self.alerts:
            alerts_text.append("暂无警报", style="green")
        
        return Panel(alerts_text, border_style="red")
    
    def _create_stats_panel(self) -> Panel:
        """创建统计面板"""
        stats_text = Text()
        
        pnl_color = "green" if self.stats["total_pnl"] >= 0 else "red"
        risk_color = "green" if self.stats["risk_level"] == "低" else "yellow" if self.stats["risk_level"] == "中" else "red"
        
        stats_text.append("📈 统计: ", style="bold")
        stats_text.append(f"盈亏: ${self.stats['total_pnl']:+,.2f} ", style=pnl_color)
        stats_text.append(f"| 胜率: {self.stats['win_rate']:.1f}% ")
        stats_text.append(f"| 今日交易: {self.stats['daily_trades']} ")
        stats_text.append(f"| 持仓: {self.stats['active_positions']} ")
        stats_text.append(f"| 风险: {self.stats['risk_level']} ", style=risk_color)
        
        return Panel(stats_text, style="bold blue")
    
    def _display_simple_dashboard(self):
        """显示简单仪表板"""
        # 计算运行时间
        uptime = datetime.now() - self.system_status["start_time"]
        
        # 打印头部
        print("=" * 60)
        print(f"         Tiger System Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"         状态: {self.system_status['status']} | 运行时间: {str(uptime).split('.')[0]}")
        print("=" * 60)
        
        # 市场行情
        print("\n📊 市场行情:")
        print("-" * 40)
        if self.market_data:
            print(f"{'币种':<8} {'价格':>12} {'24h涨跌':>10} {'成交量':>12}")
            for symbol, data in list(self.market_data.items())[:5]:
                change_sign = "+" if data.change_24h >= 0 else ""
                print(f"{symbol:<8} ${data.price:>11,.2f} {change_sign}{data.change_24h:>9.2f}% ${data.volume_24h/1e6:>10.1f}M")
        else:
            print("暂无数据")
        
        # 持仓信息
        print("\n💼 当前持仓:")
        print("-" * 40)
        if self.positions:
            print(f"{'币种':<8} {'方向':<6} {'入场价':>10} {'当前价':>10} {'盈亏':>15}")
            for pos in self.positions[:5]:
                pnl_str = f"${pos.pnl:+,.2f} ({pos.pnl_percent:+.1f}%)"
                print(f"{pos.symbol:<8} {pos.side:<6} ${pos.entry_price:>9,.2f} ${pos.current_price:>9,.2f} {pnl_str:>15}")
        else:
            print("无持仓")
        
        # 最近信号
        print("\n📡 最近信号:")
        print("-" * 40)
        if self.signals:
            for signal in list(self.signals)[:3]:
                time_str = signal.timestamp.strftime("%H:%M:%S")
                print(f"{time_str} {signal.symbol} {signal.type} 置信度:{signal.confidence}/10 {signal.status}")
        else:
            print("暂无信号")
        
        # 统计信息
        print("\n📈 统计信息:")
        print("-" * 40)
        print(f"总盈亏: ${self.stats['total_pnl']:+,.2f} | 胜率: {self.stats['win_rate']:.1f}%")
        print(f"今日交易: {self.stats['daily_trades']} | 活跃持仓: {self.stats['active_positions']} | 风险等级: {self.stats['risk_level']}")
        
        print("=" * 60)
    
    def _update_data(self):
        """更新数据（模拟）"""
        now = datetime.now()
        
        # 更新系统运行时间
        self.system_status["uptime"] = now - self.system_status["start_time"]
        
        # 检查是否需要更新各类数据
        if (now - self.last_refresh["prices"]).seconds >= self.refresh_rates["prices"]:
            self._update_market_data()
            self.last_refresh["prices"] = now
        
        if (now - self.last_refresh["positions"]).seconds >= self.refresh_rates["positions"]:
            self._update_positions()
            self.last_refresh["positions"] = now
        
        if (now - self.last_refresh["signals"]).seconds >= self.refresh_rates["signals"]:
            self._update_signals()
            self.last_refresh["signals"] = now
    
    def _update_market_data(self):
        """更新市场数据（模拟）"""
        import random
        
        # 模拟市场数据
        symbols = ["BTC", "ETH", "BNB", "SOL", "ADA"]
        for symbol in symbols:
            if symbol not in self.market_data:
                self.market_data[symbol] = MarketData(
                    symbol=symbol,
                    price=random.uniform(100, 70000),
                    change_24h=random.uniform(-10, 10),
                    volume_24h=random.uniform(1e6, 1e9),
                    last_update=datetime.now()
                )
            else:
                # 小幅波动
                data = self.market_data[symbol]
                data.price *= (1 + random.uniform(-0.001, 0.001))
                data.change_24h += random.uniform(-0.1, 0.1)
                data.last_update = datetime.now()
    
    def _update_positions(self):
        """更新持仓数据（模拟）"""
        import random
        
        # 模拟持仓更新
        for pos in self.positions:
            # 价格小幅波动
            pos.current_price *= (1 + random.uniform(-0.002, 0.002))
            # 重新计算盈亏
            if pos.side == "LONG":
                pos.pnl = (pos.current_price - pos.entry_price) * pos.size
            else:
                pos.pnl = (pos.entry_price - pos.current_price) * pos.size
            pos.pnl_percent = (pos.pnl / (pos.entry_price * pos.size)) * 100
        
        # 更新统计
        self.stats["active_positions"] = len(self.positions)
        self.stats["total_pnl"] = sum(p.pnl for p in self.positions)
    
    def _update_signals(self):
        """更新信号数据（模拟）"""
        import random
        
        # 随机生成新信号
        if random.random() < 0.1:  # 10%概率生成新信号
            symbols = ["BTC", "ETH", "BNB", "SOL", "ADA"]
            types = ["LONG", "SHORT", "CLOSE"]
            statuses = ["执行", "待定", "取消"]
            
            signal = Signal(
                timestamp=datetime.now(),
                symbol=random.choice(symbols),
                type=random.choice(types),
                confidence=random.randint(3, 10),
                status=random.choice(statuses)
            )
            self.signals.append(signal)
    
    # 公共API方法
    def update_market(self, symbol: str, price: float, change_24h: float, volume_24h: float):
        """更新市场数据"""
        self.market_data[symbol] = MarketData(
            symbol=symbol,
            price=price,
            change_24h=change_24h,
            volume_24h=volume_24h,
            last_update=datetime.now()
        )
    
    def update_position(self, position: Position):
        """更新持仓"""
        # 查找并更新或添加
        for i, pos in enumerate(self.positions):
            if pos.symbol == position.symbol:
                self.positions[i] = position
                return
        self.positions.append(position)
    
    def add_signal(self, symbol: str, signal_type: str, confidence: int, status: str = "待定"):
        """添加信号"""
        signal = Signal(
            timestamp=datetime.now(),
            symbol=symbol,
            type=signal_type,
            confidence=confidence,
            status=status
        )
        self.signals.append(signal)
    
    def add_alert(self, alert_message: str):
        """添加警报"""
        self.alerts.append(f"{datetime.now().strftime('%H:%M:%S')} - {alert_message}")
    
    def update_stats(self, **kwargs):
        """更新统计信息"""
        self.stats.update(kwargs)
    
    def clear_positions(self):
        """清空持仓"""
        self.positions.clear()
        self.stats["active_positions"] = 0
        self.stats["total_pnl"] = 0