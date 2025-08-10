import uuid
import os
from typing import List
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.database.models import FileConversion, Job
from app.tasks import unzip_and_schedule_file_conversion
import boto3
import io
from app.config import UPLOAD_DIR, USE_S3, S3_BUCKET_NAME

s3 = boto3.client("s3")


async def save_file(job_id: uuid.UUID, file: UploadFile) -> str:
    """
    Save the uploaded file to S3 or local storage based on configuration.
    Returns the file path or S3 key where the file is stored.
    """
    filename = file.filename
    if USE_S3:
        s3_key = f"{job_id}/{filename}"
        contents = await file.read()
        s3.upload_fileobj(io.BytesIO(contents), S3_BUCKET_NAME, s3_key)
        return s3_key
    else:
        print(f"Saving file locally: {filename}")
        job_dir = os.path.join(UPLOAD_DIR, str(job_id))
        os.makedirs(job_dir, exist_ok=True)
        file_path = os.path.join(job_dir, filename)
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # chunks
                f.write(chunk)
        await file.close()
        return file_path


async def handle_file_upload(file: UploadFile, db: Session) -> tuple[uuid.UUID, int]:
    """
    File upload handler that saves files and creates a job entry.
    This function is called by the API endpoint to handle file uploads.
    Returns the job ID and the count of files uploaded.
    """
    try:
        job = Job()
        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id
        print(f"Job created with ID: {job_id}")
        zip_path = await save_file(job_id, file)
        unzip_and_schedule_file_conversion.apply_async(
            (zip_path, job_id), queue="file_conversion_queue"
        )
        return job_id
    except Exception as e:
        print(f"Error handling file upload: {e}")
        db.rollback()
        raise e
