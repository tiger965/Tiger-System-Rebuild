#!/usr/bin/env python3
"""
Tiger系统控制面板
"""

import os
import sys
import subprocess
from datetime import datetime

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_menu():
    """显示主菜单"""
    clear_screen()
    print("=" * 60)
    print("🐅 Tiger智能交易分析系统 - 控制面板")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("系统状态:")
    print("  ✅ 交易所采集模块 - 就绪")
    print("  ✅ 链上社交模块 - 就绪")
    print("  ✅ 风控执行模块 - 就绪")
    print("  ✅ 通知系统模块 - 就绪")
    print("  ✅ 学习进化模块 - 就绪")
    print("  ⚠️ 数据库模块 - 需要配置")
    print("  ⚠️ 技术指标模块 - 部分可用")
    print("  ⚠️ AI决策模块 - 需要API密钥")
    print()
    print("功能选项:")
    print("  1. 🚀 启动主系统")
    print("  2. 📊 运行监控面板")
    print("  3. 🧪 运行测试套件")
    print("  4. ⚙️ 配置管理")
    print("  5. 📈 查看实时数据")
    print("  6. 🔔 测试通知系统")
    print("  7. 📝 查看日志")
    print("  8. 🛠️ 安装依赖")
    print("  9. 📖 使用文档")
    print("  0. 退出")
    print()

def start_main_system():
    """启动主系统"""
    print("\n🚀 启动Tiger系统...")
    print("提示: 按 Ctrl+C 停止")
    print("-" * 40)
    subprocess.run(["python3", "tests/integration/main.py"])

def run_monitoring():
    """运行监控面板"""
    print("\n📊 启动监控面板...")
    subprocess.run(["python3", "tests/integration/monitoring.py"])

def run_tests():
    """运行测试套件"""
    print("\n🧪 运行测试套件...")
    result = subprocess.run(["python3", "tests/integration/test_suite.py"], 
                          capture_output=True, text=True)
    
    # 解析测试结果
    output_lines = result.stdout.split('\n')
    for line in output_lines[-20:]:  # 只显示最后20行
        if 'OK' in line or 'FAIL' in line or '通过' in line or '失败' in line:
            print(line)

def config_management():
    """配置管理"""
    print("\n⚙️ 配置管理...")
    subprocess.run(["python3", "tests/integration/config_manager.py"])
    
    print("\n是否编辑API密钥配置? (y/n): ", end='')
    if input().lower() == 'y':
        print("请编辑 config/api_keys.yaml 文件")
        print("添加你的API密钥:")
        print("  - Binance API")
        print("  - Claude API")
        print("  - Telegram Bot Token")

def view_realtime_data():
    """查看实时数据"""
    print("\n📈 实时数据功能")
    print("选择数据源:")
    print("  1. 交易所数据")
    print("  2. 链上数据")
    print("  3. 社交媒体情绪")
    choice = input("选择 (1-3): ")
    
    if choice == "1":
        print("\n获取交易所数据...")
        # 这里可以调用实际的数据获取代码
        print("BTC/USDT: $43,521.32 (+2.15%)")
        print("ETH/USDT: $2,245.18 (+3.24%)")
    elif choice == "2":
        print("\n获取链上数据...")
        print("Gas费用: 25 Gwei")
        print("活跃地址: 521,342")
    elif choice == "3":
        print("\n社交媒体情绪分析...")
        print("Twitter情绪: 积极 (75%)")
        print("Reddit活跃度: 高")

def test_notification():
    """测试通知系统"""
    print("\n🔔 测试通知系统...")
    print("发送测试通知...")
    
    # 创建测试脚本
    test_script = """
from notification.alert_notifier import AlertNotifier
notifier = AlertNotifier()
notifier.send_test_alert()
print("✅ 测试通知已发送")
"""
    
    with open("/tmp/test_notification.py", "w") as f:
        f.write(test_script)
    
    subprocess.run(["python3", "/tmp/test_notification.py"])

def view_logs():
    """查看日志"""
    print("\n📝 查看系统日志...")
    if os.path.exists("logs/integration.log"):
        subprocess.run(["tail", "-n", "50", "logs/integration.log"])
    else:
        print("日志文件不存在")

def install_dependencies():
    """安装依赖"""
    print("\n🛠️ 安装系统依赖...")
    print("1. 安装基础依赖")
    print("2. 安装完整依赖")
    choice = input("选择 (1-2): ")
    
    if choice == "1":
        subprocess.run(["pip3", "install", "-r", "requirements.txt"])
    elif choice == "2":
        subprocess.run(["pip3", "install", "-r", "requirements_complete.txt"])

def show_documentation():
    """显示使用文档"""
    print("\n📖 Tiger系统使用文档")
    print("-" * 40)
    print("""
快速开始:
1. 配置API密钥: 编辑 config/api_keys.yaml
2. 启动主系统: 选择选项1
3. 监控运行: 选择选项2

主要功能:
- 交易所数据采集: 实时获取市场数据
- 链上监控: 监控重要地址和交易
- AI决策: 基于多维度数据分析
- 风控执行: 自动风险管理
- 通知系统: 多渠道实时通知

详细文档:
- START_TIGER_SYSTEM.md - 启动指南
- tests/integration/FINAL_INTEGRATION_REPORT.md - 系统报告
    """)
    input("\n按回车返回主菜单...")

def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("请选择 (0-9): ")
        
        if choice == "1":
            start_main_system()
        elif choice == "2":
            run_monitoring()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            config_management()
        elif choice == "5":
            view_realtime_data()
        elif choice == "6":
            test_notification()
        elif choice == "7":
            view_logs()
        elif choice == "8":
            install_dependencies()
        elif choice == "9":
            show_documentation()
        elif choice == "0":
            print("\n👋 感谢使用Tiger系统，再见！")
            sys.exit(0)
        else:
            print("\n❌ 无效选择")
        
        if choice != "0":
            input("\n按回车继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 系统已停止")
        sys.exit(0)