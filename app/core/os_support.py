import asyncio
from cryptography.fernet import Fernet
import os


def ensure_path_exists(save_path):
    os.makedirs(save_path, exist_ok=True)


async def saveFile(save_path, data):
    with open(save_path, "wb") as buffer:
        buffer.write(data)
