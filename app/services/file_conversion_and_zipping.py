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
    if USE_S3:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                f"{output_dir}",
                f"{docx_path}",
            ],
            capture_output=True,
            text=True,
        )
    else:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "file-upload-task-libreoffice-1",  # container name from compose
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                f"/app/{output_dir}",
                f"/app/{docx_path}",
            ],
            capture_output=True,
            text=True,
        )

    if result.returncode == 0:
        pdf_path = docx_path.replace(".docx", ".pdf")
        return {
            "status": "success",
            "converted_file": f"{output_dir}/{Path(pdf_path).name}",
        }
    return {"status": "error", "error_message": result.stderr}


def file_zip(files: List[str], zip_name: str):
    """
    Create a zip file containing the converted files.
    """

    with zipfile.ZipFile(zip_name, "w") as zipf:
        for file in files:
            zipf.write(file, arcname=Path(file).name)
    return zip_name
