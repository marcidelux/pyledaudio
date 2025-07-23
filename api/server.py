# api/server.py

# Builtin and third-party imports
import asyncio
import uvicorn
import threading
from fastapi import FastAPI

# Local imports
from . import config
from .broadcasters import (
    bands_broadcaster_loop,
    led_broadcaster_loop,
    register_websockets
)
from .endpoints import register_endpoints
from .mounts import mount_client_page


def start():
    app = FastAPI()
    mount_client_page(app)
    register_endpoints(app)
    register_websockets(app)

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        uvicorn_config = uvicorn.Config(
            app,
            host=config.SERVER_IP,
            port=config.SERVER_PORT,
            log_level="info")

        server_instance = uvicorn.Server(uvicorn_config)

        loop.create_task(bands_broadcaster_loop())
        loop.create_task(led_broadcaster_loop())
        loop.run_until_complete(server_instance.serve())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
