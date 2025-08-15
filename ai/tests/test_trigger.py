"""
触发机制系统测试
"""

import asyncio
import pytest
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trigger.trigger_system import TriggerSystem, TriggerLevel


class TestTriggerSystem:
    """触发系统测试类"""
    
    @pytest.fixture
    def trigger_system(self):
        """创建触发系统实例"""
        return TriggerSystem()
    
    @pytest.mark.asyncio
    async def test_level_1_trigger(self, trigger_system):
        """测试Level 1触发"""
        market_data = {
            'symbol': 'BTC/USDT',
            'price_change_24h': 1.8,  # Level 1触发
            'volume_ratio': 1.5,
            'rsi': 45,
            'whale_transfer': 0,
            'liquidations': 0,
            'top_traders_action': [],
            'social_mention_spike': 1.0,
            'news_importance': 0
        }
        
        signal = await trigger_system.evaluate_trigger(market_data)
        
        assert signal is not None
        assert signal.level == TriggerLevel.LEVEL_1
        assert signal.symbol == 'BTC/USDT'
        print(f"✓ Level 1 triggered for {signal.symbol}: {signal.trigger_reason}")
    
    @pytest.mark.asyncio
    async def test_level_2_trigger(self, trigger_system):
        """测试Level 2触发"""
        market_data = {
            'symbol': 'ETH/USDT',
            'price_change_24h': 4.5,  # Level 2触发
            'volume_ratio': 3.5,
            'rsi': 75,
            'whale_transfer': 15_000_000,
            'liquidations': 5_000_000,
            'top_traders_action': ['trader1', 'trader2'],
            'social_mention_spike': 2.5,
            'news_importance': 5,
            'technical_signals_count': 4
        }
        
        signal = await trigger_system.evaluate_trigger(market_data)
        
        assert signal is not None
        assert signal.level == TriggerLevel.LEVEL_2
        assert signal.priority == 5
        print(f"✓ Level 2 triggered for {signal.symbol}: {signal.trigger_reason}")
    
    @pytest.mark.asyncio
    async def test_level_3_trigger(self, trigger_system):
        """测试Level 3紧急触发"""
        market_data = {
            'symbol': 'SOL/USDT',
            'price_change_24h': 15.0,  # Level 3触发
            'volume_ratio': 8.0,
            'rsi': 85,
            'whale_transfer': 100_000_000,
            'liquidations': 150_000_000,
            'top_traders_action': ['trader1', 'trader2', 'trader3'],
            'social_mention_spike': 5.0,
            'news_importance': 9,
            'panic_selling': True
        }
        
        signal = await trigger_system.evaluate_trigger(market_data)
        
        assert signal is not None
        assert signal.level == TriggerLevel.LEVEL_3
        assert signal.priority >= 9
        print(f"✓ Level 3 URGENT triggered for {signal.symbol}: {signal.trigger_reason}")
    
    @pytest.mark.asyncio
    async def test_cooldown_mechanism(self, trigger_system):
        """测试冷却机制"""
        market_data = {
            'symbol': 'BTC/USDT',
            'price_change_24h': 3.5,
            'volume_ratio': 3.0,
            'rsi': 75,
            'technical_signals_count': 3
        }
        
        # 第一次触发应该成功
        signal1 = await trigger_system.evaluate_trigger(market_data)
        assert signal1 is not None
        
        # 立即再次触发应该被冷却阻止
        signal2 = await trigger_system.evaluate_trigger(market_data)
        assert signal2 is None
        
        print("✓ Cooldown mechanism working correctly")
    
    def test_threshold_update(self, trigger_system):
        """测试阈值动态调整"""
        # 牛市调整
        trigger_system.update_thresholds({'trend': 'bull'})
        assert trigger_system.thresholds.price_change_level_2 == 2.5
        
        # 熊市调整
        trigger_system.update_thresholds({'trend': 'bear'})
        assert trigger_system.thresholds.price_change_level_2 == 4.0
        
        # 高波动调整
        trigger_system.update_thresholds({'volatility': 'high'})
        assert trigger_system.thresholds.price_change_level_1 == 2.0
        
        print("✓ Dynamic threshold adjustment working")
    
    def test_stats_tracking(self, trigger_system):
        """测试统计跟踪"""
        initial_stats = trigger_system.get_stats()
        assert initial_stats['total_triggers'] == 0
        
        # 模拟一些触发
        trigger_system.stats['total_triggers'] = 10
        trigger_system.stats['level_1_count'] = 5
        trigger_system.stats['level_2_count'] = 3
        trigger_system.stats['level_3_count'] = 2
        
        stats = trigger_system.get_stats()
        assert stats['total_triggers'] == 10
        assert stats['level_1_count'] == 5
        assert stats['level_2_count'] == 3
        assert stats['level_3_count'] == 2
        
        print("✓ Statistics tracking working correctly")


if __name__ == "__main__":
    # 运行测试
    test = TestTriggerSystem()
    trigger_system = TriggerSystem()
    
    # 运行异步测试
    loop = asyncio.get_event_loop()
    
    print("\n=== Testing Trigger System ===\n")
    
    # Level 1测试
    loop.run_until_complete(test.test_level_1_trigger(trigger_system))
    
    # Level 2测试
    loop.run_until_complete(test.test_level_2_trigger(trigger_system))
    
    # Level 3测试
    loop.run_until_complete(test.test_level_3_trigger(trigger_system))
    
    # 冷却机制测试
    loop.run_until_complete(test.test_cooldown_mechanism(trigger_system))
    
    # 阈值调整测试
    test.test_threshold_update(trigger_system)
    
    # 统计测试
    test.test_stats_tracking(trigger_system)
    
    print("\n=== All Trigger Tests Passed! ===\n")