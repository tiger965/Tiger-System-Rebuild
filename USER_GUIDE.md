# Tiger系统使用手册

## 📋 目录
1. [新功能介绍](#新功能介绍)
2. [快速开始](#快速开始)
3. [双交易所监控](#双交易所监控)
4. [历史数据使用](#历史数据使用)
5. [代理配置说明](#代理配置说明)
6. [上帝视角监控](#上帝视角监控)
7. [常见问题](#常见问题)

## 🆕 新功能介绍

### 2025-08-11 更新内容
1. **双交易所同时监控** - 实时获取OKX和币安数据，自动计算价差
2. **WSL独立代理系统** - 自动处理币安地区限制，无需手动配置
3. **历史数据系统** - 310万条K线数据，支持回测和分析
4. **上帝视角监控** - 整合20+免费数据源，全方位市场监控

## 🚀 快速开始

### 一键启动
```bash
cd /mnt/c/Users/tiger/TigerSystem
python3 start.py
```

系统会自动：
1. 检测并启动WSL代理（如需要）
2. 连接OKX（直连）
3. 连接币安（通过代理）
4. 开始实时监控

## 📊 双交易所监控

### 功能说明
- **并行获取**: 同时从OKX和币安获取数据
- **价差分析**: 实时计算价格差异
- **套利提示**: 当价差超过0.1%时提示套利机会

### 使用方法
```bash
# 方式1：完整系统启动
python3 start.py

# 方式2：仅运行监控
python3 run_system.py
```

### 输出示例
```
#1 07:30:45
OKX    : $120,100.00
Binance: $120,095.00
价差   : $5.00 (0.004%)
💰 套利: Binance买 → OKX卖
```

## 📈 历史数据使用

### 数据概览
- **总量**: 310万条K线数据
- **大小**: 364MB
- **币种**: BTC, ETH, SOL, BNB, DOGE, AVAX, LINK, DOT, MATIC, ADA
- **位置**: `data/historical/`

### 查看数据
```bash
# 列出所有历史数据文件
ls -lh data/historical/

# 查看BTC数据前10行
head data/historical/BTC_USDT_*.csv

# 统计数据行数
wc -l data/historical/*.csv
```

### 使用数据进行分析
```python
import pandas as pd

# 读取BTC历史数据
btc_data = pd.read_csv('data/historical/BTC_USDT_2020-01-01_2025-01-09.csv')
print(f"数据量: {len(btc_data)}条")
print(f"时间范围: {btc_data['date'].min()} 到 {btc_data['date'].max()}")
```

### 重新下载数据
```bash
# 如需更新数据
python3 download_all_data.py
```

## 🔒 代理配置说明

### WSL独立代理特点
- **端口**: 1099
- **类型**: SOCKS5
- **服务器**: 新加坡（43.160.195.89:443）
- **加密**: aes-256-gcm

### 自动管理
系统会自动：
1. 检测代理状态
2. 需要时启动代理
3. 只对币安请求使用代理
4. OKX直连不走代理

### 手动管理（如需要）
```bash
# 查看代理进程
ps aux | grep pproxy

# 停止代理
pkill -f pproxy

# 手动启动代理
pproxy -l socks5://127.0.0.1:1099 -r ss://aes-256-gcm:kcS95i51Wt4PPu01@43.160.195.89:443 &

# 测试代理
curl --socks5 127.0.0.1:1099 https://api.binance.com/api/v3/ping
```

## 🔮 上帝视角监控

### 功能说明
整合多个免费数据源，提供全方位市场监控

### 数据源列表
| 类别 | 数据源 | 数据内容 |
|------|--------|---------|
| 交易所 | OKX, 币安, Gate.io, KuCoin | 实时价格、成交量 |
| 链上数据 | Blockchain.info, Etherscan, Mempool | 网络状态、Gas费用 |
| DeFi | DeFi Llama, Uniswap, Compound | TVL、流动性 |
| 情绪指标 | CoinGecko, Alternative.me | 热门币种、恐慌贪婪指数 |
| 新闻 | CryptoCompare, CoinDesk | 最新资讯 |
| 市场指标 | CoinGecko Global | 总市值、BTC占比 |

### 使用方法
```bash
# 运行完整扫描
python3 god_view_apis.py
```

### 输出示例
```
🔮 上帝视角监控系统 - 全面扫描
============================================================
📊 交易所数据
✅ OKX: 数据正常
✅ 币安: 数据正常
✅ Gate.io: 数据正常
✅ KuCoin: 数据正常

⛓️ 链上数据
✅ BTC网络: 哈希率 0.92 TH/s
✅ ETH Gas: 1.25 Gwei
✅ BTC费用: 快速 6 sat/vB

💬 社交情绪
✅ 恐慌贪婪指数: 70 (Greed)
✅ 热门币种: Zora, Pump.fun, Ethereum
```

## ❓ 常见问题

### Q1: 为什么币安需要代理？
**A**: 币安在某些地区有访问限制（返回451错误），系统自动使用代理绕过限制。

### Q2: 代理会影响其他网络吗？
**A**: 不会。代理只用于币安API请求，其他所有网络（包括OKX）都是直连。

### Q3: 历史数据可以用来做什么？
**A**: 
- 回测交易策略
- 训练机器学习模型
- 分析历史趋势
- 计算技术指标

### Q4: 系统会自动交易吗？
**A**: 不会。这是纯监控分析系统，不包含任何交易功能。

### Q5: 如何更新到最新代码？
```bash
git pull origin feature/window-10-integration-clean
```

### Q6: 代理连接失败怎么办？
1. 检查进程：`ps aux | grep pproxy`
2. 重启代理：`pkill -f pproxy && python3 start.py`
3. 检查端口：`netstat -an | grep 1099`

### Q7: 可以添加更多交易所吗？
**A**: 可以。系统框架支持扩展，在`god_view_apis.py`中添加新的数据源即可。

## 📞 支持

如遇到问题：
1. 查看错误日志：`tail -f /tmp/pproxy.log`
2. 查看系统状态：`python3 run_system.py`
3. 重新初始化：`python3 start.py`

---
文档更新日期：2025-08-11
系统版本：v10.1