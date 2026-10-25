"""The web app: the UI's static files, served at /."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

WEB = Path(__file__).parent / "web"


def create_app():
    app = FastAPI()
    app.mount("/", StaticFiles(directory=WEB, html=True))
    return app
