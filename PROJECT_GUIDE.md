# 财经资讯数据管道项目指南

## 项目概览
- 项目目标：从合规财经 RSS 源获取新闻，经 Kafka 管道清洗去重后写入 PostgreSQL，并通过 FastAPI 提供查询接口。
- 核心组件：
  - `src/producer/rss_producer.py`：按照 `.env` 中的 `FEEDS` 与 `POLL_INTERVAL_SECONDS` 周期抓取 RSS，写入 Kafka 主题 `raw_feed`。
  - `src/consumer/parser_consumer.py`：规范化 URL、生成内容指纹及 NLP 预留字段，将结构化结果发送至 `parsed_news`。
  - `src/consumer/db_consumer.py`：批量 upsert `parsed_news` 数据到 Postgres `articles` 表。
  - `src/api/main.py`：FastAPI 服务，提供 `/news` REST 接口按关键词或时间获取最新资讯。
- 配置来源：`src/config.py` 自动加载 `.env`，集中管理 Kafka、Postgres 及抓取参数。

## 环境准备
1. 安装依赖
   - 系统：Docker、docker-compose、Python 3.11+。
   - Python 包：`pip install -r requirements.txt`（建议使用 venv）。
2. 环境变量
   - 复制 `.env.example`（若存在）为 `.env`，或直接编辑 `.env`。
   - 关键变量：`KAFKA_BOOTSTRAP`、`POSTGRES_*`、`FEEDS`、`POLL_INTERVAL_SECONDS`、`API_HOST` / `API_PORT`。
3. 启动基础服务
   - `docker-compose up -d` 或 `make up` 启动 Kafka 与 Postgres。
   - 通过 `docker ps`、`kafkacat` 或 `pg_isready` 验证容器状态。

## 数据库初始化
- 运行 `make migrate` 或执行 `psql -h localhost -U finance -d finance -f src/db/schema.sql` 初始化 `articles` 表及索引。
- 默认账户：用户名 `finance`，密码 `finance`，端口 `5432`。

## 运行流程
在三个终端（或使用进程管理工具）分别启动核心组件，另开一个终端运行 API。

```bash
# 终端 1：RSS Producer
make prod

# 终端 2：Parser Consumer
make parse

# 终端 3：DB Consumer
make db

# 终端 4：FastAPI 服务
make api
```

运行中 producer 会周期性抓取 `.env` 中的各个 RSS 源，解析模块会对摘要做去重指纹，数据库消费者每 100 条提交一次事务，FastAPI 将查询结果作为 JSON 返回。

## 输入与输出
- **输入**：来自 `FEEDS` 的 RSS 条目（标题、摘要、链接、发布时间等原始元数据）。
- **Kafka 主题**：
  - `raw_feed`：RSS 原始 JSON（Producer 产出）。
  - `parsed_news`：清洗后的结构化 JSON（Parser 产出）。
- **数据库存储**：`articles` 表（见 `src/db/schema.sql`）持久化新闻数据及指纹字段，可扩展 NLP 标注。
- **API 输出**：访问 `http://localhost:8000/news?q=HKEX` 可得到如下结构示例：

```json
{
  "id": 42,
  "source": "https://www.sec.gov/news/pressreleases.rss",
  "url": "https://www.sec.gov/news/press-release/2024-123",
  "title": "SEC Announces ...",
  "summary": "The SEC today ...",
  "published_at": "2024-09-17T05:00:00+00:00"
}
```

## 常用命令（Makefile）
- `make up` / `make down`：启动或停止 Kafka、Postgres。
- `make deps`：创建虚拟环境并安装 Python 依赖。
- `make prod` / `make parse` / `make db`：分别启动三个 Kafka 处理进程。
- `make api`：以开发模式启动 FastAPI。
- `make migrate`：执行数据库建表脚本。

## 故障排查
- Kafka 连接异常：确认 `KAFKA_BOOTSTRAP` 与 `docker-compose` 端口是否一致，可使用 `kafkacat -b localhost:9092 -L` 测试。
- Postgres 连接失败：检查容器健康状态、端口转发及 `.env` 中凭据；必要时重新执行建表脚本。
- API 返回空数据：通过 `psql` 执行 `SELECT count(*) FROM articles;`，确认是否有入库数据及去重是否过严。
- 重复率高：确保 `src/utils/url_norm.py` 与 `src/utils/hashing.py` 生效，并检查 `articles` 表上的 `ON CONFLICT (url)` 逻辑。

## 一键启动解决方案

### 从手动启动到自动化演进

传统的手动启动方式需要在多个终端中按顺序执行8个步骤，容易出错且效率低下。为了提升开发体验，我们实现了完整的一键启动自动化系统。

**原手动流程**：

1. 启动 Docker 服务 (`docker-compose up -d`)
2. 等待 PostgreSQL 就绪
3. 初始化数据库 (`make migrate`)
4. 分别在4个终端启动各个服务
5. 手动检查各服务状态
6. 测试 API 功能

**现自动化流程**：

- 一个命令：`make start`

### 🚀 一键启动命令

```bash
# 启动整个项目（包含所有基础设施和应用服务）
make start

# 检查系统状态（Docker容器 + Python服务 + API健康检查）
make status

# 测试API功能（验证数据库连接和查询功能）
make test

# 停止所有服务（清理Docker容器和Python进程）
make stop
```

### 📊 自动化特性

**智能服务编排**：

- 自动启动 Kafka 和 PostgreSQL 容器
- 智能等待 PostgreSQL 完全就绪（健康检查）
- 自动初始化数据库表结构
- 按正确依赖顺序启动4个Python服务

**健康监控**：

- Docker 容器状态检查
- Python 进程 PID 跟踪
- API 服务响应测试
- 数据库连接验证

**错误处理**：

- 服务启动失败自动提示
- 详细的错误信息输出
- 服务依赖检查和等待机制

### 📈 自动化收益

**效率提升**：

- 启动时间：从5-10分钟减少到2-3分钟
- 操作步骤：从8个手动步骤减少到1个命令
- 错误率：消除人为操作错误

**开发体验**：

- 新团队成员可以立即上手
- 一致的开发环境启动流程
- 清晰的服务状态可视化

**运维友好**：

- 统一的服务生命周期管理
- 自动化的健康检查
- 便捷的故障排查工具

### 🔧 技术实现

**Makefile 增强**：

- `start` 目标：完整的服务启动编排
- `status` 目标：多层次的状态检查
- `test` 目标：API 功能验证
- `stop` 目标：优雅的服务关闭

**服务管理脚本**：

- 后台进程管理和 PID 跟踪
- 服务启动顺序控制
- 健康检查和等待机制

**配置管理**：

- 环境变量自动加载
- 服务端口冲突检测
- 依赖服务可用性验证

## 后续扩展建议

- 在 `src/nlp` 模块补充语言检测、情绪、实体抽取，并回填 `articles` 表对应字段。
- 为原始 HTML 留存实现对象存储接口（如 S3/MinIO），并在表中记录 `raw_ref`。
- 引入 OpenSearch/Elasticsearch 建立全文检索，增强查询能力。
- 结合 Airflow、Prometheus 等工具实现调度与可观测性。
- 考虑添加实时日志监控和性能指标收集。
- 实现配置文件验证和环境一致性检查。

