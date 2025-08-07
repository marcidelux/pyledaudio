import asyncio
from fastapi import WebSocket, WebSocketDisconnect, FastAPI
from typing import List
import socket
from . import config

bands_clients: List[WebSocket] = []
leds_clients: List[WebSocket] = []
bands_queue: asyncio.Queue = asyncio.Queue()
leds_queue: asyncio.Queue = asyncio.Queue()
udp_send_queue: asyncio.Queue = asyncio.Queue()


def register_websockets(app: FastAPI):
    @app.websocket("/ws/bands")
    async def bands_ws(websocket: WebSocket):
        await websocket.accept()
        bands_clients.append(websocket)
        print("Bands Client connected")
        try:
            while True:
                await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            bands_clients.remove(websocket)

    @app.websocket("/ws/leds")
    async def leds_ws(websocket: WebSocket):
        await websocket.accept()
        leds_clients.append(websocket)
        print("LED Client connected")
        try:
            while True:
                await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            leds_clients.remove(websocket)


async def bands_broadcaster_loop():
    print("Starting bands broadcaster loop")
    while True:
        bands = await bands_queue.get()
        for ws in bands_clients:
            try:
                await ws.send_json({"bands": list(bands)})
            except Exception:
                bands_clients.remove(ws)


async def led_broadcaster_loop():
    print("Starting LED broadcaster loop")
    while True:
        data = await leds_queue.get()
        for ws in leds_clients:
            try:
                await ws.send_bytes(data)
            except Exception:
                leds_clients.remove(ws)


async def udp_sender_loop():
    print("Starting UDP sender loop")
    loop = asyncio.get_running_loop()
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setblocking(False)
    address = (config.UDP_IP, config.UDP_PORT)

    while True:
        try:
            data = await udp_send_queue.get()
            # print(f"id:{data[0]} s:{data[1]}")
            await loop.sock_sendto(udp_socket, data, address)
            await asyncio.sleep(0.005)
        except Exception as e:
            print(f"UDP send error: {e}")
