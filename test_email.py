#!/usr/bin/env python3
"""
测试邮件发送功能
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_simple_email():
    """测试基本邮件发送"""
    
    # Gmail配置
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "a368070666@gmail.com"
    sender_name = "Tiger系统"
    receiver_email = "a368070666@gmail.com"
    
    # 需要填入应用专用密码
    password = ""  # 在这里填入16位应用密码
    
    if not password:
        print("❌ 请先设置Gmail应用专用密码!")
        print("参考 GMAIL_SETUP.md 获取应用专用密码")
        print("\n获取步骤：")
        print("1. 访问 https://myaccount.google.com/")
        print("2. 进入'安全性' -> '两步验证'")
        print("3. 生成'应用专用密码'")
        print("4. 将16位密码填入此文件的password变量")
        return False
    
    try:
        # 创建邮件
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Tiger系统测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = receiver_email
        
        # HTML内容
        html = """
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 2px solid #4CAF50; border-radius: 10px; padding: 20px;">
              <h1 style="color: #4CAF50; text-align: center;">🐅 Tiger系统邮件测试</h1>
              
              <p style="font-size: 16px;">恭喜！邮件通知功能配置成功！</p>
              
              <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #333;">✅ 测试结果</h3>
                <ul style="line-height: 1.8;">
                  <li>SMTP连接: <span style="color: green;">成功</span></li>
                  <li>身份验证: <span style="color: green;">成功</span></li>
                  <li>邮件发送: <span style="color: green;">成功</span></li>
                </ul>
              </div>
              
              <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #2e7d32;">📊 系统信息</h3>
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>发送时间</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">""" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>发件邮箱</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">""" + sender_email + """</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>收件邮箱</b></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">""" + receiver_email + """</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px;"><b>SMTP服务器</b></td>
                    <td style="padding: 8px;">""" + f"{smtp_host}:{smtp_port}" + """</td>
                  </tr>
                </table>
              </div>
              
              <div style="background: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #f57c00;">🚀 下一步</h3>
                <p>您可以开始使用Tiger系统的通知功能了！系统将自动发送：</p>
                <ul>
                  <li>交易信号通知</li>
                  <li>风险预警提醒</li>
                  <li>系统状态报告</li>
                  <li>收益统计日报</li>
                </ul>
              </div>
              
              <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
              
              <p style="text-align: center; color: #666; font-size: 12px;">
                Tiger智能交易系统 v10.2<br>
                10号窗口 - 系统集成
              </p>
            </div>
          </body>
        </html>
        """
        
        # 添加HTML内容
        part = MIMEText(html, "html")
        message.attach(part)
        
        # 连接并发送
        print(f"正在连接 {smtp_host}:{smtp_port}...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()  # 启用TLS
        
        print(f"正在登录 {sender_email}...")
        server.login(sender_email, password)
        
        print(f"正在发送邮件到 {receiver_email}...")
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        
        print("✅ 邮件发送成功！")
        print(f"   收件人: {receiver_email}")
        print(f"   主题: {message['Subject']}")
        print("\n请检查您的邮箱（包括垃圾邮件文件夹）")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ 认证失败！")
        print("   可能原因：")
        print("   1. 密码错误（需要使用应用专用密码，不是账户密码）")
        print("   2. 两步验证未启用")
        print("   3. 应用专用密码已过期")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP错误: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False


def test_notification_system():
    """测试完整的通知系统"""
    try:
        from notification_system import NotificationSystem
        
        print("\n" + "="*60)
        print("测试完整通知系统")
        print("="*60)
        
        notifier = NotificationSystem()
        
        # 测试不同类型的通知
        tests = [
            {
                'name': '交易信号',
                'func': lambda: notifier.send_trading_signal(
                    'BTC/USDT', 120500, 'BUY', 
                    'MACD金叉，RSI超卖反弹', 'high'
                )
            },
            {
                'name': '风险警报',
                'func': lambda: notifier.send_alert(
                    '价格异动', 'HIGH',
                    'BTC 5分钟内下跌3%',
                    '建议检查止损设置', 'high'
                )
            },
            {
                'name': '系统报告',
                'func': lambda: notifier.send_report(
                    '测试报告',
                    '系统运行正常\n所有模块工作正常\n通知功能测试成功',
                    'low'
                )
            }
        ]
        
        for test in tests:
            print(f"\n测试: {test['name']}")
            result = test['func']()
            if result.get('email'):
                print(f"  ✅ 发送成功")
            else:
                print(f"  ❌ 发送失败")
        
        print("\n" + "="*60)
        print("测试完成！")
        
    except ImportError:
        print("❌ 无法导入notification_system模块")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    print("="*60)
    print("Tiger系统 - 邮件通知测试")
    print("="*60)
    
    # 先测试基本邮件功能
    print("\n1. 测试基本邮件发送...")
    print("-"*40)
    
    if test_simple_email():
        # 如果基本测试成功，测试完整系统
        print("\n2. 测试完整通知系统...")
        print("-"*40)
        test_notification_system()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)