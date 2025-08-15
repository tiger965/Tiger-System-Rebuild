"""
终端纯显示执行工具 - Window 8
只负责执行显示，不做任何判断
"""

import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
import json


class TerminalDisplay:
    """终端输出工具 - 纯执行"""
    
    def __init__(self, use_color: bool = True, width: Optional[int] = None):
        """
        初始化终端显示器
        
        Args:
            use_color: 是否使用颜色
            width: 终端宽度（None表示自动检测）
        """
        self.console = Console(
            color_system="auto" if use_color else None,
            width=width
        )
        self.logger = logging.getLogger(__name__)
        
        # 显示统计
        self.stats = {
            "messages_printed": 0,
            "tables_printed": 0,
            "panels_printed": 0,
            "charts_printed": 0,
            "total_lines": 0
        }
        
        # 颜色映射
        self.colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
            "default": "white"
        }
    
    def print_message(self, 
                     message: str, 
                     color: Optional[str] = None,
                     style: Optional[str] = None,
                     highlight: bool = False,
                     timestamp: bool = True) -> Dict[str, Any]:
        """
        打印消息到终端
        
        Args:
            message: 消息内容
            color: 文本颜色
            style: 文本样式 (bold, italic, underline等)
            highlight: 是否高亮显示
            timestamp: 是否添加时间戳
            
        Returns:
            执行结果
        """
        try:
            # 构建消息
            if timestamp:
                time_str = datetime.now().strftime("%H:%M:%S")
                full_message = f"[{time_str}] {message}"
            else:
                full_message = message
            
            # 应用颜色和样式
            if color or style:
                color_str = self.colors.get(color, color) if color else ""
                style_str = f" {style}" if style else ""
                formatted_message = f"[{color_str}{style_str}]{full_message}[/]"
            else:
                formatted_message = full_message
            
            # 打印消息
            self.console.print(formatted_message, highlight=highlight)
            
            # 更新统计
            self.stats["messages_printed"] += 1
            self.stats["total_lines"] += len(full_message.split('\n'))
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "message",
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印消息失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "message",
                "error": str(e)
            }
    
    def print_table(self, 
                   data: List[Dict[str, Any]], 
                   headers: Optional[List[str]] = None,
                   title: Optional[str] = None,
                   caption: Optional[str] = None,
                   show_header: bool = True,
                   show_lines: bool = False,
                   highlight_key: Optional[str] = None,
                   highlight_value: Any = None) -> Dict[str, Any]:
        """
        显示表格
        
        Args:
            data: 表格数据（字典列表）
            headers: 列标题（None则自动从数据提取）
            title: 表格标题
            caption: 表格说明
            show_header: 是否显示表头
            show_lines: 是否显示行线
            highlight_key: 高亮字段名
            highlight_value: 高亮匹配值
            
        Returns:
            执行结果
        """
        try:
            if not data:
                return {
                    "status": "failed",
                    "channel": "terminal",
                    "type": "table",
                    "error": "无数据"
                }
            
            # 获取列标题
            if not headers:
                headers = list(data[0].keys())
            
            # 创建表格
            table = Table(
                title=title,
                caption=caption,
                show_header=show_header,
                show_lines=show_lines
            )
            
            # 添加列
            for header in headers:
                table.add_column(str(header), style="cyan", no_wrap=False)
            
            # 添加数据行
            for row_data in data:
                row = []
                for header in headers:
                    value = str(row_data.get(header, ""))
                    
                    # 高亮处理
                    if highlight_key and header == highlight_key and row_data.get(header) == highlight_value:
                        row.append(f"[bold yellow]{value}[/bold yellow]")
                    else:
                        row.append(value)
                
                table.add_row(*row)
            
            # 打印表格
            self.console.print(table)
            
            # 更新统计
            self.stats["tables_printed"] += 1
            self.stats["total_lines"] += len(data) + 3  # 数据行 + 表头和边框
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "table",
                "rows": len(data),
                "columns": len(headers),
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印表格失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "table",
                "error": str(e)
            }
    
    def print_panel(self,
                   content: str,
                   title: Optional[str] = None,
                   subtitle: Optional[str] = None,
                   border_style: str = "blue",
                   padding: int = 1) -> Dict[str, Any]:
        """
        显示面板
        
        Args:
            content: 面板内容
            title: 面板标题
            subtitle: 面板副标题
            border_style: 边框样式
            padding: 内边距
            
        Returns:
            执行结果
        """
        try:
            panel = Panel(
                content,
                title=title,
                subtitle=subtitle,
                border_style=border_style,
                padding=padding
            )
            
            self.console.print(panel)
            
            # 更新统计
            self.stats["panels_printed"] += 1
            self.stats["total_lines"] += len(content.split('\n')) + 2
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "panel",
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印面板失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "panel",
                "error": str(e)
            }
    
    def print_json(self,
                  data: Dict[str, Any],
                  title: Optional[str] = None,
                  indent: int = 2) -> Dict[str, Any]:
        """
        格式化打印JSON数据
        
        Args:
            data: JSON数据
            title: 标题
            indent: 缩进空格数
            
        Returns:
            执行结果
        """
        try:
            if title:
                self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
            
            json_str = json.dumps(data, ensure_ascii=False, indent=indent)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            self.console.print(syntax)
            
            # 更新统计
            self.stats["messages_printed"] += 1
            self.stats["total_lines"] += len(json_str.split('\n'))
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "json",
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印JSON失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "json",
                "error": str(e)
            }
    
    def print_markdown(self,
                      markdown_text: str) -> Dict[str, Any]:
        """
        打印Markdown格式文本
        
        Args:
            markdown_text: Markdown文本
            
        Returns:
            执行结果
        """
        try:
            md = Markdown(markdown_text)
            self.console.print(md)
            
            # 更新统计
            self.stats["messages_printed"] += 1
            self.stats["total_lines"] += len(markdown_text.split('\n'))
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "markdown",
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印Markdown失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "markdown",
                "error": str(e)
            }
    
    def print_progress(self,
                      task_name: str,
                      total: int,
                      current: int,
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        显示进度条
        
        Args:
            task_name: 任务名称
            total: 总数
            current: 当前进度
            description: 描述信息
            
        Returns:
            执行结果
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[cyan]{task_name}[/cyan]",
                    total=total
                )
                progress.update(task, advance=current, description=description)
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "progress",
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"显示进度条失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "progress",
                "error": str(e)
            }
    
    def print_chart(self,
                   data: List[float],
                   title: Optional[str] = None,
                   width: int = 60,
                   height: int = 10,
                   chart_type: str = "line") -> Dict[str, Any]:
        """
        打印简单图表（ASCII）
        
        Args:
            data: 数据点
            title: 图表标题
            width: 图表宽度
            height: 图表高度
            chart_type: 图表类型 (line/bar)
            
        Returns:
            执行结果
        """
        try:
            if not data:
                return {
                    "status": "failed",
                    "channel": "terminal",
                    "type": "chart",
                    "error": "无数据"
                }
            
            # 计算缩放
            max_val = max(data)
            min_val = min(data)
            range_val = max_val - min_val if max_val != min_val else 1
            
            # 创建图表
            chart_lines = []
            
            if title:
                chart_lines.append(f"[bold cyan]{title}[/bold cyan]")
                chart_lines.append("")
            
            # 绘制Y轴刻度和图表
            for h in range(height, 0, -1):
                threshold = min_val + (h - 1) * range_val / (height - 1)
                line = f"{threshold:8.2f} │"
                
                if chart_type == "line":
                    # 线图
                    for i, value in enumerate(data):
                        if i < width:
                            if abs(value - threshold) < range_val / height / 2:
                                line += "●"
                            elif value > threshold:
                                line += "·"
                            else:
                                line += " "
                elif chart_type == "bar":
                    # 柱状图
                    for i, value in enumerate(data):
                        if i < width:
                            if value >= threshold:
                                line += "█"
                            else:
                                line += " "
                
                chart_lines.append(line)
            
            # X轴
            chart_lines.append(f"{'':8} └{'─' * min(len(data), width)}")
            
            # 打印图表
            for line in chart_lines:
                self.console.print(line)
            
            # 更新统计
            self.stats["charts_printed"] += 1
            self.stats["total_lines"] += len(chart_lines)
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "chart",
                "data_points": len(data),
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印图表失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "chart",
                "error": str(e)
            }
    
    def clear(self):
        """清屏"""
        self.console.clear()
    
    def print_separator(self, 
                       style: str = "─",
                       color: Optional[str] = None):
        """打印分隔线"""
        width = self.console.width
        separator = style * width
        
        if color:
            self.console.print(f"[{color}]{separator}[/{color}]")
        else:
            self.console.print(separator)
        
        self.stats["total_lines"] += 1
    
    def print_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        打印通知（Window 6格式）
        
        Args:
            notification: 通知数据
            
        Returns:
            执行结果
        """
        try:
            # 提取通知信息
            message = notification.get("message", "")
            level = notification.get("level", "info")
            timestamp = notification.get("timestamp", datetime.now().isoformat())
            source = notification.get("source", "System")
            
            # 根据级别选择颜色
            level_colors = {
                "info": "blue",
                "important": "yellow",
                "urgent": "red",
                "critical": "bold red on white"
            }
            
            color = level_colors.get(level.lower(), "white")
            
            # 构建显示内容
            panel_content = f"""
[bold]{message}[/bold]

来源: {source}
时间: {timestamp}
            """
            
            # 显示面板
            self.print_panel(
                panel_content,
                title=f"[{color}]● {level.upper()}[/{color}]",
                border_style=color.split()[0] if ' ' in color else color
            )
            
            return {
                "status": "success",
                "channel": "terminal",
                "type": "notification",
                "printed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"打印通知失败: {e}")
            return {
                "status": "failed",
                "channel": "terminal",
                "type": "notification",
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取显示统计"""
        return {
            "messages": self.stats["messages_printed"],
            "tables": self.stats["tables_printed"],
            "panels": self.stats["panels_printed"],
            "charts": self.stats["charts_printed"],
            "total_lines": self.stats["total_lines"],
            "terminal_width": self.console.width,
            "terminal_height": self.console.height
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "messages_printed": 0,
            "tables_printed": 0,
            "panels_printed": 0,
            "charts_printed": 0,
            "total_lines": 0
        }