import uuid
import os
from typing import List
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.database.models import FileConversion, Job
from app.tasks import process_file_conversion
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
        job_dir = os.path.join(UPLOAD_DIR, str(job_id))
        os.makedirs(job_dir, exist_ok=True)
        file_path = os.path.join(job_dir, filename)
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return file_path


async def handle_file_upload(
    files: List[UploadFile], db: Session
) -> tuple[uuid.UUID, int]:
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
        count = 0
        for file in files:
            storage_path = await save_file(job_id, file)

            file_conversion = FileConversion(
                file_name=file.filename,
                job=job,
                output_file_path=storage_path,  # S3 key or local path
            )
            db.add(file_conversion)
            db.commit()
            db.refresh(file_conversion)

            process_file_conversion.apply_async(
                args=[file_conversion.id, storage_path], queue="libre_queue"
            )

            count += 1
        return job_id, count
    except Exception as e:
        print(f"Error handling file upload: {e}")
        db.rollback()
        raise e
