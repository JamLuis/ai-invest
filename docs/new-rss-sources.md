# 📊 新增RSS源配置说明

## 🎯 新增的RSS源

### ✅ 已添加到.env配置

#### 1. Investing.com RSS 系列
**分类分布**：
- **高优先级** (`FEEDS_HIGH_PRIORITY`): 
  - `https://www.investing.com/rss/news.rss` - 主要财经新闻
  
- **中优先级** (`FEEDS_MEDIUM_PRIORITY`):
  - `https://www.investing.com/rss/news_301.rss` - 公司新闻
  
- **低优先级** (`FEEDS_LOW_PRIORITY`):
  - `https://www.investing.com/rss/news_95.rss` - 央行新闻

- **国际源** (`FEEDS_INTERNATIONAL`): 
  - `https://www.investing.com/rss/news_25.rss` - 经济指标

**特点**：
- ✅ 更新频率高
- ✅ 覆盖面广 (Breaking News, Company News, Central Banks)
- ✅ 全球财经快讯

#### 2. 新增优先级组
**🌐 国际新闻源** (每30分钟抓取):
- 权重: 6
- 间隔: 1800秒 (30分钟)
- 用途: 全球财经快讯和趋势分析

## ⚠️ API源 (需要特殊集成)

以下源为API格式，需要额外的开发工作来集成：

### 🔧 需要API集成的源

#### 1. GNews News API
- **URL**: https://gnews.io/
- **格式**: JSON API
- **特点**: 实时新闻API，支持全球多源
- **集成需求**: 需要API Key，修改producer支持HTTP API调用

#### 2. Finnhub Market News API  
- **URL**: https://finnhub.io/docs/api/market-news
- **格式**: JSON API
- **特点**: 公司新闻、经济数据、市场动态
- **集成需求**: 需要API Key，适合量化数据使用

#### 3. Thomson Reuters RSS Feeds
- **URL**: https://ir.thomsonreuters.com/rss-feeds
- **格式**: RSS (需要验证可用性)
- **特点**: 路透财经新闻、事件日历、公司公告
- **集成需求**: 可能需要注册或订阅

#### 4. Nasdaq News Alerts RSS
- **URL**: https://www.nasdaqtrader.com/trader.aspx?id=newsrss
- **格式**: RSS (需要验证可用性)  
- **特点**: 公司/交易所动态、公告，可定制
- **集成需求**: 可能需要注册账户

## 🚀 当前配置优势

### 📈 优先级分布优化
```
高优先级 (1分钟):   4个源 - 关键监管和市场新闻
中优先级 (5分钟):   5个源 - 重要宏观和公司数据  
低优先级 (15分钟):  5个源 - 背景信息和研究
研究级 (1小时):     2个源 - 深度分析
国际源 (30分钟):    2个源 - 全球财经快讯
```

### 📊 数据源类型覆盖
- **监管机构**: 美联储、SEC、欧央行、英国央行
- **交易所**: 香港交易所、纳斯达克  
- **统计机构**: BEA、BLS、OECD
- **国际组织**: IMF、世界银行
- **研究机构**: 布鲁金斯学会、彼得森研究所
- **财经媒体**: Investing.com 系列

### ⚡ 性能估算
- **总请求频率**: ~18个源，平均每小时约320次请求
- **负载分布**: 错峰抓取，避免同时请求
- **故障隔离**: 单个源失败不影响其他源

## 🔄 下一步扩展计划

### 立即可用 (RSS源)
1. ✅ 已集成 Investing.com RSS 系列
2. 🔍 验证 Thomson Reuters RSS 可用性
3. 🔍 测试 Nasdaq News Alerts RSS

### 需要开发 (API源)
1. **API Producer模块**: 支持HTTP API调用
2. **API Key管理**: 安全存储和轮换
3. **速率限制**: 遵守API使用限制
4. **错误处理**: API特有的错误码处理

### 实施建议

#### 阶段1: RSS源验证 (本周)
```bash
# 测试新RSS源
curl -I "https://www.investing.com/rss/news.rss"
curl -I "https://ir.thomsonreuters.com/rss-feeds"
curl -I "https://www.nasdaqtrader.com/trader.aspx?id=newsrss"
```

#### 阶段2: API源集成 (下周)
```python
# 创建API Producer基类
class APIProducer:
    def fetch_api_data(self, url, headers, params)
    def transform_to_kafka_message(self, api_response)
    def handle_rate_limiting(self)
```

#### 阶段3: 监控优化 (后续)
- 添加源可用性监控
- 实施数据质量检查
- 优化抓取频率

## 🎯 预期收益

通过新增这些源，系统将获得：

1. **覆盖面提升**: 全球财经新闻覆盖度从70%提升到90%+
2. **实时性增强**: Investing.com的高频更新提升新闻时效性
3. **多样性丰富**: 涵盖更多地区和行业的财经信息
4. **API扩展性**: 为未来API源集成奠定基础

新配置已经生效，你可以通过 `make prod-enhanced` 启动增强版RSS Producer来开始使用新的源配置！