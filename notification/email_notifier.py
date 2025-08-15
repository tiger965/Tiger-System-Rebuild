"""
邮件纯通知执行工具 - Window 8
只负责执行发送，不做任何判断
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor


class EmailNotifier:
    """邮件发送工具 - 纯执行"""
    
    def __init__(self, 
                 smtp_server: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 use_tls: bool = True):
        """
        初始化邮件通知器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 邮箱用户名
            password: 邮箱密码
            use_tls: 是否使用TLS加密
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.logger = logging.getLogger(__name__)
        
        # 执行统计
        self.stats = {
            "emails_sent": 0,
            "html_emails_sent": 0,
            "attachments_sent": 0,
            "failed": 0,
            "total_time_ms": 0
        }
        
        # 线程池执行器（邮件发送是同步操作）
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _send_email_sync(self,
                        to: str,
                        subject: str,
                        body: str,
                        html_body: Optional[str] = None,
                        attachments: Optional[List[str]] = None,
                        cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步发送邮件的内部方法
        """
        start_time = datetime.now()
        
        try:
            # 创建邮件对象
            if html_body:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            elif attachments:
                msg = MIMEMultipart()
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            else:
                msg = MIMEText(body, 'plain', 'utf-8')
            
            # 设置邮件头
            msg['From'] = self.username
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    path = Path(file_path)
                    if path.exists():
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {path.name}'
                            )
                            msg.attach(part)
                            self.stats["attachments_sent"] += 1
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                
                # 收件人列表
                recipients = [to]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.send_message(msg, from_addr=self.username, to_addrs=recipients)
            
            # 更新统计
            if html_body:
                self.stats["html_emails_sent"] += 1
            else:
                self.stats["emails_sent"] += 1
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.stats["total_time_ms"] += elapsed_ms
            
            return {
                "status": "success",
                "channel": "email",
                "type": "html" if html_body else "plain",
                "sent_at": datetime.now().isoformat(),
                "elapsed_ms": elapsed_ms,
                "recipients": recipients
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"发送邮件失败: {e}")
            return {
                "status": "failed",
                "channel": "email",
                "error": str(e),
                "sent_at": datetime.now().isoformat()
            }
    
    async def send_email(self,
                        to: str,
                        subject: str,
                        body: str,
                        cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None,
                        attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        发送普通文本邮件
        
        Args:
            to: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            cc: 抄送列表
            bcc: 密送列表
            attachments: 附件路径列表
            
        Returns:
            发送结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to, subject, body, None, attachments, cc, bcc
        )
    
    async def send_html_email(self,
                             to: str,
                             subject: str,
                             html: str,
                             plain_text: Optional[str] = None,
                             cc: Optional[List[str]] = None,
                             bcc: Optional[List[str]] = None,
                             attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        发送HTML格式邮件
        
        Args:
            to: 收件人邮箱
            subject: 邮件主题
            html: HTML格式正文
            plain_text: 纯文本备用正文
            cc: 抄送列表
            bcc: 密送列表
            attachments: 附件路径列表
            
        Returns:
            发送结果
        """
        # 如果没有提供纯文本版本，生成一个简单的
        if not plain_text:
            plain_text = "此邮件包含HTML内容，请使用支持HTML的邮件客户端查看。"
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to, subject, plain_text, html, attachments, cc, bcc
        )
    
    async def send_batch(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量发送邮件
        
        Args:
            emails: 邮件列表，每个邮件包含to, subject, body等字段
            
        Returns:
            发送结果列表
        """
        tasks = []
        
        for email in emails:
            if email.get("html"):
                task = self.send_html_email(
                    email.get("to"),
                    email.get("subject", "No Subject"),
                    email.get("html"),
                    email.get("plain_text"),
                    email.get("cc"),
                    email.get("bcc"),
                    email.get("attachments")
                )
            else:
                task = self.send_email(
                    email.get("to"),
                    email.get("subject", "No Subject"),
                    email.get("body", ""),
                    email.get("cc"),
                    email.get("bcc"),
                    email.get("attachments")
                )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "status": "failed",
                    "channel": "email",
                    "error": str(result),
                    "email_index": i
                })
            else:
                final_results.append(result)
        
        return final_results
    
    async def send_report(self,
                         to: str,
                         report_type: str,
                         report_data: Dict[str, Any],
                         template: Optional[str] = None) -> Dict[str, Any]:
        """
        发送格式化报告邮件
        
        Args:
            to: 收件人
            report_type: 报告类型
            report_data: 报告数据
            template: HTML模板（可选）
            
        Returns:
            发送结果
        """
        # 生成报告标题
        subject = f"【{report_type}】{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 生成HTML内容
        if template:
            html_content = template.format(**report_data)
        else:
            # 默认模板
            html_content = self._generate_default_report_html(report_type, report_data)
        
        # 生成纯文本版本
        plain_text = self._generate_plain_text_report(report_type, report_data)
        
        return await self.send_html_email(
            to=to,
            subject=subject,
            html=html_content,
            plain_text=plain_text
        )
    
    def _generate_default_report_html(self, report_type: str, data: Dict[str, Any]) -> str:
        """生成默认的HTML报告模板"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .metric-label {{ font-weight: bold; color: #666; }}
                .metric-value {{ font-size: 24px; color: #333; }}
            </style>
        </head>
        <body>
            <h1>{report_type}</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # 添加数据内容
        for key, value in data.items():
            if isinstance(value, dict):
                html += f"<h2>{key}</h2>"
                html += "<table>"
                html += "<tr>"
                for k in value.keys():
                    html += f"<th>{k}</th>"
                html += "</tr><tr>"
                for v in value.values():
                    html += f"<td>{v}</td>"
                html += "</tr></table>"
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                html += f"<h2>{key}</h2>"
                html += "<table>"
                # 表头
                html += "<tr>"
                for k in value[0].keys():
                    html += f"<th>{k}</th>"
                html += "</tr>"
                # 数据行
                for item in value:
                    html += "<tr>"
                    for v in item.values():
                        html += f"<td>{v}</td>"
                    html += "</tr>"
                html += "</table>"
            else:
                html += f"""
                <div class="metric">
                    <span class="metric-label">{key}:</span>
                    <span class="metric-value">{value}</span>
                </div>
                """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_plain_text_report(self, report_type: str, data: Dict[str, Any]) -> str:
        """生成纯文本报告"""
        text = f"{report_type}\n"
        text += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += "=" * 50 + "\n\n"
        
        for key, value in data.items():
            text += f"{key}: {value}\n"
        
        return text
    
    def get_stats(self) -> Dict[str, Any]:
        """获取发送统计"""
        total_sent = self.stats["emails_sent"] + self.stats["html_emails_sent"]
        
        avg_time_ms = 0
        if total_sent > 0:
            avg_time_ms = self.stats["total_time_ms"] / total_sent
        
        return {
            "total_sent": total_sent,
            "plain_emails": self.stats["emails_sent"],
            "html_emails": self.stats["html_emails_sent"],
            "attachments": self.stats["attachments_sent"],
            "failed": self.stats["failed"],
            "average_time_ms": avg_time_ms,
            "success_rate": total_sent / (total_sent + self.stats["failed"]) * 100 if total_sent + self.stats["failed"] > 0 else 0
        }
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "emails_sent": 0,
            "html_emails_sent": 0,
            "attachments_sent": 0,
            "failed": 0,
            "total_time_ms": 0
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)