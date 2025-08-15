#!/bin/bash
#
# Tiger系统 - 完整依赖安装脚本
#

echo "============================================================"
echo "Tiger系统 - 安装所有依赖"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# 1. 更新pip
echo -e "\n[1/4] 更新pip..."
pip3 install --upgrade pip

# 2. 安装核心依赖
echo -e "\n[2/4] 安装核心依赖..."
pip3 install -q \
    pyyaml \
    redis \
    psutil \
    cryptography \
    requests \
    aiohttp \
    asyncio \
    python-dotenv

# 3. 安装数据分析依赖
echo -e "\n[3/4] 安装数据分析依赖..."
pip3 install -q \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    ta \
    ta-lib \
    ccxt \
    python-binance \
    web3 \
    tweepy

# 4. 安装AI和机器学习依赖
echo -e "\n[4/4] 安装AI和机器学习依赖..."
pip3 install -q \
    anthropic \
    openai \
    transformers \
    torch \
    tensorflow \
    xgboost \
    lightgbm

echo -e "\n✅ 所有Python依赖安装完成！"

# 检查系统服务
echo -e "\n检查系统服务..."

# Redis
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis 已安装"
    if redis-cli ping &> /dev/null; then
        echo "   Redis服务运行中"
    else
        echo "   ⚠️ Redis服务未运行，尝试启动..."
        sudo service redis-server start 2>/dev/null || echo "   需要手动启动Redis"
    fi
else
    echo "⚠️ Redis 未安装"
    echo "   安装命令: sudo apt-get install redis-server"
fi

# MySQL
if command -v mysql &> /dev/null; then
    echo "✅ MySQL 已安装"
else
    echo "⚠️ MySQL 未安装"
    echo "   安装命令: sudo apt-get install mysql-server"
fi

echo -e "\n============================================================"
echo "依赖安装完成！"
echo "============================================================"