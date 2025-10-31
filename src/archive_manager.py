"""
AI-Invest V2 - 归档和清理系统
实现90天自动归档机制，超期数据转存为文件，提供清理脚本
"""

import os
import json
import gzip
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

from src.config_v2 import ConfigV2

logging.basicConfig(level=logging.INFO, format=ConfigV2.LOGGING['format'])
logger = logging.getLogger(__name__)

class ArchiveManager:
    """文章归档管理器"""
    
    def __init__(self):
        self.config = ConfigV2()
        self.archive_path = ConfigV2.STORAGE['archive_base_path']
        self.archive_format = ConfigV2.STORAGE['archive_format']
        self.batch_size = ConfigV2.STORAGE['archive_batch_size']
        
        # 确保归档目录存在
        os.makedirs(self.archive_path, exist_ok=True)
        
        # 数据库连接
        self.db_conn = psycopg2.connect(
            host=ConfigV2.DATABASE['host'],
            port=ConfigV2.DATABASE['port'],
            dbname=ConfigV2.DATABASE['database'],
            user=ConfigV2.DATABASE['user'],
            password=ConfigV2.DATABASE['password']
        )
    
    def find_articles_to_archive(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """查找需要归档的文章"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, url, title, content, summary, authors, published_at, 
                       category, tags, importance_score, urgency_level,
                       fetched_at, created_at
                FROM articles_v2 
                WHERE published_at < %s 
                  AND is_archived = false
                ORDER BY published_at ASC
                LIMIT %s
            """, (cutoff_date, self.batch_size))
            
            return cursor.fetchall()
    
    def create_archive_file(self, articles: List[Dict[str, Any]], file_prefix: str) -> str:
        """创建归档文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.archive_format == 'jsonl.gz':
            filename = f"{file_prefix}_{timestamp}.jsonl.gz"
            filepath = os.path.join(self.archive_path, filename)
            
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                for article in articles:
                    # 转换datetime对象为字符串
                    article_dict = dict(article)
                    for key, value in article_dict.items():
                        if isinstance(value, datetime):
                            article_dict[key] = value.isoformat()
                    
                    f.write(json.dumps(article_dict, ensure_ascii=False) + '\n')
        
        elif self.archive_format == 'json':
            filename = f"{file_prefix}_{timestamp}.json"
            filepath = os.path.join(self.archive_path, filename)
            
            # 转换datetime对象
            articles_data = []
            for article in articles:
                article_dict = dict(article)
                for key, value in article_dict.items():
                    if isinstance(value, datetime):
                        article_dict[key] = value.isoformat()
                articles_data.append(article_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles_data, f, ensure_ascii=False, indent=2)
        
        elif self.archive_format == 'csv':
            filename = f"{file_prefix}_{timestamp}.csv"
            filepath = os.path.join(self.archive_path, filename)
            
            # 使用pandas导出CSV
            df = pd.DataFrame(articles)
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        else:
            raise ValueError(f"不支持的归档格式: {self.archive_format}")
        
        return filepath
    
    def mark_articles_archived(self, article_ids: List[int], file_path: str):
        """标记文章为已归档"""
        with self.db_conn.cursor() as cursor:
            # 更新文章状态
            cursor.execute("""
                UPDATE articles_v2 
                SET is_archived = true, 
                    archive_path = %s,
                    archived_at = %s
                WHERE id = ANY(%s)
            """, (file_path, datetime.now(), article_ids))
            
            # 记录归档信息
            file_size = os.path.getsize(file_path)
            cursor.execute("""
                INSERT INTO archive_records (
                    article_id, file_path, file_size, 
                    archive_reason, compression_method
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                article_ids[0],  # 代表性文章ID
                file_path,
                file_size,
                'age_limit',
                'gzip' if 'gz' in self.archive_format else 'none'
            ))
            
            self.db_conn.commit()
    
    def archive_old_articles(self, days_old: int = None) -> Dict[str, Any]:
        """归档旧文章"""
        if days_old is None:
            days_old = ConfigV2.STORAGE['archive_after_days']
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        logger.info(f"开始归档 {cutoff_date} 之前的文章")
        
        total_archived = 0
        files_created = []
        
        while True:
            # 分批处理文章
            articles = self.find_articles_to_archive(cutoff_date)
            
            if not articles:
                break
            
            # 按类别分组归档
            articles_by_category = {}
            for article in articles:
                category = article['category'] or 'general'
                if category not in articles_by_category:
                    articles_by_category[category] = []
                articles_by_category[category].append(article)
            
            # 为每个类别创建归档文件
            for category, category_articles in articles_by_category.items():
                file_prefix = f"articles_{category}"
                filepath = self.create_archive_file(category_articles, file_prefix)
                
                # 标记为已归档
                article_ids = [article['id'] for article in category_articles]
                self.mark_articles_archived(article_ids, filepath)
                
                files_created.append(filepath)
                total_archived += len(category_articles)
                
                logger.info(f"归档了 {len(category_articles)} 篇 {category} 类文章到 {filepath}")
        
        result = {
            'total_archived': total_archived,
            'files_created': files_created,
            'cutoff_date': cutoff_date.isoformat()
        }
        
        logger.info(f"归档完成：总共归档 {total_archived} 篇文章，创建 {len(files_created)} 个文件")
        return result
    
    def cleanup_old_archives(self, days_old: int = None) -> Dict[str, Any]:
        """清理旧的归档文件"""
        if days_old is None:
            days_old = ConfigV2.STORAGE['cleanup_after_days']
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        logger.info(f"开始清理 {cutoff_date} 之前的归档文件")
        
        deleted_files = []
        total_size_freed = 0
        
        # 查找旧的归档记录
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, file_path, file_size 
                FROM archive_records 
                WHERE archived_at < %s
            """, (cutoff_date,))
            
            old_archives = cursor.fetchall()
        
        for archive in old_archives:
            file_path = archive['file_path']
            
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    total_size_freed += file_size
                    
                    logger.info(f"删除归档文件: {file_path}")
                    
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path}: {e}")
            
            # 删除归档记录
            with self.db_conn.cursor() as cursor:
                cursor.execute("DELETE FROM archive_records WHERE id = %s", (archive['id'],))
        
        self.db_conn.commit()
        
        result = {
            'deleted_files': len(deleted_files),
            'size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
            'cutoff_date': cutoff_date.isoformat()
        }
        
        logger.info(f"清理完成：删除 {len(deleted_files)} 个文件，释放 {result['size_freed_mb']} MB空间")
        return result
    
    def get_archive_stats(self) -> Dict[str, Any]:
        """获取归档统计信息"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 数据库中的文章统计
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(*) FILTER (WHERE is_archived = true) as archived_articles,
                    COUNT(*) FILTER (WHERE is_archived = false) as active_articles
                FROM articles_v2
            """)
            db_stats = cursor.fetchone()
            
            # 归档文件统计
            cursor.execute("""
                SELECT 
                    COUNT(*) as archive_files,
                    SUM(file_size) as total_size,
                    MIN(archived_at) as oldest_archive,
                    MAX(archived_at) as newest_archive
                FROM archive_records
            """)
            archive_stats = cursor.fetchone()
        
        return {
            'database': dict(db_stats),
            'archives': dict(archive_stats),
            'archive_path': self.archive_path,
            'archive_format': self.archive_format
        }
    
    def close(self):
        """关闭数据库连接"""
        self.db_conn.close()


class CleanupManager:
    """清理管理器"""
    
    def __init__(self):
        self.archive_manager = ArchiveManager()
    
    def full_cleanup(self) -> Dict[str, Any]:
        """执行完整清理流程"""
        logger.info("开始执行完整清理流程")
        
        results = {}
        
        # 1. 归档旧文章
        results['archive'] = self.archive_manager.archive_old_articles()
        
        # 2. 清理旧归档文件
        results['cleanup'] = self.archive_manager.cleanup_old_archives()
        
        # 3. 获取最终统计
        results['stats'] = self.archive_manager.get_archive_stats()
        
        logger.info("完整清理流程执行完成")
        return results
    
    def close(self):
        """关闭资源"""
        self.archive_manager.close()


def main():
    """主函数 - 可用作独立清理脚本"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Invest V2 归档清理工具')
    parser.add_argument('--action', choices=['archive', 'cleanup', 'full', 'stats'], 
                       default='stats', help='执行的操作')
    parser.add_argument('--days', type=int, help='天数阈值')
    
    args = parser.parse_args()
    
    if args.action == 'archive':
        manager = ArchiveManager()
        result = manager.archive_old_articles(args.days)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        manager.close()
        
    elif args.action == 'cleanup':
        manager = ArchiveManager()
        result = manager.cleanup_old_archives(args.days)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        manager.close()
        
    elif args.action == 'full':
        cleanup = CleanupManager()
        result = cleanup.full_cleanup()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        cleanup.close()
        
    elif args.action == 'stats':
        manager = ArchiveManager()
        result = manager.get_archive_stats()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        manager.close()

if __name__ == "__main__":
    main()