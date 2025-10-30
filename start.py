#!/usr/bin/env python3
"""
AI投资财经资讯数据管道 - Python启动脚本
使用方法: python start.py [start|stop|restart|status|test]
"""

import os
import sys
import time
import signal
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional

# 配置
PROJECT_DIR = Path(__file__).parent.absolute()
VENV_PATH = PROJECT_DIR / "venv"
LOG_DIR = PROJECT_DIR / "logs"
PID_DIR = LOG_DIR

# 创建目录
LOG_DIR.mkdir(exist_ok=True)
PID_DIR.mkdir(exist_ok=True)

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def log_info(msg: str):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def log_warn(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def log_debug(msg: str):
    print(f"{Colors.BLUE}[DEBUG]{Colors.NC} {msg}")

class ServiceManager:
    def __init__(self):
        self.services = {
            'rss_producer': {
                'module': 'src.producer.rss_producer',
                'name': 'RSS Producer',
                'description': 'RSS新闻抓取服务'
            },
            'parser_consumer': {
                'module': 'src.consumer.parser_consumer',
                'name': 'Parser Consumer',
                'description': '新闻解析服务'
            },
            'db_consumer': {
                'module': 'src.consumer.db_consumer',
                'name': 'DB Consumer',
                'description': '数据库写入服务'
            },
            'api': {
                'command': ['uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8000'],
                'name': 'FastAPI',
                'description': 'REST API服务'
            }
        }

    def check_docker(self) -> bool:
        """检查Docker是否运行"""
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            log_error("Docker未运行，请启动Docker Desktop")
            return False

    def check_venv(self) -> bool:
        """检查虚拟环境"""
        if not VENV_PATH.exists():
            log_warn("虚拟环境不存在，正在创建...")
            try:
                subprocess.run([sys.executable, '-m', 'venv', str(VENV_PATH)], check=True)
                pip_path = VENV_PATH / 'bin' / 'pip'
                subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], check=True)
                log_info("虚拟环境创建完成")
                return True
            except subprocess.CalledProcessError as e:
                log_error(f"创建虚拟环境失败: {e}")
                return False
        return True

    def start_infrastructure(self) -> bool:
        """启动基础服务"""
        log_info("启动基础服务（Kafka, PostgreSQL）...")
        
        try:
            # 启动Docker服务
            subprocess.run(['docker-compose', 'up', '-d'], cwd=PROJECT_DIR, check=True)
            
            # 等待PostgreSQL启动
            log_info("等待PostgreSQL启动...")
            for i in range(30):
                try:
                    result = subprocess.run([
                        'docker', 'exec', 'ai-invest-postgres-1', 
                        'pg_isready', '-U', 'finance', '-d', 'finance'
                    ], capture_output=True, check=True)
                    log_info("PostgreSQL已就绪")
                    break
                except subprocess.CalledProcessError:
                    if i == 29:
                        log_error("PostgreSQL启动超时")
                        return False
                    log_debug(f"等待PostgreSQL启动... ({30-i})")
                    time.sleep(2)
            
            # 初始化数据库
            log_info("初始化数据库...")
            with open(PROJECT_DIR / 'src' / 'db' / 'schema.sql', 'r') as f:
                schema_sql = f.read()
            
            process = subprocess.Popen([
                'docker', 'exec', '-i', 'ai-invest-postgres-1',
                'psql', '-U', 'finance', '-d', 'finance'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = process.communicate(schema_sql.encode())
            
            log_info("基础服务启动完成")
            return True
            
        except subprocess.CalledProcessError as e:
            log_error(f"启动基础服务失败: {e}")
            return False

    def start_service(self, service_key: str) -> bool:
        """启动单个服务"""
        service = self.services[service_key]
        log_info(f"启动 {service['name']}...")
        
        try:
            # 准备命令
            if 'module' in service:
                cmd = [str(VENV_PATH / 'bin' / 'python3'), '-m', service['module']]
            else:
                cmd = [str(VENV_PATH / 'bin' / service['command'][0])] + service['command'][1:]
            
            # 启动进程
            log_file = LOG_DIR / f"{service_key}.log"
            pid_file = PID_DIR / f"{service_key}.pid"
            
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    cmd, 
                    cwd=PROJECT_DIR,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            # 保存PID
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            log_debug(f"{service['name']} 已启动 (PID: {process.pid})")
            return True
            
        except Exception as e:
            log_error(f"启动 {service['name']} 失败: {e}")
            return False

    def stop_service(self, service_key: str) -> bool:
        """停止单个服务"""
        service = self.services[service_key]
        pid_file = PID_DIR / f"{service_key}.pid"
        
        if not pid_file.exists():
            log_debug(f"{service['name']} 未运行")
            return True
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            try:
                os.kill(pid, 0)
            except OSError:
                log_debug(f"{service['name']} 进程不存在，清理PID文件")
                pid_file.unlink()
                return True
            
            # 优雅停止
            log_info(f"停止 {service['name']} (PID: {pid})")
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程结束
            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.5)
                except OSError:
                    break
            else:
                # 强制停止
                log_warn(f"强制停止 {service['name']}")
                os.kill(pid, signal.SIGKILL)
            
            pid_file.unlink()
            return True
            
        except Exception as e:
            log_error(f"停止 {service['name']} 失败: {e}")
            return False

    def get_service_status(self, service_key: str) -> Dict:
        """获取服务状态"""
        service = self.services[service_key]
        pid_file = PID_DIR / f"{service_key}.pid"
        
        if not pid_file.exists():
            return {'running': False, 'pid': None}
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            try:
                os.kill(pid, 0)
                return {'running': True, 'pid': pid}
            except OSError:
                pid_file.unlink()
                return {'running': False, 'pid': None}
                
        except Exception:
            return {'running': False, 'pid': None}

    def start_all(self) -> bool:
        """启动所有服务"""
        log_info("=== 启动AI投资财经资讯数据管道 ===")
        
        # 检查依赖
        if not self.check_docker():
            return False
        
        if not self.check_venv():
            return False
        
        # 启动基础服务
        if not self.start_infrastructure():
            return False
        
        # 启动应用服务
        log_info("启动应用服务...")
        success = True
        for service_key in self.services:
            if not self.start_service(service_key):
                success = False
        
        if success:
            time.sleep(5)  # 等待服务启动
            log_info("应用服务启动完成")
        
        return success

    def stop_all(self) -> bool:
        """停止所有服务"""
        log_info("=== 停止AI投资财经资讯数据管道 ===")
        
        # 停止应用服务
        for service_key in self.services:
            self.stop_service(service_key)
        
        # 停止基础服务
        try:
            log_info("停止基础服务...")
            subprocess.run(['docker-compose', 'down'], cwd=PROJECT_DIR, check=True)
        except subprocess.CalledProcessError as e:
            log_error(f"停止基础服务失败: {e}")
            return False
        
        log_info("所有服务已停止")
        return True

    def check_status(self):
        """检查所有服务状态"""
        log_info("检查服务状态...")
        
        # 检查Docker服务
        print(f"\n{Colors.BLUE}=== 基础服务状态 ==={Colors.NC}")
        try:
            result = subprocess.run(['docker-compose', 'ps'], cwd=PROJECT_DIR, capture_output=True, text=True)
            if 'Up' in result.stdout:
                print(result.stdout)
            else:
                log_warn("基础服务未运行")
        except subprocess.CalledProcessError:
            log_warn("无法获取基础服务状态")
        
        # 检查应用服务
        print(f"\n{Colors.BLUE}=== 应用服务状态 ==={Colors.NC}")
        for service_key, service in self.services.items():
            status = self.get_service_status(service_key)
            if status['running']:
                print(f"{Colors.GREEN}✓{Colors.NC} {service['name']} 运行中 (PID: {status['pid']})")
            else:
                print(f"{Colors.RED}✗{Colors.NC} {service['name']} 未运行")
        
        # 检查API
        print(f"\n{Colors.BLUE}=== API服务测试 ==={Colors.NC}")
        try:
            response = requests.get("http://localhost:8000/news?limit=1", timeout=5)
            if response.status_code == 200:
                print(f"{Colors.GREEN}✓{Colors.NC} API服务正常 (http://localhost:8000)")
                
                # 检查数据库文章数量
                try:
                    import psycopg2
                    sys.path.insert(0, str(PROJECT_DIR))
                    from src.config import POSTGRES
                    
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
                    cur.close()
                    conn.close()
                    print(f"{Colors.GREEN}✓{Colors.NC} 数据库中有 {count} 篇文章")
                except Exception as e:
                    print(f"{Colors.YELLOW}!{Colors.NC} 无法获取数据库文章数量: {e}")
            else:
                print(f"{Colors.RED}✗{Colors.NC} API服务返回错误状态码: {response.status_code}")
        except requests.RequestException:
            print(f"{Colors.RED}✗{Colors.NC} API服务不可用")

    def test_api(self):
        """测试API功能"""
        log_info("测试API功能...")
        
        try:
            # 测试获取最新新闻
            print(f"\n{Colors.BLUE}=== 获取最新新闻 ==={Colors.NC}")
            response = requests.get("http://localhost:8000/news?limit=3", timeout=10)
            if response.status_code == 200:
                news = response.json()
                print(json.dumps(news, indent=2, ensure_ascii=False))
            else:
                print(f"API请求失败: {response.status_code}")
            
            # 测试搜索功能
            print(f"\n{Colors.BLUE}=== 搜索SEC相关新闻 ==={Colors.NC}")
            response = requests.get("http://localhost:8000/news?q=SEC&limit=2", timeout=10)
            if response.status_code == 200:
                news = response.json()
                print(json.dumps(news, indent=2, ensure_ascii=False))
            else:
                print(f"搜索请求失败: {response.status_code}")
                
        except requests.RequestException as e:
            log_error(f"API测试失败: {e}")

def main():
    if len(sys.argv) < 2:
        command = 'start'
    else:
        command = sys.argv[1]
    
    manager = ServiceManager()
    
    if command == 'start':
        if manager.start_all():
            manager.check_status()
            print(f"\n{Colors.GREEN}🚀 系统启动完成！{Colors.NC}")
            print(f"API地址: {Colors.BLUE}http://localhost:8000{Colors.NC}")
            print(f"使用 'python start.py test' 测试API功能")
            print(f"使用 'python start.py status' 查看服务状态")
            print(f"使用 'python start.py stop' 停止所有服务")
        else:
            print(f"\n{Colors.RED}❌ 系统启动失败！{Colors.NC}")
            sys.exit(1)
            
    elif command == 'stop':
        if manager.stop_all():
            print(f"\n{Colors.GREEN}🛑 系统已停止！{Colors.NC}")
        else:
            sys.exit(1)
            
    elif command == 'restart':
        manager.stop_all()
        time.sleep(3)
        if manager.start_all():
            manager.check_status()
            print(f"\n{Colors.GREEN}🔄 系统重启完成！{Colors.NC}")
        else:
            sys.exit(1)
            
    elif command == 'status':
        manager.check_status()
        
    elif command == 'test':
        manager.test_api()
        
    else:
        print("使用方法: python start.py [start|stop|restart|status|test]")
        print("")
        print("命令说明:")
        print("  start   - 启动所有服务")
        print("  stop    - 停止所有服务")
        print("  restart - 重启所有服务")
        print("  status  - 检查服务状态")
        print("  test    - 测试API功能")
        sys.exit(1)

if __name__ == '__main__':
    main()