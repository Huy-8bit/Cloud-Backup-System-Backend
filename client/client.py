import os
import asyncio
import websockets
import json
import aiohttp
from urllib.parse import unquote
from services import directory_tree_to_json
import base64
import re


def ensure_data_directory():
    if not os.path.exists("./data"):
        os.makedirs("./data")


async def saveFile(save_path, data):
    with open(save_path, "wb") as buffer:
        buffer.write(data)


async def get_tree_structure():
    return directory_tree_to_json("./data")


async def read_file_content(file_path):

    file_path = "./data" + file_path
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


async def download_file(download_code, file_path):
    download_url = f"http://18.141.58.127/drive/download-file/{download_code}"
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

                file_path = "./data/" + file_path
                save_path = os.path.join(file_path, filename)
                print(f"Downloading file to: {save_path}")
                file_data = await response.read()
                await saveFile(save_path, file_data)
                print(f"File downloaded and saved as: {save_path}")
            else:
                print("Failed to download file.")


async def create_folder(folder_path):
    folder_path = "./data/" + folder_path
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    response = {
        "notification": "Folder created successfully",
        "folder_path": folder_path,
    }
    return response


async def handle_connect(device_id, websocket):
    try:
        message = await websocket.recv()
        if message:
            try:
                data = json.loads(message)
                await handle_request(device_id, websocket, data)
            except json.JSONDecodeError as e:
                print(
                    f"JSONDecodeError occurred while decoding message: {message}, error: {e}"
                )
        else:
            print("Received an empty message or non-JSON message.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


async def post_file_to_server(device_id, file_path):
    print(f"Sending file: {file_path}")
    print(f"Device ID: {device_id}")
    full_path = "./data" + file_path
    print(f"Sending file: {full_path}")
    try:
        with open(full_path, "rb") as file:
            file_content = file.read()
            file_name = os.path.basename(file_path)
            url = f"http://18.141.58.127/drive/send_files_from_device/{device_id}"

            async with aiohttp.ClientSession() as session:
                files = {"file": (file_name, file_content)}
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    file_content,
                    filename=file_name,
                    content_type="application/octet-stream",
                )
                data.add_field("file_path", file_path)

                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        print("File was successfully sent to the server.")
                        return await response.json()
                    else:
                        print("Failed to send file to the server.")
                        return {"error": "Failed to send file"}
    except FileNotFoundError:
        print(f"File not found: {full_path}")
    except Exception as e:
        print(f"An error occurred while sending the file: {e}")


async def handle_request(device_id, websocket, data):

    if data["action"] == "send_files":
        download_code = data["download_code"]
        file_path = data["file_path"]
        await download_file(download_code, file_path)

    elif data["action"] == "get_tree_structure":
        print("Sending directory structure")
        tree_structure = directory_tree_to_json("./data")
        try:
            response = {
                "data": "send_tree_structure",
                "action": "send_tree_structure",
                "data": tree_structure,
            }
            response = json.dumps(response)
            await websocket.send(response)
        except Exception as e:
            print(f"An error occurred: {e}")

        print("Directory structure sent")

    elif data["action"] == "create_folder":
        try:
            folder_path = data["folder_path"]
            response = await create_folder(folder_path)
            response = json.dumps(response)
            await websocket.send(response)
            print("Folder created successfully")
        except Exception as e:
            print(f"An error occurred: {e}")

    elif data["action"] == "get_files":
        file_path = data["file_path"]
        response = await post_file_to_server(device_id, file_path)
        response = json.dumps(
            {
                "action": "get_files",
                "device_id": device_id,
                "file_path": file_path,
                "download_code": response["download_code"],
            }
        )
        await websocket.send(response)
        print("File sent successfully")

    else:
        print("Invalid action")


async def request_directory_structure(device_id):
    try:

        url = f"http://18.141.58.127/drive/request-directory-structure/{device_id}"

        async with aiohttp.ClientSession() as session:

            async with session.get(
                url,
            ) as response:
                if response.status == 200:
                    print("Request successful")
                    return await response.json()
                else:
                    print("Request failed")
                    return {"error": "Failed to get directory structure"}
    except Exception as e:
        print(f"An error occurred while sending the file: {e}")


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
        print(f"Device ID: {device_id}")

    headers = {"DEVICE_ID": device_id}
    uri = "ws://18.141.58.127/drive/ws"

    print(f"Connecting to: {uri}")

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        await request_directory_structure(device_id)
        print("Connected to server...")
        while True:
            await handle_connect(device_id, websocket)


asyncio.get_event_loop().run_until_complete(connect_and_listen())
