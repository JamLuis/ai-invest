# API 文档目录

欢迎使用 Finance News API 文档！这里包含了完整的API使用指南和参考资料。

## 📁 文档结构

### 🚀 快速开始
- **[快速参考](quick-reference.md)** - 最常用的API调用方式和快速示例
- **[使用示例](examples.md)** - 详细的代码示例，包含Python、JavaScript等多种语言

### 📖 详细文档
- **[完整API文档](README.md)** - 详细的API规范、参数说明和响应格式
- **[OpenAPI规范](openapi.yaml)** - 标准的OpenAPI 3.0规范文件

### 🛠️ 开发工具
- **[Postman集合](postman-collection.json)** - 可直接导入Postman的API测试集合

## 🔗 在线文档访问

当API服务运行时，你可以通过以下链接访问交互式文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📋 API 概览

### 基本信息
- **Base URL**: `http://localhost:8000`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **认证**: 无需认证

### 可用端点

| 方法 | 端点 | 描述 | 参数 |
|------|------|------|------|
| GET | `/news` | 获取新闻列表 | `q`(搜索), `limit`(数量) |

## 🚀 快速开始

### 1. 确保服务运行
```bash
# 启动整个项目
make start

# 检查API状态
curl http://localhost:8000/news?limit=1
```

### 2. 基本使用

```bash
# 获取最新新闻
curl "http://localhost:8000/news?limit=5"

# 搜索特定内容
curl "http://localhost:8000/news?q=SEC&limit=10"
```

### 3. 导入测试集合

1. 下载 [postman-collection.json](postman-collection.json)
2. 在Postman中选择"Import" 
3. 选择下载的JSON文件
4. 开始测试API

## 📊 数据源信息

当前API聚合以下财经新闻源：

- **SEC** (美国证券交易委员会): 监管新闻和公告
- **HKEX** (香港交易所): 交易所新闻和市场动态

## 💡 使用建议

### 性能优化
- 使用合适的`limit`参数避免返回过多数据
- 针对性使用`q`参数进行关键词搜索
- 考虑在客户端实现缓存机制

### 错误处理
- 始终检查HTTP状态码
- 实现适当的重试机制
- 处理网络超时和连接错误

### 最佳实践
- 使用有意义的搜索关键词
- 分页获取大量数据
- 定期监控API响应时间

## 🔧 开发环境

### 本地开发设置

```bash
# 克隆项目
git clone <repository-url>
cd ai-invest

# 启动开发环境
make start

# 验证API
curl http://localhost:8000/news?limit=1
```

### 测试环境变量

确保以下环境变量正确配置：
- `POSTGRES_*`: PostgreSQL数据库连接信息
- `KAFKA_BOOTSTRAP`: Kafka服务器地址
- `API_HOST`/`API_PORT`: API服务配置

## 📈 监控和分析

### 健康检查
```bash
# 检查API状态
curl http://localhost:8000/news?limit=1

# 检查数据库连接
make status
```

### 性能监控
- 响应时间监控
- 数据库查询性能
- 新闻数据更新频率

## 🤝 支持和反馈

### 获取帮助
1. 查看文档中的[使用示例](examples.md)
2. 检查[常见问题](#常见问题)
3. 联系开发团队

### 报告问题
- 描述具体的API调用和期望结果
- 提供错误信息和状态码
- 包含复现步骤

## ❓ 常见问题

### Q: API返回空数据怎么办？
A: 检查数据库中是否有数据，确认RSS数据源正常工作。

### Q: 搜索没有结果？
A: 尝试使用不同的关键词，确认搜索词在标题或摘要中存在。

### Q: API响应慢？
A: 减少`limit`参数值，检查数据库性能和网络连接。

### Q: 如何获取特定时间范围的新闻？
A: 当前版本按发布时间倒序返回，可在客户端进行时间过滤。

## 🔄 版本历史

- **v1.0.0** (2024-10-30): 初始版本发布，支持基础新闻查询和搜索功能

---

📝 **文档更新**: 2024-10-30  
🔗 **项目地址**: [GitHub Repository](https://github.com/your-org/ai-invest)