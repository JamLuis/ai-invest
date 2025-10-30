#!/bin/bash

# GitHub推送脚本
# 请在GitHub上创建好ai-invest仓库后运行此脚本

echo "🚀 准备推送AI投资项目到GitHub..."

# 检查远程仓库是否已配置
if git remote -v | grep -q "origin"; then
    echo "✅ 远程仓库已配置"
else
    echo "📡 配置远程仓库..."
    git remote add origin https://github.com/JamLuis/ai-invest.git
fi

# 检查是否有提交
if git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "✅ 发现本地提交"
else
    echo "❌ 没有找到提交，请先执行 git commit"
    exit 1
fi

# 推送到GitHub
echo "🌐 推送到GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 成功推送到GitHub!"
    echo "📍 仓库地址: https://github.com/JamLuis/ai-invest"
    echo ""
    echo "📋 项目特性:"
    echo "  ✨ 多优先级RSS数据采集系统"
    echo "  🔄 实时金融新闻处理管道"
    echo "  🌐 FastAPI REST接口"
    echo "  📊 完整的API文档和示例"
    echo "  🚀 一键启动自动化"
    echo ""
    echo "🎯 下一步:"
    echo "  1. 访问仓库页面查看代码"
    echo "  2. 配置GitHub Pages (如果需要)"
    echo "  3. 设置GitHub Actions CI/CD (可选)"
    echo "  4. 邀请协作者 (如果需要)"
else
    echo "❌ 推送失败，请检查："
    echo "  1. GitHub仓库是否已创建"
    echo "  2. 网络连接是否正常"
    echo "  3. 是否有推送权限"
fi