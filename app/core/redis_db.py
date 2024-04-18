import redis
import json


async def get_redis_client():
    return redis.Redis(host="54.254.58.42", port=6379, db=0)


async def get_data(client, key):
    data = client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_data(client, key, data):
    client.set(key, json.dumps(data))
