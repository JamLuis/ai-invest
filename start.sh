#!/bin/bash

# AI投资财经资讯数据管道启动脚本
# 使用方法: ./start.sh [start|stop|restart|status|logs]

set -e

PROJECT_DIR="/Users/lucas/Documents/code/ai-invest"
VENV_PATH="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查Docker服务是否运行
check_docker() {
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker未运行，请启动Docker Desktop"
        exit 1
    fi
}

# 检查Python虚拟环境
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        log_warn "虚拟环境不存在，正在创建..."
        cd "$PROJECT_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        log_info "虚拟环境创建完成"
    fi
}

# 启动基础服务（Kafka, PostgreSQL）
start_infrastructure() {
    log_info "启动基础服务（Kafka, PostgreSQL）..."
    cd "$PROJECT_DIR"
    
    # 启动Docker服务
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查PostgreSQL是否就绪
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker exec ai-invest-postgres-1 pg_isready -U finance -d finance > /dev/null 2>&1; then
            log_info "PostgreSQL已就绪"
            break
        fi
        log_debug "等待PostgreSQL启动... ($retries)"
        sleep 2
        retries=$((retries-1))
    done
    
    if [ $retries -eq 0 ]; then
        log_error "PostgreSQL启动超时"
        exit 1
    fi
    
    # 初始化数据库
    log_info "初始化数据库..."
    docker exec -i ai-invest-postgres-1 psql -U finance -d finance < src/db/schema.sql 2>/dev/null || true
    
    log_info "基础服务启动完成"
}

# 启动应用服务
start_applications() {
    log_info "启动应用服务..."
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # 启动RSS Producer
    log_info "启动RSS Producer..."
    nohup python3 -m src.producer.rss_producer > "$LOG_DIR/rss_producer.log" 2>&1 &
    echo $! > "$LOG_DIR/rss_producer.pid"
    
    # 启动Parser Consumer
    log_info "启动Parser Consumer..."
    nohup python3 -m src.consumer.parser_consumer > "$LOG_DIR/parser_consumer.log" 2>&1 &
    echo $! > "$LOG_DIR/parser_consumer.pid"
    
    # 启动DB Consumer
    log_info "启动DB Consumer..."
    nohup python3 -m src.consumer.db_consumer > "$LOG_DIR/db_consumer.log" 2>&1 &
    echo $! > "$LOG_DIR/db_consumer.pid"
    
    # 启动FastAPI服务
    log_info "启动FastAPI服务..."
    nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/api.log" 2>&1 &
    echo $! > "$LOG_DIR/api.pid"
    
    # 等待服务启动
    sleep 5
    
    log_info "应用服务启动完成"
}

# 停止所有服务
stop_services() {
    log_info "停止所有服务..."
    cd "$PROJECT_DIR"
    
    # 停止应用进程
    for service in rss_producer parser_consumer db_consumer api; do
        if [ -f "$LOG_DIR/${service}.pid" ]; then
            local pid=$(cat "$LOG_DIR/${service}.pid")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "停止 $service (PID: $pid)"
                kill "$pid"
                rm -f "$LOG_DIR/${service}.pid"
            else
                log_warn "$service 进程不存在，清理PID文件"
                rm -f "$LOG_DIR/${service}.pid"
            fi
        fi
    done
    
    # 停止Docker服务
    log_info "停止基础服务..."
    docker-compose down
    
    log_info "所有服务已停止"
}

# 检查服务状态
check_status() {
    log_info "检查服务状态..."
    cd "$PROJECT_DIR"
    
    # 检查Docker服务
    echo -e "\n${BLUE}=== 基础服务状态 ===${NC}"
    if docker-compose ps | grep -q "Up"; then
        docker-compose ps
    else
        log_warn "基础服务未运行"
    fi
    
    # 检查应用进程
    echo -e "\n${BLUE}=== 应用服务状态 ===${NC}"
    for service in rss_producer parser_consumer db_consumer api; do
        if [ -f "$LOG_DIR/${service}.pid" ]; then
            local pid=$(cat "$LOG_DIR/${service}.pid")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}✓${NC} $service 运行中 (PID: $pid)"
            else
                echo -e "${RED}✗${NC} $service 已停止"
                rm -f "$LOG_DIR/${service}.pid"
            fi
        else
            echo -e "${RED}✗${NC} $service 未启动"
        fi
    done
    
    # 检查API可用性
    echo -e "\n${BLUE}=== API服务测试 ===${NC}"
    if curl -s "http://localhost:8000/news?limit=1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} API服务正常 (http://localhost:8000)"
        # 显示数据库中的文章数量
        local count=$(cd "$PROJECT_DIR" && source venv/bin/activate && python3 -c "
import psycopg2
from src.config import POSTGRES
try:
    conn = psycopg2.connect(
        host=POSTGRES['host'],
        port=POSTGRES['port'],
        dbname=POSTGRES['db'],
        user=POSTGRES['user'],
        password=POSTGRES['password']
    )
    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM articles')
    count = cur.fetchone()[0]
    print(count)
    cur.close()
    conn.close()
except:
    print('0')
" 2>/dev/null)
        echo -e "${GREEN}✓${NC} 数据库中有 $count 篇文章"
    else
        echo -e "${RED}✗${NC} API服务不可用"
    fi
}

# 显示日志
show_logs() {
    local service=${2:-"all"}
    cd "$PROJECT_DIR"
    
    if [ "$service" = "all" ]; then
        log_info "显示所有服务日志（最近50行）..."
        for log_file in rss_producer parser_consumer db_consumer api; do
            if [ -f "$LOG_DIR/${log_file}.log" ]; then
                echo -e "\n${BLUE}=== $log_file 日志 ===${NC}"
                tail -n 50 "$LOG_DIR/${log_file}.log"
            fi
        done
    else
        if [ -f "$LOG_DIR/${service}.log" ]; then
            log_info "显示 $service 日志..."
            tail -f "$LOG_DIR/${service}.log"
        else
            log_error "日志文件不存在: $service"
        fi
    fi
}

# 测试API
test_api() {
    log_info "测试API功能..."
    
    echo -e "\n${BLUE}=== 获取最新新闻 ===${NC}"
    curl -s "http://localhost:8000/news?limit=3" | python3 -m json.tool 2>/dev/null || echo "API请求失败"
    
    echo -e "\n${BLUE}=== 搜索SEC相关新闻 ===${NC}"
    curl -s "http://localhost:8000/news?q=SEC&limit=2" | python3 -m json.tool 2>/dev/null || echo "搜索请求失败"
}

# 主函数
main() {
    local command=${1:-"start"}
    
    case $command in
        "start")
            log_info "=== 启动AI投资财经资讯数据管道 ==="
            check_docker
            check_venv
            start_infrastructure
            start_applications
            check_status
            echo -e "\n${GREEN}🚀 系统启动完成！${NC}"
            echo -e "API地址: ${BLUE}http://localhost:8000${NC}"
            echo -e "使用 './start.sh test' 测试API功能"
            echo -e "使用 './start.sh logs' 查看运行日志"
            echo -e "使用 './start.sh stop' 停止所有服务"
            ;;
        "stop")
            log_info "=== 停止AI投资财经资讯数据管道 ==="
            stop_services
            echo -e "\n${GREEN}🛑 系统已停止！${NC}"
            ;;
        "restart")
            log_info "=== 重启AI投资财经资讯数据管道 ==="
            stop_services
            sleep 3
            main "start"
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs "$@"
            ;;
        "test")
            test_api
            ;;
        *)
            echo "使用方法: $0 [start|stop|restart|status|logs|test]"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动所有服务"
            echo "  stop    - 停止所有服务"
            echo "  restart - 重启所有服务"
            echo "  status  - 检查服务状态"
            echo "  logs    - 查看服务日志"
            echo "  test    - 测试API功能"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"