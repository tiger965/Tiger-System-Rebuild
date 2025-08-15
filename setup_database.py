#!/usr/bin/env python3
"""
Tiger系统 - 数据库配置向导
"""

import os
import yaml
import json
from pathlib import Path

def setup_database():
    """配置数据库"""
    print("=" * 60)
    print("🗄️ Tiger系统 - 数据库配置向导")
    print("=" * 60)
    print()
    
    print("请选择数据库类型:")
    print("1. SQLite (最简单，无需安装)")
    print("2. MySQL (推荐用于生产)")
    print("3. PostgreSQL (高性能)")
    print()
    
    choice = input("请选择 (1-3) [默认: 1]: ") or "1"
    
    config = {}
    
    if choice == "1":
        # SQLite配置
        print("\n✅ 使用SQLite数据库")
        config = {
            "type": "sqlite",
            "database": "data/tiger_system.db",
            "echo": False,
            "pool_size": 5,
            "max_overflow": 10
        }
        
        # 创建data目录
        os.makedirs("data", exist_ok=True)
        print("数据库文件将保存在: data/tiger_system.db")
        
    elif choice == "2":
        # MySQL配置
        print("\n配置MySQL数据库")
        print("请输入以下信息 (直接回车使用默认值):")
        
        config = {
            "type": "mysql",
            "host": input("  主机 [localhost]: ") or "localhost",
            "port": int(input("  端口 [3306]: ") or "3306"),
            "database": input("  数据库名 [tiger_system]: ") or "tiger_system",
            "username": input("  用户名 [root]: ") or "root",
            "password": input("  密码: "),
            "echo": False,
            "pool_size": 10,
            "max_overflow": 20
        }
        
        # 创建数据库
        print("\n是否自动创建数据库? (y/n): ", end='')
        if input().lower() == 'y':
            create_mysql_database(config)
            
    elif choice == "3":
        # PostgreSQL配置
        print("\n配置PostgreSQL数据库")
        print("请输入以下信息 (直接回车使用默认值):")
        
        config = {
            "type": "postgresql",
            "host": input("  主机 [localhost]: ") or "localhost",
            "port": int(input("  端口 [5432]: ") or "5432"),
            "database": input("  数据库名 [tiger_system]: ") or "tiger_system",
            "username": input("  用户名 [postgres]: ") or "postgres",
            "password": input("  密码: "),
            "echo": False,
            "pool_size": 10,
            "max_overflow": 20
        }
    
    # 保存配置
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "database.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"\n✅ 数据库配置已保存到: {config_file}")
    
    # 测试连接
    print("\n测试数据库连接...")
    if test_connection(config):
        print("✅ 数据库连接成功！")
        
        # 初始化数据库表
        print("\n是否初始化数据库表? (y/n): ", end='')
        if input().lower() == 'y':
            init_database_tables(config)
    else:
        print("❌ 数据库连接失败，请检查配置")
    
    return config

def create_mysql_database(config):
    """创建MySQL数据库"""
    try:
        import pymysql
        
        # 连接MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['username'],
            password=config['password']
        )
        
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} "
                      f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print(f"✅ 数据库 {config['database']} 创建成功")
        
        cursor.close()
        conn.close()
        
    except ImportError:
        print("⚠️ 需要安装pymysql: pip3 install pymysql")
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")

def test_connection(config):
    """测试数据库连接"""
    try:
        if config['type'] == 'sqlite':
            import sqlite3
            conn = sqlite3.connect(config['database'])
            conn.execute("SELECT 1")
            conn.close()
            return True
            
        elif config['type'] == 'mysql':
            import pymysql
            conn = pymysql.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['username'],
                password=config['password']
            )
            conn.close()
            return True
            
        elif config['type'] == 'postgresql':
            import psycopg2
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['username'],
                password=config['password']
            )
            conn.close()
            return True
            
    except ImportError as e:
        print(f"⚠️ 缺少数据库驱动: {e}")
        if 'pymysql' in str(e):
            print("  安装: pip3 install pymysql")
        elif 'psycopg2' in str(e):
            print("  安装: pip3 install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def init_database_tables(config):
    """初始化数据库表"""
    print("\n初始化数据库表...")
    
    # 运行数据库初始化脚本
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "database/init_database.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 数据库表初始化成功")
        else:
            print(f"⚠️ 初始化警告: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        
    # 显示创建的表
    print("\n创建的数据库表:")
    tables = [
        "market_data - 市场数据",
        "trading_signals - 交易信号",
        "risk_alerts - 风险警报",
        "opportunities - 交易机会",
        "system_logs - 系统日志",
        "learning_records - 学习记录"
    ]
    
    for table in tables:
        print(f"  ✅ {table}")

def show_current_config():
    """显示当前配置"""
    config_file = Path("config/database.yaml")
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print("\n当前数据库配置:")
        print("-" * 40)
        for key, value in config.items():
            if key == 'password':
                value = '***' if value else '(未设置)'
            print(f"  {key}: {value}")
    else:
        print("\n❌ 还没有数据库配置")

def main():
    """主函数"""
    print("选择操作:")
    print("1. 配置新数据库")
    print("2. 查看当前配置")
    print("3. 测试数据库连接")
    print("4. 初始化数据库表")
    print()
    
    choice = input("请选择 (1-4): ")
    
    if choice == "1":
        setup_database()
        
    elif choice == "2":
        show_current_config()
        
    elif choice == "3":
        config_file = Path("config/database.yaml")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            if test_connection(config):
                print("✅ 数据库连接成功")
            else:
                print("❌ 数据库连接失败")
        else:
            print("❌ 请先配置数据库")
            
    elif choice == "4":
        config_file = Path("config/database.yaml")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            init_database_tables(config)
        else:
            print("❌ 请先配置数据库")

if __name__ == "__main__":
    main()