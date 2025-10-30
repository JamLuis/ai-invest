import psycopg2
import psycopg2.extras

from src.config import POSTGRES

def get_conn():
    return psycopg2.connect(
        host=POSTGRES["host"],
        port=POSTGRES["port"],
        dbname=POSTGRES["db"],
        user=POSTGRES["user"],
        password=POSTGRES["password"],
    )

def upsert_article(cur, article: dict) -> None:
    cur.execute(
        """
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
        """,
        article,
    )
