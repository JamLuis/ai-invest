# Finance News API 文档

## 概述

Finance News API 是一个基于 FastAPI 构建的财经新闻查询服务，提供从多个 RSS 源收集的财经新闻数据的检索功能。

## 基本信息

- **Base URL**: `http://localhost:8000`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

当前版本不需要认证。

## 错误处理

API 使用标准的 HTTP 状态码来表示请求的成功或失败：

- `200 OK` - 请求成功
- `400 Bad Request` - 请求参数错误
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器内部错误

错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

## API 端点

### 1. 获取新闻列表

获取财经新闻列表，支持关键词搜索和分页。

**端点**: `GET /news`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| q | string | 否 | - | 搜索关键词，在标题和摘要中进行模糊匹配 |
| limit | integer | 否 | 50 | 返回结果数量限制，最小值1 |

**请求示例**:

```bash
# 获取最新的50篇新闻
GET /news

# 搜索包含"SEC"的新闻，限制返回10条
GET /news?q=SEC&limit=10

# 搜索包含"香港交易所"的新闻
GET /news?q=香港交易所
```

**响应格式**:

```json
[
  {
    "id": 1,
    "source": "https://www.sec.gov/news/pressreleases.rss",
    "url": "https://www.sec.gov/news/press-release/2024-123",
    "title": "SEC Announces New Regulatory Framework",
    "summary": "The Securities and Exchange Commission today announced...",
    "published_at": "2024-10-30T10:30:00+00:00"
  },
  {
    "id": 2,
    "source": "https://www.hkex.com.hk/eng/newscalc/hkexnews.xml",
    "url": "https://www.hkex.com.hk/News/Market-Communications/2024/241030news",
    "title": "Hong Kong Exchanges and Clearing Limited Updates",
    "summary": "Hong Kong Exchanges and Clearing Limited today released...",
    "published_at": "2024-10-30T09:15:00+00:00"
  }
]
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 新闻唯一标识符 |
| source | string | 新闻来源 RSS URL |
| url | string | 新闻原文链接 |
| title | string | 新闻标题 |
| summary | string | 新闻摘要 |
| published_at | string (ISO 8601) | 新闻发布时间 |

**状态码**:

- `200 OK` - 成功返回新闻列表
- `400 Bad Request` - 参数错误（如 limit 值无效）
- `500 Internal Server Error` - 数据库连接错误或其他服务器错误

## 数据源

当前支持的新闻源：

1. **SEC (美国证券交易委员会)**
   - RSS URL: `https://www.sec.gov/news/pressreleases.rss`
   - 内容: 美国证券监管相关新闻

2. **HKEX (香港交易所)**
   - RSS URL: `https://www.hkex.com.hk/eng/newscalc/hkexnews.xml`
   - 内容: 香港交易所相关新闻和公告

## 使用限制

- 单次查询最大返回条数: 建议不超过 1000 条
- 查询频率: 无限制（建议合理使用）
- 数据更新频率: 实时更新（取决于 RSS 源的更新频率）

## 示例代码

### Python 示例

```python
import requests

# 基本查询
response = requests.get('http://localhost:8000/news?limit=10')
news_list = response.json()

# 关键词搜索
response = requests.get('http://localhost:8000/news?q=SEC&limit=5')
sec_news = response.json()

for article in sec_news:
    print(f"标题: {article['title']}")
    print(f"时间: {article['published_at']}")
    print(f"链接: {article['url']}")
    print("---")
```

### curl 示例

```bash
# 获取最新新闻
curl "http://localhost:8000/news?limit=5"

# 搜索特定关键词
curl "http://localhost:8000/news?q=regulatory&limit=10"

# 格式化输出
curl -s "http://localhost:8000/news?limit=3" | jq '.[0]'
```

### JavaScript 示例

```javascript
// 使用 fetch API
async function fetchNews(query = '', limit = 50) {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  params.append('limit', limit.toString());
  
  const response = await fetch(`http://localhost:8000/news?${params}`);
  const data = await response.json();
  return data;
}

// 使用示例
fetchNews('SEC', 10).then(news => {
  console.log('SEC 相关新闻:', news);
});
```

## OpenAPI 规范

本 API 完全兼容 OpenAPI 3.0 规范。你可以通过以下 URL 访问：

- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 更新日志

### v1.0.0 (2024-10-30)

- 初始版本发布
- 支持新闻列表查询
- 支持关键词搜索
- 支持结果数量限制

## 技术支持

如有问题或建议，请联系开发团队或在项目仓库中提交 Issue。