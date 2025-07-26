# Route for handling file uploads
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import boto3
from botocore.exceptions import ClientError


from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database.models import Job
from app.database.session import get_db
from app.services.file_upload import handle_file_upload
from app.api.v1.schemas import (
    JobResponse,
    JobStatusResponse,
    FileConversionStatusResponse,
)
from app.config import S3_BUCKET_NAME, USE_S3, UPLOAD_DIR

upload_router = APIRouter()


@upload_router.post("/", response_model=JobResponse, status_code=202)
async def create_conversion_job(
    files: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    """
    Create a new file conversion job.
    This endpoint accepts multiple files and returns a job ID
    along with the count of files uploaded.
    """
    job_id, file_count = await handle_file_upload(files, db)
    return JobResponse(job_id=job_id, file_count=file_count)


@upload_router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    response_model_exclude_none=True,
    status_code=200,
)
async def get_conversion_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve the status of a file conversion job.
    This endpoint returns the current status of the
    job along with details of the files being processed.
    """
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        print(
            f"Retrieving job status for {job_id}: {job.file_conversions[0].output_file_path}"
        )
        if not job:
            return JobStatusResponse(
                job_id=job_id,
                status="not_found",
                files=[],
                created_at="",
                downloaded_url=None,
            )

        file_conversions = [
            FileConversionStatusResponse(
                file_name=fc.file_name,
                status=fc.status.value,
                error_message=fc.error_message,
            )
            for fc in job.file_conversions
        ]

        return JobStatusResponse(
            job_id=job.id,
            status=job.status.value,
            files=file_conversions,
            created_at=job.created_at.isoformat(),
            downloaded_url=job.download_url if job.download_url else None,
        )
    except Exception as e:
        print(f"Error retrieving job status for {job_id}: {e}")
        return JobStatusResponse(
            job_id=job_id, status="error", files=[], created_at="", downloaded_url=None
        )


@upload_router.get("/{job_id}/download", status_code=200)
async def download_converted_files(job_id: uuid.UUID):
    """
    Stream the converted ZIP file for a specific job from S3.
    """
    if not USE_S3:
        file_path = f"/app/{UPLOAD_DIR}/{job_id}/{job_id}.zip"  # Adjust path as per your project

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=file_path, filename=f"{job_id}.zip", media_type="application/zip"
        )

    key = f"{job_id}/{job_id}.zip"
    s3 = boto3.client("s3")

    try:
        s3_response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        file_stream = s3_response["Body"]

        return StreamingResponse(
            file_stream,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{job_id}.zip"'},
        )

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(status_code=404, detail="ZIP file not found in S3")
        else:
            raise HTTPException(
                status_code=500, detail=f"S3 Error: {e.response['Error']['Message']}"
            )
