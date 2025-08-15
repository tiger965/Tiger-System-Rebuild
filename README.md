# 🐯 Tiger智能交易监控系统

> 一个集成12个专业API的加密货币智能监控系统  
> 版本：v1.0.0 | 更新：2025-08-11

## 🆕 最新更新（2025-08-11）
- ✅ **12个API全面集成** - 覆盖交易所、链上、DeFi、AI分析
- ✅ **外部AI信号融合** - 多源AI预警2分钟响应
- ✅ **双交易所同时监控** - OKX和币安实时数据
- ✅ **WSL独立代理** - 自动处理币安地区限制
- ✅ **历史数据下载** - 310万条K线数据（364MB）
- ✅ **上帝视角监控** - 完整API文档已更新

## 🎯 系统概述

Tiger系统是一个全方位的加密货币市场监控平台，通过集成多个专业API和AI分析，提供实时市场监控、风险预警、智能决策支持。

### 核心特性
- 🔍 **全方位监控**：12个专业API数据源
- 🤖 **AI智能分析**：Claude AI + 外部AI信号融合
- ⚡ **实时预警**：2分钟内响应重大事件
- 📊 **专业数据**：交易所、链上、DeFi全覆盖
- 🔔 **多渠道通知**：邮件、Telegram即时推送

## 📦 已接入API（12个）

| 类别 | API名称 | 费用 | 状态 | 用途 |
|------|---------|------|------|------|
| **交易所** | Binance | 免费 | ✅ | 实时行情、K线、深度 |
| | OKX | 免费 | ✅ | 现货、合约、期权数据 |
| **链上数据** | WhaleAlert | 免费额度 | ✅ | 巨鲸转账监控 |
| | Etherscan | 免费 | ✅ | ETH链上数据、Gas费 |
| | DeFiLlama | 免费 | ✅ | DeFi TVL、借贷数据 |
| **专业数据** | Coinglass | 免费额度 | ✅ | 清算、多空比、资金费率 |
| | Alternative.me | 免费 | ✅ | 恐慌贪婪指数 |
| | CoinGecko | 免费 | ✅ | 币种信息、市值排名 |
| **通知服务** | Gmail | 免费 | ✅ | 邮件通知 |
| | Telegram | 免费 | ✅ | 即时消息推送 |
| **AI分析** | Claude API | 待接入 | ⏳ | 智能分析决策 |
| | 外部AI信号 | 部分免费 | ✅ | 多源AI预警聚合 |

详细API文档：[📚 API集成完整文档](docs/API_INTEGRATION.md)

## 🚀 快速开始

```bash
# 一键启动（推荐）
python3 start.py
```

系统会自动：
1. 启动WSL独立代理（币安需要，端口1099）
2. 同时连接OKX和币安交易所
3. 开始实时监控和价差分析
4. 集成所有API数据源
5. 启动AI信号监控

## ✅ 系统状态

| 组件 | 状态 | 说明 |
|------|------|------|
| OKX数据 | ✅ 正常 | 直连，无需代理 |
| 币安数据 | ✅ 正常 | 通过WSL代理(端口1099) |
| 历史数据 | ✅ 310万条 | 364MB K线数据 |
| 代理系统 | ✅ 运行中 | WSL独立代理 |

## 📊 核心功能（纯监控分析）

### 1. 双交易所实时监控 🆕
- **OKX**: 直连访问，无需代理
- **币安**: 通过WSL独立代理（自动启动）
- **实时价差**: 自动计算套利机会
- **同步获取**: 并行处理，数据同步

### 2. 历史数据系统 🆕
- **数据量**: 310万条K线数据
- **大小**: 364MB
- **币种**: BTC, ETH, SOL等10个主流币种
- **用途**: 回测、机器学习、趋势分析

### 3. WSL独立代理 🆕
- **端口**: 1099（自动配置）
- **类型**: SOCKS5代理
- **特点**: 不依赖Windows Shadowsocks
- **命令**: `pproxy -l socks5://127.0.0.1:1099 -r ss://...`

### 4. 上帝视角监控 🆕
- **交易所**: OKX, 币安, Gate.io, KuCoin
- **链上数据**: BTC网络, ETH Gas, Mempool
- **DeFi协议**: TVL, Uniswap, Compound
- **社交情绪**: 恐慌贪婪指数, 热门币种
- **新闻资讯**: CryptoCompare, CoinDesk
- **市场指标**: 总市值, BTC占比, 稳定币供应

**注意**：本系统是纯监控分析工具，不包含任何交易功能

## 📁 项目结构

```
TigerSystem/
├── config/
│   ├── api_keys.yaml         # API密钥（已配置OKX）
│   ├── shadowsocks.json      # 代理配置 🆕
│   └── binance_config.yaml   # 币安代理设置 🆕
├── data/
│   └── historical/           # 历史数据（364MB） 🆕
│       ├── BTC_USDT_*.csv   # 比特币K线数据
│       ├── ETH_USDT_*.csv   # 以太坊K线数据
│       └── ...              # 其他币种数据
├── start.py                  # 🎯 主启动文件（自动配置代理）
├── run_system.py            # 系统核心
├── god_view_apis.py         # 上帝视角监控 🆕
├── download_all_data.py     # 历史数据下载工具 🆕
└── SYSTEM_STATUS.md         # 详细状态文档
```

## 🔑 关键信息

### OKX配置（已完成）
- API已配置，只读权限
- 无需代理，直接访问

### 币安访问（自动处理）
- 地区限制，需要代理
- WSL独立代理：`127.0.0.1:1099`
- 自动启动，无需手动配置

### 代理信息
```
服务器：新加坡（43.160.195.89:443）
加密：aes-256-gcm
WSL端口：1099
```

## 🛠️ 使用指南

### 1. 查看双交易所实时数据
```bash
python3 start.py
# 输出示例：
# OKX    : $120,100.00
# Binance: $120,095.00
# 价差   : $5.00 (0.004%)
# 💰 套利: Binance买 → OKX卖
```

### 2. 运行上帝视角扫描
```bash
python3 god_view_apis.py
# 扫描20+数据源，包括：
# - 4个交易所
# - 3个链上数据
# - DeFi TVL
# - 恐慌贪婪指数
# - 新闻热点
```

### 3. 下载历史数据
```bash
python3 download_all_data.py
# 下载指定币种的历史K线数据
```

### 4. 查看代理状态
```bash
# 检查WSL代理
ps aux | grep pproxy
netstat -an | grep 1099

# 如需重启代理
pkill -f pproxy
python3 start.py  # 会自动重启
```

## 🔧 故障排除

### 币安显示"无数据"？
```bash
# 1. 检查代理是否运行
ps aux | grep pproxy

# 2. 如果没有，手动启动
pproxy -l socks5://127.0.0.1:1099 -r ss://aes-256-gcm:kcS95i51Wt4PPu01@43.160.195.89:443 &

# 3. 测试币安连接
python3 -c "import requests; r=requests.get('https://api.binance.com/api/v3/ping', proxies={'http':'socks5://127.0.0.1:1099','https':'socks5://127.0.0.1:1099'}); print('成功' if r.status_code==200 else '失败')"
```

### OKX显示"无数据"？
```bash
# 测试OKX连接（直连，无需代理）
curl https://www.okx.com/api/v5/public/time
```

### 历史数据在哪里？
```bash
# 查看历史数据
ls -lh data/historical/
# 总大小：364MB
# 文件数：10个币种的CSV文件
```

## 📈 使用示例

启动后你会看到：
```
#1 07:30:45
OKX    : $120,100.00
Binance: $120,095.00
价差   : $5.00 (0.004%)
💰 套利: Binance买 → OKX卖
```

## ⚠️ 重要提醒

1. **不要提交api_keys.yaml到GitHub**
2. **代理密码已在代码中，注意保密**
3. **系统完全独立运行，不依赖Windows**

## 📝 更多信息

详细配置和技术细节见：[SYSTEM_STATUS.md](SYSTEM_STATUS.md)

---
系统由10号窗口维护 | 最后更新：2025-08-11