#!/usr/bin/env python3
"""Window 1 主程序 - 数据库工具服务"""

import asyncio
import logging
import sys
import signal
import time
from datetime import datetime, timedelta
from typing import Dict
import json
import argparse
import random

from api_interface import Window1API, process_command, get_window1_api

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('window1.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Window1Service:
    """Window 1 服务主类"""
    
    def __init__(self, test_mode: bool = False):
        """初始化服务
        
        Args:
            test_mode: 是否为测试模式
        """
        self.api = get_window1_api()
        self.running = False
        self.test_mode = test_mode
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        
    async def start(self):
        """启动服务"""
        logger.info("=" * 50)
        logger.info("Window 1 - 数据库工具服务启动")
        logger.info(f"启动时间: {self.start_time}")
        logger.info(f"测试模式: {self.test_mode}")
        logger.info("=" * 50)
        
        self.running = True
        
        # 启动健康检查
        asyncio.create_task(self.health_check_loop())
        
        # 启动清理任务
        asyncio.create_task(self.cleanup_loop())
        
        if self.test_mode:
            # 测试模式下启动模拟请求
            asyncio.create_task(self.simulate_requests())
        
        # 主循环
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # 检查是否达到测试时长
                if self.test_mode:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if '--test-mode' in sys.argv:
                        test_duration = self._parse_test_duration()
                        if elapsed >= test_duration:
                            logger.info(f"测试时间到达 {test_duration} 秒，准备停止")
                            await self.stop()
                            break
                            
        except KeyboardInterrupt:
            logger.info("收到中断信号，准备停止服务")
            await self.stop()
    
    async def stop(self):
        """停止服务"""
        logger.info("正在停止Window 1服务...")
        self.running = False
        
        # 清理资源
        await self.api.cleanup()
        
        # 打印统计
        self._print_statistics()
        
        logger.info("Window 1服务已停止")
    
    async def health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                health = await self.api.health_check()
                
                if health['status'] != 'healthy':
                    logger.warning(f"健康检查异常: {health}")
                else:
                    logger.debug(f"健康检查正常: API调用数={health['api_stats']['total_calls']}")
                
                # 每30秒检查一次
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                await asyncio.sleep(30)
    
    async def cleanup_loop(self):
        """清理任务循环"""
        while self.running:
            try:
                # 每小时清理一次
                await asyncio.sleep(3600)
                
                logger.info("执行定期清理任务")
                await self.api.account_cache.cleanup_old_cache()
                await self.api.decision_tracker.cleanup_old_decisions(90)
                
            except Exception as e:
                logger.error(f"清理任务失败: {e}")
    
    async def simulate_requests(self):
        """模拟请求（测试模式）"""
        logger.info("开始模拟请求...")
        
        request_types = [
            ('get_account_cache', lambda: {'user_id': f'user_{random.randint(1, 10)}'}),
            ('record_decision', lambda: {
                'decision_data': {
                    'type': random.choice(['buy', 'sell', 'hold']),
                    'symbol': random.choice(['BTCUSDT', 'ETHUSDT', 'BNBUSDT']),
                    'price': random.uniform(20000, 60000),
                    'amount': random.uniform(0.01, 1.0),
                    'confidence': random.uniform(0.5, 0.95),
                    'risk_level': random.uniform(0.1, 0.9)
                }
            }),
            ('get_success_rate', lambda: {
                'period': random.choice(['last_7_days', 'last_30_days', 'last_90_days'])
            }),
            ('query_kline_patterns', lambda: {
                'symbol': random.choice(['BTCUSDT', 'ETHUSDT']),
                'pattern_type': random.choice(['double_bottom', 'head_shoulders', 'triangle']),
                'timeframe': random.choice(['1h', '4h', '1d']),
                'limit': random.randint(10, 100)
            })
        ]
        
        while self.running:
            try:
                # 随机选择请求类型
                function_name, params_generator = random.choice(request_types)
                
                # 构建命令
                command = {
                    'window': 1,
                    'function': function_name,
                    'params': params_generator()
                }
                
                # 执行命令
                start_time = time.time()
                result = await process_command(command)
                elapsed = (time.time() - start_time) * 1000  # 毫秒
                
                self.request_count += 1
                
                if result.get('success'):
                    logger.debug(f"请求成功: {function_name} (耗时: {elapsed:.2f}ms)")
                else:
                    self.error_count += 1
                    logger.warning(f"请求失败: {function_name} - {result.get('error')}")
                
                # 随机延迟
                await asyncio.sleep(random.uniform(0.1, 2.0))
                
            except Exception as e:
                logger.error(f"模拟请求异常: {e}")
                self.error_count += 1
                await asyncio.sleep(1)
    
    async def handle_command(self, command: Dict) -> Dict:
        """处理外部命令
        
        Args:
            command: 命令字典
            
        Returns:
            执行结果
        """
        try:
            self.request_count += 1
            result = await process_command(command)
            
            if not result.get('success'):
                self.error_count += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"处理命令失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_test_duration(self) -> int:
        """解析测试时长"""
        if '--test-mode' in sys.argv:
            idx = sys.argv.index('--test-mode')
            if idx + 1 < len(sys.argv):
                duration_str = sys.argv[idx + 1]
                
                # 解析时长
                if duration_str.endswith('h'):
                    return int(duration_str[:-1]) * 3600
                elif duration_str.endswith('m'):
                    return int(duration_str[:-1]) * 60
                else:
                    return int(duration_str)
        
        return 60  # 默认60秒
    
    def _print_statistics(self):
        """打印统计信息"""
        elapsed = datetime.now() - self.start_time
        
        logger.info("=" * 50)
        logger.info("Window 1 服务统计")
        logger.info(f"运行时长: {elapsed}")
        logger.info(f"总请求数: {self.request_count}")
        logger.info(f"错误数: {self.error_count}")
        
        if self.request_count > 0:
            error_rate = self.error_count / self.request_count * 100
            logger.info(f"错误率: {error_rate:.2f}%")
            
            # 计算QPS
            total_seconds = elapsed.total_seconds()
            if total_seconds > 0:
                qps = self.request_count / total_seconds
                logger.info(f"平均QPS: {qps:.2f}")
        
        logger.info("=" * 50)


async def run_performance_test():
    """运行性能测试"""
    logger.info("开始性能测试...")
    
    api = get_window1_api()
    
    # 测试1: 账户缓存查询性能
    logger.info("测试1: 账户缓存查询性能")
    start = time.time()
    for i in range(100):
        await api.get_account_cache(f'perf_test_{i}')
    elapsed = time.time() - start
    logger.info(f"100次账户查询耗时: {elapsed:.2f}秒, 平均: {elapsed/100*1000:.2f}ms")
    
    # 测试2: 决策记录性能
    logger.info("测试2: 决策记录性能")
    start = time.time()
    for i in range(100):
        await api.record_decision({
            'type': 'buy',
            'symbol': 'BTCUSDT',
            'price': 50000 + i,
            'amount': 0.1,
            'confidence': 0.8
        })
    elapsed = time.time() - start
    logger.info(f"100次决策记录耗时: {elapsed:.2f}秒, 平均: {elapsed/100*1000:.2f}ms")
    
    # 测试3: 成功率计算性能
    logger.info("测试3: 成功率计算性能")
    start = time.time()
    for period in ['last_7_days', 'last_30_days', 'last_90_days']:
        await api.get_success_rate(period)
    elapsed = time.time() - start
    logger.info(f"3次成功率计算耗时: {elapsed:.2f}秒, 平均: {elapsed/3:.2f}秒")
    
    # 测试4: 批量查询性能
    logger.info("测试4: 批量查询性能")
    queries = [
        {'function': 'get_account_cache', 'params': {'user_id': f'batch_{i}'}}
        for i in range(50)
    ]
    start = time.time()
    results = await api.batch_query(queries)
    elapsed = time.time() - start
    logger.info(f"50个批量查询耗时: {elapsed:.2f}秒")
    
    # 测试5: 并发性能
    logger.info("测试5: 并发性能")
    async def concurrent_request(i):
        return await api.get_account_cache(f'concurrent_{i}')
    
    start = time.time()
    tasks = [concurrent_request(i) for i in range(100)]
    await asyncio.gather(*tasks)
    elapsed = time.time() - start
    logger.info(f"100个并发请求耗时: {elapsed:.2f}秒")
    
    logger.info("性能测试完成！")
    
    # 打印性能报告
    health = await api.health_check()
    logger.info(f"API统计: {json.dumps(health['api_stats'], indent=2)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Window 1 - 数据库工具服务')
    parser.add_argument('--test-mode', type=str, help='测试模式 (例如: 60, 1h, 24h)')
    parser.add_argument('--performance-test', action='store_true', help='运行性能测试')
    
    args = parser.parse_args()
    
    if args.performance_test:
        # 运行性能测试
        asyncio.run(run_performance_test())
    else:
        # 运行服务
        service = Window1Service(test_mode=bool(args.test_mode))
        
        # 设置信号处理
        def signal_handler(sig, frame):
            logger.info(f"收到信号 {sig}")
            asyncio.create_task(service.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动服务
        try:
            asyncio.run(service.start())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"服务异常: {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    main()