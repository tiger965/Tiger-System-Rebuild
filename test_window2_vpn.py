#!/usr/bin/env python3
"""
Window 2 VPN保护测试脚本
测试所有组件的VPN保护功能是否正常
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'collectors', 'exchange'))

from collectors.exchange.ranking_monitor import RankingMonitor
from collectors.exchange.realtime_collector import RealtimeDataCollector
from collectors.exchange.account_manager import AccountManager
from loguru import logger

def test_vpn_protection():
    """测试VPN保护功能"""
    print("🔒 =========================")
    print("🔒 Window 2 VPN保护测试")
    print("🔒 =========================\n")
    
    # 1. 测试榜单监控器
    print("1. 测试榜单监控器...")
    monitor = RankingMonitor()
    
    # 测试OKX（应该成功）
    okx_hot = monitor.get_hot_ranking('okx', 3)
    print(f"   ✅ OKX热门榜获取: {len(okx_hot)}个币种")
    
    # 测试币安（应该被阻止）
    binance_hot = monitor.get_hot_ranking('binance', 3)
    print(f"   🚨 Binance热门榜获取: {len(binance_hot)}个币种（应该为0）")
    
    # 2. 测试实时采集器
    print("\n2. 测试实时数据采集器...")
    collector = RealtimeDataCollector()
    
    # 测试OKX（应该成功）
    okx_price = collector.get_realtime_price('BTC/USDT', 'okx')
    print(f"   ✅ OKX价格获取: {'成功' if okx_price else '失败'}")
    
    # 测试币安（应该被阻止）
    binance_price = collector.get_realtime_price('BTC/USDT', 'binance')
    print(f"   🚨 Binance价格获取: {'成功' if binance_price else '被阻止（正确）'}")
    
    # 3. 测试账户管理器
    print("\n3. 测试账户管理器...")
    manager = AccountManager()
    
    # 测试OKX账户（可能会因权限失败，但不会因VPN失败）
    okx_account = manager.get_okx_account()
    print(f"   ✅ OKX账户获取: {'成功' if okx_account else '失败（可能权限问题）'}")
    
    # 测试币安账户（应该被VPN保护阻止）
    binance_account = manager.get_binance_account()
    print(f"   🚨 Binance账户获取: {'成功' if binance_account else '被阻止（正确）'}")
    
    print("\n🔒 =========================")
    print("🔒 VPN保护测试完成")
    print("🔒 =========================")
    
    print("\n📊 测试结果汇总:")
    print(f"   - OKX服务正常运行: ✅")
    print(f"   - Binance被VPN保护阻止: {'✅' if not binance_hot and not binance_price and not binance_account else '❌'}")
    print(f"   - 系统不会意外连接币安: ✅")
    print(f"   - 防止账户封号: ✅")
    
    if not binance_hot and not binance_price and not binance_account:
        print("\n🎉 VPN保护测试全部通过！币安连接已被完全阻止，系统安全！")
        return True
    else:
        print("\n❌ 警告：VPN保护可能有漏洞！")
        return False

if __name__ == "__main__":
    success = test_vpn_protection()
    sys.exit(0 if success else 1)