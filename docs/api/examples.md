# API 使用示例

本文档提供了 Finance News API 的详细使用示例，包括各种编程语言的实现。

## 基础设置

确保API服务正在运行：
```bash
# 启动项目
make start

# 检查API状态
curl http://localhost:8000/news?limit=1
```

## Python 示例

### 基础使用

```python
import requests
import json
from datetime import datetime

class FinanceNewsAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_news(self, query=None, limit=50):
        """获取新闻列表"""
        params = {"limit": limit}
        if query:
            params["q"] = query
        
        response = requests.get(f"{self.base_url}/news", params=params)
        response.raise_for_status()
        return response.json()
    
    def search_news(self, keyword, limit=10):
        """搜索特定关键词的新闻"""
        return self.get_news(query=keyword, limit=limit)
    
    def get_latest_news(self, count=5):
        """获取最新新闻"""
        return self.get_news(limit=count)

# 使用示例
api = FinanceNewsAPI()

# 获取最新新闻
latest = api.get_latest_news(10)
print(f"获取到 {len(latest)} 条最新新闻")

# 搜索SEC相关新闻
sec_news = api.search_news("SEC", 5)
for article in sec_news:
    print(f"标题: {article['title']}")
    print(f"时间: {article['published_at']}")
    print(f"链接: {article['url']}")
    print("---")
```

### 高级功能示例

```python
import pandas as pd
from datetime import datetime, timedelta

def analyze_news_trends(api, days=7):
    """分析最近几天的新闻趋势"""
    news = api.get_news(limit=1000)
    
    # 转换为DataFrame
    df = pd.DataFrame(news)
    df['published_at'] = pd.to_datetime(df['published_at'])
    
    # 过滤最近几天的新闻
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_news = df[df['published_at'] >= cutoff_date]
    
    # 按来源统计
    source_counts = recent_news['source'].value_counts()
    print("新闻来源统计:")
    for source, count in source_counts.items():
        print(f"  {source}: {count} 条")
    
    # 按日期统计
    daily_counts = recent_news.groupby(recent_news['published_at'].dt.date).size()
    print("\n每日新闻数量:")
    for date, count in daily_counts.items():
        print(f"  {date}: {count} 条")
    
    return recent_news

# 使用示例
api = FinanceNewsAPI()
trend_analysis = analyze_news_trends(api)
```

## JavaScript 示例

### Node.js 示例

```javascript
const axios = require('axios');

class FinanceNewsAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async getNews(options = {}) {
        const { query, limit = 50 } = options;
        const params = new URLSearchParams({ limit: limit.toString() });
        
        if (query) {
            params.append('q', query);
        }

        try {
            const response = await axios.get(`${this.baseUrl}/news?${params}`);
            return response.data;
        } catch (error) {
            console.error('获取新闻失败:', error.message);
            throw error;
        }
    }

    async searchNews(keyword, limit = 10) {
        return this.getNews({ query: keyword, limit });
    }

    async getLatestNews(count = 5) {
        return this.getNews({ limit: count });
    }
}

// 使用示例
async function main() {
    const api = new FinanceNewsAPI();

    try {
        // 获取最新新闻
        const latest = await api.getLatestNews(10);
        console.log(`获取到 ${latest.length} 条最新新闻`);

        // 搜索特定关键词
        const secNews = await api.searchNews('SEC', 5);
        console.log('\nSEC相关新闻:');
        secNews.forEach(article => {
            console.log(`标题: ${article.title}`);
            console.log(`时间: ${article.published_at}`);
            console.log(`链接: ${article.url}`);
            console.log('---');
        });
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

### 浏览器端示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>Finance News Demo</title>
    <style>
        .news-item { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .news-title { font-weight: bold; color: #333; }
        .news-summary { margin: 10px 0; color: #666; }
        .news-meta { font-size: 0.9em; color: #999; }
    </style>
</head>
<body>
    <h1>Finance News</h1>
    
    <div>
        <input type="text" id="searchInput" placeholder="输入搜索关键词...">
        <button onclick="searchNews()">搜索</button>
        <button onclick="loadLatestNews()">最新新闻</button>
    </div>
    
    <div id="newsContainer"></div>

    <script>
        const API_BASE = 'http://localhost:8000';

        async function fetchNews(query = '', limit = 10) {
            const params = new URLSearchParams({ limit: limit.toString() });
            if (query) params.append('q', query);

            try {
                const response = await fetch(`${API_BASE}/news?${params}`);
                if (!response.ok) throw new Error('网络请求失败');
                return await response.json();
            } catch (error) {
                console.error('获取新闻失败:', error);
                return [];
            }
        }

        function displayNews(newsArray) {
            const container = document.getElementById('newsContainer');
            
            if (newsArray.length === 0) {
                container.innerHTML = '<p>没有找到相关新闻</p>';
                return;
            }

            const newsHtml = newsArray.map(article => `
                <div class="news-item">
                    <div class="news-title">
                        <a href="${article.url}" target="_blank">${article.title}</a>
                    </div>
                    <div class="news-summary">${article.summary}</div>
                    <div class="news-meta">
                        来源: ${article.source} | 
                        发布时间: ${new Date(article.published_at).toLocaleString()}
                    </div>
                </div>
            `).join('');

            container.innerHTML = newsHtml;
        }

        async function searchNews() {
            const query = document.getElementById('searchInput').value;
            const news = await fetchNews(query, 20);
            displayNews(news);
        }

        async function loadLatestNews() {
            const news = await fetchNews('', 20);
            displayNews(news);
        }

        // 页面加载时获取最新新闻
        loadLatestNews();
    </script>
</body>
</html>
```

## curl 示例

### 基础查询

```bash
# 获取最新新闻
curl -X GET "http://localhost:8000/news?limit=5" | jq '.'

# 搜索SEC相关新闻
curl -X GET "http://localhost:8000/news?q=SEC&limit=10" | jq '.'

# 搜索中文关键词（需要URL编码）
curl -X GET "http://localhost:8000/news?q=%E9%A6%99%E6%B8%AF%E4%BA%A4%E6%98%93%E6%89%80" | jq '.'
```

### 高级查询和数据处理

```bash
# 获取新闻并保存到文件
curl -s "http://localhost:8000/news?limit=100" > news_data.json

# 统计新闻来源
curl -s "http://localhost:8000/news?limit=1000" | jq -r '.[].source' | sort | uniq -c

# 提取所有新闻标题
curl -s "http://localhost:8000/news?limit=50" | jq -r '.[].title'

# 按发布时间排序并显示最新的5条
curl -s "http://localhost:8000/news?limit=100" | jq 'sort_by(.published_at) | reverse | .[0:5]'

# 搜索并格式化输出
curl -s "http://localhost:8000/news?q=regulatory&limit=5" | \
jq -r '.[] | "标题: \(.title)\n时间: \(.published_at)\n链接: \(.url)\n---"'
```

## 错误处理示例

### Python 错误处理

```python
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

def safe_api_call(api_func, *args, **kwargs):
    """安全的API调用包装器"""
    try:
        return api_func(*args, **kwargs)
    except ConnectionError:
        print("错误: 无法连接到API服务，请检查服务是否运行")
        return None
    except Timeout:
        print("错误: 请求超时，请稍后重试")
        return None
    except HTTPError as e:
        print(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        return None
    except RequestException as e:
        print(f"请求错误: {e}")
        return None

# 使用示例
api = FinanceNewsAPI()
news = safe_api_call(api.get_news, limit=10)
if news:
    print(f"成功获取 {len(news)} 条新闻")
```

## 性能优化示例

### 并发请求

```python
import asyncio
import aiohttp

async def fetch_news_async(session, query=None, limit=50):
    """异步获取新闻"""
    params = {"limit": limit}
    if query:
        params["q"] = query
    
    async with session.get("http://localhost:8000/news", params=params) as response:
        return await response.json()

async def fetch_multiple_topics():
    """并发获取多个主题的新闻"""
    topics = ["SEC", "HKEX", "regulatory", "crypto", "ESG"]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_news_async(session, topic, 10) for topic in topics]
        results = await asyncio.gather(*tasks)
        
        for i, topic in enumerate(topics):
            print(f"{topic}: {len(results[i])} 条新闻")
        
        return dict(zip(topics, results))

# 运行示例
# asyncio.run(fetch_multiple_topics())
```

## 数据分析示例

### 新闻数据分析

```python
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import jieba

def analyze_news_content(api):
    """分析新闻内容"""
    # 获取大量新闻数据
    news = api.get_news(limit=1000)
    df = pd.DataFrame(news)
    
    # 1. 来源分布分析
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    source_counts = df['source'].value_counts()
    plt.pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%')
    plt.title('新闻来源分布')
    
    # 2. 发布时间分布
    plt.subplot(1, 2, 2)
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['hour'] = df['published_at'].dt.hour
    hourly_counts = df['hour'].value_counts().sort_index()
    plt.bar(hourly_counts.index, hourly_counts.values)
    plt.title('新闻发布时间分布')
    plt.xlabel('小时')
    plt.ylabel('新闻数量')
    
    plt.tight_layout()
    plt.show()
    
    # 3. 词云分析（中文）
    all_text = ' '.join(df['title'] + ' ' + df['summary'])
    words = jieba.cut(all_text)
    text_for_cloud = ' '.join(words)
    
    wordcloud = WordCloud(font_path='simhei.ttf', width=800, height=400, 
                         background_color='white').generate(text_for_cloud)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('新闻关键词云')
    plt.show()
    
    return df

# 使用示例
# api = FinanceNewsAPI()
# analysis_df = analyze_news_content(api)
```

## 实际应用场景

### 新闻监控脚本

```python
import time
import smtplib
from email.mime.text import MIMEText

class NewsMonitor:
    def __init__(self, api, keywords, check_interval=300):
        self.api = api
        self.keywords = keywords
        self.check_interval = check_interval
        self.seen_articles = set()
    
    def check_for_keywords(self):
        """检查是否有包含关键词的新新闻"""
        new_articles = []
        
        for keyword in self.keywords:
            articles = self.api.search_news(keyword, 10)
            for article in articles:
                if article['id'] not in self.seen_articles:
                    self.seen_articles.add(article['id'])
                    new_articles.append((keyword, article))
        
        return new_articles
    
    def send_alert(self, articles):
        """发送新闻提醒"""
        if not articles:
            return
        
        content = "发现新的相关新闻:\n\n"
        for keyword, article in articles:
            content += f"关键词: {keyword}\n"
            content += f"标题: {article['title']}\n"
            content += f"链接: {article['url']}\n"
            content += f"时间: {article['published_at']}\n\n"
        
        print(content)  # 实际应用中可以发送邮件或推送通知
    
    def start_monitoring(self):
        """开始监控"""
        print(f"开始监控关键词: {', '.join(self.keywords)}")
        while True:
            try:
                new_articles = self.check_for_keywords()
                if new_articles:
                    self.send_alert(new_articles)
                
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"监控出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续

# 使用示例
# api = FinanceNewsAPI()
# monitor = NewsMonitor(api, ["SEC enforcement", "crypto regulation", "ESG"])
# monitor.start_monitoring()
```

这些示例涵盖了API的各种使用场景，从基础查询到高级数据分析和实际应用。你可以根据具体需求选择合适的示例进行修改和使用。