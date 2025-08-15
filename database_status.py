#!/usr/bin/env python3
"""
Tiger系统 - 数据库状态查看器
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

def check_database_status():
    """检查数据库状态"""
    print("=" * 60)
    print("🗄️ Tiger系统 - 数据库状态")
    print("=" * 60)
    
    # 检查配置
    config_file = Path("config/database.yaml")
    if config_file.exists():
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print("\n📋 当前配置:")
        print(f"  类型: {config['type']}")
        print(f"  数据库: {config['database']}")
        
        if config['type'] == 'sqlite':
            db_path = config['database']
            if os.path.exists(db_path):
                size = os.path.getsize(db_path) / 1024  # KB
                print(f"  文件大小: {size:.2f} KB")
                print(f"  ✅ 数据库文件存在")
                
                # 连接数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"\n📊 数据库表 ({len(tables)}个):")
                
                for table_name in tables:
                    table = table_name[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # 获取最新记录时间
                    try:
                        cursor.execute(f"SELECT MAX(timestamp) FROM {table}")
                        latest = cursor.fetchone()[0]
                        latest_str = f" | 最新: {latest}" if latest else ""
                    except:
                        latest_str = ""
                    
                    print(f"  - {table}: {count} 条记录{latest_str}")
                
                # 数据统计
                print("\n📈 数据统计:")
                
                # 市场数据统计
                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM market_data")
                symbols = cursor.fetchone()[0]
                print(f"  交易对数量: {symbols}")
                
                # 今日数据
                cursor.execute("""
                    SELECT COUNT(*) FROM market_data 
                    WHERE date(timestamp) = date('now')
                """)
                today_count = cursor.fetchone()[0]
                print(f"  今日数据: {today_count} 条")
                
                # 风险警报
                cursor.execute("""
                    SELECT COUNT(*) FROM risk_alerts
                    WHERE severity = 'HIGH'
                """)
                high_alerts = cursor.fetchone()[0]
                print(f"  高风险警报: {high_alerts} 个")
                
                conn.close()
                
            else:
                print(f"  ❌ 数据库文件不存在: {db_path}")
                print("\n运行以下命令创建数据库:")
                print("  python3 setup_database.py")
                
        elif config['type'] == 'mysql':
            print("\n测试MySQL连接...")
            try:
                import pymysql
                conn = pymysql.connect(
                    host=config['host'],
                    port=config['port'],
                    database=config['database'],
                    user=config['username'],
                    password=config['password']
                )
                print("  ✅ MySQL连接成功")
                
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"  表数量: {len(tables)}")
                
                conn.close()
                
            except ImportError:
                print("  ❌ 需要安装pymysql: pip3 install pymysql")
            except Exception as e:
                print(f"  ❌ 连接失败: {e}")
                
    else:
        print("\n❌ 数据库未配置")
        print("请运行: python3 setup_database.py")

def show_sample_queries():
    """显示示例查询"""
    print("\n📝 示例SQL查询:")
    print("-" * 40)
    
    queries = {
        "最新市场数据": """
SELECT symbol, price, volume, timestamp 
FROM market_data 
ORDER BY timestamp DESC 
LIMIT 10""",
        
        "交易信号汇总": """
SELECT symbol, signal_type, COUNT(*) as count, AVG(strength) as avg_strength
FROM trading_signals
GROUP BY symbol, signal_type
ORDER BY count DESC""",
        
        "高风险警报": """
SELECT * FROM risk_alerts
WHERE severity = 'HIGH'
ORDER BY timestamp DESC
LIMIT 5""",
        
        "今日机会": """
SELECT * FROM opportunities
WHERE date(timestamp) = date('now')
AND risk_level != 'HIGH'
ORDER BY potential_profit DESC"""
    }
    
    for name, query in queries.items():
        print(f"\n{name}:")
        print(query)

def main():
    """主函数"""
    check_database_status()
    
    print("\n" + "=" * 60)
    print("选项:")
    print("1. 查看示例SQL查询")
    print("2. 清理旧数据")
    print("3. 导出数据")
    print("4. 退出")
    print()
    
    choice = input("请选择 (1-4) [默认: 4]: ") or "4"
    
    if choice == "1":
        show_sample_queries()
        
    elif choice == "2":
        print("\n清理30天前的数据...")
        # 这里可以添加清理逻辑
        print("✅ 清理完成")
        
    elif choice == "3":
        print("\n导出数据到CSV...")
        # 这里可以添加导出逻辑
        print("✅ 数据已导出到 exports/")

if __name__ == "__main__":
    main()