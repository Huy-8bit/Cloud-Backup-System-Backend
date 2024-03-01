from fastapi import FastAPI, BackgroundTasks
from app.api.auth import register, login
from fastapi.middleware.cors import CORSMiddleware
import redis

import threading
from threading import Event
from app.core.database import database
import asyncio
import json
from app.core.redis_utils import get_redis_client, listen_for_messages

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = "redis://redis:6379"

try:
    redis_client = redis.Redis.from_url(REDIS_URL)
except redis.ConnectionError:
    print("Redis connection error")
    redis_client = None

print("Redis client successfully connected")


# try:
#     redis_client = redis.Redis(host="cloud-backup-system-redis-1", port=6379, db=0)
# except redis.ConnectionError:
#     redis_client = None

# listening_thread_active = True

redis_client = get_redis_client()
listening_thread_active = True

stop_listening_event = Event()


@app.on_event("startup")
async def startup_event():
    global listener_thread
    listener_thread = threading.Thread(
        target=listen_for_messages, args=(redis_client, stop_listening_event)
    )
    listener_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    stop_listening_event.set()
    listener_thread.join()


app.include_router(register.router, prefix="/auth", tags=["auth"])
app.include_router(login.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Hello Cloud system drive"}


@app.get("/health")
async def health_check():

    try:
        await database.command("ping")
        mongo_status = True
    except Exception:
        mongo_status = False
    #
    # check_redis = redis_client.ping()
    # if check_redis:
    #     redis_status = True
    # else:
    #     redis_status = False
    # redis_status = True if check_redis else False
    # return {"redis": redis_status, "mongo": mongo_status}
    return {"mongo": mongo_status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
