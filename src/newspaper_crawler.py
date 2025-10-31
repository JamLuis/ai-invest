"""
AI-Invest V2 - Newspaper网页内容抓取与分析
支持：网页内容提取、分类、标签、重要性评分、持久化存储
"""
import os
import sys
import time
import logging
from typing import List, Dict, Any
from newspaper import Article
import psycopg2
from datetime import datetime
from src.config_v2 import ConfigV2

logging.basicConfig(level=logging.INFO, format=ConfigV2.LOGGING['format'])

class NewsCrawler:
    def __init__(self):
        self.db = ConfigV2.DATABASE
        self.conn = psycopg2.connect(
            host=self.db['host'],
            port=self.db['port'],
            dbname=self.db['database'],
            user=self.db['user'],
            password=self.db['password']
        )
        self.cursor = self.conn.cursor()
        self.user_agent = ConfigV2.CRAWLING['user_agent']
        self.timeout = ConfigV2.CRAWLING['request_timeout']

    def fetch_and_parse(self, url: str) -> Dict[str, Any]:
        """抓取并解析网页内容"""
        article = Article(url, language='en')
        article.download()
        article.parse()
        article.nlp()
        return {
            'url': url,
            'title': article.title,
            'content': article.text,
            'summary': article.summary,
            'authors': article.authors,
            'published_at': article.publish_date or datetime.utcnow(),
            'top_image': article.top_image,
            'images': list(article.images),
            'keywords': article.keywords,
            'raw_html': article.html
        }

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分类、标签、重要性评分"""
        title = data['title']
        content = data['content']
        # 分类
        category = ConfigV2.detect_category(title, content) or 'general'
        # 紧急程度
        urgency = ConfigV2.detect_urgency(title, content)
        # 标签
        tags = data['keywords']
        # 重要性评分
        score = ConfigV2.get_keyword_score(title + ' ' + content)
        # VIP实体
        vip_entities = ConfigV2.is_vip_entity_mentioned(title + ' ' + content)
        if vip_entities:
            score += 20
            tags += vip_entities
        score = min(score, 100)
        return {
            'category': category,
            'urgency_level': urgency,
            'tags': tags,
            'importance_score': score
        }

    def save_to_db(self, data: Dict[str, Any], analysis: Dict[str, Any]):
        """存储到数据库"""
        sql = '''
        INSERT INTO articles_v2 (
            url, title, content, summary, authors, published_at, top_image, images, keywords,
            category, urgency_level, tags, importance_score, raw_html, fetched_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
        '''
        self.cursor.execute(sql, (
            data['url'], data['title'], data['content'], data['summary'], data['authors'],
            data['published_at'], data['top_image'], data['images'], data['keywords'],
            analysis['category'], analysis['urgency_level'], analysis['tags'], analysis['importance_score'],
            data['raw_html'], datetime.utcnow()
        ))
        self.conn.commit()

    def crawl(self, url: str):
        try:
            logging.info(f"抓取: {url}")
            data = self.fetch_and_parse(url)
            analysis = self.analyze(data)
            self.save_to_db(data, analysis)
            logging.info(f"已保存: {data['title']} [{analysis['category']}] 重要性:{analysis['importance_score']}")
        except Exception as e:
            logging.error(f"抓取失败: {url} 错误: {e}")

    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    crawler = NewsCrawler()
    # 示例：从命令行参数抓取
    if len(sys.argv) > 1:
        for url in sys.argv[1:]:
            crawler.crawl(url)
    else:
        # 默认抓取高优先级源首页
        for url in ConfigV2.NEWS_SOURCES['high_priority']['urls']:
            crawler.crawl(url)
    crawler.close()
