import os
import asyncio
import websockets
import json
import aiohttp
from urllib.parse import unquote
from services import directory_tree_to_json

import re


def ensure_data_directory():
    if not os.path.exists("./data"):
        os.makedirs("./data")


async def saveFile(save_path, data):
    with open(save_path, "wb") as buffer:
        buffer.write(data)


async def download_file(download_code):
    download_url = f"http://localhost:8000/drive/download-file/{download_code}"
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as response:
            print(f"Response status: {response.status}")
            if response.status == 200:
                content_disp = response.headers.get("Content-Disposition")
                print(content_disp)
                if content_disp and "filename=" in content_disp:

                    filename = (
                        content_disp.split("filename=")[1].split(";")[0].strip('"')
                    )

                    filename = unquote(filename)
                else:
                    filename = f"{download_code}.bin"

                save_path = os.path.join("./data", filename)
                print(f"Downloading file to: {save_path}")
                file_data = await response.read()
                await saveFile(save_path, file_data)
                print(f"File downloaded and saved as: {save_path}")
            else:
                print("Failed to download file.")


async def handle_file(websocket):
    message = await websocket.recv()
    message = json.loads(message)
    if "download_code" in message:
        await download_file(message["download_code"])
    else:
        await handle_request(websocket, message)


async def read_file_content(file_path):
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()
            return file_content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


async def handle_request(websocket, message):
    if message["action"] == "get_tree_structure":
        tree_structure = await get_tree_structure()
        await websocket.send(json.dumps(tree_structure))
    elif message["action"] == "get_file":
        file_path = message["file_path"]
        file_content = await read_file_content(file_path)
        await websocket.send(file_content)


async def get_tree_structure():
    return directory_tree_to_json("./data")


async def connect_and_listen():
    ensure_data_directory()
    id_file_path = "./id.txt"

    if not os.path.exists(id_file_path):
        device_id = input("Enter your device_id: ").strip()
        with open(id_file_path, "w") as f:
            f.write(device_id)
    else:
        with open(id_file_path, "r") as f:
            device_id = f.read().strip()

    headers = {"DEVICE_ID": device_id}
    uri = "ws://localhost:8000/drive/ws"

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        while True:
            await handle_file(websocket)


asyncio.get_event_loop().run_until_complete(connect_and_listen())
