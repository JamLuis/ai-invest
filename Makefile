.PHONY: up down deps api prod parse db migrate start stop restart status test clean logs

# 基础服务管理
up:
	docker-compose up -d

down:
	docker-compose down

# 依赖和环境
deps:
	python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

# 数据库初始化
migrate:
	docker exec -i ai-invest-postgres-1 psql -U finance -d finance < src/db/schema.sql

# 智能数据库初始化（仅当表不存在时才运行）
migrate-if-needed:
	@if ! docker exec ai-invest-postgres-1 psql -U finance -d finance -c "SELECT 1 FROM articles LIMIT 1;" >/dev/null 2>&1; then \
		echo "初始化数据库schema..."; \
		docker exec -i ai-invest-postgres-1 psql -U finance -d finance < src/db/schema.sql; \
	else \
		echo "数据库已存在，跳过初始化"; \
	fi

# 强制重置数据库（清空所有数据）
reset-db:
	@echo "⚠️  警告：这将清空所有数据！"
	@read -p "确认要重置数据库吗？(y/N): " confirm && [ "$$confirm" = "y" ] || { echo "操作已取消"; exit 1; }
	@echo "重置数据库..."
	@docker exec ai-invest-postgres-1 psql -U finance -d finance -c "DROP TABLE IF EXISTS articles;"
	@docker exec -i ai-invest-postgres-1 psql -U finance -d finance < src/db/schema.sql
	@echo "数据库已重置"

# 单独服务启动（需要在虚拟环境中运行）
api:
	. venv/bin/activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

prod:
	. venv/bin/activate && python3 -m src.producer.rss_producer

# 增强版多优先级RSS Producer
prod-enhanced:
	. venv/bin/activate && python3 -m src.producer.enhanced_rss_producer

parse:
	. venv/bin/activate && python3 -m src.consumer.parser_consumer

db:
	. venv/bin/activate && python3 -m src.consumer.db_consumer

# 一键启动/停止
start: check-deps up wait-postgres migrate-if-needed start-services
	@echo "🚀 AI投资财经资讯数据管道启动完成！"
	@echo "API地址: http://localhost:8000"
	@echo "使用 'make status' 查看服务状态"
	@echo "使用 'make test' 测试API功能"
	@echo "使用 'make stop' 停止所有服务"

stop:
	@echo "🛑 停止所有服务..."
	@pkill -f "src.producer.rss_producer" || true
	@pkill -f "src.consumer.parser_consumer" || true
	@pkill -f "src.consumer.db_consumer" || true
	@pkill -f "uvicorn.*src.api.main" || true
	@make down
	@echo "所有服务已停止"

restart: stop
	@sleep 3
	@make start

# 检查依赖
check-deps:
	@echo "检查依赖..."
	@command -v docker >/dev/null 2>&1 || { echo "错误: Docker未安装"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "错误: Python3未安装"; exit 1; }
	@[ -d venv ] || { echo "创建虚拟环境..."; make deps; }

# 等待PostgreSQL启动
wait-postgres:
	@echo "等待PostgreSQL启动..."
	@for i in $$(seq 1 30); do \
		if docker exec ai-invest-postgres-1 pg_isready -U finance -d finance >/dev/null 2>&1; then \
			echo "PostgreSQL已就绪"; \
			break; \
		fi; \
		echo "等待PostgreSQL启动... ($$i/30)"; \
		sleep 2; \
	done

# 启动应用服务
start-services:
	@echo "启动应用服务..."
	@mkdir -p logs
	@. venv/bin/activate && nohup python3 -m src.producer.enhanced_rss_producer > logs/rss_producer.log 2>&1 & echo $$! > logs/rss_producer.pid
	@sleep 2
	@. venv/bin/activate && nohup python3 -m src.consumer.parser_consumer > logs/parser_consumer.log 2>&1 & echo $$! > logs/parser_consumer.pid
	@sleep 2
	@. venv/bin/activate && nohup python3 -m src.consumer.db_consumer > logs/db_consumer.log 2>&1 & echo $$! > logs/db_consumer.pid
	@sleep 2
	@. venv/bin/activate && nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 & echo $$! > logs/api.pid
	@sleep 3
	@echo "应用服务启动完成"

# 检查服务状态
status:
	@echo "=== 基础服务状态 ==="
	@docker-compose ps 2>/dev/null || echo "基础服务未运行"
	@echo ""
	@echo "=== 应用服务状态 ==="
	@for service in rss_producer parser_consumer db_consumer api; do \
		if [ -f logs/$$service.pid ]; then \
			pid=$$(cat logs/$$service.pid); \
			if kill -0 $$pid 2>/dev/null; then \
				echo "✓ $$service 运行中 (PID: $$pid)"; \
			else \
				echo "✗ $$service 已停止"; \
				rm -f logs/$$service.pid; \
			fi; \
		else \
			echo "✗ $$service 未启动"; \
		fi; \
	done
	@echo ""
	@echo "=== API服务测试 ==="
	@if curl -s "http://localhost:8000/news?limit=1" > /dev/null 2>&1; then \
		echo "✓ API服务正常 (http://localhost:8000)"; \
		count=$$(. venv/bin/activate && python3 -c "import psycopg2; from src.config import POSTGRES; conn = psycopg2.connect(host=POSTGRES['host'], port=POSTGRES['port'], dbname=POSTGRES['db'], user=POSTGRES['user'], password=POSTGRES['password']); cur = conn.cursor(); cur.execute('SELECT count(*) FROM articles'); print(cur.fetchone()[0]); cur.close(); conn.close()" 2>/dev/null || echo "0"); \
		echo "✓ 数据库中有 $$count 篇文章"; \
	else \
		echo "✗ API服务不可用"; \
	fi

# 测试API
test:
	@echo "=== 测试API功能 ==="
	@echo "获取最新新闻:"
	@curl -s "http://localhost:8000/news?limit=3" | python3 -m json.tool 2>/dev/null || echo "API请求失败"
	@echo ""
	@echo "搜索SEC相关新闻:"
	@curl -s "http://localhost:8000/news?q=SEC&limit=2" | python3 -m json.tool 2>/dev/null || echo "搜索请求失败"

# 查看日志
logs:
	@if [ -n "$(SERVICE)" ]; then \
		if [ -f logs/$(SERVICE).log ]; then \
			tail -f logs/$(SERVICE).log; \
		else \
			echo "日志文件不存在: $(SERVICE)"; \
		fi; \
	else \
		echo "查看指定服务日志: make logs SERVICE=rss_producer|parser_consumer|db_consumer|api"; \
		echo "或查看所有服务的最新日志:"; \
		for service in rss_producer parser_consumer db_consumer api; do \
			if [ -f logs/$$service.log ]; then \
				echo ""; \
				echo "=== $$service 日志 (最近10行) ==="; \
				tail -n 10 logs/$$service.log; \
			fi; \
		done; \
	fi

# 清理
clean:
	@echo "清理日志和PID文件..."
	@rm -rf logs/*.log logs/*.pid
	@echo "清理完成"
