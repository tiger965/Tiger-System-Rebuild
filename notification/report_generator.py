"""
报告生成系统
生成日报、周报、月报
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

# 尝试导入报告生成相关库
try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

@dataclass
class TradeRecord:
    """交易记录"""
    timestamp: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_percent: float
    duration: timedelta

@dataclass
class ReportData:
    """报告数据"""
    period_start: datetime
    period_end: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    max_drawdown: float
    win_rate: float
    average_win: float
    average_loss: float
    best_trade: TradeRecord
    worst_trade: TradeRecord
    trades: List[TradeRecord]

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: str = "reports/generated"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 报告模板
        self.templates = {
            "daily": self._get_daily_template(),
            "weekly": self._get_weekly_template(),
            "monthly": self._get_monthly_template()
        }
        
        # 报告配置
        self.report_configs = {
            "daily": {
                "sections": [
                    "市场概览",
                    "交易执行",
                    "盈亏分析", 
                    "风险事件",
                    "明日展望"
                ],
                "metrics": [
                    "总交易次数",
                    "胜率",
                    "盈亏金额",
                    "最大回撤"
                ],
                "charts": [
                    "日内资金曲线",
                    "交易分布",
                    "盈亏分布"
                ]
            },
            "weekly": {
                "sections": [
                    "周度总结",
                    "策略表现",
                    "市场分析",
                    "交易复盘",
                    "下周计划"
                ],
                "charts": [
                    "资金曲线",
                    "胜率趋势",
                    "持仓分布",
                    "风险热力图"
                ]
            },
            "monthly": {
                "sections": [
                    "月度业绩",
                    "深度分析",
                    "策略评估",
                    "风险总结",
                    "改进建议"
                ],
                "analysis": [
                    "归因分析",
                    "相关性分析",
                    "情景分析",
                    "压力测试"
                ]
            }
        }
        
        # 统计缓存
        self.stats_cache = {}
        
        # 初始化Jinja环境
        if JINJA_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.output_dir.parent / "templates")),
                autoescape=True
            )
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> str:
        """
        生成日报
        
        Args:
            date: 日期（默认今天）
            
        Returns:
            报告文件路径
        """
        if date is None:
            date = datetime.now().date()
        
        self.logger.info(f"生成日报: {date}")
        
        # 收集数据
        report_data = self._collect_daily_data(date)
        
        # 生成内容
        content = self._generate_report_content("daily", report_data)
        
        # 生成图表
        charts = self._generate_charts("daily", report_data)
        
        # 组合报告
        report = self._combine_report(content, charts, "daily", date)
        
        # 保存报告
        filename = f"daily_report_{date.strftime('%Y%m%d')}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"日报已生成: {filepath}")
        return str(filepath)
    
    def generate_weekly_report(self, week_start: Optional[datetime] = None) -> str:
        """
        生成周报
        
        Args:
            week_start: 周开始日期
            
        Returns:
            报告文件路径
        """
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        self.logger.info(f"生成周报: {week_start} 至 {week_end}")
        
        # 收集数据
        report_data = self._collect_weekly_data(week_start, week_end)
        
        # 生成内容
        content = self._generate_report_content("weekly", report_data)
        
        # 生成图表
        charts = self._generate_charts("weekly", report_data)
        
        # 组合报告
        report = self._combine_report(content, charts, "weekly", week_start)
        
        # 保存报告
        filename = f"weekly_report_{week_start.strftime('%Y%m%d')}_{week_end.strftime('%Y%m%d')}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"周报已生成: {filepath}")
        return str(filepath)
    
    def generate_monthly_report(self, year: int, month: int) -> str:
        """
        生成月报
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            报告文件路径
        """
        from calendar import monthrange
        
        month_start = datetime(year, month, 1).date()
        month_end = datetime(year, month, monthrange(year, month)[1]).date()
        
        self.logger.info(f"生成月报: {year}年{month}月")
        
        # 收集数据
        report_data = self._collect_monthly_data(month_start, month_end)
        
        # 生成内容
        content = self._generate_report_content("monthly", report_data)
        
        # 生成图表
        charts = self._generate_charts("monthly", report_data)
        
        # 深度分析
        analysis = self._generate_deep_analysis(report_data)
        
        # 组合报告
        report = self._combine_report(content, charts, "monthly", month_start, analysis)
        
        # 保存报告
        filename = f"monthly_report_{year}{month:02d}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"月报已生成: {filepath}")
        return str(filepath)
    
    def _collect_daily_data(self, date) -> ReportData:
        """收集日报数据（模拟）"""
        import random
        
        # 模拟交易数据
        trades = []
        for i in range(random.randint(5, 15)):
            trade = TradeRecord(
                timestamp=datetime.combine(date, datetime.min.time()) + timedelta(hours=random.randint(0, 23)),
                symbol=random.choice(["BTC", "ETH", "BNB", "SOL"]),
                side=random.choice(["LONG", "SHORT"]),
                entry_price=random.uniform(1000, 50000),
                exit_price=0,
                size=random.uniform(0.01, 1),
                pnl=0,
                pnl_percent=0,
                duration=timedelta(minutes=random.randint(5, 300))
            )
            
            # 计算出场价和盈亏
            pnl_percent = random.uniform(-5, 10)
            if trade.side == "LONG":
                trade.exit_price = trade.entry_price * (1 + pnl_percent/100)
            else:
                trade.exit_price = trade.entry_price * (1 - pnl_percent/100)
            
            trade.pnl = (trade.exit_price - trade.entry_price) * trade.size
            if trade.side == "SHORT":
                trade.pnl = -trade.pnl
            trade.pnl_percent = pnl_percent
            
            trades.append(trade)
        
        # 计算统计
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        report_data = ReportData(
            period_start=datetime.combine(date, datetime.min.time()),
            period_end=datetime.combine(date, datetime.max.time()),
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            total_pnl=sum(t.pnl for t in trades),
            max_drawdown=min((sum(t.pnl for t in trades[:i+1]) for i in range(len(trades))), default=0),
            win_rate=len(winning_trades) / len(trades) * 100 if trades else 0,
            average_win=sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            average_loss=sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            best_trade=max(trades, key=lambda t: t.pnl) if trades else None,
            worst_trade=min(trades, key=lambda t: t.pnl) if trades else None,
            trades=trades
        )
        
        return report_data
    
    def _collect_weekly_data(self, week_start, week_end) -> ReportData:
        """收集周报数据"""
        # 这里应该从数据库或其他数据源收集真实数据
        # 现在使用模拟数据
        return self._collect_daily_data(week_start)  # 简化处理
    
    def _collect_monthly_data(self, month_start, month_end) -> ReportData:
        """收集月报数据"""
        # 这里应该从数据库或其他数据源收集真实数据
        # 现在使用模拟数据
        return self._collect_daily_data(month_start)  # 简化处理
    
    def _generate_report_content(self, report_type: str, data: ReportData) -> str:
        """生成报告内容"""
        template = self.templates[report_type]
        
        # 准备模板数据
        template_data = {
            "period_start": data.period_start.strftime("%Y-%m-%d"),
            "period_end": data.period_end.strftime("%Y-%m-%d"),
            "total_trades": data.total_trades,
            "winning_trades": data.winning_trades,
            "losing_trades": data.losing_trades,
            "total_pnl": f"${data.total_pnl:+,.2f}",
            "max_drawdown": f"${data.max_drawdown:,.2f}",
            "win_rate": f"{data.win_rate:.1f}%",
            "average_win": f"${data.average_win:+,.2f}",
            "average_loss": f"${data.average_loss:+,.2f}",
            "best_trade": self._format_trade(data.best_trade) if data.best_trade else "N/A",
            "worst_trade": self._format_trade(data.worst_trade) if data.worst_trade else "N/A"
        }
        
        # 渲染模板
        if JINJA_AVAILABLE:
            template_obj = Template(template)
            content = template_obj.render(**template_data)
        else:
            # 简单字符串替换
            content = template
            for key, value in template_data.items():
                content = content.replace(f"{{{key}}}", str(value))
        
        return content
    
    def _generate_charts(self, report_type: str, data: ReportData) -> Dict[str, str]:
        """生成图表"""
        charts = {}
        
        if not MATPLOTLIB_AVAILABLE:
            self.logger.warning("Matplotlib未安装，跳过图表生成")
            return charts
        
        # 生成资金曲线
        if data.trades:
            chart_path = self._generate_equity_curve(data)
            charts["equity_curve"] = chart_path
        
        # 生成其他图表...
        
        return charts
    
    def _generate_equity_curve(self, data: ReportData) -> str:
        """生成资金曲线"""
        if not data.trades:
            return ""
        
        # 计算累计盈亏
        cumulative_pnl = []
        current_pnl = 0
        timestamps = []
        
        for trade in sorted(data.trades, key=lambda t: t.timestamp):
            current_pnl += trade.pnl
            cumulative_pnl.append(current_pnl)
            timestamps.append(trade.timestamp)
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, cumulative_pnl, 'b-', linewidth=2)
        plt.fill_between(timestamps, cumulative_pnl, alpha=0.3)
        
        # 设置标题和标签
        plt.title('资金曲线', fontsize=14, fontweight='bold')
        plt.xlabel('时间')
        plt.ylabel('累计盈亏 ($)')
        
        # 格式化x轴
        plt.gcf().autofmt_xdate()
        
        # 添加网格
        plt.grid(True, alpha=0.3)
        
        # 添加零线
        plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # 保存图表
        chart_filename = f"equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = self.output_dir / "charts" / chart_filename
        chart_path.parent.mkdir(exist_ok=True)
        
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    def _generate_deep_analysis(self, data: ReportData) -> str:
        """生成深度分析"""
        analysis = []
        
        # 归因分析
        analysis.append("## 归因分析\n")
        if data.trades:
            by_symbol = {}
            for trade in data.trades:
                if trade.symbol not in by_symbol:
                    by_symbol[trade.symbol] = []
                by_symbol[trade.symbol].append(trade.pnl)
            
            for symbol, pnls in by_symbol.items():
                total = sum(pnls)
                avg = total / len(pnls)
                analysis.append(f"- {symbol}: 总盈亏 ${total:+,.2f}, 平均 ${avg:+,.2f}\n")
        
        # 风险分析
        analysis.append("\n## 风险分析\n")
        analysis.append(f"- 最大回撤: ${data.max_drawdown:,.2f}\n")
        analysis.append(f"- 胜率: {data.win_rate:.1f}%\n")
        analysis.append(f"- 盈亏比: {abs(data.average_win/data.average_loss):.2f}\n" if data.average_loss != 0 else "")
        
        return "".join(analysis)
    
    def _combine_report(self, content: str, charts: Dict[str, str], 
                       report_type: str, date, analysis: str = "") -> str:
        """组合报告"""
        report = []
        
        # 标题
        report.append(f"# Tiger系统 {self._get_report_title(report_type)}\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("=" * 60 + "\n\n")
        
        # 内容
        report.append(content)
        
        # 图表
        if charts:
            report.append("\n## 图表分析\n")
            for chart_name, chart_path in charts.items():
                report.append(f"![{chart_name}]({chart_path})\n")
        
        # 深度分析
        if analysis:
            report.append("\n" + analysis)
        
        # 页脚
        report.append("\n" + "=" * 60 + "\n")
        report.append("报告由Tiger系统自动生成\n")
        
        return "".join(report)
    
    def _format_trade(self, trade: TradeRecord) -> str:
        """格式化交易记录"""
        return (f"{trade.symbol} {trade.side} "
                f"入场${trade.entry_price:,.2f} "
                f"出场${trade.exit_price:,.2f} "
                f"盈亏${trade.pnl:+,.2f} ({trade.pnl_percent:+.1f}%)")
    
    def _get_report_title(self, report_type: str) -> str:
        """获取报告标题"""
        titles = {
            "daily": "日报",
            "weekly": "周报",
            "monthly": "月报"
        }
        return titles.get(report_type, "报告")
    
    def _get_daily_template(self) -> str:
        """获取日报模板"""
        return """
## 市场概览
- 交易日期: {period_start} 
- 市场情绪: 中性
- 主要事件: 无

## 交易执行
- 总交易次数: {total_trades}
- 成功交易: {winning_trades}
- 失败交易: {losing_trades}
- 胜率: {win_rate}

## 盈亏分析
- 总盈亏: {total_pnl}
- 平均盈利: {average_win}
- 平均亏损: {average_loss}
- 最佳交易: {best_trade}
- 最差交易: {worst_trade}

## 风险事件
- 最大回撤: {max_drawdown}
- 风险警报: 0次
- 止损触发: 0次

## 明日展望
- 关注币种: BTC, ETH
- 风险提示: 保持谨慎
- 仓位建议: 维持当前
"""
    
    def _get_weekly_template(self) -> str:
        """获取周报模板"""
        return """
## 周度总结
- 交易周期: {period_start} 至 {period_end}
- 总交易次数: {total_trades}
- 总盈亏: {total_pnl}
- 胜率: {win_rate}

## 策略表现
- 趋势策略: 表现良好
- 套利策略: 正常
- 网格策略: 待优化

## 市场分析
- BTC: 震荡上行
- ETH: 强势突破
- 整体: 牛市初期

## 交易复盘
- 最佳交易: {best_trade}
- 最差交易: {worst_trade}
- 经验教训: 严格止损

## 下周计划
- 重点关注: Layer2项目
- 风险控制: 加强
- 仓位调整: 适度增加
"""
    
    def _get_monthly_template(self) -> str:
        """获取月报模板"""
        return """
## 月度业绩
- 报告期间: {period_start} 至 {period_end}
- 总交易次数: {total_trades}
- 总盈亏: {total_pnl}
- 胜率: {win_rate}
- 最大回撤: {max_drawdown}

## 深度分析
### 盈亏分析
- 平均盈利: {average_win}
- 平均亏损: {average_loss}
- 盈亏比: 计算中

### 最佳/最差交易
- 最佳: {best_trade}
- 最差: {worst_trade}

## 策略评估
- 策略有效性: 良好
- 需要改进: 入场时机
- 优势: 风险控制

## 风险总结
- 风险事件: 2次
- 及时止损: 15次
- 风控有效性: 95%

## 改进建议
1. 优化入场信号
2. 加强仓位管理
3. 提高执行效率
"""