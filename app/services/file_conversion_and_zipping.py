import os
import time
from typing import List
import zipfile
import subprocess
from pathlib import Path
from app.config import USE_S3


def convert_docx_to_pdf(docx_path: str):
    """
    Process the uploaded file.
    This function is called by the Celery worker to handle the file conversion in the background.
    """
    output_dir = Path(docx_path).parent
    print(f"Converting {output_dir} to PDF in {docx_path}")
    # if USE_S3:
    result = subprocess.run(
        [
            "libreoffice",
            "--invisible",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            f"{output_dir}",
            f"{docx_path}",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        pdf_path = docx_path.replace(".docx", ".pdf")
        time.sleep(0.1)

        return {
            "status": "success",
            "converted_file": f"{output_dir}/{Path(pdf_path).name}",
        }
    time.sleep(0.1)
    return {"status": "error", "error_message": result.stderr}


def file_zip(files: List[str], zip_name: str):
    """
    Create a zip file containing the converted files.
    """

    with zipfile.ZipFile(zip_name, "w") as zipf:
        for file in files:
            zipf.write(file, arcname=Path(file).name)
    return zip_name


def unzip_file(zip_path: str) -> List[str]:
    """
    Unzip the uploaded file and return a list of file paths.
    This function is called by the Celery worker to handle unzipping in the background.
    """
    extracted_files = []
    print(f"Unzipping file: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(os.path.dirname(zip_path))
        import shutil

        shutil.rmtree(os.path.dirname(zip_path) + "/__MACOSX", ignore_errors=True)

        extracted_files = [
            f
            for f in zip_ref.namelist()
            if not f.startswith("__MACOSX/")
            and not f.endswith("/")
            and not f.startswith(".~")
        ]
    return extracted_files
