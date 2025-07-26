import os

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")  # Directory for local file uploads
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"  # Use S3 for file storage
S3_BUCKET_NAME = os.getenv("S3_BUCKET", "upload")  # bucket name of S3 storage
STATIC_BASE_URL = os.getenv(
    "STATIC_BASE_URL", "http://localhost:8088"
)  # Base URL for static files for local
USE_PRESIGNED_URL = (
    os.getenv("USE_S3_PRESIGNED_URL", "false").lower() == "true"
)  # Use presigned URLs for S3 access
