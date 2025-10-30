# API 快速参考

## 基本信息
- **Base URL**: `http://localhost:8000`
- **格式**: JSON
- **认证**: 无需认证

## 端点列表

### GET /news
获取新闻列表

**参数**:
- `q` (可选): 搜索关键词
- `limit` (可选): 结果数量，默认50

**示例**:
```bash
# 获取最新新闻
curl "http://localhost:8000/news"

# 搜索SEC相关新闻
curl "http://localhost:8000/news?q=SEC&limit=10"
```

**响应示例**:
```json
[
  {
    "id": 1,
    "source": "https://www.sec.gov/news/pressreleases.rss",
    "url": "https://www.sec.gov/news/press-release/2024-123",
    "title": "SEC Announces New Framework",
    "summary": "The SEC today announced...",
    "published_at": "2024-10-30T10:30:00+00:00"
  }
]
```

## 状态码
- `200` - 成功
- `400` - 参数错误
- `500` - 服务器错误

## 测试命令

```bash
# 健康检查（如果已实现）
curl http://localhost:8000/health

# 获取最新5条新闻
curl "http://localhost:8000/news?limit=5"

# 搜索关键词
curl "http://localhost:8000/news?q=regulatory"

# 格式化输出
curl -s "http://localhost:8000/news?limit=1" | jq '.'
```