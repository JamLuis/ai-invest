# 多优先级RSS源配置指南

## 📊 配置概览

我们为你设计了一个分层RSS抓取系统，根据新闻源的重要性和时效性要求，将其分为4个优先级：

### 🎯 优先级分类

#### 高优先级 (每分钟) - 权重10
**实时监管和政策新闻**
- 🏛️ **美联储**: https://www.federalreserve.gov/feeds/press_all.xml
- 📋 **SEC**: https://www.sec.gov/news/pressreleases.rss  
- 🏢 **香港交易所**: https://www.hkex.com.hk/News/News-Release/News-Release?format=rss

#### 中优先级 (每5分钟) - 权重8-9
**重要市场和宏观数据**
- 📈 **纳斯达克**: https://www.nasdaq.com/feed/rssoutbound?category=All
- 🏦 **欧洲央行**: https://www.ecb.europa.eu/rss/press.html
- 📊 **美国经济分析局**: https://www.bea.gov/news/rss.xml
- 👷 **美国劳工统计局**: https://www.bls.gov/news/news_releases.rss

#### 低优先级 (每15分钟) - 权重6-7
**国际组织和背景信息**
- 🌍 **OECD**: https://www.oecd.org/newsroom/newsroom_rss.xml
- 🏦 **世界银行**: https://blogs.worldbank.org/feed
- 🎓 **布鲁金斯学会**: https://www.brookings.edu/topic/economy/feed/
- 🇬🇧 **英国央行**: https://www.bankofengland.co.uk/rss/news

#### 研究优先级 (每小时) - 权重5
**深度研究和分析**
- 📚 **彼得森研究所**: https://www.piie.com/rss/publications
- 🌐 **IMF**: https://www.imf.org/en/rss/press-release

## 🚀 使用方法

### 1. 使用增强版Producer
```bash
# 启动多优先级RSS抓取
make prod-enhanced
```

### 2. 自定义配置
编辑 `.env` 文件中的相应配置：

```bash
# 修改高优先级源
FEEDS_HIGH_PRIORITY=your,custom,sources
POLL_INTERVAL_HIGH=60

# 修改抓取间隔
POLL_INTERVAL_MEDIUM=600  # 改为10分钟
```

### 3. 监控和调试
```bash
# 查看系统状态
make status

# 查看API测试
make test

# 查看日志（如果实现了日志聚合）
make logs
```

## 📈 性能和资源考虑

### 资源使用估算
- **高优先级**: 3个源 × 每分钟 = 180次/小时
- **中优先级**: 4个源 × 每5分钟 = 48次/小时  
- **低优先级**: 4个源 × 每15分钟 = 16次/小时
- **研究级**: 2个源 × 每小时 = 2次/小时

**总计**: ~246次HTTP请求/小时，平均每分钟约4次请求

### 负载优化建议
1. **错峰抓取**: 不同优先级组在不同时间启动
2. **故障降级**: 如果高优先级源失败，不影响其他组
3. **缓存策略**: 相同文章不重复处理
4. **限流保护**: 避免对源服务器造成压力

## 🛠️ 技术实现

### 增强功能
新的`enhanced_rss_producer.py`提供：
- ✅ 多线程并行抓取
- ✅ 按优先级分组管理
- ✅ 智能重试机制
- ✅ 详细的日志记录
- ✅ 故障隔离
- ✅ 元数据丰富（权重、分类、抓取时间）

### 消息结构增强
```json
{
  "source": "https://www.sec.gov/news/pressreleases.rss",
  "title": "SEC Announces...",
  "summary": "...",
  "published_at": "2024-10-30T15:00:00+00:00",
  "priority": "high",
  "weight": 10,
  "category": "regulation",
  "fetch_time": "2024-10-30T15:30:00+00:00",
  "tags": ["enforcement", "securities"]
}
```

## 🔧 故障排查

### 常见问题
1. **源无响应**: 检查网络连接和源URL有效性
2. **解析错误**: 查看RSS格式是否标准
3. **内存不足**: 减少并发线程数或降低抓取频率
4. **Kafka队列堆积**: 检查consumer处理能力

### 调试命令
```bash
# 测试单个RSS源
curl -I "https://www.sec.gov/news/pressreleases.rss"

# 验证RSS格式
curl -s "https://www.sec.gov/news/pressreleases.rss" | head -20

# 检查Kafka主题
docker exec ai-invest-kafka-1 kafka-topics.sh --list --bootstrap-server localhost:9092
```

## 📋 扩展建议

### 添加新源
1. 验证RSS源有效性
2. 确定优先级分类
3. 添加到对应的环境变量
4. 重启producer服务

### 地区扩展
考虑添加亚太地区央行：
- 澳大利亚央行: https://www.rba.gov.au/rss/
- 新西兰央行: https://www.rbnz.govt.nz/rss/
- 韩国央行: https://www.bok.or.kr/eng/

### 行业扩展
- 能源: IEA、OPEC新闻
- 科技: 主要科技公司财报和新闻
- 房地产: 住房数据和政策

这个配置为你提供了全球主要金融新闻源的全覆盖，既保证了重要信息的实时性，又优化了系统资源使用。