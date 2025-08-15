#!/usr/bin/env python3
"""
邮件通知配置助手
帮助用户设置Gmail应用专用密码
"""

import os
import sys
import getpass
import json

def setup_email_password():
    """配置邮件密码"""
    print("="*60)
    print("Tiger系统 - 邮件配置助手")
    print("="*60)
    print()
    print("📧 配置Gmail邮件通知")
    print("-"*40)
    print()
    print("您需要获取Gmail应用专用密码（不是账户密码）")
    print()
    print("获取步骤：")
    print("1. 访问 https://myaccount.google.com/")
    print("2. 登录账号: a368070666@gmail.com")
    print("3. 进入【安全性】设置")
    print("4. 启用【两步验证】（如果还没启用）")
    print("5. 在两步验证下方找到【应用专用密码】")
    print("6. 生成新的应用专用密码")
    print("   - 选择应用: 邮件")
    print("   - 选择设备: 其他（输入'Tiger系统'）")
    print("7. 复制生成的16位密码")
    print()
    print("-"*40)
    
    # 询问是否已获取密码
    ready = input("\n您是否已获取应用专用密码？(y/n): ").strip().lower()
    
    if ready != 'y':
        print("\n请先按照上述步骤获取密码，然后重新运行此脚本")
        print("提示：密码只显示一次，请务必复制保存")
        return False
    
    # 输入密码
    print("\n请输入16位应用专用密码")
    print("（密码可以包含空格，例如: abcd efgh ijkl mnop）")
    password = getpass.getpass("密码: ").strip()
    
    # 去除空格（Gmail接受带空格或不带空格的密码）
    password_clean = password.replace(" ", "")
    
    # 验证密码长度
    if len(password_clean) != 16:
        print(f"\n❌ 密码长度不正确（当前{len(password_clean)}位，应该16位）")
        return False
    
    # 确认
    print(f"\n您输入的密码: {'*' * 4} {'*' * 4} {'*' * 4} {'*' * 4}")
    confirm = input("确认保存此密码？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("已取消")
        return False
    
    # 保存到配置文件
    config_file = 'config/email_password.json'
    os.makedirs('config', exist_ok=True)
    
    config = {
        'gmail': {
            'username': 'a368070666@gmail.com',
            'password': password_clean,
            'configured_at': datetime.now().isoformat()
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # 设置文件权限（仅用户可读写）
    os.chmod(config_file, 0o600)
    
    print(f"\n✅ 密码已保存到: {config_file}")
    print("   （文件权限已设置为仅用户可访问）")
    
    # 更新notification_system.py
    update_notification_system(password_clean)
    
    # 提示测试
    print("\n" + "="*60)
    print("配置完成！")
    print("="*60)
    print("\n现在可以测试邮件功能：")
    print("  python3 test_email.py")
    print("\n或使用通知系统：")
    print("  python3 notification_system.py")
    
    return True


def update_notification_system(password):
    """更新notification_system.py中的密码"""
    try:
        # 读取文件
        with open('notification_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换密码
        old_line = "'password': '',  # 需要应用专用密码"
        new_line = f"'password': '{password}',  # 已配置"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            # 写回文件
            with open('notification_system.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已更新 notification_system.py")
        else:
            print("⚠️ notification_system.py 已有密码配置")
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")


def load_password():
    """加载已保存的密码"""
    config_file = 'config/email_password.json'
    
    if not os.path.exists(config_file):
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('gmail', {}).get('password')
    except:
        return None


def check_current_config():
    """检查当前配置状态"""
    print("\n当前配置状态：")
    print("-"*40)
    
    # 检查密码文件
    password = load_password()
    if password:
        print(f"✅ 密码已配置: {'*' * 4} {'*' * 4} {'*' * 4} {'*' * 4}")
    else:
        print("❌ 密码未配置")
    
    # 检查配置文件
    if os.path.exists('config/notification_config.yaml'):
        print("✅ 通知配置文件存在")
    else:
        print("❌ 通知配置文件不存在")
    
    # 检查通知系统
    if os.path.exists('notification_system.py'):
        print("✅ 通知系统已创建")
    else:
        print("❌ 通知系统未创建")
    
    print()
    return password is not None


if __name__ == "__main__":
    from datetime import datetime
    
    # 检查当前状态
    configured = check_current_config()
    
    if configured:
        print("系统已配置，是否重新配置？")
        reconfigure = input("(y/n): ").strip().lower()
        if reconfigure != 'y':
            print("已取消")
            sys.exit(0)
    
    # 运行配置
    if setup_email_password():
        print("\n✅ 配置成功！")
    else:
        print("\n❌ 配置失败或已取消")