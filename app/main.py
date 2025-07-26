from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.jobs import upload_router
import os
from app.config import USE_S3

app = FastAPI()

app.include_router(upload_router, prefix="/api/v1/jobs", tags=["upload"])

if not USE_S3:
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join("file_upload", "data", "uploads")),
        name="static",
    )


@app.get("/")
async def root():
    return {"message": "Welcome to the File Upload API"}
