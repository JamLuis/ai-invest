import json
import logging

from kafka import KafkaConsumer

from src.config import KAFKA_BOOTSTRAP, PARSED_TOPIC
from src.db.pg import get_conn, upsert_article

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

consumer = KafkaConsumer(
    PARSED_TOPIC,
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_deserializer=lambda payload: json.loads(payload.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

def run() -> None:
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    batch = 0
    try:
        for message in consumer:
            article = message.value
            try:
                upsert_article(cur, article)
                batch += 1
                if batch >= 100:
                    conn.commit()
                    batch = 0
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                logging.exception("DB error: %s", exc)
    finally:
        conn.commit()
        cur.close()
        conn.close()

if __name__ == "__main__":  # pragma: no cover
    run()
