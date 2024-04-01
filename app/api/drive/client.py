import websocket
import os
import sys

device_code = input("Nhập mã code của thiết bị: ")

ws = websocket.create_connection("wss://localhost:8000/ws")


ws.send(device_code)

while True:
    message = ws.recv()
    if message.startswith("cmd:"):
        cmd, action = message.split(":")[1:]
        if cmd == "create_folder":
            os.makedirs(action, exist_ok=True)
            print(f"Folder {action} đã được tạo.")
    else:
        print(f"Dữ liệu nhận được: {message}")
