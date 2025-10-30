from datetime import datetime, timezone

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def feed_time_to_utc(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        dt = getattr(entry, key, None)
        if dt:
            return datetime(*dt[:6], tzinfo=timezone.utc)
    return now_utc()
