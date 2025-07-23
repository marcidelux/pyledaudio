from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI


def mount_client_page(app: FastAPI):
    """
    Mount the static files for the client page.
    """
    app.mount("/ui", StaticFiles(directory="page", html=True), name="static")
