# Window 1 - 数据库工具

## 概述

Window 1 是Tiger Trading System的数据存储和记忆中枢，负责管理所有数据的存储、缓存和查询。

## 功能特性

### 1. 账户缓存系统 (account_cache.py)
- 7天历史数据缓存
- 实时账户余额跟踪
- 持仓信息管理
- 风险等级计算

### 2. 决策记录系统 (decision_tracker.py)
- AI决策记录和跟踪
- 决策状态管理
- 执行结果追踪
- 历史决策查询

### 3. 成功率计算系统 (success_calculator.py)
- 多维度成功率统计
- 策略效果评估
- 风险调整指标计算
- 智能推荐建议

### 4. 统一API接口 (api_interface.py)
- Window 6调用接口
- 批量查询支持
- 健康检查
- 性能监控

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- psycopg2-binary: PostgreSQL连接
- redis: 缓存系统
- numpy: 数学计算
- pytest-asyncio: 异步测试

## 使用方法

### 1. 作为模块使用

```python
from database.api_interface import get_window1_api

# 获取API实例
api = get_window1_api()

# 获取账户缓存
account = await api.get_account_cache("user_id")

# 记录决策
await api.record_decision({
    "type": "buy",
    "symbol": "BTCUSDT",
    "price": 50000,
    "amount": 0.1
})

# 获取成功率
success_rate = await api.get_success_rate("last_30_days")
```

### 2. 作为服务运行

```bash
# 运行服务
python window1_main.py

# 测试模式（60秒）
python window1_main.py --test-mode 60

# 24小时测试
python window1_main.py --test-mode 24h

# 性能测试
python window1_main.py --performance-test
```

### 3. Window 6调用示例

```python
command = {
    "window": 1,
    "function": "get_account_cache",
    "params": {"user_id": "default"}
}

result = await process_command(command)
```

## 测试

```bash
# 运行所有测试
python -m pytest tests/test_window1.py -v

# 运行性能测试
python window1_main.py --performance-test

# 运行覆盖率测试
python -m pytest --cov=. --cov-report=html
```

## API文档

### get_account_cache(user_id)
获取7天账户缓存数据

**参数：**
- user_id: 用户ID（默认："default"）

**返回：**
```json
{
    "total_balance": 100000,
    "available": 70000,
    "positions": [...],
    "last_7d_trades": [...],
    "risk_level": 0.3
}
```

### record_decision(decision_data)
记录AI决策

**参数：**
- decision_data: 决策数据字典

**返回：**
- bool: 是否记录成功

### get_success_rate(period)
获取成功率统计

**参数：**
- period: 统计周期（"last_7_days", "last_30_days", "last_90_days"）

**返回：**
```json
{
    "total_decisions": 28,
    "success_rate": 0.678,
    "profit_rate": 0.032,
    "win_rate": 0.65,
    "overall_metrics": {...},
    "strategy_metrics": {...}
}
```

### query_kline_patterns(symbol, pattern_type, timeframe, limit)
查询K线形态

**参数：**
- symbol: 交易对
- pattern_type: 形态类型
- timeframe: 时间周期
- limit: 返回数量

**返回：**
- List[Dict]: K线形态列表

## 性能指标

基于性能测试结果：

- 账户查询：< 1ms（内存缓存）
- 决策记录：< 2ms
- 成功率计算：< 100ms
- 批量查询：100个查询 < 200ms
- 并发能力：> 1000 QPS

## 架构设计

```
Window 1
├── API接口层 (api_interface.py)
│   └── 统一对外接口
├── 业务逻辑层
│   ├── 账户缓存 (account_cache.py)
│   ├── 决策跟踪 (decision_tracker.py)
│   └── 成功率计算 (success_calculator.py)
└── 数据访问层 (dal/)
    └── 基础DAL (base_dal.py)
```

## 数据库模式

支持PostgreSQL和Redis：
- PostgreSQL: 持久化存储
- Redis: 高速缓存

在无数据库环境下自动切换到模拟模式。

## 版本历史

- v1.1: 初始版本，实现基础功能
- 待发布: v1.2 优化性能

## 联系方式

负责人：Window 1开发组
验收人：Tiger（总工）