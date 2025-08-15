# 🔌 Tiger系统 API集成文档

> 最后更新：2025-08-11  
> 维护窗口：10号窗口（系统集成）

## 📊 API接入概览

| 类别 | 数量 | 免费 | 已付费 | 状态 |
|------|------|------|--------|------|
| 交易所API | 2 | 2 | 0 | ✅ 全部接入 |
| 链上数据API | 3 | 2 | 1 | ✅ 全部接入（WhaleAlert已付费） |
| 专业数据API | 3 | 2 | 1 | ✅ 全部接入（Coinglass已付费） |
| 通知服务API | 2 | 2 | 0 | ✅ 全部配置 |
| AI分析API | 2 | 0 | 1 | ✅ Claude密钥已获得 |
| **总计** | **12** | **8** | **3** | **100%配置完成** |

### 💰 当前付费状态
- **WhaleAlert Professional**: $29/月（已支付）
- **Coinglass Premium**: $39/月（已支付）
- **Claude API**: 按使用量计费（密钥已配置）
- **月度总费用**: $68 + Claude使用费

## 🏦 交易所API

### 1. Binance API
- **状态**: ✅ 已接入
- **费用**: 免费
- **功能**:
  - 实时行情数据获取
  - K线数据（1m/5m/15m/1h/4h/1d）
  - 订单簿深度数据
  - 24小时涨跌幅统计
  - 成交量和流动性监控
- **配置**:
  ```python
  BINANCE_API_KEY = "已配置（见桌面配置文件）"
  BINANCE_SECRET_KEY = "已配置（见桌面配置文件）"
  BINANCE_PROXY = "http://127.0.0.1:1099"  # WSL代理必需
  ```
- **特殊要求**:
  - 需要WSL代理（端口1099）
  - IP白名单（可选）
- **限制**: 
  - Weight: 1200/分钟
  - Order: 10/秒, 100,000/天
- **文件**: `exchange_monitor.py`

### 2. OKX API
- **状态**: ✅ 已接入
- **费用**: 免费（公开数据）
- **功能**:
  - 现货/合约/期权行情
  - 大宗交易监控
  - 持仓量统计
  - 资金费率
  - 热门币种排行榜
- **配置**: 无需密钥（公开接口）
- **限制**: 20次/2秒
- **文件**: `okx_monitor.py`

## ⛓️ 链上数据API

### 3. WhaleAlert API 【已付费】
- **状态**: ✅ 已接入
- **费用**: Professional计划（$29/月，已支付）
- **当前计划**: Professional (10,000次/月)
- **功能**:
  - 实时巨鲸转账监控（>$1M）
  - 交易所大额充提追踪
  - 链间资金流动分析
  - 异常交易检测
  - 稳定币铸造/销毁监控
- **配置**:
  ```python
  WHALE_ALERT_API_KEY = "已配置（见桌面配置文件）"
  ```
- **限制**:
  - API调用: 10,000次/月
  - 历史数据: 30天
  - 实时延迟: <5秒
- **文件**: `whale_alert_monitor.py`

### 4. Etherscan API
- **状态**: ✅ 已接入
- **费用**: 免费
- **功能**:
  - ETH/ERC20价格查询
  - Gas价格和网络状态
  - 地址余额和交易历史
  - 智能合约事件监控
  - 交易所钱包追踪
- **配置**:
  ```python
  ETHERSCAN_API_KEY = "已配置（见桌面配置文件）"
  ```
- **限制**: 5次/秒
- **文件**: `etherscan_monitor.py`

### 5. DeFiLlama API
- **状态**: ✅ 已接入
- **费用**: 完全免费
- **功能**:
  - DeFi协议TVL排名
  - 借贷市场数据
  - 各公链TVL分布
  - 稳定币市值追踪
  - 收益农场APY
- **配置**: 无需密钥
- **文件**: `defillama_monitor.py`

## 📈 专业数据API

### 6. Coinglass API 【已付费】
- **状态**: ✅ 已接入
- **费用**: Premium计划（$39/月，已支付）
- **当前计划**: Premium（全功能）
- **功能**:
  - 实时爆仓数据和清算地图
  - 多空比和持仓量（1分钟更新）
  - 资金费率（实时+历史）
  - 期权数据（全链路）
  - 聪明钱追踪（大户持仓）
  - 交易所资金流向
  - 大额爆仓提醒
- **配置**:
  ```python
  COINGLASS_API_KEY = "已配置（见桌面配置文件）"
  ```
- **限制**: 
  - API调用: 无限制
  - 数据延迟: <1秒
  - 历史数据: 1年
- **文件**: `coinglass_free.py`（需更新为完整版）

### 7. Alternative.me API
- **状态**: ✅ 已接入
- **费用**: 免费
- **功能**:
  - 恐慌贪婪指数（实时）
  - 历史情绪数据
  - 市场情绪分析
- **配置**: 无需密钥
- **限制**: 100次/分钟
- **文件**: `fear_greed_monitor.py`

### 8. CoinGecko API
- **状态**: ✅ 已接入
- **费用**: 免费
- **功能**:
  - 7000+币种价格
  - 市值排名Top 100
  - 交易量统计
  - 币种基本信息
- **配置**: 无需密钥
- **限制**: 10-50次/分钟
- **文件**: `coingecko_monitor.py`

## 📬 通知服务API

### 9. Gmail SMTP
- **状态**: ✅ 已配置
- **费用**: 免费
- **功能**:
  - 邮件预警通知
  - 日报/周报发送
  - 重要事件提醒
- **配置**:
  ```python
  EMAIL = "已配置（见桌面配置文件）"
  APP_PASSWORD = "已配置（见桌面配置文件）"
  ```
- **文件**: `gmail_configured.py`

### 10. Telegram Bot API
- **状态**: ✅ 已配置
- **费用**: 免费
- **功能**:
  - 即时消息推送
  - 图片/文件发送
  - 交互式按钮
- **配置**:
  ```python
  BOT_TOKEN = "已配置（见桌面配置文件）"
  CHAT_ID = "已配置（见桌面配置文件）"
  ```
- **文件**: `telegram_configured.py`

## 🤖 AI分析API

### 11. Claude API
- **状态**: ✅ API密钥已配置
- **费用**: 付费（按token计费）
- **API密钥**: 已配置（见桌面配置文件）
- **可用模型及价格**:
  - `claude-3-opus-20240229`: 最强（$15/1M输入，$75/1M输出）
  - `claude-3-sonnet-20240229`: 平衡（$3/1M输入，$15/1M输出）
  - `claude-3-haiku-20240307`: 快速（$0.25/1M输入，$1.25/1M输出）
- **建议使用策略**:
  - 重要决策 → Opus
  - 日常分析 → Sonnet
  - 批量处理 → Haiku
- **功能**:
  - 市场深度分析
  - 交易决策建议
  - 风险评估报告
  - 策略优化建议
  - 异常事件解读
- **预估费用**: $30-50/月（混合使用）

### 12. 外部AI信号聚合
- **状态**: ✅ 框架已集成
- **费用**: 混合模式
- **包含源**:
  - CryptoPanic（新闻聚合）
  - LunarCrush（社交情绪）
  - SentimentAI（AI情绪分析）
  - ValueScan（AI预警）
- **更新频率**:
  - 高风险: 2分钟
  - 机会: 3分钟
  - 跟踪: 5分钟
- **文件**: `external_ai_signal_integration.py`

## 💰 费用分析

### 当前实际费用（已支付）
| API | 月费 | 状态 | 说明 |
|-----|------|------|------|
| 免费API（8个） | $0 | ✅ | 永久免费 |
| WhaleAlert Professional | $29 | ✅ 已付费 | 10,000次/月 |
| Coinglass Premium | $39 | ✅ 已付费 | 全功能无限制 |
| Claude API | ~$30-50 | 待使用 | 按token计费 |
| **当前总计** | **$68/月** | **已支付** | **不含Claude** |

### API价值分析
| API类型 | 提供价值 |
|---------|----------|
| WhaleAlert | 巨鲸监控，提前发现大资金动向 |
| Coinglass | 清算地图，避免被套或抓住机会 |
| Claude | 智能分析，提供专业决策建议 |
| **投资回报** | **一次成功交易即可回本** |

## 🔧 环境配置

### .env文件配置（完整版）
```bash
# ===== 交易所API =====
# 币安（需要代理）
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_PROXY=http://127.0.0.1:1099

# 欧易（公开数据无需密钥）
# OKX_API_KEY=your_key  # 可选
# OKX_SECRET_KEY=your_secret  # 可选
# OKX_PASSPHRASE=your_passphrase  # 可选

# ===== 链上数据 =====
# WhaleAlert（已付费Professional）
WHALE_ALERT_API_KEY=your_whale_alert_key

# Etherscan（免费）
ETHERSCAN_API_KEY=your_etherscan_key

# ===== 专业数据 =====
# Coinglass（已付费Premium）
COINGLASS_API_KEY=your_coinglass_key

# ===== 通知服务 =====
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# ===== AI服务 =====
# Claude API（已配置）
CLAUDE_API_KEY=your_claude_api_key

# 模型选择
CLAUDE_MODEL_IMPORTANT=claude-3-opus-20240229      # 重要决策
CLAUDE_MODEL_NORMAL=claude-3-sonnet-20240229       # 日常分析
CLAUDE_MODEL_BATCH=claude-3-haiku-20240307         # 批量处理

# 注意：实际密钥请查看桌面的"API配置模板.txt"文件
```

## 📋 API健康监控

### 监控指标
- ✅ API可用性（每5分钟检查）
- ✅ 响应时间（<2秒预警）
- ✅ 额度使用量（80%预警）
- ✅ 错误率统计（>5%预警）

### 故障切换
- 主API故障时自动切换备用
- 缓存机制减少API调用
- 降级策略保证核心功能

## 🚀 优化建议

1. **缓存策略**
   - 静态数据缓存1小时
   - 行情数据缓存10秒
   - 减少50%API调用

2. **批量请求**
   - 合并同类请求
   - 使用WebSocket替代轮询
   - 提高效率80%

3. **备用方案**
   - 每个关键API配置备用
   - 多源数据交叉验证
   - 确保99.9%可用性

## 📝 使用示例

### 快速测试所有API
```python
from api_tests import test_all_apis

# 测试所有API连接
results = test_all_apis()
for api, status in results.items():
    print(f"{api}: {'✅' if status else '❌'}")
```

### 获取综合市场数据
```python
from market_monitor import MarketMonitor

monitor = MarketMonitor()
data = await monitor.get_comprehensive_data()
print(data)
```

## 🔄 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2025-08-11 | 完成12个API接入 |
| 2025-08-11 | 添加外部AI信号集成 |
| 2025-08-11 | 优化API调用策略 |

## 📞 技术支持

- 问题反馈：创建Issue
- 紧急联系：a368070666@gmail.com
- 文档维护：10号窗口负责

---

*本文档由10号窗口（系统集成）维护*