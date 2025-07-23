from pydantic import BaseModel
from typing import List, Optional

class JobResponse(BaseModel):
    job_id: str
    file_count: int

class FileConversionStatusResponse(BaseModel):
    file_name: str
    status: str
    error_message: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    files: List[FileConversionStatusResponse] = []
    created_at: str
    downloaded_url: Optional[str] = None
