import uuid
import os
from typing import List
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.database.models import FileConversion, Job
from app.tasks import process_file_conversion

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")


async def handle_file_upload(
    files: List[UploadFile], db: Session
) -> tuple[uuid.UUID, int]:
    try:
        # Create a new job entry in the database
        job = Job()
        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id
        job_dir = os.path.join(UPLOAD_DIR, str(job_id))
        os.makedirs(job_dir, exist_ok=True)

        count = 0
        for file in files:
            contents = await file.read()
            file_path = os.path.join(job_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(contents)
            # Create a FileConversion entry for each file
            file_conversion = FileConversion(file_name=file.filename, job=job)
            db.add(file_conversion)
            db.commit()
            db.refresh(file_conversion)
            process_file_conversion.delay(file_conversion.id, file_path)
            count += 1
        return job_id, count
    except Exception as e:
        print(f"Error handling file upload: {e}")
        db.rollback()
        raise e
