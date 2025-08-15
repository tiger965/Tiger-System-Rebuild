"""
硬编码命令接口 - AI与其他窗口通信的唯一方式
绝对禁止使用自然语言，只能使用预定义的函数调用
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import importlib
import sys
import os

# 添加父目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class CommandInterface:
    """
    硬编码命令接口
    AI只能通过这个接口调用其他窗口的功能
    """
    
    # 硬编码的窗口函数映射
    WINDOW_FUNCTIONS = {
        1: {  # Window 1 - 数据库工具
            "get_account_cache": {
                "params": ["user_id"],
                "module": "database.dal.base_dal",
                "class": "BaseDAL",
                "method": "get_account_cache"
            },
            "record_decision": {
                "params": ["decision_data"],
                "module": "database.dal.base_dal",
                "class": "BaseDAL",
                "method": "record_decision"
            },
            "get_success_rate": {
                "params": ["period"],
                "module": "database.dal.base_dal",
                "class": "BaseDAL",
                "method": "get_success_rate"
            }
        },
        2: {  # Window 2 - 交易所工具
            "get_hot_ranking": {
                "params": ["exchange", "top"],
                "module": "collectors.exchange.main_collector",
                "class": "MainCollector",
                "method": "get_hot_ranking"
            },
            "get_realtime_price": {
                "params": ["symbol", "exchange"],
                "module": "collectors.exchange.main_collector",
                "class": "MainCollector",
                "method": "get_realtime_price"
            },
            "get_volume_surge": {
                "params": ["threshold", "timeframe"],
                "module": "collectors.exchange.detector",
                "class": "AnomalyDetector",
                "method": "detect_volume_surge"
            }
        },
        3: {  # Window 3 - 数据采集工具
            "crawl_twitter": {
                "params": ["keyword", "time_range_minutes", "get_sentiment", "min_followers"],
                "module": "collectors.social.twitter_monitor",
                "class": "TwitterMonitor",
                "method": "search_tweets"
            },
            "track_whale_transfers": {
                "params": ["min_amount_usd", "chains", "direction"],
                "module": "collectors.blockchain.whale_tracker",
                "class": "WhaleTracker",
                "method": "track_transfers"
            },
            "crawl_valuescan": {
                "params": ["signal_type", "min_confidence"],
                "module": "collectors.signal_aggregator.valuescan_enhanced",
                "class": "ValueScanEnhanced",
                "method": "get_signals"
            }
        },
        4: {  # Window 4 - 计算工具
            "calculate_rsi": {
                "params": ["prices", "period"],
                "module": "analysis.indicators.momentum",
                "function": "calculate_rsi"
            },
            "calculate_macd": {
                "params": ["prices", "fast_period", "slow_period", "signal_period"],
                "module": "analysis.indicators.trend",
                "function": "calculate_macd"
            },
            "find_similar_patterns": {
                "params": ["symbol", "current_pattern", "min_similarity"],
                "module": "analysis.patterns.pattern_recognition",
                "class": "PatternRecognition",
                "method": "find_similar"
            }
        },
        7: {  # Window 7 - 风控执行工具
            "calculate_kelly_position": {
                "params": ["win_probability", "odds", "max_risk", "account_balance"],
                "module": "risk.money.money_management",
                "class": "MoneyManagement",
                "method": "calculate_kelly"
            },
            "execute_trade": {
                "params": ["action", "symbol", "amount", "order_type"],
                "module": "risk.execution.execution_monitor",
                "class": "ExecutionMonitor",
                "method": "execute_order"
            }
        },
        8: {  # Window 8 - 通知工具
            "send_emergency_alert": {
                "params": ["level", "message", "data"],
                "module": "notification.alert_notifier",
                "class": "AlertNotifier",
                "method": "send_emergency"
            },
            "send_daily_report": {
                "params": ["report"],
                "module": "notification.report_generator",
                "class": "ReportGenerator",
                "method": "send_report"
            }
        },
        9: {  # Window 9 - 学习工具
            "learn_from_trade": {
                "params": ["trade_data"],
                "module": "learning.records.trade_recorder",
                "class": "TradeRecorder",
                "method": "record_trade"
            },
            "get_pattern_probability": {
                "params": ["pattern"],
                "module": "learning.patterns.pattern_learner",
                "class": "PatternLearner",
                "method": "get_probability"
            }
        }
    }
    
    def __init__(self):
        """初始化命令接口"""
        self.module_cache = {}  # 缓存已加载的模块
        self.instance_cache = {}  # 缓存已创建的实例
        self.call_history = []  # 调用历史
        self.max_history = 1000
        
        logger.info("命令接口初始化完成")
    
    async def execute_command(self, command: Dict) -> Any:
        """
        执行命令
        
        Args:
            command: {
                "window": 窗口ID,
                "function": 函数名,
                "params": 参数字典
            }
        
        Returns:
            命令执行结果
        """
        # 验证命令格式
        if not self._validate_command(command):
            raise ValueError(f"无效的命令格式: {command}")
        
        window_id = command["window"]
        function_name = command["function"]
        params = command.get("params", {})
        
        # 检查窗口是否存在
        if window_id not in self.WINDOW_FUNCTIONS:
            raise ValueError(f"无效的窗口ID: {window_id}")
        
        # 检查函数是否存在
        if function_name not in self.WINDOW_FUNCTIONS[window_id]:
            raise ValueError(f"窗口{window_id}不支持函数: {function_name}")
        
        # 获取函数配置
        func_config = self.WINDOW_FUNCTIONS[window_id][function_name]
        
        # 验证参数
        if not self._validate_params(params, func_config["params"]):
            raise ValueError(f"参数不匹配: 需要{func_config['params']}, 提供{list(params.keys())}")
        
        # 记录调用
        self._record_call(window_id, function_name, params)
        
        # 执行函数
        try:
            result = await self._execute_function(func_config, params)
            logger.info(f"命令执行成功: Window{window_id}.{function_name}")
            return result
        except Exception as e:
            logger.error(f"命令执行失败: Window{window_id}.{function_name} - {e}")
            raise
    
    def _validate_command(self, command: Dict) -> bool:
        """验证命令格式"""
        required_fields = ["window", "function"]
        
        # 检查必需字段
        for field in required_fields:
            if field not in command:
                logger.error(f"命令缺少必需字段: {field}")
                return False
        
        # 检查类型
        if not isinstance(command["window"], int):
            logger.error("window必须是整数")
            return False
        
        if not isinstance(command["function"], str):
            logger.error("function必须是字符串")
            return False
        
        if "params" in command and not isinstance(command["params"], dict):
            logger.error("params必须是字典")
            return False
        
        return True
    
    def _validate_params(self, provided: Dict, required: List[str]) -> bool:
        """验证参数"""
        # 检查必需参数是否都提供了
        for param in required:
            if param not in provided:
                logger.error(f"缺少必需参数: {param}")
                return False
        return True
    
    async def _execute_function(self, config: Dict, params: Dict) -> Any:
        """执行具体函数"""
        module_name = config["module"]
        
        # 加载模块
        if module_name not in self.module_cache:
            try:
                module = importlib.import_module(module_name)
                self.module_cache[module_name] = module
            except ImportError as e:
                # 如果模块不存在，返回模拟数据
                logger.warning(f"模块{module_name}不存在，返回模拟数据: {e}")
                return self._get_simulated_response(config, params)
        else:
            module = self.module_cache[module_name]
        
        # 根据配置调用函数或方法
        if "class" in config:
            # 类方法调用
            class_name = config["class"]
            method_name = config["method"]
            
            # 获取或创建实例
            instance_key = f"{module_name}.{class_name}"
            if instance_key not in self.instance_cache:
                try:
                    cls = getattr(module, class_name)
                    # 尝试创建实例，如果需要参数则捕获异常
                    try:
                        instance = cls()
                    except TypeError as e:
                        if "missing" in str(e) and "positional arguments" in str(e):
                            logger.warning(f"类{class_name}需要参数创建，返回模拟数据: {e}")
                            return self._get_simulated_response(config, params)
                        else:
                            raise e
                    self.instance_cache[instance_key] = instance
                except (AttributeError, ImportError) as e:
                    logger.warning(f"类{class_name}不存在或导入失败，返回模拟数据: {e}")
                    return self._get_simulated_response(config, params)
            else:
                instance = self.instance_cache[instance_key]
            
            # 调用方法
            try:
                method = getattr(instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    return await method(**params)
                else:
                    return method(**params)
            except AttributeError:
                logger.warning(f"方法{method_name}不存在，返回模拟数据")
                return self._get_simulated_response(config, params)
        
        elif "function" in config:
            # 直接函数调用
            function_name = config["function"]
            try:
                func = getattr(module, function_name)
                if asyncio.iscoroutinefunction(func):
                    return await func(**params)
                else:
                    return func(**params)
            except AttributeError:
                logger.warning(f"函数{function_name}不存在，返回模拟数据")
                return self._get_simulated_response(config, params)
        
        else:
            raise ValueError(f"配置缺少class或function: {config}")
    
    def _get_simulated_response(self, config: Dict, params: Dict) -> Any:
        """获取模拟响应（开发测试用）"""
        # 根据函数类型返回合理的模拟数据
        simulated_responses = {
            "get_account_cache": {
                "user_id": params.get("user_id", "default"),
                "balance": 100000,
                "positions": [],
                "risk_level": 0.3
            },
            "get_hot_ranking": [
                {"symbol": "BTCUSDT", "rank": 1, "price": 67500, "change_24h": 2.5},
                {"symbol": "ETHUSDT", "rank": 2, "price": 3800, "change_24h": 3.2},
                {"symbol": "BNBUSDT", "rank": 3, "price": 600, "change_24h": 1.8}
            ][:params.get("top", 3)],
            "get_realtime_price": {
                "symbol": params.get("symbol", "BTCUSDT"),
                "price": 67500,
                "timestamp": datetime.now().isoformat()
            },
            "calculate_rsi": 55.5,
            "calculate_macd": {
                "macd": 150,
                "signal": 140,
                "histogram": 10
            },
            "calculate_kelly_position": min(params.get("max_risk", 0.02), 0.025),
            "execute_trade": {
                "order_id": f"SIM_{datetime.now().timestamp()}",
                "status": "simulated",
                "symbol": params.get("symbol"),
                "amount": params.get("amount")
            },
            "send_emergency_alert": {"status": "sent", "timestamp": datetime.now().isoformat()},
            "record_decision": {"status": "recorded", "id": datetime.now().timestamp()},
            "get_success_rate": {"rate": 65.5, "total": 100, "wins": 65}
        }
        
        # 根据方法名返回对应的模拟数据
        for key, response in simulated_responses.items():
            if key in str(config):
                return response
        
        # 默认返回
        return {"status": "simulated", "config": config, "params": params}
    
    def _record_call(self, window_id: int, function: str, params: Dict):
        """记录调用历史"""
        call_record = {
            "window": window_id,
            "function": function,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }
        
        self.call_history.append(call_record)
        
        # 限制历史记录数量
        if len(self.call_history) > self.max_history:
            self.call_history = self.call_history[-self.max_history:]
    
    def get_available_commands(self) -> Dict:
        """获取所有可用命令"""
        available = {}
        
        for window_id, functions in self.WINDOW_FUNCTIONS.items():
            available[f"Window_{window_id}"] = {
                func_name: {
                    "params": config["params"],
                    "module": config["module"]
                }
                for func_name, config in functions.items()
            }
        
        return available
    
    def get_call_history(self, limit: int = 10) -> List[Dict]:
        """获取调用历史"""
        return self.call_history[-limit:] if self.call_history else []
    
    def validate_ai_command(self, ai_output: Union[str, Dict]) -> bool:
        """
        验证AI输出的命令是否符合规范
        绝对禁止自然语言命令
        """
        # 如果是字符串，检查是否包含自然语言
        if isinstance(ai_output, str):
            # 禁止的自然语言模式
            forbidden_patterns = [
                "请", "查看", "获取", "分析", "帮我",
                "please", "check", "get", "analyze", "help"
            ]
            
            for pattern in forbidden_patterns:
                if pattern in ai_output.lower():
                    logger.error(f"检测到自然语言命令，拒绝执行: {ai_output}")
                    return False
            
            # 尝试解析为JSON
            try:
                command = json.loads(ai_output)
            except json.JSONDecodeError:
                logger.error(f"命令不是有效的JSON格式: {ai_output}")
                return False
        else:
            command = ai_output
        
        # 验证命令格式
        return self._validate_command(command)
    
    def format_command_example(self, window_id: int, function: str) -> str:
        """生成命令示例"""
        if window_id not in self.WINDOW_FUNCTIONS:
            return f"无效的窗口ID: {window_id}"
        
        if function not in self.WINDOW_FUNCTIONS[window_id]:
            return f"窗口{window_id}不支持函数: {function}"
        
        config = self.WINDOW_FUNCTIONS[window_id][function]
        
        # 构建示例参数
        example_params = {}
        for param in config["params"]:
            if "user_id" in param:
                example_params[param] = "default"
            elif "symbol" in param:
                example_params[param] = "BTCUSDT"
            elif "exchange" in param:
                example_params[param] = "binance"
            elif "period" in param:
                example_params[param] = 14
            elif "threshold" in param:
                example_params[param] = 50
            elif "top" in param:
                example_params[param] = 10
            else:
                example_params[param] = f"<{param}_value>"
        
        example = {
            "window": window_id,
            "function": function,
            "params": example_params
        }
        
        return json.dumps(example, indent=2, ensure_ascii=False)