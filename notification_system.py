#!/usr/bin/env python3
"""
Tiger系统 - 通知推送系统
支持邮件、Telegram、钉钉、Webhook等多种通知方式
"""

import smtplib
import json
import time
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import yaml
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationSystem:
    """统一通知系统"""
    
    def __init__(self, config_file='config/notification_config.yaml'):
        """初始化通知系统"""
        self.config = self.load_config(config_file)
        self.email_client = EmailNotifier(self.config.get('email', {}))
        self.telegram_client = TelegramNotifier(self.config.get('telegram', {}))
        self.dingtalk_client = DingTalkNotifier(self.config.get('dingtalk', {}))
        self.webhook_client = WebhookNotifier(self.config.get('webhook', {}))
        
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    
    def send(self, message, priority='medium', channels=None):
        """
        发送通知
        
        Args:
            message: 消息内容
            priority: 优先级 (critical/high/medium/low)
            channels: 指定通道列表，None则使用默认
        """
        # 获取优先级配置
        priority_config = self.config.get('priority_levels', {}).get(priority, {})
        
        # 确定发送通道
        if channels is None:
            channels = priority_config.get('channels', ['email'])
        
        # 记录发送
        logger.info(f"发送{priority}级通知: {message['title']}")
        
        results = {}
        
        # 发送到各个通道
        for channel in channels:
            try:
                if channel == 'email' and self.email_client.enabled:
                    results['email'] = self.email_client.send(message)
                elif channel == 'telegram' and self.telegram_client.enabled:
                    results['telegram'] = self.telegram_client.send(message)
                elif channel == 'dingtalk' and self.dingtalk_client.enabled:
                    results['dingtalk'] = self.dingtalk_client.send(message)
                elif channel == 'webhook' and self.webhook_client.enabled:
                    results['webhook'] = self.webhook_client.send(message)
            except Exception as e:
                logger.error(f"{channel}发送失败: {e}")
                results[channel] = False
        
        return results
    
    def send_trading_signal(self, symbol, price, action, reason, priority='high'):
        """发送交易信号"""
        message = {
            'title': f'交易信号 - {symbol}',
            'type': 'signal',
            'data': {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'price': price,
                'action': action,
                'reason': reason,
                'signal_type': '买入' if action == 'BUY' else '卖出'
            }
        }
        return self.send(message, priority)
    
    def send_alert(self, alert_type, level, detail, suggestion='', priority='high'):
        """发送警报"""
        message = {
            'title': f'系统警报 - {alert_type}',
            'type': 'alert',
            'data': {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'alert_type': alert_type,
                'level': level,
                'detail': detail,
                'suggestion': suggestion
            }
        }
        return self.send(message, priority)
    
    def send_report(self, report_type, content, priority='low'):
        """发送报告"""
        message = {
            'title': f'系统报告 - {report_type}',
            'type': 'report',
            'data': {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'report_type': report_type,
                'content': content
            }
        }
        return self.send(message, priority)


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config):
        """初始化邮件通知器"""
        self.config = config
        self.enabled = config.get('enabled', False)
        
        # Gmail配置（已配置好）
        self.smtp_config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'username': 'a368070666@gmail.com',
            'password': '',  # 需要应用专用密码
            'sender_name': 'Tiger系统通知',
            'sender_address': 'a368070666@gmail.com'
        }
        
        # 收件人
        self.recipients = {
            'default': ['a368070666@gmail.com'],  # 自己给自己发
            'critical': ['a368070666@gmail.com'],
            'report': ['a368070666@gmail.com']
        }
        
    def send(self, message):
        """发送邮件"""
        if not self.enabled:
            logger.warning("邮件通知未启用")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f"{self.smtp_config['sender_name']} <{self.smtp_config['sender_address']}>"
            msg['To'] = ', '.join(self.recipients['default'])
            msg['Subject'] = message['title']
            
            # 构建邮件内容
            body = self.format_message(message)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                
                # 登录
                if self.smtp_config.get('password'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                # 发送
                server.send_message(msg)
                
            logger.info(f"邮件发送成功: {message['title']}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def format_message(self, message):
        """格式化邮件内容"""
        msg_type = message.get('type', 'default')
        data = message.get('data', {})
        
        if msg_type == 'signal':
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2e7d32;">🚀 交易信号</h2>
                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>时间</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('time')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>币种</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('symbol')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>价格</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">${data.get('price')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>操作</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b style="color: {'green' if data.get('action') == 'BUY' else 'red'};">{data.get('action')}</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>原因</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('reason')}</td>
                    </tr>
                </table>
                <hr style="margin-top: 20px;">
                <p style="color: #666; font-size: 12px;">Tiger智能交易系统 - 自动生成</p>
            </body>
            </html>
            """
        
        elif msg_type == 'alert':
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">⚠️ 系统警报</h2>
                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>时间</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('time')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>类型</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('alert_type')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>级别</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b style="color: red;">{data.get('level')}</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>详情</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('detail')}</td>
                    </tr>
                    {f'''<tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>建议</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data.get('suggestion')}</td>
                    </tr>''' if data.get('suggestion') else ''}
                </table>
                <hr style="margin-top: 20px;">
                <p style="color: #666; font-size: 12px;">Tiger智能交易系统 - 自动生成</p>
            </body>
            </html>
            """
        
        else:
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>📊 {message['title']}</h2>
                <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
                    <pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
                </div>
                <hr style="margin-top: 20px;">
                <p style="color: #666; font-size: 12px;">Tiger智能交易系统 - 自动生成</p>
            </body>
            </html>
            """
        
        return html


class TelegramNotifier:
    """Telegram通知器"""
    
    def __init__(self, config):
        """初始化Telegram通知器"""
        self.config = config
        self.enabled = config.get('enabled', False)
        self.bot_token = config.get('bot', {}).get('token', '')
        self.chat_ids = {
            'default': config.get('channels', {}).get('default', {}).get('chat_id', ''),
            'signals': config.get('channels', {}).get('signals', {}).get('chat_id', ''),
            'alerts': config.get('channels', {}).get('alerts', {}).get('chat_id', '')
        }
        
    def send(self, message, chat_id=None):
        """发送Telegram消息"""
        if not self.enabled or not self.bot_token:
            logger.warning("Telegram通知未启用或未配置")
            return False
        
        try:
            # 确定发送目标
            if chat_id is None:
                msg_type = message.get('type', 'default')
                chat_id = self.chat_ids.get(msg_type, self.chat_ids['default'])
            
            if not chat_id:
                logger.warning("Telegram chat_id未配置")
                return False
            
            # 构建消息
            text = self.format_message(message)
            
            # 发送请求
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_notification': False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram发送成功: {message['title']}")
                return True
            else:
                logger.error(f"Telegram发送失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram发送异常: {e}")
            return False
    
    def format_message(self, message):
        """格式化Telegram消息"""
        msg_type = message.get('type', 'default')
        data = message.get('data', {})
        
        if msg_type == 'signal':
            text = f"""
🚀 *交易信号*
⏰ 时间: `{data.get('time')}`
💰 币种: *{data.get('symbol')}*
💵 价格: `${data.get('price')}`
📊 操作: *{data.get('action')}*
📝 原因: {data.get('reason')}
"""
        elif msg_type == 'alert':
            text = f"""
⚠️ *系统警报*
⏰ 时间: `{data.get('time')}`
🔴 类型: *{data.get('alert_type')}*
📊 级别: {data.get('level')}
📝 详情: {data.get('detail')}
"""
            if data.get('suggestion'):
                text += f"💡 建议: {data.get('suggestion')}\n"
        else:
            text = f"*{message['title']}*\n"
            text += "```\n"
            text += json.dumps(data, indent=2, ensure_ascii=False)
            text += "\n```"
        
        return text


class DingTalkNotifier:
    """钉钉通知器"""
    
    def __init__(self, config):
        """初始化钉钉通知器"""
        self.config = config
        self.enabled = config.get('enabled', False)
        self.webhooks = config.get('robots', {})
        
    def send(self, message, robot='default'):
        """发送钉钉消息"""
        if not self.enabled:
            logger.warning("钉钉通知未启用")
            return False
        
        webhook_config = self.webhooks.get(robot, {})
        webhook_url = webhook_config.get('webhook', '')
        
        if not webhook_url:
            logger.warning("钉钉Webhook未配置")
            return False
        
        try:
            # 构建消息
            payload = self.format_message(message)
            
            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info(f"钉钉发送成功: {message['title']}")
                    return True
                else:
                    logger.error(f"钉钉发送失败: {result}")
                    return False
            else:
                logger.error(f"钉钉请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"钉钉发送异常: {e}")
            return False
    
    def format_message(self, message):
        """格式化钉钉消息"""
        msg_type = message.get('type', 'default')
        data = message.get('data', {})
        
        title = message['title']
        
        if msg_type == 'signal':
            text = f"""## {title}
- 时间: {data.get('time')}
- 币种: **{data.get('symbol')}**
- 价格: ${data.get('price')}
- 操作: **{data.get('action')}**
- 原因: {data.get('reason')}"""
        
        elif msg_type == 'alert':
            text = f"""## ⚠️ {title}
- 时间: {data.get('time')}
- 类型: **{data.get('alert_type')}**
- 级别: {data.get('level')}
- 详情: {data.get('detail')}"""
            if data.get('suggestion'):
                text += f"\n- 建议: {data.get('suggestion')}"
        
        else:
            text = f"## {title}\n"
            text += json.dumps(data, indent=2, ensure_ascii=False)
        
        return {
            'msgtype': 'markdown',
            'markdown': {
                'title': title,
                'text': text
            }
        }


class WebhookNotifier:
    """Webhook通知器"""
    
    def __init__(self, config):
        """初始化Webhook通知器"""
        self.config = config
        self.enabled = config.get('enabled', False)
        self.endpoints = config.get('endpoints', {})
        
    def send(self, message, endpoint='default'):
        """发送Webhook通知"""
        if not self.enabled:
            logger.warning("Webhook通知未启用")
            return False
        
        endpoint_config = self.endpoints.get(endpoint, {})
        url = endpoint_config.get('url', '')
        
        if not url:
            logger.warning("Webhook URL未配置")
            return False
        
        try:
            # 构建负载
            payload = {
                'timestamp': datetime.now().isoformat(),
                'type': message.get('type', 'default'),
                'title': message['title'],
                'data': message.get('data', {})
            }
            
            # 请求配置
            method = endpoint_config.get('method', 'POST')
            headers = endpoint_config.get('headers', {'Content-Type': 'application/json'})
            timeout = endpoint_config.get('timeout', 30)
            
            # 发送请求
            if method.upper() == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            else:
                response = requests.get(url, params=payload, headers=headers, timeout=timeout)
            
            if response.status_code in [200, 201, 202, 204]:
                logger.info(f"Webhook发送成功: {message['title']}")
                return True
            else:
                logger.error(f"Webhook发送失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook发送异常: {e}")
            return False


# 测试函数
def test_notification():
    """测试通知系统"""
    print("="*60)
    print("Tiger系统 - 通知测试")
    print("="*60)
    
    # 创建通知系统
    notifier = NotificationSystem()
    
    # 测试交易信号
    print("\n1. 测试交易信号通知...")
    result = notifier.send_trading_signal(
        symbol='BTC/USDT',
        price=120000,
        action='BUY',
        reason='突破关键阻力位，MACD金叉',
        priority='high'
    )
    print(f"   结果: {result}")
    
    # 测试警报
    print("\n2. 测试系统警报...")
    result = notifier.send_alert(
        alert_type='价格异动',
        level='HIGH',
        detail='BTC 5分钟内上涨5%',
        suggestion='关注市场动向，考虑加仓',
        priority='high'
    )
    print(f"   结果: {result}")
    
    # 测试报告
    print("\n3. 测试系统报告...")
    result = notifier.send_report(
        report_type='日报',
        content='今日收益: +5.2%\n交易次数: 12\n成功率: 75%',
        priority='low'
    )
    print(f"   结果: {result}")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_notification()