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
from app.core.mongo_db import database
from bson import ObjectId
import json
from ...core.os_support import (
    ensure_path_exists,
    saveFile,
)
import datetime
from app.core.redis_db import get_data, get_redis_client, set_data
import time
from fastapi import BackgroundTasks

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


async def send_data_to_user(device_id: str, data: str):
    websocket = active_connections.get(device_id)
    if websocket:
        await websocket.send_text(data)
    else:
        print(f"No active connection for device_id: {device_id}")


async def verify_user_ownership(user: dict, device_id: str):
    device = await device_collection.find_one({"device_id": device_id})
    if device is None or device.get("user_id") != user.get("id"):
        raise HTTPException(
            status_code=403, detail="User is not the owner of the device"
        )
    return True


async def get_data_from_response(field, data):
    try:
        return data[field]
    except Exception as e:
        print(f"Error: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client = await get_redis_client()
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
            action = await get_data_from_response("action", json.loads(data))
            print(f"Action: {action}")
            if action != "get_files":
                data = clean_data(json.loads(data), ["action"])
                await set_data(client, f"{device_id}", data)
            else:
                await file_collection.insert_one(json.loads(data))

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


@router.get("/request-directory-structure/{device_id}")
async def request_directory_structure(device_id: str):
    connection_info = active_connections.get(device_id)
    if not connection_info:
        raise HTTPException(status_code=404, detail="Device not connected")
    websocket = connection_info["websocket"]
    await websocket.send_text(json.dumps({"action": "get_tree_structure"}))
    client = await get_redis_client()
    try:
        data = await get_data(client, f"{device_id}")
        client.close()
        if data:
            response = data["data"]
            return json.loads(response)
    except Exception as e:
        print(f"Error: {e}")


@router.post("/create-folder/{device_id}")
async def create_folder(
    device_id: str, folder_path: str, user=Depends(get_current_active_user)
):
    connection_info = active_connections.get(device_id)
    if not connection_info:
        raise HTTPException(status_code=404, detail="Device not connected")
    await verify_user_ownership(user, device_id)
    websocket = connection_info["websocket"]
    await websocket.send_text(
        json.dumps({"action": "create_folder", "folder_path": folder_path})
    )
    return {"message": "Folder creation initiated"}


@router.post("/send_files_from_device/{device_id}")
async def send_files_from_device(
    device_id: str,
    file_path: str = Form(...),
    file: UploadFile = File(...),
):
    print("send_files_from_device")
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
            "client_path": file_path,
            "download_code": hash_code,
            "upload_time": timestamp,
        }
    )

    return {"message": "File processing initiated", "download_code": hash_code}


@router.get("/get-files/{device_id}")
async def get_files(
    device_id: str,
    file_path: str = Form(...),
    user=Depends(get_current_active_user),
):
    print("get_files")
    connection_info = active_connections.get(device_id)
    if not connection_info:
        raise HTTPException(status_code=404, detail="Device not connected")
    await verify_user_ownership(user, device_id)
    websocket = connection_info["websocket"]
    print(f"File path: {file_path}")
    count = 0
    try:
        file_info = await file_collection.find_one(
            {"device_id": device_id, "file_path": file_path}
        )
        print(f"File info: {file_info}")
        if file_info:
            return clean_data(file_info, ["_id", "action", "device_id", "file_path"])
    except Exception as e:
        print(f"Error: {e}")

    await websocket.send_text(
        json.dumps({"action": "get_files", "file_path": file_path})
    )
    count = 0
    try:
        while count < 10:
            # check database for file
            time.sleep(0.2)
            file_info = await file_collection.find_one(
                {"device_id": device_id, "file_path": file_path}
            )
            if file_info:
                return clean_data(
                    file_info, ["_id", "action", "device_id", "file_path"]
                )
            count += 1
    except Exception as e:
        print(f"Error: {e}")

    return {"message": "File not found"}


@router.post("/send-file/{device_id}")
async def send_file(
    device_id: str,
    file_path: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_active_user),
):
    print("send_file")
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
            "client_path": file_path,
            "download_code": hash_code,
            "upload_time": timestamp,
        }
    )

    websocket = connection_info["websocket"]
    await websocket.send_text(
        json.dumps(
            {"action": "send_files", "download_code": hash_code, "file_path": file_path}
        )
    )

    return {"message": "File processing initiated", "download_code": hash_code}


@router.get("/download-file/{file_code}")
async def download_file(file_code: str, background_tasks: BackgroundTasks):
    file_info = await database["filesManager"].find_one(
        {"hash_name": {"$regex": f"^{file_code}"}}
    )
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = file_info["file_path"]
    file_name = file_info["file_name"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    def remove_file(path):
        os.remove(path)
        # remove database entry

    response = FileResponse(
        file_path,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )

    await database["filesManager"].delete_one({"file_path": file_path})
    await database["filesManager"].delete_one({"download_code": file_code})

    background_tasks.add_task(remove_file, file_path)

    return response


@router.post("/setDevice")
async def setDevice(
    user_id: str = Depends(get_current_active_user),
    device_name: str = Form(...),
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    device = await device_collection.find_one({"user_id": user_id["id"]})
    device_id = hashlib.sha256((device_name + user_id["id"]).encode()).hexdigest()

    if device:
        await device_collection.update_one(
            {"user_id": user_id["id"]},
            {"$set": {"device_name": device_name, "device_id": device_id}},
        )
    else:
        await device_collection.insert_one(
            {
                "user_id": user_id["id"],
                "device_name": device_name,
                "device_id": device_id,
            }
        )

    return {"message": "Device set successfully", "device_id": device_id}


@router.get("/getClientExecutable")
async def getClientExecutable(
    os_device: str = Form(...),
):
    filename_os = ""
    if os_device == "windows":
        filename_os = "client-windows.zip"
        client_executable_path = os.path.join("client", "dist", "client-windows.zip")
    elif os_device == "macos":
        filename_os = "client-mac.zip"
        client_executable_path = os.path.join("client", "dist", "client-macos.zip")

    # client_executable_path = os.path.join("client", "dist", "client.zip")

    if not os.path.exists(client_executable_path):
        raise HTTPException(status_code=404, detail="Client executable not found")

    return FileResponse(
        path=client_executable_path,
        filename=filename_os,
        media_type="application/zip",
    )
