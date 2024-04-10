from fastapi import FastAPI, BackgroundTasks
from app.api.auth import register, login
from app.api.drive import drive
from fastapi.middleware.cors import CORSMiddleware
from app.core.mongo_db import database
import threading
from threading import Event
from app.core.redis_db import get_redis_client, get_data, set_data


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(register.router, prefix="/auth", tags=["auth"])
app.include_router(login.router, prefix="/auth", tags=["auth"])
app.include_router(drive.router, prefix="/drive", tags=["drive"])


@app.get("/")
async def root():
    return {"message": "Hello Project 1!"}


@app.get("/healthCheck")
async def healthCheck():
    mongoDb = False
    redisDb = False
    try:
        # check if redisDb is working by setting and getting a key
        client = await get_redis_client()
        await set_data(client, "test", "test")
        checkRedis = await get_data(client, "test")
        if checkRedis:
            redisDb = True
            # delete the key
            client.delete("test")
    except Exception as e:
        print(e)

    try:
        # check if mongoDb is created collection test
        checkMongo = await database.command("ping")

        if checkMongo:
            mongoDb = True
    except Exception as e:
        print(e)

    if mongoDb and redisDb:
        return {"message": "All services are up and running"}
    else:
        return {
            "message": "Some services are down",
            "mongoDb": mongoDb,
            "redisDb": redisDb,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
