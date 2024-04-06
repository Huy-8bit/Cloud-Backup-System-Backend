from fastapi import (
    Depends,
    Form,
    APIRouter,
    HTTPException,
    WebSocket,
    UploadFile,
    File,
    Path,
)
import os
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import hashlib
import random
from app.core.dependencies import get_current_active_user
from app.core.accesstoken import check_user_exit
from app.core.database import database
from bson import ObjectId
import json
from ...core.os_support import (
    ensure_path_exists,
    saveFile,
)
import datetime


router = APIRouter()

device_collection = database.get_collection("deviceInfo")
user_collection = database.get_collection("usersInfo")
file_collection = database.get_collection("filesManager")

active_connections: Dict[str, dict] = {}


def clean_data(item, exclude_keys):
    if isinstance(item, ObjectId):
        return str(item)
    if isinstance(item, list):
        return [clean_data(i, exclude_keys) for i in item]
    if isinstance(item, dict):
        return {
            k: clean_data(v, exclude_keys)
            for k, v in item.items()
            if k not in exclude_keys
        }
    return item


async def send_data_to_user(client_id: str, data: str):
    if client_id in active_connections:
        websocket = active_connections[client_id]
        await websocket.send_text(data)
    else:
        print(f"No active connection for client_id: {client_id}")


async def verify_user_ownership(user: dict, device_id: str):
    device = await device_collection.find_one({"device_id": device_id})
    if device is None or device.get("user_id") != user.get("id"):
        raise HTTPException(
            status_code=403, detail="User is not the owner of the device"
        )
    return True


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    device_id = websocket.headers.get("device_id")
    if not device_id:
        await websocket.close(code=4001)
        return
    random_id = str(random.randint(1, 1000000000))
    active_connections[device_id] = {"websocket": websocket, "random_id": random_id}
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        del active_connections[device_id]


@router.get("/active-connections")
async def get_active_connections():
    try:

        active_count = len(active_connections)
        return {"active_connections": active_count}
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-file/{device_id}")
async def send_file(
    device_id: str, file: UploadFile = File(...), user=Depends(get_current_active_user)
):
    connection_info = active_connections.get(device_id)
    if not connection_info:
        raise HTTPException(status_code=404, detail="Device not connected")
    await verify_user_ownership(user, device_id)

    file_content = await file.read()
    file_name = file.filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    hash_code = hashlib.sha256(f"{file_name}{timestamp}".encode()).hexdigest()
    extension = os.path.splitext(file_name)[1]
    new_file_name = f"{hash_code}{extension}"
    save_path = os.path.join("data", new_file_name)

    ensure_path_exists("data")
    await saveFile(save_path, file_content)

    await file_collection.insert_one(
        {
            "file_name": file_name,
            "hash_name": new_file_name,
            "file_path": save_path,
            "upload_time": timestamp,
        }
    )

    websocket = connection_info["websocket"]
    await websocket.send_text(json.dumps({"download_code": hash_code}))

    return {"message": "File processing initiated", "download_code": hash_code}


@router.get("/download-file/{file_code}")
async def download_file(
    file_code: str = Path(..., title="The file code"),
    user=Depends(get_current_active_user),
):

    file_info = await database["filesManager"].find_one(
        {"hash_name": {"$regex": f"^{file_code}"}}
    )
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    await verify_user_ownership(user, file_info["user_id"])

    file_path = file_info["file_path"]
    file_name = file_info["file_name"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}

    return FileResponse(file_path, headers=headers)


@router.post("/setDevice")
async def setDevice(
    user_id: str = Depends(get_current_active_user),
    device_name: str = Form(...),
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    device = await device_collection.find_one({"user_id": user_id["id"]})
    if device:
        await device_collection.update_one(
            {"user_id": user_id}, {"$set": {"device_name": device_name}}
        )
    else:
        await device_collection.insert_one(
            {"user_id": user_id, "device_name": device_name}
        )

    device_id = hashlib.sha256(device_name.encode()).hexdigest()

    await device_collection.update_one(
        {"user_id": user_id}, {"$set": {"device_id": device_id}}
    )

    return {"message": "Device set successfully", "device_id": device_id}


@router.get("/getClientExecutable")
async def getClientExecutable():

    client_executable_path = os.path.join("client", "dist", "client.zip")

    if not os.path.exists(client_executable_path):
        raise HTTPException(status_code=404, detail="Client executable not found")

    return FileResponse(
        path=client_executable_path,
        filename="client.zip",
        media_type="application/zip",
    )
