⸻

Finance News Ingestion Pipeline (RSS→Kafka→Parser→DB→API)

目标：从合规来源（以 RSS/官网公告为主）抓取一手财经/政策新闻，经清洗/去重/打标后存入数据库，支持检索/服务端 API，作为后续量化交易/大模型选股分析的数据源。优先可授权/公开源；对禁止抓取的商业新闻（如付费墙）仅保留元数据与链接，不抓取全文。

⸻

1. 关键需求（Requirements）
	1.	数据源（首批）
	•	RSS/Feed（示例，可替换为你确认可抓/允许的）：
	•	https://www.hkex.com.hk/News/News-Release/News-Release?format=rss
	•	https://www.sec.gov/news/pressreleases.rss
	•	支持后续扩展到：交易所公告、监管机构、央行/政府官网、公司 IR 新闻室、经济数据日历（需许可的 API）。
	2.	合规
	•	遵守 robots.txt 与站点 ToS。
	•	禁止绕过登录/付费墙/验证码；优先 RSS/API 与官方公告。
	•	时区统一存 UTC；保留 source_tz 元数据。
	3.	数据处理
	•	生产者：RSS 拉取→写入 Kafka（Topic: raw_feed）
	•	解析器：提取标题/摘要/发布时间/正文（若许可）；去重（URL 规范化 + 内容指纹 SimHash/MD5 简化版）；
	•	打标（第一版可选）：语言检测、情绪评分（占位）、实体识别（占位），留出接口。
	•	存储：PostgreSQL（结构化）+（可选）OpenSearch/Elasticsearch（全文检索）；原始 HTML 快照可写入对象存储（此处留接口）。
	•	服务：FastAPI 暴露 REST（按时间/关键词/Ticker 查询）。
	4.	性能与稳定
	•	可通过 Kafka 横向扩展；抓取周期默认 60s，可配置。
	•	记录日志与基本指标（入库量/重复率/失败率），打印到 stdout，后续接入 Prometheus/Grafana。
	5.	可运行性
	•	提供 docker-compose.yml 一键起 Zookeeper + Kafka + Postgres（可选再加 OpenSearch）。
	•	Python 组件使用 venv 或 poetry，提供 requirements.txt。
	•	提供 VS Code 运行/调试配置（.vscode/launch.json）和常用脚本（Makefile 可选）。

⸻

2. 技术栈（Tech Stack）
	•	消息队列：Kafka（topic: raw_feed → parsed_news）
	•	抓取：feedparser（RSS）；为后续 Scrapy/Playwright 预留
	•	解析/清洗：trafilatura（正文抽取）、readability-lxml（可选）
	•	NLP 占位：langdetect/cld3、transformers（FinBERT 可后续引入）
	•	存储：PostgreSQL（结构化）+ pgvector（可选向量）；OpenSearch（可选）
	•	服务：FastAPI + Uvicorn
	•	运维：docker-compose；日志用 Python logging；监控预留

⸻

3. 目标目录结构（Project Layout）

finance-news-pipeline/
├─ .env.example
├─ docker-compose.yml
├─ requirements.txt
├─ Makefile                 # 可选：常用命令封装
├─ README.md                # 本文件
├─ src/
│  ├─ config.py
│  ├─ utils/
│  │  ├─ url_norm.py        # URL 归一化
│  │  ├─ hashing.py         # 指纹/SimHash（先用MD5/简化版）
│  │  └─ timeutil.py        # 时区与时间解析
│  ├─ producer/
│  │  └─ rss_producer.py    # RSS→Kafka raw_feed
│  ├─ consumer/
│  │  ├─ parser_consumer.py # raw_feed→解析→parsed_news
│  │  └─ db_consumer.py     # parsed_news→PostgreSQL
│  ├─ nlp/
│  │  ├─ language.py        # 语言检测
│  │  ├─ sentiment.py       # 情绪占位（可返回0）
│  │  └─ entities.py        # 实体识别占位（先空实现）
│  ├─ db/
│  │  ├─ schema.sql         # 建表脚本
│  │  └─ pg.py              # Postgres 连接与插入
│  └─ api/
│     └─ main.py            # FastAPI 查询接口
└─ .vscode/
   ├─ launch.json           # VS Code 调试
   └─ settings.json         # Black/Flake8等可选


⸻

4. 环境变量（.env）

复制 .env.example 为 .env，内容示例：

# Kafka
KAFKA_BOOTSTRAP=localhost:9092
RAW_TOPIC=raw_feed
PARSED_TOPIC=parsed_news

# DB
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=finance
POSTGRES_USER=finance
POSTGRES_PASSWORD=finance

# Producer
FEEDS=https://www.hkex.com.hk/News/News-Release/News-Release?format=rss,https://www.sec.gov/news/pressreleases.rss
POLL_INTERVAL_SECONDS=60

# Service
API_HOST=0.0.0.0
API_PORT=8000


⸻

5. Docker Compose（最小集）

version: '3.8'
services:
  zookeeper:
    image: bitnami/zookeeper:latest
    environment:
      - ALLOW_ANONYMOUS_LOGIN=yes
    ports: ["2181:2181"]

  kafka:
    image: bitnami/kafka:latest
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_LISTENERS=PLAINTEXT://:9092
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - ALLOW_PLAINTEXT_LISTENER=yes

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: finance
      POSTGRES_USER: finance
      POSTGRES_PASSWORD: finance
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U finance -d finance"]
      interval: 5s
      timeout: 3s
      retries: 30


⸻

6. Python 依赖（requirements.txt）

feedparser==6.0.11
kafka-python==2.0.2
trafilatura==1.6.3
readability-lxml==0.8.1
beautifulsoup4==4.12.3
langdetect==1.0.9
python-dotenv==1.0.1
psycopg2-binary==2.9.9
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2


⸻

7. 数据库 schema（src/db/schema.sql）

CREATE TABLE IF NOT EXISTS articles (
  id BIGSERIAL PRIMARY KEY,
  source VARCHAR(128),
  source_type VARCHAR(32),
  url TEXT UNIQUE,
  url_norm TEXT,
  title TEXT,
  summary TEXT,
  published_at TIMESTAMPTZ,  -- UTC
  source_tz VARCHAR(64),
  language VARCHAR(16),
  authors TEXT[],
  tickers TEXT[],
  entities JSONB,
  countries TEXT[],
  sectors TEXT[],
  topics TEXT[],
  sentiment NUMERIC,
  text TEXT,
  hash_title TEXT,
  hash_content TEXT,
  raw_ref TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_language ON articles (language);


⸻

8. 核心代码骨架

8.1 配置加载（src/config.py）

import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
RAW_TOPIC = os.getenv("RAW_TOPIC", "raw_feed")
PARSED_TOPIC = os.getenv("PARSED_TOPIC", "parsed_news")

POSTGRES = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "db": os.getenv("POSTGRES_DB", "finance"),
    "user": os.getenv("POSTGRES_USER", "finance"),
    "password": os.getenv("POSTGRES_PASSWORD", "finance"),
}

FEEDS = [u.strip() for u in os.getenv("FEEDS", "").split(",") if u.strip()]
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

8.2 URL 归一化（src/utils/url_norm.py）

from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

def normalize(u: str) -> str:
    if not u: return u
    parts = urlsplit(u)
    # 过滤常见追踪参数
    query = [(k,v) for k,v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    query.sort()
    return urlunsplit((parts.scheme.lower(),
                       parts.netloc.lower(),
                       parts.path,
                       urlencode(query),
                       ""))  # 去掉 fragment

8.3 指纹（src/utils/hashing.py）

import re, hashlib
_ws = re.compile(r"\s+")

def md5_fingerprint(text: str) -> str:
    if not text: return ""
    norm = _ws.sub(" ", text).strip().lower()
    return hashlib.md5(norm.encode("utf-8")).hexdigest()

8.4 时间工具（src/utils/timeutil.py）

from datetime import datetime, timezone

def now_utc():
    return datetime.now(timezone.utc)

def feed_time_to_utc(entry) -> datetime:
    for k in ("published_parsed","updated_parsed"):
        dt = getattr(entry, k, None)
        if dt: return datetime(*dt[:6], tzinfo=timezone.utc)
    return now_utc()

8.5 RSS 生产者（src/producer/rss_producer.py）

import json, time, feedparser, logging
from kafka import KafkaProducer
from src.config import FEEDS, POLL_INTERVAL_SECONDS, KAFKA_BOOTSTRAP, RAW_TOPIC
from src.utils.timeutil import feed_time_to_utc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
)

def run():
    if not FEEDS:
        logging.error("No FEEDS configured.")
        return
    logging.info(f"Starting RSS producer with {len(FEEDS)} feeds")

    while True:
        for url in FEEDS:
            try:
                feed = feedparser.parse(url)
                for e in feed.entries:
                    msg = {
                        "source": url,
                        "title": e.get("title"),
                        "link": e.get("link"),
                        "summary": e.get("summary"),
                        "published_at": feed_time_to_utc(e).isoformat(),
                        "source_tz": "UTC",  # RSS 常见为 UTC；若有原始时区字段可补
                    }
                    producer.send(RAW_TOPIC, value=msg)
                producer.flush()
                logging.info(f"Pushed {len(feed.entries)} entries from {url}")
            except Exception as ex:
                logging.exception(f"Feed error: {url}: {ex}")
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()

8.6 解析消费者（src/consumer/parser_consumer.py）

import json, logging
from kafka import KafkaConsumer, KafkaProducer
from trafilatura import extract
from src.config import KAFKA_BOOTSTRAP, RAW_TOPIC, PARSED_TOPIC
from src.utils.url_norm import normalize
from src.utils.hashing import md5_fingerprint

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

consumer = KafkaConsumer(
    RAW_TOPIC,
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
)

def run():
    for msg in consumer:
        d = msg.value
        # 这里仅处理 RSS 元数据；如需抓正文，请在**允许**的源上用 requests 获取 HTML 再 extract
        text = d.get("summary") or ""
        # 占位：extract(html) 可接对象存储/requests拉取的HTML
        url_norm = normalize(d.get("link"))
        hash_content = md5_fingerprint(text) if text else ""
        payload = {
            "source": d.get("source"),
            "source_type": "publisher",
            "url": d.get("link"),
            "url_norm": url_norm,
            "title": d.get("title"),
            "summary": d.get("summary"),
            "published_at": d.get("published_at"),
            "source_tz": d.get("source_tz"),
            "language": None,   # 留给 NLP 步骤
            "sentiment": None,  # 留给 NLP 步骤
            "entities": None,   # 留给 NLP 步骤
            "text": text or None,
            "hash_title": md5_fingerprint(d.get("title") or ""),
            "hash_content": hash_content,
        }
        producer.send(PARSED_TOPIC, value=payload)

if __name__ == "__main__":
    run()

8.7 DB 插入消费者（src/db/pg.py & src/consumer/db_consumer.py）

src/db/pg.py

import psycopg2, psycopg2.extras
from src.config import POSTGRES

def get_conn():
    return psycopg2.connect(
        host=POSTGRES["host"], port=POSTGRES["port"],
        dbname=POSTGRES["db"], user=POSTGRES["user"], password=POSTGRES["password"]
    )

def upsert_article(cur, a: dict):
    cur.execute("""
        INSERT INTO articles (source, source_type, url, url_norm, title, summary,
          published_at, source_tz, language, sentiment, entities, text,
          hash_title, hash_content)
        VALUES (%(source)s, %(source_type)s, %(url)s, %(url_norm)s, %(title)s, %(summary)s,
          %(published_at)s, %(source_tz)s, %(language)s, %(sentiment)s, %(entities)s, %(text)s,
          %(hash_title)s, %(hash_content)s)
        ON CONFLICT (url) DO UPDATE SET
          title=EXCLUDED.title,
          summary=EXCLUDED.summary,
          published_at=EXCLUDED.published_at,
          text=EXCLUDED.text,
          hash_content=EXCLUDED.hash_content;
    """, a)

src/consumer/db_consumer.py

import json, logging
from kafka import KafkaConsumer
from src.config import KAFKA_BOOTSTRAP, PARSED_TOPIC
from src.db.pg import get_conn, upsert_article

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

consumer = KafkaConsumer(
    PARSED_TOPIC,
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

def run():
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    batch = 0
    try:
        for msg in consumer:
            a = msg.value
            try:
                upsert_article(cur, a)
                batch += 1
                if batch >= 100:
                    conn.commit()
                    batch = 0
            except Exception as ex:
                conn.rollback()
                logging.exception(f"DB error: {ex}")
    finally:
        conn.commit()
        cur.close()
        conn.close()

if __name__ == "__main__":
    run()

8.8 查询 API（src/api/main.py）

from fastapi import FastAPI, Query
import psycopg2, psycopg2.extras
from src.config import POSTGRES

app = FastAPI(title="Finance News API")

def query_db(sql, params):
    conn = psycopg2.connect(
        host=POSTGRES["host"], port=POSTGRES["port"],
        dbname=POSTGRES["db"], user=POSTGRES["user"], password=POSTGRES["password"]
    )
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

@app.get("/news")
def list_news(q: str | None = None, limit: int = 50):
    if q:
        sql = """
          SELECT id, source, url, title, summary, published_at
          FROM articles
          WHERE (title ILIKE %s OR summary ILIKE %s)
          ORDER BY published_at DESC
          LIMIT %s
        """
        return query_db(sql, (f"%{q}%", f"%{q}%", limit))
    else:
        sql = """
          SELECT id, source, url, title, summary, published_at
          FROM articles
          ORDER BY published_at DESC
          LIMIT %s
        """
        return query_db(sql, (limit,))


⸻

9. 运行步骤（VS Code）
	1.	起基础服务

docker-compose up -d


	2.	初始化数据库

psql -h localhost -U finance -d finance -f src/db/schema.sql
# 密码 finance


	3.	创建并激活虚拟环境，安装依赖

python -m venv venv
source venv/bin/activate         # Windows 用 venv\Scripts\activate
pip install -r requirements.txt


	4.	配置 .env
	•	复制 .env.example 为 .env，按需修改（尤其是 FEEDS、KAFKA_BOOTSTRAP）。
	5.	启动 3 个进程（建议 3 个终端）

# 1) RSS Producer
python -m src.producer.rss_producer

# 2) Parser Consumer
python -m src.consumer.parser_consumer

# 3) DB Consumer
python -m src.consumer.db_consumer


	6.	启动 API

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

	•	打开 http://localhost:8000/news?q=HKEX 验证返回数据。

VS Code 调试：创建 .vscode/launch.json，为以上四个入口分别配置 Python Launch（module 分别为 src.producer.rss_producer / src.consumer.parser_consumer / src.consumer.db_consumer / src.api.main）。

⸻

10. 验证与排错
	•	Kafka 连接失败：检查 KAFKA_BOOTSTRAP 与容器端口映射；确认容器健康。
	•	Postgres 连接失败：检查端口 5432 与账户密码；先执行 schema.sql。
	•	API 无数据：先看 DB 是否有入库；select count(*) from articles;
	•	重复率高：启用 url_norm 与 hash_content，并在 DB ON CONFLICT(url) 去重。

⸻

11. 扩展建议（下一步）
	•	NLP 打标：在 src/nlp/ 实现语言检测（cld3）、情绪（FinBERT）、实体（公司名→Ticker 映射），写入 articles 表对应字段。
	•	对象存储：将 HTML 快照（若许可）写入 MinIO/S3，表中保留 raw_ref。
	•	全文检索：接入 OpenSearch/ES；按 title/summary/text 建索引；API 增加高亮与聚合。
	•	调度：引入 Airflow 统一编排；不同源建不同 DAG；监控延迟与失败率。
	•	监控与告警：Prometheus/Grafana 指标（生产速率、消费滞后、入库失败、重复率、空文率）。
	•	RAG/LLM 接口：提供 /news/rag，按 tickers/topics/time_window 返回 Top-k 文本块与元数据，供 LLM 消费。

⸻

12. 安全与合规提示
	•	不要抓取/存储禁止再分发的付费内容全文。
	•	面向交易使用的低延迟数据，建议签约付费源（Refinitiv/B-PIPE/Newswires等），并与法务确认许可范围。
	•	所有服务默认只在内网使用；如需对外，要增加鉴权、限流与审计日志。

⸻

13. 可选：Makefile（快捷命令）

.PHONY: up down deps api prod parse db migrate

up:
\tdocker-compose up -d

down:
\tdocker-compose down

deps:
\tpython -m venv venv && . venv/bin/activate && pip install -r requirements.txt

api:
\tuvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

prod:
\tpython -m src.producer.rss_producer

parse:
\tpython -m src.consumer.parser_consumer

db:
\tpython -m src.consumer.db_consumer

migrate:
\tpsql -h localhost -U finance -d finance -f src/db/schema.sql