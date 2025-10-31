# 数据持久化配置说明 💾

## ✅ 问题解决

### 之前的问题
- 每次启动服务时，PostgreSQL数据库数据会被清空
- 容器重启后所有收集的新闻数据丢失
- 需要重新运行数据库初始化脚本

### ✅ 解决方案

#### 1. PostgreSQL数据持久化
在`docker-compose.yml`中添加了卷挂载：

```yaml
postgres:
  image: postgres:16
  volumes:
    - postgres_data:/var/lib/postgresql/data  # 数据持久化
  # ... 其他配置

volumes:
  postgres_data:  # 定义数据卷
```

#### 2. 智能数据库初始化
在`Makefile`中添加了智能初始化逻辑：

```makefile
# 智能数据库初始化（仅当表不存在时才运行）
migrate-if-needed:
	@if ! docker exec ai-invest-postgres-1 psql -U finance -d finance -c "SELECT 1 FROM articles LIMIT 1;" >/dev/null 2>&1; then \
		echo "初始化数据库schema..."; \
		docker exec -i ai-invest-postgres-1 psql -U finance -d finance < src/db/schema.sql; \
	else \
		echo "数据库已存在，跳过初始化"; \
	fi
```

#### 3. 增强版RSS Producer集成
- 默认使用`enhanced_rss_producer`而不是原版
- 支持多优先级RSS源收集
- 更好的错误处理和日志记录

### 📊 验证结果

#### 测试步骤
1. 启动服务并收集数据：`make start`
2. 收集了**100篇文章**
3. 停止所有服务：`make stop`  
4. 重新启动服务：`make start`
5. 检查数据：仍然有**100篇文章** ✅

#### 观察到的行为
- ✅ 第一次启动：显示"初始化数据库schema..."
- ✅ 重启后：显示"数据库已存在，跳过初始化"
- ✅ 数据完全保留，无数据丢失

## 🛠️ 可用命令

### 正常操作
```bash
make start    # 启动服务（智能初始化）
make stop     # 停止服务
make restart  # 重启服务
make status   # 检查状态
```

### 数据库管理
```bash
make migrate-if-needed  # 仅在需要时初始化数据库
make migrate           # 强制运行数据库初始化
make reset-db          # ⚠️ 清空所有数据并重新初始化（需确认）
```

### 服务控制
```bash
make prod-enhanced  # 单独启动增强版RSS Producer
make api           # 单独启动API服务
make parse         # 单独启动解析器
make db            # 单独启动数据库消费者
```

## 🎯 数据保护特性

### 🔒 自动保护
- **容器重启**：数据自动保留
- **系统重启**：数据永久存储在Docker卷中
- **意外关闭**：PostgreSQL数据不会丢失

### ⚠️ 数据清空场景
数据只会在以下情况下被清空：
- 手动运行`make reset-db`
- 删除Docker卷：`docker volume rm ai-invest_postgres_data`
- 手动删除表或数据

### 🚀 最佳实践
- 使用`make start`进行正常启动
- 定期检查`make status`确认服务健康
- 需要清空数据时明确使用`make reset-db`
- 重要数据可以通过API导出备份

## 📈 性能影响

### 存储需求
- **Docker卷**：随数据增长，预计1-10GB/月
- **数据表**：100-1000篇文章/天，约1-10MB/天

### 启动时间
- **首次启动**：需要运行schema初始化（+3-5秒）
- **后续启动**：跳过初始化，启动更快（-3-5秒）

---
*配置更新：2025-10-31*  
*测试验证：✅ 数据持久化正常工作*