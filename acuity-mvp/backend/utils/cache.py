from __future__ import annotations

import time
from typing import Generic, TypeVar


T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None

        expires_at, value = entry
        if expires_at < time.time():
            self._store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: T) -> T:
        self._store[key] = (time.time() + self.ttl_seconds, value)
        return value
