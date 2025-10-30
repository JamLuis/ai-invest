from fastapi import FastAPI
from typing import Optional
import psycopg2
import psycopg2.extras

from src.config import POSTGRES

app = FastAPI(title="Finance News API")

def query_db(sql: str, params: tuple):
    conn = psycopg2.connect(
        host=POSTGRES["host"],
        port=POSTGRES["port"],
        dbname=POSTGRES["db"],
        user=POSTGRES["user"],
        password=POSTGRES["password"],
    )
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

@app.get("/news")
def list_news(q: Optional[str] = None, limit: int = 50):
    if q:
        sql = """
          SELECT id, source, url, title, summary, published_at
          FROM articles
          WHERE (title ILIKE %s OR summary ILIKE %s)
          ORDER BY published_at DESC
          LIMIT %s
        """
        return query_db(sql, (f"%{q}%", f"%{q}%", limit))
    sql = """
          SELECT id, source, url, title, summary, published_at
          FROM articles
          ORDER BY published_at DESC
          LIMIT %s
        """
    return query_db(sql, (limit,))
