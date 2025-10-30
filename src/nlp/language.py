from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0

def detect_language(text: str | None) -> str | None:
    if not text:
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None
