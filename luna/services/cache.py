import ast
import os

import redis as pyredis

from luna import log


class CacheManageService:
    def __init__(self, key_dict: any):
        self.key = f"luna/caches/{key_dict}"
        self.redis = pyredis.Redis(host=os.getenv("REDIS_HOST", "127.0.0.1"),
                                   port=int(os.getenv("REDIS_PORT", "6379")),
                                   db=int(os.getenv("REDIS_DB", "1")))

    def exists(self) -> bool:
        if self.redis.exists(self.key) != 0:
            return True
        else:
            return False

    def get(self) -> dict:
        value_str = self.redis.get(self.key).decode("UTF-8")
        log.dbg(f"CACHE_LOADED: \n\033[90;1m{self.key}\n^^^^\n{value_str}\n\n\033[0m")
        return ast.literal_eval(value_str)

    def set(self, value: dict, expire_days: int):
        log.dbg(f"CACHE_SAVED: \n\033[90;1m{self.key}\n↓↓↓↓\n<{value}\n\n\033[0m")
        value_str = str(value)
        self.redis.set(self.key, value_str)
        self.redis.expire(self.key, expire_days * 24 * 60 * 60)