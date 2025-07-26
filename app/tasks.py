import uuid
from app.database.models import FileConversion, Job, JobStatusEnum
from app.database.session import SessionLocal
from app.services.file_conversion_and_zipping import convert_docx_to_pdf, file_zip
from app.services.generate_s3_url import generate_presigned_url
from celery import shared_task
from pathlib import Path
import os
from app.celery import celery_app
from app.config import USE_S3, S3_BUCKET_NAME, BASE_URL
import boto3
import tempfile


s3 = boto3.client("s3")


@shared_task
def process_file_conversion(file_id: uuid.UUID, file_path: str):
    """
    Celery task to convert a DOCX file to PDF.
    Supports both local and S3 file paths.
    """
    session = SessionLocal()
    temp_docx_path = ""
    try:
        file_to_convert = (
            session.query(FileConversion).filter(FileConversion.id == file_id).first()
        )
        # If Its prod, store in S3 else store locally
        if USE_S3:
            s3_key = file_path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx:
                s3.download_fileobj(S3_BUCKET_NAME, s3_key, temp_docx)
                temp_docx_path = temp_docx.name
        else:
            temp_docx_path = file_path

        # Convert docx to pdf
        result = convert_docx_to_pdf(temp_docx_path)
        print(f"Conversion result: {result}")
        if result["status"] == "success":
            file_to_convert.status = JobStatusEnum.completed

            if USE_S3:
                # Upload result PDF to S3
                converted_path = result["converted_file"]
                s3_key_out = f"{file_to_convert.job_id}/converted/{os.path.basename(converted_path)}"
                with open(converted_path, "rb") as f:
                    s3.upload_fileobj(f, S3_BUCKET_NAME, s3_key_out)
                file_to_convert.output_file_path = s3_key_out
            else:
                file_to_convert.output_file_path = result["converted_file"]

            file_to_convert.error_message = None
        else:
            file_to_convert.status = JobStatusEnum.failed
            file_to_convert.error_message = result["error_message"]

        session.commit()

        # If all files are done, trigger zipping
        job = file_to_convert.job
        all_done = all(
            f.status in [JobStatusEnum.completed, JobStatusEnum.failed]
            for f in job.file_conversions
        )
        if all_done:
            zip_converted_files.delay(str(job.id))

    except Exception as e:
        session.rollback()
        print(f"Error in process_file_conversion: {e}")
    finally:
        session.close()

        # Clean up temp files
        if USE_S3 and os.path.exists(temp_docx_path):
            os.remove(temp_docx_path)


@shared_task
def zip_converted_files(job_id: uuid.UUID):
    """
    Celery task to zip all converted files for a job.
    Supports both local and S3 storage.
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

        if USE_S3:
            # Download all files locally into a temp dir
            with tempfile.TemporaryDirectory() as temp_dir:
                local_paths = []
                for s3_key in converted_files:
                    local_file_path = os.path.join(temp_dir, os.path.basename(s3_key))
                    with open(local_file_path, "wb") as f:
                        s3.download_fileobj(S3_BUCKET_NAME, s3_key, f)
                    local_paths.append(local_file_path)

                # Zip them
                zip_path = os.path.join(temp_dir, f"{job_id}.zip")
                file_zip(local_paths, zip_path)

                # Upload zip
                zip_s3_key = f"{job_id}/{job_id}.zip"
                with open(zip_path, "rb") as f:
                    s3.upload_fileobj(f, S3_BUCKET_NAME, zip_s3_key)

                # Set URL
                BASE_STATIC_URL = os.getenv(
                    "STATIC_BASE_URL", f"https://{S3_BUCKET_NAME}.s3.amazonaws.com"
                )
                job.download_url = f"{BASE_STATIC_URL}/{zip_s3_key}"
        else:
            # Local mode
            zip_name = f"{Path(converted_files[0]).parent}/{job_id}.zip"
            zip_path = file_zip(converted_files, zip_name)

            url = f"http://{BASE_URL}/api/v1/jobs/{job_id}/download"
            job.download_url = url

        job.status = JobStatusEnum.completed
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Error in zip_converted_files: {e}")
    finally:
        session.close()
