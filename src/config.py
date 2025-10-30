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
