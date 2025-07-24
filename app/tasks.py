import uuid
from app.database.models import FileConversion, Job, JobStatusEnum
from app.database.session import SessionLocal
from app.services.file_conversion_and_zipping import convert_docx_to_pdf, file_zip
from celery import shared_task
from pathlib import Path
import os
from app.celery import celery_app


@shared_task
def process_file_conversion(file_id: uuid.UUID, file_path: str):
    """
    Celery task to convert a DOCX file to PDF.
    This function is called by the Celery worker to handle the file conversion in the background.
    """
    session = SessionLocal()
    try:
        file_to_convert = (
            session.query(FileConversion).filter(FileConversion.id == file_id).first()
        )
        result = convert_docx_to_pdf(file_path)
        if result["status"] == "success":
            file_to_convert.status = JobStatusEnum.completed
            file_to_convert.output_file_path = result["converted_file"]
            file_to_convert.error_message = None
        else:
            file_to_convert.status = JobStatusEnum.failed
            file_to_convert.error_message = result["error_message"]
        session.commit()

        job = file_to_convert.job
        all_done = all(
            f.status in ["completed", "failed"] for f in job.file_conversions
        )

        if all_done:
            zip_converted_files.delay(str(job.id))

    finally:
        session.close()


@shared_task
def zip_converted_files(job_id: uuid.UUID):
    """
    Celery task to zip all converted files for a job.
    This function is called by the Celery worker to create a zip file of all converted files.
    """
    session = SessionLocal()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        converted_files = [
            fc.output_file_path
            for fc in job.file_conversions
            if fc.status == JobStatusEnum.completed
        ]
        if not converted_files:
            return

        zip_name = f"{Path(converted_files[0]).parent}/{job_id}.zip"
        zip_path = file_zip(converted_files, zip_name)
        BASE_STATIC_URL = os.getenv("STATIC_BASE_URL", "http://localhost:8088/static")
        job.download_url = f"{BASE_STATIC_URL}/{job_id}/{job_id}.zip"

        job.status = JobStatusEnum.completed
        session.commit()
    finally:
        session.close()
