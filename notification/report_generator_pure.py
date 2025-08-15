"""
报告纯生成执行工具 - Window 8
只负责执行生成，不做任何判断
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd
from jinja2 import Template
try:
    import pdfkit
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ReportGenerator:
    """报告生成工具 - 纯执行"""
    
    def __init__(self, 
                 output_dir: str = "./reports",
                 template_dir: Optional[str] = None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
            template_dir: 模板目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_dir = Path(template_dir) if template_dir else None
        self.logger = logging.getLogger(__name__)
        
        # 生成统计
        self.stats = {
            "daily_reports": 0,
            "trade_reports": 0,
            "pdf_exports": 0,
            "excel_exports": 0,
            "failed": 0,
            "total_size_kb": 0
        }
        
        # 线程池执行器（PDF生成是同步操作）
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def generate_daily_report(self, 
                             data: Dict[str, Any],
                             date: Optional[datetime] = None,
                             format: str = "html") -> Dict[str, Any]:
        """
        生成日报
        
        Args:
            data: 报告数据（由Window 6提供）
            date: 报告日期
            format: 输出格式 (html/pdf/json)
            
        Returns:
            生成结果
        """
        try:
            report_date = date or datetime.now()
            date_str = report_date.strftime("%Y%m%d")
            
            # 生成文件名
            filename = f"daily_report_{date_str}.{format}"
            filepath = self.output_dir / filename
            
            # 根据格式生成报告
            if format == "html":
                content = self._generate_daily_html(data, report_date)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == "pdf":
                if not PDF_AVAILABLE:
                    return {
                        "status": "failed",
                        "type": "daily_report",
                        "error": "PDF功能不可用，需要安装pdfkit和wkhtmltopdf"
                    }
                html_content = self._generate_daily_html(data, report_date)
                try:
                    pdfkit.from_string(html_content, str(filepath))
                    self.stats["pdf_exports"] += 1
                except Exception as e:
                    return {
                        "status": "failed",
                        "type": "daily_report", 
                        "error": f"PDF生成失败: {str(e)} (可能需要安装wkhtmltopdf)"
                    }
            elif format == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                return {
                    "status": "failed",
                    "type": "daily_report",
                    "error": f"不支持的格式: {format}"
                }
            
            # 获取文件大小
            file_size_kb = filepath.stat().st_size / 1024
            self.stats["daily_reports"] += 1
            self.stats["total_size_kb"] += file_size_kb
            
            return {
                "status": "success",
                "type": "daily_report",
                "filepath": str(filepath),
                "format": format,
                "size_kb": file_size_kb,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"生成日报失败: {e}")
            return {
                "status": "failed",
                "type": "daily_report",
                "error": str(e)
            }
    
    def generate_trade_report(self,
                             trades: List[Dict[str, Any]],
                             period_start: Optional[datetime] = None,
                             period_end: Optional[datetime] = None,
                             format: str = "html") -> Dict[str, Any]:
        """
        生成交易报告
        
        Args:
            trades: 交易记录列表
            period_start: 统计开始时间
            period_end: 统计结束时间
            format: 输出格式 (html/pdf/excel)
            
        Returns:
            生成结果
        """
        try:
            # 确定时间范围
            end_time = period_end or datetime.now()
            start_time = period_start or (end_time - timedelta(days=1))
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trade_report_{timestamp}.{format}"
            filepath = self.output_dir / filename
            
            # 根据格式生成报告
            if format == "html":
                content = self._generate_trade_html(trades, start_time, end_time)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == "pdf":
                if not PDF_AVAILABLE:
                    return {
                        "status": "failed",
                        "type": "trade_report",
                        "error": "PDF功能不可用，需要安装pdfkit和wkhtmltopdf"
                    }
                html_content = self._generate_trade_html(trades, start_time, end_time)
                try:
                    pdfkit.from_string(html_content, str(filepath))
                    self.stats["pdf_exports"] += 1
                except Exception as e:
                    return {
                        "status": "failed",
                        "type": "trade_report",
                        "error": f"PDF生成失败: {str(e)} (可能需要安装wkhtmltopdf)"
                    }
            elif format == "excel":
                df = pd.DataFrame(trades)
                df.to_excel(filepath, index=False, engine='openpyxl')
                self.stats["excel_exports"] += 1
            else:
                return {
                    "status": "failed",
                    "type": "trade_report",
                    "error": f"不支持的格式: {format}"
                }
            
            # 获取文件大小
            file_size_kb = filepath.stat().st_size / 1024
            self.stats["trade_reports"] += 1
            self.stats["total_size_kb"] += file_size_kb
            
            return {
                "status": "success",
                "type": "trade_report",
                "filepath": str(filepath),
                "format": format,
                "trades_count": len(trades),
                "size_kb": file_size_kb,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"生成交易报告失败: {e}")
            return {
                "status": "failed",
                "type": "trade_report",
                "error": str(e)
            }
    
    async def export_to_pdf(self,
                           html_content: str,
                           output_filename: str,
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        导出为PDF
        
        Args:
            html_content: HTML内容
            output_filename: 输出文件名
            options: wkhtmltopdf选项
            
        Returns:
            生成结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._export_to_pdf_sync,
            html_content,
            output_filename,
            options
        )
    
    def _export_to_pdf_sync(self,
                           html_content: str,
                           output_filename: str,
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """同步导出PDF的内部方法"""
        try:
            filepath = self.output_dir / output_filename
            
            # 默认选项
            pdf_options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            
            if options:
                pdf_options.update(options)
            
            # 生成PDF
            if not PDF_AVAILABLE:
                raise Exception("PDF功能不可用，需要安装pdfkit和wkhtmltopdf")
            pdfkit.from_string(html_content, str(filepath), options=pdf_options)
            
            # 获取文件大小
            file_size_kb = filepath.stat().st_size / 1024
            self.stats["pdf_exports"] += 1
            self.stats["total_size_kb"] += file_size_kb
            
            return {
                "status": "success",
                "type": "pdf_export",
                "filepath": str(filepath),
                "size_kb": file_size_kb,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"导出PDF失败: {e}")
            return {
                "status": "failed",
                "type": "pdf_export",
                "error": str(e)
            }
    
    def generate_custom_report(self,
                              template_name: str,
                              data: Dict[str, Any],
                              output_filename: str,
                              format: str = "html") -> Dict[str, Any]:
        """
        使用自定义模板生成报告
        
        Args:
            template_name: 模板名称
            data: 模板数据
            output_filename: 输出文件名
            format: 输出格式
            
        Returns:
            生成结果
        """
        try:
            # 加载模板
            if self.template_dir:
                template_path = self.template_dir / f"{template_name}.html"
                if template_path.exists():
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                    template = Template(template_content)
                    html_content = template.render(**data)
                else:
                    # 使用默认模板
                    html_content = self._generate_default_html(data)
            else:
                html_content = self._generate_default_html(data)
            
            # 生成报告
            filepath = self.output_dir / output_filename
            
            if format == "html":
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            elif format == "pdf":
                if not PDF_AVAILABLE:
                    return {
                        "status": "failed",
                        "type": "custom_report",
                        "error": "PDF功能不可用，需要安装pdfkit和wkhtmltopdf"
                    }
                try:
                    pdfkit.from_string(html_content, str(filepath))
                    self.stats["pdf_exports"] += 1
                except Exception as e:
                    return {
                        "status": "failed",
                        "type": "custom_report",
                        "error": f"PDF生成失败: {str(e)} (可能需要安装wkhtmltopdf)"
                    }
            else:
                return {
                    "status": "failed",
                    "type": "custom_report",
                    "error": f"不支持的格式: {format}"
                }
            
            # 获取文件大小
            file_size_kb = filepath.stat().st_size / 1024
            self.stats["total_size_kb"] += file_size_kb
            
            return {
                "status": "success",
                "type": "custom_report",
                "filepath": str(filepath),
                "format": format,
                "template": template_name,
                "size_kb": file_size_kb,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"生成自定义报告失败: {e}")
            return {
                "status": "failed",
                "type": "custom_report",
                "error": str(e)
            }
    
    def _generate_daily_html(self, data: Dict[str, Any], report_date: datetime) -> str:
        """生成日报HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>日报 - {report_date.strftime('%Y-%m-%d')}</title>
            <style>
                body {{ 
                    font-family: 'Microsoft YaHei', Arial, sans-serif; 
                    margin: 40px;
                    background: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .section {{
                    background: white;
                    padding: 25px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #4CAF50;
                }}
                .metric-value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #333;
                }}
                .metric-label {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 15px;
                }}
                th {{
                    background: #4CAF50;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:hover {{
                    background: #f5f5f5;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 交易系统日报</h1>
                <p>{report_date.strftime('%Y年%m月%d日 %A')}</p>
            </div>
        """
        
        # 添加各个section
        for section_name, section_data in data.items():
            html += f"""
            <div class="section">
                <h2>{section_name}</h2>
            """
            
            if isinstance(section_data, dict):
                html += '<div class="metric-grid">'
                for key, value in section_data.items():
                    html += f"""
                    <div class="metric-card">
                        <div class="metric-value">{value}</div>
                        <div class="metric-label">{key}</div>
                    </div>
                    """
                html += '</div>'
            elif isinstance(section_data, list) and section_data:
                if isinstance(section_data[0], dict):
                    # 表格数据
                    html += "<table>"
                    html += "<tr>"
                    for key in section_data[0].keys():
                        html += f"<th>{key}</th>"
                    html += "</tr>"
                    for item in section_data:
                        html += "<tr>"
                        for value in item.values():
                            html += f"<td>{value}</td>"
                        html += "</tr>"
                    html += "</table>"
                else:
                    # 列表数据
                    html += "<ul>"
                    for item in section_data:
                        html += f"<li>{item}</li>"
                    html += "</ul>"
            else:
                html += f"<p>{section_data}</p>"
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_trade_html(self, trades: List[Dict[str, Any]], 
                           start_time: datetime, 
                           end_time: datetime) -> str:
        """生成交易报告HTML"""
        # 计算统计数据
        total_trades = len(trades)
        profit_trades = [t for t in trades if t.get('profit', 0) > 0]
        loss_trades = [t for t in trades if t.get('profit', 0) < 0]
        total_profit = sum(t.get('profit', 0) for t in trades)
        win_rate = len(profit_trades) / total_trades * 100 if total_trades > 0 else 0
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>交易报告</title>
            <style>
                body {{ 
                    font-family: 'Microsoft YaHei', Arial, sans-serif; 
                    margin: 40px;
                    background: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .summary {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin-bottom: 30px;
                }}
                .summary-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .profit {{ color: #4CAF50; }}
                .loss {{ color: #f44336; }}
                .trades-table {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th {{
                    background: #333;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📈 交易报告</h1>
                <p>{start_time.strftime('%Y-%m-%d %H:%M')} 至 {end_time.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="summary">
                <div class="summary-card">
                    <h3>总交易数</h3>
                    <div style="font-size: 32px; font-weight: bold;">{total_trades}</div>
                </div>
                <div class="summary-card">
                    <h3>盈利交易</h3>
                    <div class="profit" style="font-size: 32px; font-weight: bold;">{len(profit_trades)}</div>
                </div>
                <div class="summary-card">
                    <h3>亏损交易</h3>
                    <div class="loss" style="font-size: 32px; font-weight: bold;">{len(loss_trades)}</div>
                </div>
                <div class="summary-card">
                    <h3>总盈亏</h3>
                    <div class="{'profit' if total_profit >= 0 else 'loss'}" style="font-size: 32px; font-weight: bold;">
                        {total_profit:+.2f}
                    </div>
                </div>
                <div class="summary-card">
                    <h3>胜率</h3>
                    <div style="font-size: 32px; font-weight: bold;">{win_rate:.1f}%</div>
                </div>
            </div>
            
            <div class="trades-table">
                <h2>交易明细</h2>
                <table>
                    <tr>
                        <th>时间</th>
                        <th>交易对</th>
                        <th>方向</th>
                        <th>数量</th>
                        <th>价格</th>
                        <th>盈亏</th>
                        <th>状态</th>
                    </tr>
        """
        
        # 添加交易记录
        for trade in trades:
            profit = trade.get('profit', 0)
            profit_class = 'profit' if profit >= 0 else 'loss'
            html += f"""
                    <tr>
                        <td>{trade.get('time', '')}</td>
                        <td>{trade.get('symbol', '')}</td>
                        <td>{trade.get('side', '')}</td>
                        <td>{trade.get('quantity', '')}</td>
                        <td>{trade.get('price', '')}</td>
                        <td class="{profit_class}">{profit:+.2f}</td>
                        <td>{trade.get('status', '')}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_default_html(self, data: Dict[str, Any]) -> str:
        """生成默认HTML模板"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>报告</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 40px;
                    background: #f5f5f5;
                }
                .content {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                pre {
                    background: #f4f4f4;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <div class="content">
                <h1>报告数据</h1>
                <pre>{}</pre>
            </div>
        </body>
        </html>
        """.format(json.dumps(data, ensure_ascii=False, indent=2))
        
        return html
    
    def get_stats(self) -> Dict[str, Any]:
        """获取生成统计"""
        total_reports = (self.stats["daily_reports"] + 
                        self.stats["trade_reports"])
        
        return {
            "total_reports": total_reports,
            "daily_reports": self.stats["daily_reports"],
            "trade_reports": self.stats["trade_reports"],
            "pdf_exports": self.stats["pdf_exports"],
            "excel_exports": self.stats["excel_exports"],
            "failed": self.stats["failed"],
            "total_size_mb": self.stats["total_size_kb"] / 1024,
            "success_rate": total_reports / (total_reports + self.stats["failed"]) * 100 if total_reports + self.stats["failed"] > 0 else 0
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "daily_reports": 0,
            "trade_reports": 0,
            "pdf_exports": 0,
            "excel_exports": 0,
            "failed": 0,
            "total_size_kb": 0
        }
    
    def cleanup_old_reports(self, days: int = 7):
        """清理旧报告"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for filepath in self.output_dir.glob("*"):
            if filepath.is_file():
                file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                if file_time < cutoff_time:
                    filepath.unlink()
                    self.logger.info(f"删除旧报告: {filepath.name}")
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)