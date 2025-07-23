from fastapi import FastAPI
from app.api.v1.jobs import upload_router

app = FastAPI()

app.include_router(upload_router, prefix="/api/v1/jobs", tags=["upload"])
