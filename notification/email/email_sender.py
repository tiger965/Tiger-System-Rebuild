"""
邮件发送模块
负责发送邮件通知
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

class EmailSender:
    """邮件发送器"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 username: str = None, password: str = None):
        """
        初始化邮件发送器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 用户名
            password: 密码
        """
        self.logger = logging.getLogger(__name__)
        
        # SMTP配置
        self.config = {
            "smtp_server": smtp_server or "smtp.gmail.com",
            "smtp_port": smtp_port,
            "username": username or "",
            "password": password or "",
            "use_tls": True
        }
        
        # 邮件模板
        self.templates = {
            "alert": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #ff6b6b;">⚠️ Tiger系统警报</h2>
    <div style="border-left: 4px solid #ff6b6b; padding-left: 10px;">
        <p><strong>警报类型:</strong> {alert_type}</p>
        <p><strong>警报级别:</strong> {alert_level}</p>
        <p><strong>时间:</strong> {timestamp}</p>
    </div>
    <div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <h3>{title}</h3>
        <p>{message}</p>
    </div>
    <div style="margin-top: 20px;">
        <p><strong>建议操作:</strong></p>
        <ul>{actions}</ul>
    </div>
    <hr style="border: none; border-top: 1px solid #dee2e6;">
    <p style="color: #6c757d; font-size: 12px;">
        此邮件由Tiger系统自动发送，请勿回复。
    </p>
</body>
</html>
""",
            "report": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #28a745;">📊 Tiger系统{report_type}报告</h2>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        <p><strong>报告周期:</strong> {period}</p>
        <p><strong>生成时间:</strong> {timestamp}</p>
    </div>
    
    <h3>核心指标</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background-color: #e9ecef;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>总盈亏</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{total_pnl}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>胜率</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{win_rate}</td>
        </tr>
        <tr style="background-color: #e9ecef;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>交易次数</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{total_trades}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>最大回撤</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{max_drawdown}</td>
        </tr>
    </table>
    
    <div style="margin-top: 20px;">
        <p>详细报告请查看附件。</p>
    </div>
    
    <hr style="border: none; border-top: 1px solid #dee2e6;">
    <p style="color: #6c757d; font-size: 12px;">
        Tiger系统 - 智能交易助手
    </p>
</body>
</html>
"""
        }
        
        # 统计信息
        self.stats = {
            "sent": 0,
            "failed": 0
        }
    
    def send(self, message: str, notification: Any = None) -> bool:
        """
        发送邮件（实现通知系统接口）
        
        Args:
            message: 消息内容
            notification: 通知对象
            
        Returns:
            是否成功
        """
        # 默认收件人
        to_emails = [self.config.get("default_recipient", self.config["username"])]
        subject = "Tiger系统通知"
        
        if notification and hasattr(notification, 'title'):
            subject = f"Tiger系统 - {notification.title}"
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=message,
            html_body=None
        )
    
    def send_email(self, 
                  to_emails: List[str],
                  subject: str,
                  body: str,
                  html_body: Optional[str] = None,
                  attachments: Optional[List[str]] = None,
                  cc_emails: Optional[List[str]] = None,
                  bcc_emails: Optional[List[str]] = None) -> bool:
        """
        发送邮件
        
        Args:
            to_emails: 收件人列表
            subject: 主题
            body: 纯文本内容
            html_body: HTML内容
            attachments: 附件路径列表
            cc_emails: 抄送列表
            bcc_emails: 密送列表
            
        Returns:
            是否成功
        """
        try:
            # 创建消息
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config["username"]
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 添加正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # 发送邮件
            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                if self.config["use_tls"]:
                    server.starttls()
                
                if self.config["username"] and self.config["password"]:
                    server.login(self.config["username"], self.config["password"])
                
                all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
                server.send_message(msg, to_addrs=all_recipients)
            
            self.stats["sent"] += 1
            self.logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_alert_email(self, 
                        alert_type: str,
                        alert_level: str,
                        title: str,
                        message: str,
                        actions: List[str],
                        to_emails: List[str]) -> bool:
        """发送警报邮件"""
        html_body = self.templates["alert"].format(
            alert_type=alert_type,
            alert_level=alert_level,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            title=title,
            message=message,
            actions="".join([f"<li>{action}</li>" for action in actions])
        )
        
        subject = f"[{alert_level}] {title}"
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=f"{title}\n\n{message}",
            html_body=html_body
        )
    
    def send_report_email(self,
                         report_type: str,
                         period: str,
                         metrics: Dict[str, Any],
                         to_emails: List[str],
                         attachment_path: Optional[str] = None) -> bool:
        """发送报告邮件"""
        html_body = self.templates["report"].format(
            report_type=report_type,
            period=period,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_pnl=metrics.get("total_pnl", "N/A"),
            win_rate=metrics.get("win_rate", "N/A"),
            total_trades=metrics.get("total_trades", "N/A"),
            max_drawdown=metrics.get("max_drawdown", "N/A")
        )
        
        subject = f"Tiger系统{report_type}报告 - {period}"
        
        attachments = [attachment_path] if attachment_path else None
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=f"Tiger系统{report_type}报告\n\n报告周期: {period}\n\n详情请查看附件。",
            html_body=html_body,
            attachments=attachments
        )
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """添加附件"""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"附件不存在: {file_path}")
                return
            
            with open(file_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {path.name}'
                )
                msg.attach(part)
                
        except Exception as e:
            self.logger.error(f"添加附件失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()