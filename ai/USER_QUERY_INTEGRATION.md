# 用户主动查询功能 - 集成说明

## ⚠️ 重要声明

**如果其他窗口（1-9号）未与6号窗口同步实现用户主动查询功能的接口对接，则由10号窗口负责补全所有集成工作。**

## 📋 需要集成的接口

### 1. 从2号窗口获取实时数据
```python
# user_query.py 第273行
async def _fetch_market_data(self, symbol: str) -> Dict[str, Any]:
    # TODO: 需要从2号窗口获取实时数据
    # 当前使用模拟数据，需要替换为：
    from window2.market_data import get_realtime_data
    return await get_realtime_data(symbol)
```

### 2. 从3号窗口获取链上和社交数据
```python
# 需要在查询时获取：
- 链上活动数据
- 社交媒体情绪
- 新闻事件
```

### 3. 从4号窗口获取技术指标
```python
# 需要获取：
- RSI, MACD, 布林带等指标
- 支撑阻力位
- 形态识别结果
```

### 4. 从5号窗口获取交易员数据
```python
# 短线查询时需要：
- 顶级交易员当前持仓
- 近期操作记录
- 跟单建议
```

### 5. 向7号窗口发送风险评估
```python
# 用户查询后需要：
- 将决策发送给风控系统
- 获取风险审核结果
```

### 6. 向8号窗口发送通知
```python
# 查询完成后：
- 发送查询结果通知
- 重要决策推送
```

## 🔧 集成方式

### 方案A：直接函数调用
```python
# 在user_query.py中导入其他窗口模块
from window2.market_data import MarketDataProvider
from window3.chain_social import ChainSocialAnalyzer
from window4.technical import TechnicalIndicators
from window5.trader_monitor import TraderMonitor

class UserQueryHandler:
    def __init__(self):
        self.market_data = MarketDataProvider()
        self.chain_social = ChainSocialAnalyzer()
        self.technical = TechnicalIndicators()
        self.trader_monitor = TraderMonitor()
```

### 方案B：消息队列（推荐）
```python
# 使用Redis或RabbitMQ
import redis

class UserQueryHandler:
    def __init__(self):
        self.redis = redis.Redis()
    
    async def _fetch_market_data(self, symbol: str):
        # 发送请求到2号窗口
        request_id = str(uuid.uuid4())
        self.redis.publish('market_data_request', json.dumps({
            'request_id': request_id,
            'symbol': symbol,
            'requester': 'window6'
        }))
        
        # 等待响应
        response = await self._wait_for_response(request_id)
        return response
```

## 📊 用户查询流程

```
用户发起查询
    ↓
6号窗口接收请求
    ↓
收集所需数据：
├── 2号窗口：市场数据
├── 3号窗口：链上/社交
├── 4号窗口：技术指标
└── 5号窗口：交易员数据
    ↓
构建查询上下文
    ↓
调用Claude API
    ↓
解析AI响应
    ↓
发送结果：
├── 7号窗口：风控审核
├── 8号窗口：用户通知
└── 返回给用户
```

## 🎯 10号窗口的补全责任

如果在系统集成时发现以下情况，10号窗口需要补全：

1. **数据获取接口缺失**
   - 实现统一的数据获取层
   - 为每个窗口创建数据适配器

2. **通信机制未建立**
   - 搭建消息队列系统
   - 实现窗口间RPC调用

3. **数据格式不统一**
   - 创建数据转换层
   - 统一各窗口的数据格式

4. **错误处理不完善**
   - 实现降级策略
   - 添加重试机制

## 📝 验收标准

用户主动查询功能必须满足：

- [ ] 8种查询类型全部可用
- [ ] 响应时间 < 30秒
- [ ] 数据来源完整（2-5号窗口）
- [ ] 风控审核通过（7号窗口）
- [ ] 通知发送成功（8号窗口）
- [ ] 错误处理完善
- [ ] 降级策略有效

## 🚨 注意事项

1. **优先级**: 用户主动查询应该有较高优先级
2. **成本控制**: 避免用户频繁查询导致成本失控
3. **缓存策略**: 相同查询5分钟内使用缓存
4. **并发限制**: 同一用户同时只能有1个查询
5. **权限控制**: 某些高级查询需要权限验证

## 📞 联系方式

如有集成问题，请联系：
- 6号窗口：AI决策系统
- 10号窗口：系统集成负责人

---

**重要提醒：此功能是用户体验的关键部分，必须确保完整实现！**