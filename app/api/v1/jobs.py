# Route for handling file uploads
from fastapi import APIRouter, UploadFile, File, Response
from typing import List
from app.services.file_upload import handle_file_upload
from app.api.v1.schemas import JobResponse, JobStatusResponse, FileConversionStatusResponse

upload_router = APIRouter()

@upload_router.post("/", response_model=JobResponse, status_code=202)
async def create_conversion_job(files: List[UploadFile] = File(...)):
    """
    Create a new file conversion job.
    This endpoint accepts multiple files and returns a job ID along with the count of files uploaded.
    """
    job_id, file_count = await handle_file_upload(files)
    return JobResponse(job_id=job_id, file_count=file_count)

@upload_router.get("/{job_id}", response_model=JobStatusResponse, response_model_exclude_none=True, status_code=200)
async def get_conversion_job_status(job_id: str):
    """
    Retrieve the status of a file conversion job.
    This endpoint returns the current status of the job along with details of the files being processed.
    """
    # TODO: Implement logic to retrieve the status of the conversion job aftre db integration
    return JobStatusResponse(
        job_id=job_id, status="processing",
        files=[FileConversionStatusResponse(file_name="example.txt", status="processing")],
        created_at="2023-01-01T00:00:00Z"
    )