# 🚀 Tiger系统快速启动指南

## 一、立即启动（最简单）

```bash
# 进入项目目录
cd /mnt/c/Users/tiger/TigerSystem

# 一键启动
./tests/integration/deploy.sh development
```

---

## 二、分步启动（推荐）

### 步骤1：配置环境

```bash
# 1. 进入项目目录
cd /mnt/c/Users/tiger/TigerSystem

# 2. 安装Python依赖
pip3 install -r requirements.txt

# 3. 初始化配置
python3 tests/integration/config_manager.py
```

### 步骤2：启动核心服务

```bash
# 启动监控系统（可选，但推荐）
python3 tests/integration/monitoring.py &

# 启动主系统
python3 tests/integration/main.py
```

---

## 三、各功能模块单独运行

### 1. 数据采集模块

```bash
# 交易所数据采集
python3 collectors/exchange/main_collector.py

# 链上数据监控
python3 collectors/chain_social/early_warning.py

# 币Coin爬虫
python3 collectors/bicoin/bicoin_auth.py
```

### 2. 分析模块

```bash
# 技术指标分析
python3 analysis/test_all_indicators.py

# AI决策系统
python3 ai/test_ai_system.py
```

### 3. 风控和通知

```bash
# 风控系统
python3 risk/alert_executor.py

# 通知系统
python3 notification/alert_notifier.py
```

---

## 四、测试系统

```bash
# 运行完整测试套件
python3 tests/integration/test_suite.py

# 查看测试报告
cat test_report_*.json
```

---

## 五、需要配置的内容

### 1. API密钥配置
编辑 `config/api_keys.yaml`:
```yaml
binance_api_key: "你的Binance API Key"
binance_secret: "你的Binance Secret"
claude_api_key: "你的Claude API Key"
telegram_bot_token: "你的Telegram Bot Token"
```

### 2. 数据库配置（可选）
如果要使用MySQL：
```bash
# 安装MySQL
sudo apt-get install mysql-server

# 创建数据库
mysql -u root -p < database/create_database.sql
```

### 3. Redis配置（可选）
如果要使用消息队列：
```bash
# 安装Redis
sudo apt-get install redis-server

# 启动Redis
redis-server
```

---

## 六、监控系统运行

### 实时监控
```bash
# 查看系统监控
python3 tests/integration/monitoring.py

# 查看日志
tail -f logs/integration.log
```

### 系统状态检查
```bash
# 健康检查
python3 -c "
from tests.integration.main import TigerSystem
import asyncio

async def check():
    system = TigerSystem()
    system.initialize_modules()
    status = system.get_status()
    print('系统状态:', status)

asyncio.run(check())
"
```

---

## 七、常见问题解决

### 问题1：模块导入错误
```bash
# 解决方案：设置Python路径
export PYTHONPATH=/mnt/c/Users/tiger/TigerSystem:$PYTHONPATH
```

### 问题2：权限问题
```bash
# 解决方案：给脚本执行权限
chmod +x tests/integration/deploy.sh
```

### 问题3：依赖缺失
```bash
# 解决方案：安装所有依赖
pip3 install pyyaml redis psutil cryptography
```

---

## 八、生产环境部署

### Docker部署（推荐）
```bash
# 创建Dockerfile
cat > Dockerfile << EOF
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python3", "tests/integration/main.py"]
EOF

# 构建镜像
docker build -t tiger-system .

# 运行容器
docker run -d --name tiger tiger-system
```

### 系统服务部署
```bash
# 创建systemd服务
sudo cat > /etc/systemd/system/tiger.service << EOF
[Unit]
Description=Tiger Trading System
After=network.target

[Service]
Type=simple
User=tiger
WorkingDirectory=/mnt/c/Users/tiger/TigerSystem
ExecStart=/usr/bin/python3 /mnt/c/Users/tiger/TigerSystem/tests/integration/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl start tiger
sudo systemctl enable tiger
```

---

## 九、开发模式

如果你想修改代码：

```bash
# 1. 查看特定模块代码
git checkout feature/window-6-ai-clean  # 查看AI模块
ls -la ai/

# 2. 修改后测试
python3 ai/test_ai_system.py

# 3. 提交修改
git add .
git commit -m "你的修改说明"
```

---

## 🎯 最简单的启动命令

如果你只想立即看到系统运行：

```bash
cd /mnt/c/Users/tiger/TigerSystem
python3 tests/integration/main.py
```

系统会自动初始化所有模块并开始运行！

---

**提示**: 
- 首次运行建议先执行测试：`python3 tests/integration/test_suite.py`
- 查看监控了解系统状态：`python3 tests/integration/monitoring.py`
- 有问题查看日志：`tail -f logs/integration.log`

祝你使用愉快！🚀