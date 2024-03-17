from fastapi import (
    BackgroundTasks,
    Depends,
    Form,
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Body,
)
from fastapi.responses import FileResponse
import os
import shutil
from fastapi.responses import FileResponse
from typing import List, Dict
import hashlib
import time
import base64
import io
from fastapi.responses import StreamingResponse
import random
from app.core.dependencies import get_current_active_user
from app.core.accesstoken import check_user_exit
from app.core.database import database
from app.api.drive.models import ChatRoom
from cryptography.fernet import Fernet
from pathlib import Path
from app.api.drive.crypted import (
    saveFile,
    ensure_path_exists,
    generate_and_save_key,
    load_key,
    encrypt_file,
    decrypt_file,
)

from bson import ObjectId


router = APIRouter()


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


device_collection = database.get_collection("deviceInfo")


@router.post("/setDevice")
async def setDevice(
    user_id: str = Depends(get_current_active_user),
    device_name: str = Form(...),
):
    if not check_user_exit(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    device = await device_collection.find_one({"user_id": user_id})
    if device:
        await device_collection.update_one(
            {"user_id": user_id}, {"$set": {"device_name": device_name}}
        )
    else:
        await device_collection.insert_one(
            {"user_id": user_id, "device_name": device_name}
        )
    return {"status": "success"}
