"""
AI-Invest V2 - 智能任务调度器
基于schedule库实现多优先级新闻源定时抓取
"""

import schedule
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from newspaper import build
import psycopg2
from psycopg2.extras import RealDictCursor

from src.config_v2 import ConfigV2
from src.newspaper_crawler import NewsCrawler

logging.basicConfig(level=logging.INFO, format=ConfigV2.LOGGING['format'])
logger = logging.getLogger(__name__)

class NewsScheduler:
    """智能新闻调度器"""
    
    def __init__(self):
        self.config = ConfigV2()
        self.crawler = NewsCrawler()
        self.running = True
        
        # 数据库连接
        self.db_conn = psycopg2.connect(
            host=ConfigV2.DATABASE['host'],
            port=ConfigV2.DATABASE['port'],
            dbname=ConfigV2.DATABASE['database'],
            user=ConfigV2.DATABASE['user'],
            password=ConfigV2.DATABASE['password']
        )
        
    def get_news_sources_from_db(self) -> List[Dict[str, Any]]:
        """从数据库获取新闻源配置"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, name, base_url, category, credibility_score, 
                       update_frequency, is_active
                FROM news_sources 
                WHERE is_active = true
                ORDER BY credibility_score DESC
            """)
            return cursor.fetchall()
    
    def discover_articles_from_source(self, source_url: str) -> List[str]:
        """从新闻源发现文章URL"""
        try:
            logger.info(f"发现文章: {source_url}")
            
            # 使用newspaper构建新闻源
            paper = build(source_url, language='en')
            article_urls = []
            
            # 获取文章URL
            for article in paper.articles[:20]:  # 限制每次最多20篇
                article_urls.append(article.url)
            
            logger.info(f"从 {source_url} 发现 {len(article_urls)} 篇文章")
            return article_urls
            
        except Exception as e:
            logger.error(f"发现文章失败 {source_url}: {e}")
            return []
    
    def crawl_high_priority_sources(self):
        """抓取高优先级新闻源"""
        logger.info("开始抓取高优先级新闻源")
        
        sources = self.get_news_sources_from_db()
        high_priority_sources = [
            s for s in sources 
            if s['credibility_score'] >= 90 or s['category'] in ['regulation', 'central_bank']
        ]
        
        for source in high_priority_sources:
            self._crawl_source_articles(source)
    
    def crawl_medium_priority_sources(self):
        """抓取中优先级新闻源"""
        logger.info("开始抓取中优先级新闻源")
        
        sources = self.get_news_sources_from_db()
        medium_priority_sources = [
            s for s in sources 
            if 70 <= s['credibility_score'] < 90 and s['category'] in ['financial', 'markets']
        ]
        
        for source in medium_priority_sources:
            self._crawl_source_articles(source)
    
    def crawl_low_priority_sources(self):
        """抓取低优先级新闻源"""
        logger.info("开始抓取低优先级新闻源")
        
        sources = self.get_news_sources_from_db()
        low_priority_sources = [
            s for s in sources 
            if s['credibility_score'] < 70
        ]
        
        for source in low_priority_sources:
            self._crawl_source_articles(source)
    
    def _crawl_source_articles(self, source: Dict[str, Any]):
        """抓取单个新闻源的文章"""
        try:
            # 发现文章URL
            article_urls = self.discover_articles_from_source(source['base_url'])
            
            # 过滤已存在的文章
            new_urls = self._filter_existing_urls(article_urls)
            
            logger.info(f"从 {source['name']} 发现 {len(new_urls)} 篇新文章")
            
            # 抓取新文章
            for url in new_urls:
                try:
                    self.crawler.crawl(url)
                    time.sleep(ConfigV2.CRAWLING['rate_limit_delay'])  # 速率限制
                except Exception as e:
                    logger.error(f"抓取文章失败 {url}: {e}")
                    
        except Exception as e:
            logger.error(f"抓取新闻源失败 {source['name']}: {e}")
    
    def _filter_existing_urls(self, urls: List[str]) -> List[str]:
        """过滤已存在的URL"""
        if not urls:
            return []
            
        with self.db_conn.cursor() as cursor:
            # 检查哪些URL已存在
            placeholders = ','.join(['%s'] * len(urls))
            cursor.execute(
                f"SELECT url FROM articles_v2 WHERE url IN ({placeholders})",
                urls
            )
            existing_urls = {row[0] for row in cursor.fetchall()}
            
            # 返回不存在的URL
            return [url for url in urls if url not in existing_urls]
    
    def cleanup_old_articles(self):
        """清理旧文章（归档处理）"""
        logger.info("开始清理旧文章")
        
        cutoff_date = datetime.now() - timedelta(days=ConfigV2.STORAGE['archive_after_days'])
        
        with self.db_conn.cursor() as cursor:
            # 查找需要归档的文章
            cursor.execute("""
                SELECT COUNT(*) FROM articles_v2 
                WHERE published_at < %s AND is_archived = false
            """, (cutoff_date,))
            
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"发现 {count} 篇文章需要归档")
                # 这里调用归档服务
                self._archive_old_articles(cutoff_date)
    
    def _archive_old_articles(self, cutoff_date: datetime):
        """归档旧文章的实际逻辑"""
        # 这个方法将在归档模块中实现
        logger.info(f"归档 {cutoff_date} 之前的文章")
        pass
    
    def setup_schedules(self):
        """设置调度任务"""
        logger.info("设置调度任务")
        
        # 高优先级: 每30分钟
        schedule.every(30).minutes.do(self.crawl_high_priority_sources)
        
        # 中优先级: 每1小时  
        schedule.every().hour.do(self.crawl_medium_priority_sources)
        
        # 低优先级: 每2小时
        schedule.every(2).hours.do(self.crawl_low_priority_sources)
        
        # 清理任务: 每天凌晨2点
        schedule.every().day.at("02:00").do(self.cleanup_old_articles)
        
        # 立即执行一次高优先级抓取
        self.crawl_high_priority_sources()
    
    def run(self):
        """运行调度器"""
        logger.info("启动智能新闻调度器")
        self.setup_schedules()
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止调度器"""
        logger.info("停止智能新闻调度器")
        self.running = False
        self.crawler.close()
        self.db_conn.close()

def main():
    """主函数"""
    scheduler = NewsScheduler()
    scheduler.run()

if __name__ == "__main__":
    main()