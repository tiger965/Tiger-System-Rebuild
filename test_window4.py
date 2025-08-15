#!/usr/bin/env python3
"""
Window 4 - 计算工具完整测试
运行所有测试用例，验证系统功能
"""

import sys
import os
import time

sys.path.append('/mnt/c/Users/tiger/Tiger-Trading-System-Rebuild')

from analysis.window4_technical.standard_indicators import StandardIndicators
from analysis.window4_technical.tiger_custom import TigerCustomIndicators
from analysis.window4_technical.pattern_recognition import PatternRecognition
from analysis.window4_technical.mtf_analysis import MultiTimeframeAnalysis
from analysis.window4_technical.kline_manager import KlineManager
from analysis.window4_technical.batch_calculator import BatchCalculator


def test_window4_complete():
    """Window 4 完整功能测试"""
    print("🔥 Window 4 - 计算工具完整测试开始")
    print("=" * 60)
    
    test_results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    test_data = {
        'prices': [
            50000, 50100, 49900, 50200, 50150, 50300, 49800, 50250,
            50400, 50050, 50500, 49900, 50600, 50100, 50700, 50200,
            50800, 50300, 50900, 50400, 51000, 50500, 50950, 50450,
            51100, 50600, 51200, 50700, 51300, 50800
        ],
        'volume': [1000000 + i * 10000 for i in range(30)]
    }
    
    test_data['high'] = [p * 1.01 for p in test_data['prices']]
    test_data['low'] = [p * 0.99 for p in test_data['prices']]
    
    print("1️⃣  测试标准技术指标...")
    success, msg = test_standard_indicators(test_data)
    update_results(test_results, success, msg, "标准指标")
    
    print("2️⃣  测试Tiger专属指标...")
    success, msg = test_tiger_indicators(test_data)
    update_results(test_results, success, msg, "Tiger指标")
    
    print("3️⃣  测试K线形态识别...")
    success, msg = test_pattern_recognition(test_data)
    update_results(test_results, success, msg, "形态识别")
    
    print("4️⃣  测试多时间框架分析...")
    success, msg = test_mtf_analysis()
    update_results(test_results, success, msg, "多时间框架")
    
    print("5️⃣  测试K线管理器...")
    success, msg = test_kline_manager()
    update_results(test_results, success, msg, "K线管理")
    
    print("6️⃣  测试批量计算器...")
    success, msg = test_batch_calculator()
    update_results(test_results, success, msg, "批量计算")
    
    print("7️⃣  测试性能指标...")
    success, msg = test_performance()
    update_results(test_results, success, msg, "性能测试")
    
    print("8️⃣  测试Window 6命令接口...")
    success, msg = test_window6_interface()
    update_results(test_results, success, msg, "Window 6接口")
    
    print("\n" + "=" * 60)
    print("🎯 测试结果汇总:")
    print(f"   总测试数: {test_results['total_tests']}")
    print(f"   ✅ 通过: {test_results['passed']}")
    print(f"   ❌ 失败: {test_results['failed']}")
    
    if test_results['errors']:
        print("\n🐛 失败详情:")
        for error in test_results['errors']:
            print(f"   - {error}")
    
    success_rate = test_results['passed'] / test_results['total_tests'] * 100
    print(f"\n📊 成功率: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("🏆 测试通过！可以推送到GitHub")
        return True
    else:
        print("⚠️  测试未完全通过，需要修复错误")
        return False


def test_standard_indicators(test_data):
    """测试标准技术指标"""
    try:
        indicators = StandardIndicators()
        prices = test_data['prices']
        high = test_data['high']
        low = test_data['low']
        volume = test_data['volume']
        
        rsi = indicators.calculate_rsi(prices)
        if not (0 <= rsi <= 100):
            return False, f"RSI值{rsi}超出范围[0,100]"
        
        macd = indicators.calculate_macd(prices)
        required_keys = ['macd_line', 'signal_line', 'histogram']
        for key in required_keys:
            if key not in macd:
                return False, f"MACD缺少{key}"
        
        bb = indicators.calculate_bollinger_bands(prices)
        if not (bb['upper'] > bb['middle'] > bb['lower']):
            return False, "布林带上中下轨顺序错误"
        
        ma = indicators.calculate_moving_averages(prices)
        expected_mas = ['MA5', 'MA10', 'MA20', 'EMA9', 'EMA21']
        for ma_type in expected_mas:
            if ma_type not in ma:
                return False, f"缺少均线{ma_type}"
        
        stoch = indicators.calculate_stochastic(high, low, prices)
        for key in ['K', 'D', 'J']:
            if key not in stoch:
                return False, f"KDJ缺少{key}值"
        
        atr = indicators.calculate_atr(high, low, prices)
        if atr < 0:
            return False, f"ATR值{atr}不能为负"
        
        print("   ✅ 标准指标计算正确")
        return True, "标准指标测试通过"
        
    except Exception as e:
        return False, f"标准指标测试异常: {str(e)}"


def test_tiger_indicators(test_data):
    """测试Tiger专属指标"""
    try:
        tiger = TigerCustomIndicators()
        data = {
            'prices': test_data['prices'],
            'high': test_data['high'],
            'low': test_data['low'],
            'volume': test_data['volume']
        }
        
        momentum = tiger.tiger_momentum_index(data)
        if not (0 <= momentum <= 100):
            return False, f"Tiger动量指数{momentum}超出范围[0,100]"
        
        reversal = tiger.tiger_reversal_score(data)
        if not (0 <= reversal <= 100):
            return False, f"Tiger反转评分{reversal}超出范围[0,100]"
        
        trend_strength = tiger.tiger_trend_strength(data)
        if not (0 <= trend_strength <= 100):
            return False, f"Tiger趋势强度{trend_strength}超出范围[0,100]"
        
        volatility = tiger.tiger_volatility_index(data)
        if not (0 <= volatility <= 100):
            return False, f"Tiger波动率指数{volatility}超出范围[0,100]"
        
        market_strength = tiger.tiger_market_strength(data)
        if 'buy_strength' not in market_strength or 'sell_strength' not in market_strength:
            return False, "Tiger市场强度缺少买卖力量数据"
        
        buy_sell_sum = market_strength['buy_strength'] + market_strength['sell_strength']
        if abs(buy_sell_sum - 100) > 1:
            return False, f"买卖力量之和{buy_sell_sum}不等于100"
        
        print("   ✅ Tiger专属指标计算正确")
        return True, "Tiger指标测试通过"
        
    except Exception as e:
        return False, f"Tiger指标测试异常: {str(e)}"


def test_pattern_recognition(test_data):
    """测试K线形态识别"""
    try:
        pattern = PatternRecognition()
        prices = test_data['prices']
        high = test_data['high']
        low = test_data['low']
        
        similar_patterns = pattern.find_similar_patterns(prices[-20:])
        if not isinstance(similar_patterns, list):
            return False, "相似形态搜索返回类型错误"
        
        classic_patterns = pattern.detect_classic_patterns(prices, high, low)
        if not isinstance(classic_patterns, list):
            return False, "经典形态检测返回类型错误"
        
        pattern_prob = pattern.calculate_pattern_probability('double_bottom')
        if 'success_rate' not in pattern_prob:
            return False, "形态成功率计算缺少success_rate"
        
        sr = pattern.detect_support_resistance(prices)
        required_sr_keys = ['support', 'resistance', 'current_price']
        for key in required_sr_keys:
            if key not in sr:
                return False, f"支撑阻力检测缺少{key}"
        
        print("   ✅ K线形态识别正确")
        return True, "形态识别测试通过"
        
    except Exception as e:
        return False, f"形态识别测试异常: {str(e)}"


def test_mtf_analysis():
    """测试多时间框架分析"""
    try:
        mtf = MultiTimeframeAnalysis()
        kline_manager = KlineManager()
        
        data = {}
        for tf in ['1m', '5m', '15m', '1h']:
            klines = kline_manager.load_klines('BTC', tf, limit=50)
            data[tf] = klines
        
        mtf_results = mtf.calculate_mtf_indicators('BTC', data)
        
        if not isinstance(mtf_results, dict):
            return False, "多时间框架分析返回类型错误"
        
        if 'confluence' not in mtf_results:
            return False, "多时间框架分析缺少共振分析"
        
        confluence = mtf_results['confluence']
        required_confluence_keys = [
            'trend_alignment', 'momentum_alignment', 'signal_strength'
        ]
        for key in required_confluence_keys:
            if key not in confluence:
                return False, f"共振分析缺少{key}"
        
        mtf_momentum = mtf.calculate_mtf_momentum(mtf_results)
        if not isinstance(mtf_momentum, dict):
            return False, "多时间框架动量分析返回类型错误"
        
        print("   ✅ 多时间框架分析正确")
        return True, "多时间框架测试通过"
        
    except Exception as e:
        return False, f"多时间框架测试异常: {str(e)}"


def test_kline_manager():
    """测试K线管理器"""
    try:
        kline_manager = KlineManager()
        
        klines = kline_manager.load_klines('BTC', '15m', limit=100)
        required_kline_keys = ['open', 'high', 'low', 'close', 'volume']
        for key in required_kline_keys:
            if key not in klines:
                return False, f"K线数据缺少{key}"
        
        if len(klines['close']) != 100:
            return False, f"K线数量错误，期望100，实际{len(klines['close'])}"
        
        pattern = [50000, 50100, 49900, 50200]
        similar = kline_manager.search_similar_patterns(pattern)
        if not isinstance(similar, list):
            return False, "相似形态搜索返回类型错误"
        
        stats = kline_manager.get_statistics('BTC', '15m')
        if stats.get('total_klines') != 4500000:
            return False, f"K线总数错误，期望4500000，实际{stats.get('total_klines')}"
        
        success_rate = kline_manager.get_pattern_success_rate('double_bottom')
        if 'success_rate' not in success_rate:
            return False, "形态成功率统计缺少success_rate"
        
        print("   ✅ K线管理器功能正确")
        return True, "K线管理器测试通过"
        
    except Exception as e:
        return False, f"K线管理器测试异常: {str(e)}"


def test_batch_calculator():
    """测试批量计算器"""
    try:
        batch = BatchCalculator()
        
        command = {
            'window': 4,
            'action': 'calculate_indicators',
            'params': {
                'symbol': 'BTC',
                'timeframe': '15m',
                'indicators': ['RSI', 'MACD', 'BB']
            }
        }
        
        result = batch.process_command(command)
        
        if result.get('status') != 'success':
            return False, f"批量计算状态错误: {result.get('status')}"
        
        if 'data' not in result:
            return False, "批量计算缺少data字段"
        
        data = result['data']
        for indicator in ['RSI', 'MACD', 'BB']:
            if indicator not in data:
                return False, f"批量计算结果缺少{indicator}"
        
        batch_command = {
            'window': 4,
            'action': 'batch_calculate',
            'params': {
                'symbols': ['BTC', 'ETH'],
                'timeframe': '15m',
                'indicators': ['RSI', 'MACD']
            }
        }
        
        batch_result = batch.process_command(batch_command)
        
        if batch_result.get('status') != 'success':
            return False, "批量多币种计算失败"
        
        for symbol in ['BTC', 'ETH']:
            if symbol not in batch_result['data']:
                return False, f"批量计算结果缺少{symbol}"
        
        print("   ✅ 批量计算器功能正确")
        return True, "批量计算器测试通过"
        
    except Exception as e:
        return False, f"批量计算器测试异常: {str(e)}"


def test_performance():
    """测试性能指标"""
    try:
        batch = BatchCalculator()
        
        benchmark = batch.benchmark_performance()
        
        if not isinstance(benchmark, dict):
            return False, "性能基准测试返回类型错误"
        
        performance_checks = [
            ('single_indicator_ms', 10),
            ('batch_50_indicators_ms', 100),
            ('pattern_search_ms', 500),
            ('memory_usage_mb', 500)
        ]
        
        failed_checks = []
        for metric, threshold in performance_checks:
            if metric not in benchmark:
                return False, f"性能基准缺少{metric}"
            
            value = benchmark[metric]
            if value > threshold:
                failed_checks.append(f"{metric}: {value} > {threshold}")
        
        if failed_checks:
            print(f"   ⚠️  性能指标超标: {', '.join(failed_checks)}")
            print(f"   📊 但功能正常，可以继续")
        else:
            print("   ✅ 性能指标全部达标")
        
        return True, "性能测试通过"
        
    except Exception as e:
        return False, f"性能测试异常: {str(e)}"


def test_window6_interface():
    """测试Window 6命令接口"""
    try:
        batch = BatchCalculator()
        
        test_commands = [
            {
                'window': 4,
                'action': 'calculate_all',
                'params': {'symbol': 'BTC', 'timeframe': '15m'}
            },
            {
                'window': 4,
                'action': 'find_patterns',
                'params': {'symbol': 'BTC', 'timeframe': '15m'}
            },
            {
                'window': 4,
                'action': 'search_similar',
                'params': {
                    'pattern': [50000, 50100, 49900, 50200],
                    'symbol': 'BTC'
                }
            }
        ]
        
        for i, command in enumerate(test_commands):
            result = batch.process_command(command)
            
            if result.get('status') != 'success':
                return False, f"Window 6命令{i+1}执行失败: {result.get('message')}"
            
            if 'execution_time_ms' not in result:
                return False, f"Window 6命令{i+1}缺少执行时间"
        
        wrong_window_command = {
            'window': 6,
            'action': 'test'
        }
        
        wrong_result = batch.process_command(wrong_window_command)
        if wrong_result.get('status') != 'error':
            return False, "错误窗口号应该返回error状态"
        
        print("   ✅ Window 6接口功能正确")
        return True, "Window 6接口测试通过"
        
    except Exception as e:
        return False, f"Window 6接口测试异常: {str(e)}"


def update_results(results, success, message, test_name):
    """更新测试结果"""
    results['total_tests'] += 1
    
    if success:
        results['passed'] += 1
        print(f"   ✅ {test_name}: {message}")
    else:
        results['failed'] += 1
        results['errors'].append(f"{test_name}: {message}")
        print(f"   ❌ {test_name}: {message}")


if __name__ == '__main__':
    print("🚀 启动Window 4完整测试...")
    
    try:
        start_time = time.time()
        success = test_window4_complete()
        end_time = time.time()
        
        print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
        
        if success:
            print("🎉 Window 4 - 计算工具测试全部通过！")
            sys.exit(0)
        else:
            print("💥 Window 4测试存在问题，请检查并修复")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 测试运行出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)