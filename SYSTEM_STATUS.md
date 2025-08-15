# Tiger系统状态文档
最后更新：2025-08-11

## 🔴 重要信息汇总

### 已完成配置
1. **OKX API** ✅
   - API Key: `79d7b5b4-2e9b-4a31-be9c-95527d618739`
   - Secret: `070B16A29AF22C13A67D9CB807B5693D`
   - Passphrase: `Yzh198796&`
   - 权限：只读
   - 连接方式：直连（无需代理）

2. **币安数据访问** ✅ 已完成
   - 代理配置完成（端口1099）
   - 可以获取所有公开市场数据
   - 实时价格、K线、深度等数据正常
   - 不需要API密钥（纯监控系统）

2. **历史数据** ✅
   - 数量：310万条K线数据
   - 大小：364MB
   - 位置：`data/historical/`
   - 包含：BTC、ETH、SOL等主要币种

3. **币安代理** ✅
   - Shadowsocks服务器：`43.160.195.89:443`
   - 密码：`kcS95i51Wt4PPu01`
   - 加密：`aes-256-gcm`
   - WSL代理端口：`1099`
   - 使用命令：`pproxy -l socks5://127.0.0.1:1099 -r ss://aes-256-gcm:kcS95i51Wt4PPu01@43.160.195.89:443`

### 系统架构
```
双交易所数据采集：
- OKX：直接连接（无需代理）
- 币安：通过WSL独立代理（端口1099）

独立运行特性：
- 不依赖Windows Shadowsocks
- WSL内部独立代理
- 自动启动和管理
```

## 📊 运行状态

### 快速启动
```bash
# 主命令（推荐）
python3 start.py

# 备用命令
python3 run_system.py
```

### 当前功能
- ✅ OKX实时数据获取
- ✅ 币安通过代理获取（WSL独立）
- ✅ 双交易所同时监控
- ✅ 价差分析和套利提示
- ✅ 历史数据回测支持

## 🔧 关键配置文件

1. **config/api_keys.yaml** - API密钥配置
2. **config/shadowsocks.json** - 代理服务器信息
3. **config/binance_config.yaml** - 币安代理设置
4. **data/historical/** - 历史K线数据

## ⚠️ 注意事项

1. **币安必须通过代理访问**（地区限制451错误）
2. **WSL代理端口1099**（独立于Windows）
3. **OKX可以直连**（无需任何代理）

## 🚀 操作指南

### 启动系统
1. 运行 `python3 start.py`
2. 系统会自动：
   - 启动WSL独立代理（端口1099）
   - 连接OKX（直连）
   - 连接币安（通过代理）
   - 开始双交易所监控

### 验证连接
```python
# 测试OKX
curl https://www.okx.com/api/v5/public/time

# 测试币安（需要代理）
curl --socks5 127.0.0.1:1099 https://api.binance.com/api/v3/ping
```

### 查看代理状态
```bash
# 检查端口
netstat -an | grep 1099

# 查看进程
ps aux | grep pproxy
```

## 📝 开发备注

### 为什么需要独立代理？
- Windows Shadowsocks配置为PAC模式（只有特定网站走代理）
- WSL无法访问Windows的127.0.0.1:1080
- 解决方案：WSL内部运行独立的pproxy代理

### 技术栈
- Python 3.10
- pproxy（代理工具）
- requests + PySocks（HTTP客户端）
- pandas（数据分析）

### GitHub提交注意
- **不要提交** config/api_keys.yaml（包含密钥）
- **不要提交** 代理密码和服务器信息
- 使用.gitignore排除敏感文件

## 🎯 下一步计划
- [ ] 添加更多交易对
- [ ] 实现自动交易功能
- [ ] 优化套利算法
- [ ] 添加Web界面

---
文档由10号窗口维护
联系：通过主窗口转达