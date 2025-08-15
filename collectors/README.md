# Window 3 - 数据采集工具

## 📌 重要说明

Window 3是Tiger交易系统的**纯数据收集工具**，不包含任何分析逻辑。

### ⚠️ 核心定位
- **是什么**：数据采集管道、API调用工具、触发系统
- **不是什么**：不是分析系统、不是决策系统、不生成交易信号

### 🔴 架构位置
```
Window 2 (交易所数据) → Window 3 (数据汇聚) → Window 6 (AI分析大脑)
                            ↑
                     各种外部数据源
```

## 🚀 核心功能

### 1. 三级监控激活系统（核心）
- **文件**：`monitoring_activation_system.py`
- **功能**：监控市场变化，根据阈值触发不同级别警报
- **触发阈值**：
  - 一级：价格变化0.3%、成交量增长50%、转账5万美元
  - 二级：价格变化0.5%、成交量增长100%、转账10万美元
  - 三级：价格变化1.0%、成交量增长200%、转账100万美元
  - VIP账号（马斯克等）任何动作直接三级触发

### 2. 数据链整合器
- **文件**：`data_chain_integrator.py`
- **功能**：整合多源数据，发现关联关系
- **数据源**：
  - Window 2数据（价格、资金费率、储备）
  - 链上数据（巨鲸、Gas、DeFi）
  - 社交数据（Twitter、Reddit、恐慌贪婪）
  - 新闻数据

### 3. API接口
- **文件**：`api_interface.py`
- **功能**：为Window 6提供标准化接口
- **主要接口**：
  - `get_intelligence_package()` - 获取综合情报包
  - `track_whale_transfers()` - 追踪巨鲸转账
  - `crawl_twitter()` - 爬取Twitter数据
  - `monitor_kol_accounts()` - 监控KOL账号

## 📦 安装依赖

```bash
pip install aiohttp asyncio
```

## 🏃 运行方式

### 正常运行
```bash
cd /mnt/c/Users/tiger/Tiger-Trading-System-Rebuild/collectors
python3 window3_main.py
```

### 测试模式
```bash
python3 window3_main.py --test
```

## 🔌 Window 6调用示例

```python
# Window 6调用Window 3获取情报包
command = {
    "window": 3,
    "function": "get_intelligence_package",
    "params": {
        "symbol": "BTC",
        "include_window2_data": True,
        "analysis_depth": "deep"
    }
}

# Window 3返回纯数据，不含分析结论
response = {
    "package_id": "W3_PKG_1_1736936700",
    "raw_data": {...},      # 原始数据
    "correlations": [...],  # 数据关联
    "data_quality": {...},  # 数据质量指标
    # 注意：没有交易建议、没有买卖信号
}
```

## 📊 数据流向

1. **输入**：
   - Window 2的交易所数据
   - WhaleAlert巨鲸数据
   - CoinGecko价格数据
   - 社交媒体情绪数据

2. **处理**：
   - 数据收集
   - 格式标准化
   - 关联检测
   - 触发判断

3. **输出**：
   - 发送触发信号到Window 6
   - 提供原始数据包
   - 不含任何分析结论

## ⚠️ 注意事项

1. **API配额管理**
   - WhaleAlert: 个人级别，每小时100个警报
   - CryptoPanic: 配额已用完，需要等待重置
   - CoinGecko: 免费API，有频率限制

2. **错误处理**
   - 所有API调用都有重试机制
   - 失败的触发信号会保存到文件
   - 数据缓存30秒，减少重复调用

3. **性能要求**
   - 价格监控延迟 < 1秒
   - 触发响应 < 100ms
   - 24/7稳定运行

## 🔧 配置文件

API密钥已硬编码在`api_interface.py`中：
- WhaleAlert: `pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU`
- CryptoPanic: `e79d3bb95497a40871d90a82056e3face2050c53`

## 📝 版本历史

- **v3.1** - 重建正确的Window 3架构
  - 移除所有分析功能
  - 实现三级监控激活系统
  - 添加数据链整合器
  - 创建标准API接口

## 🐛 已知问题

1. CryptoPanic API配额已耗尽
2. Twitter爬虫需要配置API密钥
3. ValueScan需要登录凭证

## 📞 联系方式

- 项目负责人：Tiger
- GitHub: https://github.com/tiger965/Tiger-Trading-System-Rebuild

---

**记住：Window 3是纯工具，只收集数据，不做分析！**