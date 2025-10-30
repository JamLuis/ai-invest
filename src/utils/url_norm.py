from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

def normalize(u: str) -> str:
    if not u:
        return u
    parts = urlsplit(u)
    # remove common tracking parameters
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith(("utm_", "fbclid", "gclid"))
    ]
    query.sort()
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path,
            urlencode(query),
            "",
        )
    )
