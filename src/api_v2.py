"""
AI-Invest V2 - 升级版FastAPI接口
支持分类搜索、重要性过滤、标签查询等新功能
"""

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

from src.config_v2 import ConfigV2

# 创建FastAPI应用
app = FastAPI(
    title="AI-Invest V2 API",
    description="增强版财经新闻分析API，支持智能分类、重要性评分和标签查询",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ConfigV2.API['cors_origins'] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: Optional[str]
    content: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    tags: List[str]
    importance_score: int
    urgency_level: str
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    authors: List[str]
    published_at: datetime
    fetched_at: datetime
    source_name: Optional[str]
    credibility_score: Optional[int]
    
class SearchFilters(BaseModel):
    categories: Optional[List[str]] = None
    min_importance: Optional[int] = None
    max_importance: Optional[int] = None
    urgency_levels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sentiment: Optional[str] = None

class StatsResponse(BaseModel):
    total_articles: int
    categories: Dict[str, int]
    urgency_levels: Dict[str, int]
    avg_importance_score: float
    articles_today: int
    articles_this_week: int

# 数据库依赖
def get_db():
    conn = psycopg2.connect(
        host=ConfigV2.DATABASE['host'],
        port=ConfigV2.DATABASE['port'],
        dbname=ConfigV2.DATABASE['database'],
        user=ConfigV2.DATABASE['user'],
        password=ConfigV2.DATABASE['password']
    )
    try:
        yield conn
    finally:
        conn.close()

@app.get("/", summary="API根端点")
async def root():
    """API根端点，返回基本信息"""
    return {
        "message": "AI-Invest V2 API",
        "version": "2.0.0",
        "features": [
            "智能内容抓取",
            "自动分类标记",
            "重要性评分",
            "情感分析",
            "标签管理",
            "归档清理"
        ]
    }

@app.get("/health", summary="健康检查")
async def health_check(db=Depends(get_db)):
    """健康检查端点"""
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")

@app.get("/articles", response_model=List[ArticleResponse], summary="获取文章列表")
async def get_articles(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(ConfigV2.API['default_page_size'], description="返回记录数"),
    category: Optional[str] = Query(None, description="文章分类"),
    min_importance: Optional[int] = Query(None, description="最低重要性评分"),
    urgency: Optional[str] = Query(None, description="紧急程度"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    q: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("published_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db=Depends(get_db)
):
    """获取文章列表，支持多种过滤和搜索条件"""
    
    # 构建查询条件
    where_conditions = ["a.is_archived = false"]
    params = []
    
    if category:
        where_conditions.append("a.category = %s")
        params.append(category)
    
    if min_importance is not None:
        where_conditions.append("a.importance_score >= %s")
        params.append(min_importance)
    
    if urgency:
        where_conditions.append("a.urgency_level = %s")
        params.append(urgency)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        where_conditions.append("a.tags && %s")
        params.append(tag_list)
    
    if q:
        where_conditions.append("""
            (a.title ILIKE %s OR a.content ILIKE %s OR a.summary ILIKE %s)
        """)
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term])
    
    # 验证排序字段
    valid_sort_fields = ['published_at', 'importance_score', 'fetched_at', 'title']
    if sort_by not in valid_sort_fields:
        sort_by = 'published_at'
    
    if sort_order.lower() not in ['asc', 'desc']:
        sort_order = 'desc'
    
    where_clause = " AND ".join(where_conditions)
    
    query = f"""
        SELECT 
            a.id, a.url, a.title, a.summary, a.content,
            a.category, a.subcategory, a.tags, a.importance_score,
            a.urgency_level, a.sentiment_score, a.sentiment_label,
            a.authors, a.published_at, a.fetched_at,
            ns.name as source_name, ns.credibility_score
        FROM articles_v2 a
        LEFT JOIN news_sources ns ON a.source_id = ns.id
        WHERE {where_clause}
        ORDER BY a.{sort_by} {sort_order.upper()}
        LIMIT %s OFFSET %s
    """
    
    params.extend([limit, skip])
    
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        articles = cursor.fetchall()
    
    return [dict(article) for article in articles]

@app.get("/articles/{article_id}", response_model=ArticleResponse, summary="获取单篇文章")
async def get_article(article_id: int, db=Depends(get_db)):
    """获取单篇文章的详细信息"""
    
    query = """
        SELECT 
            a.id, a.url, a.title, a.summary, a.content,
            a.category, a.subcategory, a.tags, a.importance_score,
            a.urgency_level, a.sentiment_score, a.sentiment_label,
            a.authors, a.published_at, a.fetched_at,
            ns.name as source_name, ns.credibility_score
        FROM articles_v2 a
        LEFT JOIN news_sources ns ON a.source_id = ns.id
        WHERE a.id = %s AND a.is_archived = false
    """
    
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (article_id,))
        article = cursor.fetchone()
    
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")
    
    return dict(article)

@app.get("/categories", summary="获取所有分类")
async def get_categories(db=Depends(get_db)):
    """获取所有文章分类及其数量"""
    
    query = """
        SELECT category, COUNT(*) as count
        FROM articles_v2 
        WHERE is_archived = false AND category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """
    
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        categories = cursor.fetchall()
    
    return [dict(cat) for cat in categories]

@app.get("/tags", summary="获取热门标签")
async def get_popular_tags(
    limit: int = Query(50, description="返回标签数量"),
    db=Depends(get_db)
):
    """获取热门标签"""
    
    query = """
        SELECT unnest(tags) as tag, COUNT(*) as count
        FROM articles_v2 
        WHERE is_archived = false AND tags IS NOT NULL
        GROUP BY tag
        ORDER BY count DESC
        LIMIT %s
    """
    
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (limit,))
        tags = cursor.fetchall()
    
    return [dict(tag) for tag in tags]

@app.get("/stats", response_model=StatsResponse, summary="获取统计信息")
async def get_stats(db=Depends(get_db)):
    """获取文章统计信息"""
    
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        # 总体统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                AVG(importance_score) as avg_importance_score
            FROM articles_v2 
            WHERE is_archived = false
        """)
        overall_stats = cursor.fetchone()
        
        # 分类统计
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM articles_v2 
            WHERE is_archived = false AND category IS NOT NULL
            GROUP BY category
        """)
        categories = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # 紧急程度统计
        cursor.execute("""
            SELECT urgency_level, COUNT(*) as count
            FROM articles_v2 
            WHERE is_archived = false
            GROUP BY urgency_level
        """)
        urgency_levels = {row['urgency_level']: row['count'] for row in cursor.fetchall()}
        
        # 今日文章
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM articles_v2 
            WHERE is_archived = false 
              AND published_at >= CURRENT_DATE
        """)
        articles_today = cursor.fetchone()['count']
        
        # 本周文章
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM articles_v2 
            WHERE is_archived = false 
              AND published_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        articles_this_week = cursor.fetchone()['count']
    
    return {
        "total_articles": overall_stats['total_articles'],
        "categories": categories,
        "urgency_levels": urgency_levels,
        "avg_importance_score": round(overall_stats['avg_importance_score'] or 0, 2),
        "articles_today": articles_today,
        "articles_this_week": articles_this_week
    }

@app.get("/search", response_model=List[ArticleResponse], summary="高级搜索")
async def advanced_search(
    q: str = Query(..., description="搜索关键词"),
    filters: SearchFilters = Depends(),
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(ConfigV2.API['default_page_size'], description="返回记录数"),
    db=Depends(get_db)
):
    """高级搜索接口，支持全文搜索和复杂过滤条件"""
    
    where_conditions = ["a.is_archived = false"]
    params = []
    
    # 全文搜索
    where_conditions.append("""
        (to_tsvector('english', a.title || ' ' || COALESCE(a.content, '') || ' ' || COALESCE(a.summary, ''))
         @@ plainto_tsquery('english', %s))
    """)
    params.append(q)
    
    # 应用过滤条件
    if filters.categories:
        where_conditions.append("a.category = ANY(%s)")
        params.append(filters.categories)
    
    if filters.min_importance is not None:
        where_conditions.append("a.importance_score >= %s")
        params.append(filters.min_importance)
    
    if filters.max_importance is not None:
        where_conditions.append("a.importance_score <= %s")
        params.append(filters.max_importance)
    
    if filters.urgency_levels:
        where_conditions.append("a.urgency_level = ANY(%s)")
        params.append(filters.urgency_levels)
    
    if filters.tags:
        where_conditions.append("a.tags && %s")
        params.append(filters.tags)
    
    if filters.date_from:
        where_conditions.append("a.published_at >= %s")
        params.append(filters.date_from)
    
    if filters.date_to:
        where_conditions.append("a.published_at <= %s")
        params.append(filters.date_to)
    
    if filters.sentiment:
        where_conditions.append("a.sentiment_label = %s")
        params.append(filters.sentiment)
    
    where_clause = " AND ".join(where_conditions)
    
    query = f"""
        SELECT 
            a.id, a.url, a.title, a.summary, a.content,
            a.category, a.subcategory, a.tags, a.importance_score,
            a.urgency_level, a.sentiment_score, a.sentiment_label,
            a.authors, a.published_at, a.fetched_at,
            ns.name as source_name, ns.credibility_score,
            ts_rank(to_tsvector('english', a.title || ' ' || COALESCE(a.content, '')), 
                   plainto_tsquery('english', %s)) as relevance
        FROM articles_v2 a
        LEFT JOIN news_sources ns ON a.source_id = ns.id
        WHERE {where_clause}
        ORDER BY relevance DESC, a.importance_score DESC, a.published_at DESC
        LIMIT %s OFFSET %s
    """
    
    # 添加相关性参数
    params.insert(-2, q)  # 在limit和offset之前插入
    params.extend([limit, skip])
    
    with db.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        articles = cursor.fetchall()
    
    return [dict(article) for article in articles]

@app.post("/crawl", summary="手动抓取文章")
async def manual_crawl(
    url: str = Query(..., description="要抓取的文章URL"),
    db=Depends(get_db)
):
    """手动抓取指定URL的文章"""
    from src.newspaper_crawler import NewsCrawler
    
    try:
        crawler = NewsCrawler()
        crawler.crawl(url)
        crawler.close()
        
        return {"message": "文章抓取成功", "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")

@app.get("/archive/stats", summary="归档统计")
async def get_archive_stats(db=Depends(get_db)):
    """获取归档统计信息"""
    from src.archive_manager import ArchiveManager
    
    try:
        manager = ArchiveManager()
        stats = manager.get_archive_stats()
        manager.close()
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=ConfigV2.API['host'], 
        port=ConfigV2.API['port'],
        log_level="info"
    )