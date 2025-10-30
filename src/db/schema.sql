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
