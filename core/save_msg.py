
import redis.asyncio as redis
import time


class MessageStore:
    def __init__(self, host="localhost", port=6379, ttl=86400):
        self.redis = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.ttl = ttl

    async def save(self, message_id, group_guid, user_guid):
        key = f"msg:{message_id}"
        await self.redis.hset(key, mapping={
            "group_guid": group_guid,
            "user_guid": user_guid,
            "created_at": int(time.time())
        })
        await self.redis.expire(key, self.ttl)

    async def get(self, message_id):
        key = f"msg:{message_id}"
        data = await self.redis.hgetall(key)
        if not data:
            return None
        return {
            "message_id": message_id,
            "group_guid": data["group_guid"],
            "user_guid": data["user_guid"]
        }

    async def delete(self, message_id):
        await self.redis.delete(f"msg:{message_id}")

    async def get_last_messages(self, group_guid, count):
        keys = await self.redis.keys("msg:*")

        ids = []

        pipe = self.redis.pipeline()
        for k in keys:
            pipe.hget(k, "group_guid")

        groups = await pipe.execute()

        for key, g in zip(keys, groups):
            if g == group_guid:
                ids.append(int(key[4:]))

        ids.sort(reverse=True)

        return [str(i) for i in ids[:count]]