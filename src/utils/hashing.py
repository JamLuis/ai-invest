import hashlib
import re

_ws = re.compile(r"\s+")

def md5_fingerprint(text: str) -> str:
    if not text:
        return ""
    norm = _ws.sub(" ", text).strip().lower()
    return hashlib.md5(norm.encode("utf-8")).hexdigest()
