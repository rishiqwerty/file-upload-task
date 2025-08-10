from pydantic import BaseModel
import uuid
from typing import List, Optional


class JobResponse(BaseModel):
    job_id: uuid.UUID
    file_count: Optional[int] = None


class FileConversionStatusResponse(BaseModel):
    file_name: str
    status: str
    error_message: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    files: List[FileConversionStatusResponse] = []
    created_at: str
    downloaded_url: Optional[str] = None
