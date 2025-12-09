import time
from collections import OrderedDict
from app.core.config import settings

MAX_ITEMS = settings.max_cached_items
MAX_CHARS_PER_CV = settings.max_cv_chars

_cache = OrderedDict()   # cv_id -> {text, size, ts}

def get(cv_id):
    return _cache.get(cv_id)

def set(cv_id, text):
    text = text[:MAX_CHARS_PER_CV]
    entry = {"text": text, "size": len(text), "ts": time.time()}
    if cv_id in _cache:
        _cache.move_to_end(cv_id)
    _cache[cv_id] = entry
    while len(_cache) > MAX_ITEMS:
        _cache.popitem(last=False)
    return entry

def has(cv_id):
    return cv_id in _cache
