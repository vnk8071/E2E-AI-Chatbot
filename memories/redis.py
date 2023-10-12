import json
from typing import List, Optional

from loggers import AppLogger
from memories.base import MemoryBase

logger = AppLogger().get_logger()


class RedisMemory(MemoryBase):
    """Redis-based memory."""

    def __init__(
        self,
        session_id: str,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "message_store:",
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Could not import redis python package. "
                "Please install it with `pip install redis`."
            )

        try:
            self.redis_client = redis.from_url(url=url)
            self.session_id = session_id
            self.key_prefix = key_prefix
        except redis.exceptions.ConnectionError as error:
            logger.error(error)

    @property
    def key(self) -> str:
        """Construct the record key to use"""
        return self.key_prefix + self.session_id

    def get_answer(self, question) -> Optional[str]:
        """Retrieve the messages from Redis"""
        _items = self.redis_client.lrange(self.key, 0, -1)
        items = [json.loads(m.decode("utf-8")) for m in _items[::-1]]
        for item in items:
            if item[0].lower() == question.lower():
                return item[1]

    def add_chat_history(self, question, answer) -> None:
        """Append the pair of (question, answer) to the record in Redis"""
        self.redis_client.lpush(self.key, json.dumps((question, answer)))

    def remove_chat_history(self) -> None:
        """Remove the pair of (question, answer) from the record in Redis"""
        self.redis_client.rpop(self.key)

    def clear(self) -> None:
        """Clear session memory from Redis"""
        self.redis_client.delete(self.key)

    def check_length(self) -> int:
        """Check the length of the session memory"""
        return self.redis_client.llen(self.key)
