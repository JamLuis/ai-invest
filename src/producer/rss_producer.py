import json
import logging
import time

import feedparser
from kafka import KafkaProducer

from src.config import FEEDS, POLL_INTERVAL_SECONDS, KAFKA_BOOTSTRAP, RAW_TOPIC
from src.utils.timeutil import feed_time_to_utc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
)

def run() -> None:
    if not FEEDS:
        logging.error("No FEEDS configured.")
        return
    logging.info("Starting RSS producer with %s feeds", len(FEEDS))

    while True:
        for url in FEEDS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    msg = {
                        "source": url,
                        "title": entry.get("title"),
                        "link": entry.get("link"),
                        "summary": entry.get("summary"),
                        "published_at": feed_time_to_utc(entry).isoformat(),
                        "source_tz": "UTC",  # RSS 常见为 UTC；若有原始时区字段可补
                    }
                    producer.send(RAW_TOPIC, value=msg)
                producer.flush()
                logging.info("Pushed %s entries from %s", len(feed.entries), url)
            except Exception as exc:  # pragma: no cover - defensive logging
                logging.exception("Feed error: %s: %s", url, exc)
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":  # pragma: no cover - script entrypoint
    run()
