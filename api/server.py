# api/server.py
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel
from . import config
from state import state_manager
from effects.effects_manager import effect_manager, dynamic_names, static_names, EffectPair
import uvicorn
import threading
from http import HTTPStatus

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


class EffectPreviewRequest(BaseModel):
    effect: Optional[str] = None
    primary: Optional[bool] = None


class SelectEffectsListRequest(BaseModel):
    name: str


class AddEffectPairToCurrentListRequest(BaseModel):
    primary: str
    secondary: Optional[str] = None


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


@app.post("/effect-preview")
def set_effect_preview(req: EffectPreviewRequest):
    if req.effect is not None and req.primary is not None:
        if req.primary:
            effect_manager.set_primary_effect_by_name(req.effect)
        else:
            effect_manager.set_secondary_effect_by_name(req.effect)
        print(f"Preview effect set to: {req.effect}")
    else:
        print("No effect value provided in request.")

    return {"effect": req.effect}


@app.get("/effects-lists-names")
def get_effects_lists_names():
    effects_lists_names = effect_manager.memory_manager.get_names()
    print(f"Available effects lists: {effects_lists_names}")
    if effects_lists_names is None:
        return {"error": "No effects lists found"}, 404
    return {"effects_lists_names": effects_lists_names}


@app.post("/select-effects-list")
def post_select_effects_list(req: SelectEffectsListRequest):
    if req.name is None:
        return {"error": "Effects list name is required"}, 400

    effects_list = effect_manager.memory_manager.get_effect_list(req.name)
    if effects_list is None:
        return {"error": f"Effects list '{req.name}' not found"}, HTTPStatus.NOT_FOUND

    if effect_manager.select_effects_list(req.name) == HTTPStatus.NOT_FOUND:
        return {"error": f"Effects list '{req.name}' not found"}, HTTPStatus.NOT_FOUND

    return {"effects_list": effects_list}


@app.post("/next-effect-pair")
def post_next_effect_pair():
    next_index = effect_manager.next_effect_pair()
    if next_index == HTTPStatus.NOT_FOUND:
        return {"error": "Current effects list not selected"}, HTTPStatus.NOT_FOUND

    return {"current_index": next_index}


@app.post("/previous-effect-pair")
def post_previous_effect_pair():
    previous_index = effect_manager.previous_effect_pair()
    if previous_index == HTTPStatus.NOT_FOUND:
        return {"error": "Current effects list not selected"}, HTTPStatus.NOT_FOUND

    return {"current_index": previous_index}


@app.post("/add-effect-pair-to-current-list")
def post_add_effect_pair_to_current_list(req: AddEffectPairToCurrentListRequest):
    if req.primary is None or req.primary == "":
        return {"error": "Primary effect name is required"}, HTTPStatus.BAD_REQUEST

    if effect_manager.memory_manager.add_effect_to_list(
            effect_manager.current_effects_list.name,
            EffectPair(primary=req.primary, secondary=req.secondary)) == HTTPStatus.NOT_FOUND:
        return {"error": f"Current effects list '{effect_manager.current_effects_list.name}' not found"}, HTTPStatus.NOT_FOUND

    effects_list = effect_manager.memory_manager.get_effect_list(
        effect_manager.current_effects_list.name)

    return {"effects_list": effects_list}


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
