#!/bin/bash

# Finance News API 测试脚本
# 使用 curl 测试 API 功能

API_BASE="http://localhost:8000"

echo "🧪 Finance News API 测试开始..."
echo "=================================================="

# 测试API连通性
echo ""
echo "📡 测试API连通性..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/news?limit=1")
if [ "$response" = "200" ]; then
    echo "✅ API服务正常运行"
    api_healthy=true
else
    echo "❌ API服务异常，状态码: $response"
    api_healthy=false
fi

if [ "$api_healthy" = true ]; then
    # 测试基本新闻获取
    echo ""
    echo "📰 测试新闻列表获取..."
    news_response=$(curl -s "$API_BASE/news?limit=5")
    news_count=$(echo "$news_response" | grep -o '"id"' | wc -l | tr -d ' ')
    
    if [ "$news_count" -gt 0 ]; then
        echo "✅ 成功获取 $news_count 条新闻"
        
        # 显示第一条新闻的标题
        first_title=$(echo "$news_response" | grep -o '"title":"[^"]*"' | head -1 | sed 's/"title":"//;s/"//')
        if [ -n "$first_title" ]; then
            echo "   示例标题: ${first_title:0:50}..."
        fi
    else
        echo "⚠️  返回的新闻列表为空"
    fi
    
    # 测试搜索功能
    echo ""
    echo "🔍 测试新闻搜索功能..."
    
    # 搜索SEC
    sec_response=$(curl -s "$API_BASE/news?q=SEC&limit=3")
    sec_count=$(echo "$sec_response" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "✅ 搜索 'SEC': 找到 $sec_count 条结果"
    
    # 搜索Hong Kong
    hk_response=$(curl -s "$API_BASE/news?q=Hong%20Kong&limit=3")
    hk_count=$(echo "$hk_response" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "✅ 搜索 'Hong Kong': 找到 $hk_count 条结果"
    
    # 测试参数限制
    echo ""
    echo "⚙️  测试API参数..."
    
    limit1_response=$(curl -s "$API_BASE/news?limit=1")
    limit1_count=$(echo "$limit1_response" | grep -o '"id"' | wc -l | tr -d ' ')
    
    limit10_response=$(curl -s "$API_BASE/news?limit=10")
    limit10_count=$(echo "$limit10_response" | grep -o '"id"' | wc -l | tr -d ' ')
    
    echo "✅ limit=1: 返回 $limit1_count 条记录"
    echo "✅ limit=10: 返回 $limit10_count 条记录"
    
    # 测试数据格式
    echo ""
    echo "📊 测试数据格式..."
    
    sample_response=$(curl -s "$API_BASE/news?limit=1")
    
    # 检查必要字段
    required_fields=("id" "source" "url" "title" "summary" "published_at")
    missing_fields=()
    
    for field in "${required_fields[@]}"; do
        if ! echo "$sample_response" | grep -q "\"$field\""; then
            missing_fields+=("$field")
        fi
    done
    
    if [ ${#missing_fields[@]} -eq 0 ]; then
        echo "✅ 数据格式正确，包含所有必要字段"
    else
        echo "❌ 数据缺少字段: ${missing_fields[*]}"
    fi
    
    # 检查URL格式
    url_count=$(echo "$sample_response" | grep -o '"url":"http[^"]*"' | wc -l | tr -d ' ')
    if [ "$url_count" -gt 0 ]; then
        echo "✅ URL格式有效"
    else
        echo "⚠️  URL格式可能有问题"
    fi
    
    echo ""
    echo "=================================================="
    echo "🏁 测试完成！"
    echo ""
    echo "📋 API端点总结:"
    echo "   GET /news              - 获取新闻列表"
    echo "   GET /news?q=keyword    - 搜索新闻"
    echo "   GET /news?limit=N      - 限制返回数量"
    echo ""
    echo "🔗 在线文档:"
    echo "   Swagger UI: $API_BASE/docs"
    echo "   ReDoc:      $API_BASE/redoc"
    echo ""
    echo "📁 文档文件:"
    echo "   完整文档:   docs/api/README.md"
    echo "   快速参考:   docs/api/quick-reference.md"
    echo "   使用示例:   docs/api/examples.md"
    echo "   OpenAPI:    docs/api/openapi.yaml"
    echo "   Postman:    docs/api/postman-collection.json"
    
else
    echo ""
    echo "❌ API服务未运行，请先启动服务:"
    echo "   make start"
fi