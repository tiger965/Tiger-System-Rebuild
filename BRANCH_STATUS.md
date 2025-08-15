# Tiger系统 - 分支状态总览

## 🎯 当前状态 (2025-08-11)

### ✅ 已完成整理的分支

| 窗口 | 功能模块 | 干净分支名 | 状态 | 主要目录 |
|------|---------|-----------|------|---------|
| 1号 | 数据库基础设施 | feature/window-1-database-clean | ✅ 完整 | /database/ |
| 2号 | 交易所数据采集 | feature/window-2-exchange-clean | ✅ 完整 | /collectors/exchange/ |
| 3号 | 链上社交新闻 | feature/window-3-chain-social-clean | ✅ 完整 | /collectors/chain_social/ |
| 4号 | 技术指标引擎 | feature/window-4-indicators-clean | ✅ 完整 | /analysis/indicators/ |
| 5号 | 币Coin爬虫 | feature/window-5-bitcoin-clean | ✅ 完整 | /collectors/bicoin/ |
| 6号 | AI决策系统 | feature/window-6-ai-clean | ✅ 完整 | /ai/ |
| 7号 | 风控执行 | feature/window-7-risk-control-clean | ✅ 完整 | /risk/ |
| 8号 | 通知报告 | feature/window-8-notification-clean | ✅ 完整 | /notification/ |
| 9号 | 学习进化 | feature/window-9-learning-clean | ✅ 完整 | /learning/ |
| 10号 | 系统集成 | feature/window-10-integration-clean | ⏳ 待开发 | /integration/ |

### 🗑️ 需要删除的旧分支

以下分支包含混乱代码，确认切换到clean分支后可删除：
- feature/window-1-database (被clean替代)
- feature/window-2-exchange (被clean替代)
- feature/window-3-chain-social (被clean替代)
- feature/window-4-indicators (被clean替代)
- feature/window-5-bicoin (拼写错误，被bitcoin-clean替代)
- feature/window-7-risk-control (被clean替代)
- feature/window-8-notification (被clean替代)
- feature/window-9-learning (被clean替代)

### 📝 使用说明

1. **切换到你的分支**
   ```bash
   # 方法1：使用切换脚本
   ./switch_to_clean.sh
   
   # 方法2：手动切换
   git checkout feature/window-[你的窗口号]-[功能名]-clean
   ```

2. **确认当前分支**
   ```bash
   git branch --show-current
   ```

3. **提交代码前检查**
   ```bash
   # 确保在正确分支
   git branch --show-current
   # 查看将要提交的内容
   git status
   git diff --staged
   ```

### ⚠️ 重要规则

1. **只在自己的分支工作**
   - 1号只能在 feature/window-1-database-clean
   - 2号只能在 feature/window-2-exchange-clean
   - 以此类推...

2. **查看其他窗口代码不要切换分支**
   ```bash
   # 正确方式
   git show origin/feature/window-3-chain-social-clean:文件路径
   
   # 错误方式
   git checkout feature/window-3-chain-social-clean
   ```

3. **发现问题立即上报**
   - 发现代码混乱
   - 发现文件缺失
   - 发现提交错误

### 🔄 最后更新

- **更新时间**: 2025-08-11
- **更新人**: 11号窗口
- **下次检查**: 每周一检查分支状态

---

**记住口诀：我是几号窗，只推几号分支！**