import json
import logging
import time
import threading
from typing import List, Dict, Any
from datetime import datetime, timedelta

import feedparser
from kafka import KafkaProducer

from src.config import KAFKA_BOOTSTRAP, RAW_TOPIC
from src.utils.timeutil import feed_time_to_utc
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class EnhancedRSSProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP],
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        )
        
        # 从环境变量加载多优先级配置
        self.feed_configs = self._load_feed_configs()
        self.threads = []
        self.running = True
        
    def _load_feed_configs(self) -> List[Dict[str, Any]]:
        """从环境变量加载RSS源配置"""
        configs = []
        
        # 高优先级源
        high_feeds = os.getenv("FEEDS_HIGH_PRIORITY", "").split(",")
        high_interval = int(os.getenv("POLL_INTERVAL_HIGH", "60"))
        for feed_url in high_feeds:
            if feed_url.strip():
                configs.append({
                    "urls": [feed_url.strip()],
                    "interval": high_interval,
                    "priority": "high",
                    "weight": 10
                })
        
        # 中优先级源
        medium_feeds = os.getenv("FEEDS_MEDIUM_PRIORITY", "").split(",")
        medium_interval = int(os.getenv("POLL_INTERVAL_MEDIUM", "300"))
        for feed_url in medium_feeds:
            if feed_url.strip():
                configs.append({
                    "urls": [feed_url.strip()],
                    "interval": medium_interval,
                    "priority": "medium",
                    "weight": 8
                })
        
        # 低优先级源
        low_feeds = os.getenv("FEEDS_LOW_PRIORITY", "").split(",")
        low_interval = int(os.getenv("POLL_INTERVAL_LOW", "900"))
        for feed_url in low_feeds:
            if feed_url.strip():
                configs.append({
                    "urls": [feed_url.strip()],
                    "interval": low_interval,
                    "priority": "low",
                    "weight": 6
                })
        
        # 研究源
        research_feeds = os.getenv("FEEDS_RESEARCH", "").split(",")
        research_interval = int(os.getenv("POLL_INTERVAL_RESEARCH", "1800"))
        for feed_url in research_feeds:
            if feed_url.strip():
                configs.append({
                    "urls": [feed_url.strip()],
                    "interval": research_interval,
                    "priority": "research",
                    "weight": 4
                })
        
        # 国际源
        international_feeds = os.getenv("FEEDS_INTERNATIONAL", "").split(",")
        international_interval = int(os.getenv("POLL_INTERVAL_INTERNATIONAL", "3600"))
        for feed_url in international_feeds:
            if feed_url.strip():
                configs.append({
                    "urls": [feed_url.strip()],
                    "interval": international_interval,
                    "priority": "international",
                    "weight": 3
                })
        
        # 如果没有配置新的优先级源，使用原有配置
        if not configs:
            legacy_feeds = os.getenv("FEEDS", "").split(",")
            legacy_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
            for feed_url in legacy_feeds:
                if feed_url.strip():
                    configs.append({
                        "urls": [feed_url.strip()],
                        "interval": legacy_interval,
                        "priority": "default",
                        "weight": 5
                    })
        
        return configs

    def _fetch_feed_worker(self, feed_config: Dict[str, Any]):
        """单个优先级组的RSS抓取工作线程"""
        urls = feed_config["urls"]
        interval = feed_config["interval"]
        priority = feed_config["priority"]
        weight = feed_config["weight"]
        
        logging.info(f"启动 {priority} 优先级RSS抓取线程，间隔 {interval}s，包含 {len(urls)} 个源")
        
        last_fetch_times = {url: datetime.min for url in urls}
        
        while self.running:
            for url in urls:
                try:
                    current_time = datetime.now()
                    
                    # 检查是否到了抓取时间
                    if current_time - last_fetch_times[url] < timedelta(seconds=interval):
                        continue
                    
                    logging.info(f"[{priority}] 开始抓取: {url}")
                    feed = feedparser.parse(url)
                    
                    if feed.bozo:
                        logging.warning(f"[{priority}] RSS解析警告 {url}: {feed.bozo_exception}")
                    
                    entry_count = 0
                    for entry in feed.entries:
                        # 增强消息结构，包含优先级和权重信息
                        msg = {
                            "source": url,
                            "title": entry.get("title"),
                            "link": entry.get("link"),
                            "summary": entry.get("summary"),
                            "published_at": feed_time_to_utc(entry).isoformat(),
                            "source_tz": "UTC",
                            # 新增字段
                            "priority": priority,
                            "weight": weight,
                            "category": self._detect_category(url),
                            "fetch_time": current_time.isoformat(),
                            "entry_id": entry.get("id", ""),
                            "author": entry.get("author", ""),
                            "tags": [tag.get("term", "") for tag in entry.get("tags", [])]
                        }
                        self.producer.send(RAW_TOPIC, value=msg)
                        entry_count += 1
                    
                    self.producer.flush()
                    last_fetch_times[url] = current_time
                    
                    logging.info(f"[{priority}] ✅ {url}: 推送 {entry_count} 条新闻")
                    
                except Exception as exc:
                    logging.exception(f"[{priority}] ❌ RSS抓取失败 {url}: {exc}")
            
            # 短暂休眠，避免CPU占用过高
            time.sleep(min(30, interval // 10))

    def _detect_category(self, url: str) -> str:
        """根据URL检测新闻源类别"""
        url_lower = url.lower()
        
        # 央行类
        if any(keyword in url_lower for keyword in ["fed", "federalreserve", "ecb", "boj", "pbc"]):
            return "central_bank"
        
        # 监管机构类
        elif any(keyword in url_lower for keyword in ["sec", "regulation", "cftc"]):
            return "regulation"
        
        # 交易所类
        elif any(keyword in url_lower for keyword in ["nasdaq", "nyse", "hkex"]):
            return "exchange"
        
        # 宏观经济类
        elif any(keyword in url_lower for keyword in ["bls", "bea", "census", "oecd", "imf"]):
            return "macro"
        
        # 研究机构类
        elif any(keyword in url_lower for keyword in ["goldman", "morgan", "brookings"]):
            return "research"
        
        # 国际财经媒体类
        elif any(keyword in url_lower for keyword in ["investing.com", "reuters", "bloomberg"]):
            return "international_finance"
        
        # 通用新闻类
        elif any(keyword in url_lower for keyword in ["news", "finance", "markets"]):
            return "general_finance"
        
        else:
            return "general"

    def start(self):
        """启动多线程RSS抓取"""
        if not self.feed_configs:
            logging.error("没有配置RSS源，请检查环境变量")
            return
        
        logging.info(f"启动增强版RSS Producer，共 {len(self.feed_configs)} 个优先级组")
        
        # 为每个优先级配置启动独立线程
        for config in self.feed_configs:
            thread = threading.Thread(
                target=self._fetch_feed_worker,
                args=(config,),
                daemon=True,
                name=f"RSS-{config['priority']}"
            )
            thread.start()
            self.threads.append(thread)
        
        try:
            # 主线程等待
            while self.running:
                time.sleep(10)
                # 检查线程健康状态
                alive_threads = [t for t in self.threads if t.is_alive()]
                if len(alive_threads) != len(self.threads):
                    logging.warning(f"检测到线程异常，存活线程: {len(alive_threads)}/{len(self.threads)}")
        
        except KeyboardInterrupt:
            logging.info("收到停止信号，正在关闭RSS Producer...")
            self.stop()

    def stop(self):
        """停止所有抓取线程"""
        self.running = False
        self.producer.close()
        logging.info("RSS Producer已停止")

def run():
    """主函数 - 向后兼容"""
    producer = EnhancedRSSProducer()
    producer.start()

if __name__ == "__main__":
    run()