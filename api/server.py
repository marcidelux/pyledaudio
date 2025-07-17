# api/server.py
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel
from . import config
from state import state_manager
from effects.effects_manager import dynamic_names, static_names
import uvicorn
import threading

app = FastAPI()
bands_clients: List[WebSocket] = []
broadcast_queue: asyncio.Queue = None
leds_clients: List[WebSocket] = []
leds_broadcast_queue: asyncio.Queue = None

app.mount("/ui", StaticFiles(directory="page", html=True), name="static")


class PowerRequest(BaseModel):
    power: Optional[bool] = None


class BrightnessRequest(BaseModel):
    brightness: Optional[int] = None


class EffectRequest(BaseModel):
    effect: Optional[str] = None


@app.get("/health")
def hello():
    return {200: "OK"}


@app.get("/config")
def get_config():
    FULL_COLOR_PALETTE = [
        '#FF0000', '#00FF00', '#0000BB', '#00FF00', '#00FFFF', '#0000FF', '#8B00FF',
        '#FF1493', '#DC143C', '#FFA500', '#FFD700', '#ADFF2F', '#32CD32', '#008080',
        '#4682B4', '#1E90FF', '#4169E1', '#4B0082', '#9400D3', '#FF69B4', '#CD5C5C',
        '#FF4500', '#FF6347', '#FF8C00', '#20B2AA', '#40E0D0', '#7FFF00', '#7CFC00',
        '#00FA9A', '#00CED1'
    ]
    num_bands = config.N_FFT_BINS
    # Select only as many colors as needed
    colors = FULL_COLOR_PALETTE[:num_bands]
    return {
        "num_bands": num_bands,
        "colors": colors
    }


@app.post("/power")
def set_power(req: PowerRequest):
    if req.power is not None:
        state_manager.power = req.power
        print(state_manager)
    else:
        print("No power value provided in request.")

    return {"power": state_manager.power}


@app.post("/brightness")
def set_brightness(req: BrightnessRequest):
    if req.brightness is not None:
        state_manager.brightness = req.brightness
        print(state_manager)
    else:
        print("No brightness value provided in request.")

    return {"brightness": state_manager.brightness}


@app.post("/effect")
def set_effect(req: EffectRequest):
    if req.effect is not None:
        state_manager.effect = req.effect
        print(state_manager)
    else:
        print("No effect value provided in request.")

    return {"effect": state_manager.effect}


@app.get("/effects-static")
def get_static_effects():
    return {"effects": static_names}


@app.get("/effects-dynamic")
def get_dynamic_effects():
    return {"effects": dynamic_names}


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
    global broadcast_queue
    broadcast_queue = asyncio.Queue()  # created HERE, on correct loop
    while True:
        bands = await broadcast_queue.get()
        for ws in bands_clients:
            try:
                await ws.send_json({"bands": list(bands)})
            except Exception:
                bands_clients.remove(ws)


async def led_broadcaster_loop():
    global leds_broadcast_queue
    leds_broadcast_queue = asyncio.Queue()
    while True:
        data = await leds_broadcast_queue.get()
        data_as_list = list(data)
        for ws in leds_clients:
            try:
                await ws.send_bytes(data)
            except Exception:
                leds_clients.remove(ws)


def start():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        uvicorn_config = uvicorn.Config(
            "api.server:app", host=config.SERVER_IP, port=config.SERVER_PORT, log_level="info")
        server_instance = uvicorn.Server(uvicorn_config)

        loop.create_task(bands_broadcaster_loop())
        loop.create_task(led_broadcaster_loop())
        loop.run_until_complete(server_instance.serve())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
