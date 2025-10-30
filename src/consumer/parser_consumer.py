import json
import logging

from kafka import KafkaConsumer, KafkaProducer
from trafilatura import extract  # noqa: F401  # reserved for future html extraction

from src.config import KAFKA_BOOTSTRAP, RAW_TOPIC, PARSED_TOPIC
from src.utils.hashing import md5_fingerprint
from src.utils.url_norm import normalize

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

consumer = KafkaConsumer(
    RAW_TOPIC,
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_deserializer=lambda payload: json.loads(payload.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
)

def run() -> None:
    for message in consumer:
        data = message.value
        # 这里仅处理 RSS 元数据；如需抓正文，请在允许的源上获取 HTML 再 extract
        text = data.get("summary") or ""
        url_norm = normalize(data.get("link"))
        hash_content = md5_fingerprint(text) if text else ""
        payload = {
            "source": data.get("source"),
            "source_type": "publisher",
            "url": data.get("link"),
            "url_norm": url_norm,
            "title": data.get("title"),
            "summary": data.get("summary"),
            "published_at": data.get("published_at"),
            "source_tz": data.get("source_tz"),
            "language": None,   # 留给 NLP 步骤
            "sentiment": None,  # 留给 NLP 步骤
            "entities": None,   # 留给 NLP 步骤
            "text": text or None,
            "hash_title": md5_fingerprint(data.get("title") or ""),
            "hash_content": hash_content,
        }
        producer.send(PARSED_TOPIC, value=payload)

if __name__ == "__main__":  # pragma: no cover
    run()
