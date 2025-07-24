from fastapi.testclient import TestClient
from app.main import app
import tempfile
from unittest.mock import MagicMock, patch
from app.database.models import Job

client = TestClient(app)


def test_upload_files(monkeypatch):
    """Test the file upload endpoint with multiple files."""
    with patch(
        "app.services.file_upload.process_file_conversion"
    ) as mock_process_file_conversion:
        mock_process_file_conversion.return_value = None
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("UPLOAD_DIR", tmpdir)
            files = [
                (
                    "files",
                    (
                        "test1.docx",
                        b"Dummy content",
                    ),
                ),
                (
                    "files",
                    (
                        "test2.docx",
                        b"More content",
                    ),
                ),
            ]
            response = client.post("/api/v1/jobs", files=files)
            assert response.status_code == 202
            assert "job_id" in response.json()


def test_upload_no_files():
    """Test the file upload endpoint with no files."""
    response = client.post("/api/v1/jobs", files=[])
    assert response.status_code == 422
