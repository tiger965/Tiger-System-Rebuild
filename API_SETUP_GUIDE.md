# 🔑 Tiger系统 API配置指南

## 一、核心API（推荐配置）

### 1. 🟡 **币安(Binance) API** - 市场数据
- **用途**: 获取实时价格、K线、成交量、深度数据
- **必要性**: 强烈推荐（主要数据源）
- **获取方法**:
  1. 登录 [币安](https://www.binance.com)
  2. 进入 用户中心 → API管理
  3. 创建API（只勾选"读取"权限）
  4. 保存 API Key 和 Secret Key
- **费用**: 免费

### 2. 🟡 **Telegram Bot** - 实时通知
- **用途**: 接收交易信号、风险警报、系统通知
- **必要性**: 推荐
- **获取方法**:
  1. Telegram中搜索 @BotFather
  2. 发送 `/newbot` 创建机器人
  3. 获得 Bot Token
  4. 创建群组，将机器人加入
  5. 获取 Chat ID
- **费用**: 免费

### 3. 🟢 **Claude AI** - 智能分析
- **用途**: AI市场分析、策略优化、智能决策
- **必要性**: 可选（增强功能）
- **获取方法**:
  1. 注册 [Anthropic](https://console.anthropic.com)
  2. 创建 API Key
- **费用**: 按使用量计费（约$0.003/1K tokens）

---

## 二、可选API（增强功能）

### 4. **CoinGecko** - 币种信息
- **用途**: 获取币种基础信息、市值排名
- **获取**: [CoinGecko API](https://www.coingecko.com/api)
- **费用**: 免费版 50次/分钟

### 5. **Twitter/X** - 社交分析
- **用途**: 社交媒体情绪分析、热点追踪
- **获取**: [Twitter Developer](https://developer.twitter.com)
- **费用**: 基础版 $100/月

### 6. **Etherscan** - 链上数据
- **用途**: 以太坊链上数据、大额转账监控
- **获取**: [Etherscan API](https://etherscan.io/apis)
- **费用**: 免费版 5次/秒

---

## 三、快速配置

### 方法1：使用配置向导（推荐）
```bash
python3 setup_api_keys.py
```

### 方法2：手动编辑配置文件
编辑 `config/api_keys.yaml`:
```yaml
# 币安API（推荐）
binance_api_key: 'your_api_key_here'
binance_secret: 'your_secret_here'

# Telegram通知（推荐）
telegram_bot_token: 'your_bot_token'
telegram_chat_id: 'your_chat_id'

# Claude AI（可选）
claude_api_key: 'your_claude_key'

# 其他可选
coingecko_api_key: ''
twitter_api_key: ''
openai_api_key: ''
```

---

## 四、功能对应关系

| 功能 | 需要的API | 优先级 |
|------|-----------|--------|
| 📊 实时行情 | Binance | 必需 |
| 📈 K线数据 | Binance | 必需 |
| 🔔 实时通知 | Telegram | 推荐 |
| 🤖 AI分析 | Claude/OpenAI | 可选 |
| 💬 情绪分析 | Twitter | 可选 |
| ⛓️ 链上监控 | Etherscan | 可选 |
| 📋 币种信息 | CoinGecko | 可选 |

---

## 五、最小配置建议

如果你只想快速体验系统，最少只需配置：

### 🔴 必需配置（至少一个）：
- **Binance API** - 获取市场数据

### 🟡 建议额外配置：
- **Telegram Bot** - 接收通知
- **Claude/OpenAI** - AI分析

---

## 六、测试API连接

配置完成后，运行以下命令测试：
```bash
python3 -c "
from config import api_keys
import requests

# 测试Binance
if api_keys.binance_api_key:
    r = requests.get('https://api.binance.com/api/v3/time')
    print('Binance API:', '✅ 正常' if r.status_code == 200 else '❌ 失败')

print('配置完成！')
"
```

---

## 七、安全提示

⚠️ **重要安全提示**:
1. **永远不要** 给API配置交易权限，只需要读取权限
2. **永远不要** 将API密钥提交到Git
3. **定期更换** API密钥
4. **使用IP白名单** 限制API访问（如果平台支持）

---

## 八、常见问题

**Q: 不配置API能用吗？**
A: 可以运行系统框架，但无法获取实时数据

**Q: 哪个API最重要？**
A: Binance API最重要，是主要数据源

**Q: API要收费吗？**
A: Binance和Telegram免费，Claude按使用量收费

**Q: 如何保护API密钥？**
A: 密钥保存在本地config文件，不要上传到GitHub

---

## 快速开始

1. 最简配置（只配置Binance）：
```bash
# 编辑文件
nano config/api_keys.yaml

# 添加Binance API
binance_api_key: 'your_key'
binance_secret: 'your_secret'
```

2. 启动系统：
```bash
python3 tiger_control.py
```

完成！系统会自动使用配置的API获取数据。