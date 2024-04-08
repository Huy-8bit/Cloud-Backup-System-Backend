import redis
import json


async def get_redis_client():
    return redis.Redis(host="localhost", port=6379, db=0)


async def listen_for_messages(client, stop_event):
    pubsub = client.pubsub()
    pubsub.subscribe("chatMessages")

    while not stop_event.is_set():
        message = pubsub.get_message()
        if message and message["type"] == "message":
            data = json.loads(message["data"].decode("utf-8"))
            print("New message received:", data)
    pubsub.unsubscribe("chatMessages")


async def get_data(client, key):
    data = client.get(key)
    if data:
        return json.loads(data)
    return None


async def send_new_notification(client, title, description):
    json_description = json.dumps(description)
    client.publish(title, json_description)
