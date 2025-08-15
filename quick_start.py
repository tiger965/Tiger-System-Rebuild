#!/usr/bin/env python3
"""
Tiger系统快速启动脚本
"""

import os
import sys
import time
from datetime import datetime

print("=" * 60)
print("🐅 Tiger智能交易分析系统")
print("=" * 60)
print(f"启动时间: {datetime.now()}")
print()

# 检查可用模块
modules = {
    "配置管理": "tests/integration/config_manager.py",
    "监控系统": "tests/integration/monitoring.py", 
    "交易所采集": "collectors/exchange/main_collector.py",
    "风控系统": "risk/alert_executor.py",
    "通知系统": "notification/alert_notifier.py",
    "技术指标": "analysis/test_all_indicators.py"
}

print("可用模块:")
available = []
for name, path in modules.items():
    if os.path.exists(path):
        print(f"  ✅ {name}")
        available.append((name, path))
    else:
        print(f"  ❌ {name}")

print()
print("请选择要启动的功能:")
print("1. 运行测试套件")
print("2. 启动监控系统")
print("3. 查看配置")
print("4. 运行主系统")
print("5. 退出")
print()

choice = input("请输入选择 (1-5): ")

if choice == "1":
    print("\n运行测试套件...")
    os.system("python3 tests/integration/test_suite.py")
    
elif choice == "2":
    print("\n启动监控系统...")
    os.system("python3 tests/integration/monitoring.py")
    
elif choice == "3":
    print("\n查看系统配置...")
    os.system("python3 tests/integration/config_manager.py")
    
elif choice == "4":
    print("\n启动主系统...")
    print("提示: 按 Ctrl+C 停止")
    time.sleep(2)
    os.system("python3 tests/integration/main.py")
    
elif choice == "5":
    print("退出系统")
    sys.exit(0)
    
else:
    print("无效选择")

print("\n✅ 操作完成")