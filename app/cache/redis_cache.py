from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

import redis

log = logging.getLogger("cache")


@dataclass
class RedisCache:
    url: str
    ttl_sec: int = 172800

    def __post_init__(self) -> None:
        self._client: Optional[redis.Redis] = None
        if self.url:
            log.info("Redis cache configured url=%s ttl_sec=%s", self.url, self.ttl_sec)
        else:
            log.info("Redis cache disabled (no url)")

    def is_configured(self) -> bool:
        return bool(self.url)

    def client(self) -> redis.Redis:
        if self._client is None:
            # Keep timeouts short so Redis issues never slow down the API.
            log.info("Redis connecting url=%s", self.url)
            self._client = redis.Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=2,
            )
            # Optional ping to confirm connectivity (fast fail)
            try:
                self._client.ping()
                log.info("Redis connected OK")
            except Exception as e:
                # Don't raise; API should continue without cache
                log.warning("Redis ping failed err=%s", str(e))
        return self._client

    def get_json(self, key: str) -> Optional[dict[str, Any]]:
        if not self.is_configured():
            return None

        try:
            raw = self.client().get(key)
            if not raw:
                log.info("Redis cache MISS key=%s", key)
                return None

            log.info("Redis cache HIT key=%s bytes=%s", key, len(raw))
            return json.loads(raw)

        except json.JSONDecodeError as e:
            # Cache entry is corrupted/unexpected; treat as miss
            log.warning("Redis cache JSON decode failed key=%s err=%s", key, str(e))
            return None

        except Exception as e:
            log.warning("Redis get failed key=%s err=%s", key, str(e))
            return None

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        if not self.is_configured():
            return

        try:
            payload = json.dumps(value, ensure_ascii=False)
            self.client().setex(key, self.ttl_sec, payload)
            log.info("Redis cache SET key=%s ttl_sec=%s bytes=%s", key, self.ttl_sec, len(payload))

        except Exception as e:
            log.warning("Redis set failed key=%s err=%s", key, str(e))
