import uuid
import os
from typing import List
from fastapi import UploadFile
# from app.services.tasks import enqueue_conversion_job

UPLOAD_DIR = "file_upload/data/uploads"

async def handle_file_upload(files: List[UploadFile]) -> str:
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    count = 0
    for file in files:
        contents = await file.read()
        file_path = os.path.join(job_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        count += 1

    # enqueue async conversion job
    # enqueue_conversion_job.delay(job_id)

    return job_id, count
