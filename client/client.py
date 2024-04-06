import os
import asyncio
import websockets
import json
import aiohttp
from urllib.parse import unquote

import re


def ensure_data_directory():
    if not os.path.exists("data"):
        os.makedirs("data")


async def saveFile(save_path, data):
    with open(save_path, "wb") as buffer:
        buffer.write(data)


async def download_file(download_code):
    download_url = f"http://54.254.58.42/drive/download-file/{download_code}"
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as response:
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

                save_path = os.path.join("data", filename)
                file_data = await response.read()
                await saveFile(save_path, file_data)
                print(f"File downloaded and saved as: {save_path}")
            else:
                print("Failed to download file.")


async def handle_file(websocket):
    message = await websocket.recv()
    message = json.loads(message)
    download_code = message["download_code"]
    await download_file(download_code)


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
    uri = "ws://54.254.58.42/drive/ws"

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        while True:
            await handle_file(websocket)


asyncio.get_event_loop().run_until_complete(connect_and_listen())
