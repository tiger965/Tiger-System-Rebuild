#!/bin/bash

# Tiger系统 - 快速切换到干净分支脚本

echo "======================================"
echo "   Tiger系统 - 分支切换工具"
echo "======================================"
echo ""
echo "请输入你的窗口号 (1-10):"
read window_num

case $window_num in
    1)
        branch="feature/window-1-database-clean"
        name="数据库基础设施"
        ;;
    2)
        branch="feature/window-2-exchange-clean"
        name="交易所数据采集"
        ;;
    3)
        branch="feature/window-3-chain-social-clean"
        name="链上社交新闻"
        ;;
    4)
        branch="feature/window-4-indicators-clean"
        name="技术指标引擎"
        ;;
    5)
        branch="feature/window-5-bitcoin-clean"
        name="币Coin爬虫系统"
        ;;
    6)
        branch="feature/window-6-ai-clean"
        name="AI决策系统"
        ;;
    7)
        branch="feature/window-7-risk-control-clean"
        name="风控执行系统"
        ;;
    8)
        branch="feature/window-8-notification-clean"
        name="通知报告系统"
        ;;
    9)
        branch="feature/window-9-learning-clean"
        name="学习进化系统"
        ;;
    10)
        branch="feature/window-10-integration-clean"
        name="系统集成测试"
        ;;
    *)
        echo "❌ 无效的窗口号！"
        exit 1
        ;;
esac

echo ""
echo "正在切换到 ${window_num}号窗口 - ${name}"
echo "目标分支: $branch"
echo ""

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "⚠️ 警告：你有未提交的更改！"
    echo "请先提交或暂存你的更改。"
    echo ""
    echo "选择操作:"
    echo "1) 暂存更改 (git stash)"
    echo "2) 取消切换"
    read -p "请选择 (1/2): " choice
    
    if [ "$choice" = "1" ]; then
        git stash
        echo "✅ 更改已暂存"
    else
        echo "❌ 取消切换"
        exit 1
    fi
fi

# 切换分支
git checkout $branch

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功切换到 $branch"
    echo ""
    echo "当前分支状态:"
    git status
    echo ""
    echo "📌 记住规则："
    echo "   你是${window_num}号窗口，只能提交到 $branch"
    echo "   提交前请再次确认: git branch --show-current"
else
    echo "❌ 切换失败！请检查分支是否存在。"
fi