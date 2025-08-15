#!/usr/bin/env python3
"""
Tiger System - Complete Test Suite
Window 4: Technical Analysis Engine
完整测试脚本 - 测试所有200+指标
"""

import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

# 导入所有指标模块
from indicators.trend import TrendIndicators, calculate_all_trend_indicators
from indicators.momentum import MomentumIndicators, calculate_all_momentum_indicators
from indicators.volatility import VolatilityIndicators, calculate_all_volatility_indicators
from indicators.volume import VolumeIndicators, calculate_all_volume_indicators
from indicators.structure import StructureIndicators, calculate_all_structure_indicators
from indicators.custom import CustomIndicators, calculate_all_custom_indicators
from patterns.pattern_recognition import PatternRecognition, detect_all_patterns
from mtf_analysis import MultiTimeframeAnalysis


def generate_test_data(size: int = 1000) -> pd.DataFrame:
    """生成测试数据"""
    np.random.seed(42)
    
    # 生成基础价格数据（模拟真实市场）
    dates = pd.date_range(end=datetime.now(), periods=size, freq='1min')
    
    # 使用布朗运动生成价格
    returns = np.random.normal(0.0001, 0.01, size)
    price = 50000 * np.exp(np.cumsum(returns))
    
    # 生成OHLCV数据
    df = pd.DataFrame(index=dates)
    df['close'] = price
    
    # 生成开高低
    daily_volatility = np.random.uniform(0.002, 0.01, size)
    df['open'] = df['close'] * (1 + np.random.normal(0, daily_volatility))
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.normal(0, daily_volatility)))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.normal(0, daily_volatility)))
    
    # 生成成交量
    base_volume = 1000000
    volume_volatility = np.random.uniform(0.5, 2.0, size)
    df['volume'] = base_volume * volume_volatility * np.abs(returns) * 100
    
    return df


def test_trend_indicators(df: pd.DataFrame) -> dict:
    """测试趋势指标"""
    print("\n测试趋势类指标...")
    start_time = time.time()
    
    indicators = TrendIndicators()
    results = {}
    errors = []
    
    try:
        # 测试所有移动平均
        results['sma_5'] = indicators.sma(df['close'], 5)
        results['ema_20'] = indicators.ema(df['close'], 20)
        results['wma_20'] = indicators.wma(df['close'], 20)
        results['dema_20'] = indicators.dema(df['close'], 20)
        results['tema_20'] = indicators.tema(df['close'], 20)
        results['kama_10'] = indicators.kama(df['close'])
        results['hma_20'] = indicators.hma(df['close'], 20)
        results['zlema_20'] = indicators.zlema(df['close'], 20)
        
        # 测试MACD
        macd = indicators.macd(df['close'])
        results['macd'] = macd['macd']
        results['macd_signal'] = macd['signal']
        
        # 测试ADX
        adx = indicators.adx(df['high'], df['low'], df['close'])
        results['adx'] = adx['adx']
        
        # 测试其他趋势指标
        results['sar'] = indicators.parabolic_sar(df['high'], df['low'])
        
        # 使用批量计算函数
        all_trend = calculate_all_trend_indicators(df)
        
        elapsed = time.time() - start_time
        print(f"✓ 趋势指标测试完成: {len(results)} 个指标, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"趋势指标错误: {str(e)}")
        print(f"✗ 趋势指标测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_momentum_indicators(df: pd.DataFrame) -> dict:
    """测试动量指标"""
    print("\n测试动量类指标...")
    start_time = time.time()
    
    indicators = MomentumIndicators()
    results = {}
    errors = []
    
    try:
        # RSI系列
        results['rsi_14'] = indicators.rsi(df['close'], 14)
        stoch_rsi = indicators.stochastic_rsi(df['close'])
        results['stoch_rsi'] = stoch_rsi['stoch_rsi']
        
        # 随机指标
        stoch = indicators.stochastic(df['high'], df['low'], df['close'])
        results['stoch_k'] = stoch['k']
        results['stoch_d'] = stoch['d']
        
        # 其他动量指标
        results['cci'] = indicators.cci(df['high'], df['low'], df['close'])
        results['williams_r'] = indicators.williams_r(df['high'], df['low'], df['close'])
        results['roc'] = indicators.roc(df['close'])
        results['tsi'] = indicators.tsi(df['close'])
        
        # 批量计算
        all_momentum = calculate_all_momentum_indicators(df)
        
        elapsed = time.time() - start_time
        print(f"✓ 动量指标测试完成: {len(results)} 个指标, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"动量指标错误: {str(e)}")
        print(f"✗ 动量指标测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_volatility_indicators(df: pd.DataFrame) -> dict:
    """测试波动率指标"""
    print("\n测试波动率指标...")
    start_time = time.time()
    
    indicators = VolatilityIndicators()
    results = {}
    errors = []
    
    try:
        # 布林带
        bb = indicators.bollinger_bands(df['close'])
        results['bb_upper'] = bb['upper']
        results['bb_lower'] = bb['lower']
        
        # ATR系列
        results['atr'] = indicators.atr(df['high'], df['low'], df['close'])
        results['natr'] = indicators.natr(df['high'], df['low'], df['close'])
        
        # 其他波动率
        results['historical_vol'] = indicators.historical_volatility(df['close'])
        results['chaikin_vol'] = indicators.chaikin_volatility(df['high'], df['low'])
        
        # 批量计算
        all_volatility = calculate_all_volatility_indicators(df)
        
        elapsed = time.time() - start_time
        print(f"✓ 波动率指标测试完成: {len(results)} 个指标, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"波动率指标错误: {str(e)}")
        print(f"✗ 波动率指标测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_volume_indicators(df: pd.DataFrame) -> dict:
    """测试成交量指标"""
    print("\n测试成交量指标...")
    start_time = time.time()
    
    indicators = VolumeIndicators()
    results = {}
    errors = []
    
    try:
        # 量价指标
        results['obv'] = indicators.obv(df['close'], df['volume'])
        results['cmf'] = indicators.cmf(df['high'], df['low'], df['close'], df['volume'])
        results['mfi'] = indicators.mfi(df['high'], df['low'], df['close'], df['volume'])
        results['vwap'] = indicators.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        # 批量计算
        all_volume = calculate_all_volume_indicators(df)
        
        elapsed = time.time() - start_time
        print(f"✓ 成交量指标测试完成: {len(results)} 个指标, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"成交量指标错误: {str(e)}")
        print(f"✗ 成交量指标测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_structure_indicators(df: pd.DataFrame) -> dict:
    """测试市场结构指标"""
    print("\n测试市场结构指标...")
    start_time = time.time()
    
    indicators = StructureIndicators()
    results = {}
    errors = []
    
    try:
        # 枢轴点
        pivots = indicators.pivot_points(df['high'], df['low'], df['close'])
        results['pivot'] = pivots['pivot']
        results['r1'] = pivots['r1']
        results['s1'] = pivots['s1']
        
        # 批量计算
        all_structure = calculate_all_structure_indicators(df)
        
        elapsed = time.time() - start_time
        print(f"✓ 市场结构指标测试完成: {len(results)} 个指标, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"市场结构指标错误: {str(e)}")
        print(f"✗ 市场结构指标测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_custom_indicators(df: pd.DataFrame) -> dict:
    """测试自定义指标"""
    print("\n测试自定义指标...")
    start_time = time.time()
    
    indicators = CustomIndicators()
    results = {}
    errors = []
    
    try:
        # Tiger专属指标
        results['tmi'] = indicators.tiger_momentum_index(df['close'], df['volume'])
        results['tts'] = indicators.tiger_trend_score(df['high'], df['low'], df['close'])
        results['tvr'] = indicators.tiger_volatility_ratio(df['high'], df['low'], df['close'])
        results['tmf'] = indicators.tiger_money_flow(df['high'], df['low'], df['close'], df['volume'])
        
        # 批量计算
        all_custom = calculate_all_custom_indicators(df)
        
        elapsed = time.time() - start_time
        print(f"✓ 自定义指标测试完成: {len(results)} 个指标, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"自定义指标错误: {str(e)}")
        print(f"✗ 自定义指标测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_pattern_recognition(df: pd.DataFrame) -> dict:
    """测试形态识别"""
    print("\n测试形态识别...")
    start_time = time.time()
    
    results = {}
    errors = []
    
    try:
        patterns = detect_all_patterns(df)
        
        pattern_count = 0
        for pattern_type, pattern_df in patterns.items():
            if not pattern_df.empty:
                pattern_count += len(pattern_df)
                results[pattern_type] = len(pattern_df)
        
        elapsed = time.time() - start_time
        print(f"✓ 形态识别测试完成: 发现 {pattern_count} 个形态, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"形态识别错误: {str(e)}")
        print(f"✗ 形态识别测试失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def test_mtf_analysis(df: pd.DataFrame) -> dict:
    """测试多时间框架分析"""
    print("\n测试多时间框架分析...")
    start_time = time.time()
    
    results = {}
    errors = []
    
    try:
        mtf = MultiTimeframeAnalysis()
        mtf_results = mtf.analyze_all_timeframes(df, '1m')
        
        # 生成报告
        report = mtf.generate_mtf_report(mtf_results)
        print(report)
        
        results['timeframes_analyzed'] = len([k for k in mtf_results.keys() if k not in ['combined_signal', 'resonance']])
        results['recommendation'] = mtf_results['combined_signal']['recommendation']
        
        elapsed = time.time() - start_time
        print(f"✓ 多时间框架分析完成: {results['timeframes_analyzed']} 个时间框架, 耗时: {elapsed:.2f}秒")
        
    except Exception as e:
        errors.append(f"多时间框架分析错误: {str(e)}")
        print(f"✗ 多时间框架分析失败: {str(e)}")
    
    return {'results': results, 'errors': errors, 'time': elapsed}


def performance_benchmark(df: pd.DataFrame):
    """性能基准测试"""
    print("\n" + "=" * 60)
    print("性能基准测试")
    print("=" * 60)
    
    # 测试单个币种全部指标计算
    print("\n测试单币种200+指标计算性能...")
    start_time = time.time()
    
    # 计算所有指标
    result_df = df.copy()
    result_df = calculate_all_trend_indicators(result_df)
    result_df = calculate_all_momentum_indicators(result_df)
    result_df = calculate_all_volatility_indicators(result_df)
    result_df = calculate_all_volume_indicators(result_df)
    result_df = calculate_all_structure_indicators(result_df)
    result_df = calculate_all_custom_indicators(result_df)
    
    single_time = time.time() - start_time
    indicator_count = len(result_df.columns) - len(df.columns)
    
    print(f"✓ 单币种计算完成:")
    print(f"  - 指标数量: {indicator_count}")
    print(f"  - 计算耗时: {single_time*1000:.2f}ms")
    print(f"  - 内存使用: {result_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f}MB")
    
    # 测试10币种并行计算
    print("\n测试10币种并行计算性能...")
    start_time = time.time()
    
    import concurrent.futures
    
    def calculate_for_symbol(symbol_df):
        result = symbol_df.copy()
        result = calculate_all_trend_indicators(result)
        result = calculate_all_momentum_indicators(result)
        result = calculate_all_volatility_indicators(result)
        result = calculate_all_volume_indicators(result)
        return result
    
    # 模拟10个币种
    symbols_data = [df.copy() for _ in range(10)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(calculate_for_symbol, data) for data in symbols_data]
        results = [f.result() for f in futures]
    
    parallel_time = time.time() - start_time
    
    print(f"✓ 10币种并行计算完成:")
    print(f"  - 总耗时: {parallel_time*1000:.2f}ms")
    print(f"  - 平均每币种: {parallel_time*100:.2f}ms")
    
    # 性能评估
    print("\n性能评估:")
    if single_time < 0.05:  # 50ms
        print("✓ 单币种性能: 优秀 (< 50ms)")
    elif single_time < 0.1:
        print("✓ 单币种性能: 良好 (< 100ms)")
    else:
        print("⚠ 单币种性能: 需优化 (> 100ms)")
    
    if parallel_time < 0.5:  # 500ms
        print("✓ 并行性能: 优秀 (< 500ms)")
    elif parallel_time < 1.0:
        print("✓ 并行性能: 良好 (< 1s)")
    else:
        print("⚠ 并行性能: 需优化 (> 1s)")


def main():
    """主测试函数"""
    print("=" * 60)
    print("Tiger System - 技术分析引擎完整测试")
    print("Window 4: 200+技术指标测试")
    print("=" * 60)
    
    # 生成测试数据
    print("\n生成测试数据...")
    df = generate_test_data(1000)
    print(f"✓ 生成 {len(df)} 条OHLCV数据")
    
    # 测试各类指标
    test_results = {}
    total_indicators = 0
    total_errors = []
    
    # 1. 趋势指标
    trend_test = test_trend_indicators(df)
    test_results['trend'] = trend_test
    total_indicators += len(trend_test['results'])
    total_errors.extend(trend_test['errors'])
    
    # 2. 动量指标
    momentum_test = test_momentum_indicators(df)
    test_results['momentum'] = momentum_test
    total_indicators += len(momentum_test['results'])
    total_errors.extend(momentum_test['errors'])
    
    # 3. 波动率指标
    volatility_test = test_volatility_indicators(df)
    test_results['volatility'] = volatility_test
    total_indicators += len(volatility_test['results'])
    total_errors.extend(volatility_test['errors'])
    
    # 4. 成交量指标
    volume_test = test_volume_indicators(df)
    test_results['volume'] = volume_test
    total_indicators += len(volume_test['results'])
    total_errors.extend(volume_test['errors'])
    
    # 5. 市场结构指标
    structure_test = test_structure_indicators(df)
    test_results['structure'] = structure_test
    total_indicators += len(structure_test['results'])
    total_errors.extend(structure_test['errors'])
    
    # 6. 自定义指标
    custom_test = test_custom_indicators(df)
    test_results['custom'] = custom_test
    total_indicators += len(custom_test['results'])
    total_errors.extend(custom_test['errors'])
    
    # 7. 形态识别
    pattern_test = test_pattern_recognition(df)
    test_results['patterns'] = pattern_test
    total_errors.extend(pattern_test['errors'])
    
    # 8. 多时间框架分析
    mtf_test = test_mtf_analysis(df)
    test_results['mtf'] = mtf_test
    total_errors.extend(mtf_test['errors'])
    
    # 性能基准测试
    performance_benchmark(df)
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试报告总结")
    print("=" * 60)
    
    print(f"\n指标统计:")
    print(f"  趋势指标: {len(test_results['trend']['results'])} 个")
    print(f"  动量指标: {len(test_results['momentum']['results'])} 个")
    print(f"  波动率指标: {len(test_results['volatility']['results'])} 个")
    print(f"  成交量指标: {len(test_results['volume']['results'])} 个")
    print(f"  市场结构指标: {len(test_results['structure']['results'])} 个")
    print(f"  自定义指标: {len(test_results['custom']['results'])} 个")
    print(f"  形态识别: {sum(test_results['patterns']['results'].values()) if test_results['patterns']['results'] else 0} 个形态")
    print(f"\n总计: {total_indicators}+ 个技术指标")
    
    # 错误报告
    if total_errors:
        print(f"\n⚠ 发现 {len(total_errors)} 个错误:")
        for error in total_errors:
            print(f"  - {error}")
    else:
        print("\n✓ 所有测试通过，无错误！")
    
    # 保存测试结果
    with open('test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_indicators': total_indicators,
            'errors': total_errors,
            'test_passed': len(total_errors) == 0
        }, f, indent=2)
    
    print("\n✓ 测试结果已保存到 test_results.json")
    
    # 返回测试状态
    return len(total_errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)