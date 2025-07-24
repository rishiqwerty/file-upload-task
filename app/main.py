from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.jobs import upload_router
import os

app = FastAPI()

app.include_router(upload_router, prefix="/api/v1/jobs", tags=["upload"])

app.mount(
    "/static",
    StaticFiles(directory=os.path.join("file_upload", "data", "uploads")),
    name="static",
)
