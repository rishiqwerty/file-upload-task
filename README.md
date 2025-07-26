# 📝 Bulk DOCX to PDF Conversion Service
This service allows users to upload multiple .docx files, which are then converted asynchronously to .pdf format using Celery workers. Once all files are converted, they are zipped and a download URL is provided.

### 📟 Tech Stack
- FastAPI – for handling HTTP requests
- Celery – for background task processing
- Redis – as the Celery broker
- PostgreSQL – for job and file metadata
- Docker & Docker Compose – for local development

### 🚀 Features
- Asynchronous file processing
- Bulk .docx to .pdf conversion
- Zipped result download
- S3-backed storage (with local development support)
- REST API to upload and track jobs

### 🗂️ Project Structure
```
.
├── app/
|   ├── api/
│   │   └── v1/                  # Routes
│   │       └── jobs.py          # Routes for jobs
│   │       └── schemas.py
|   ├── database/
│   │   └── base.py
│   │   └── models.py
│   │   └── session.py
|   ├── services/                # utils for file conversion and zipping used by celery
│   │   └── file_conversion_and_zippping.py
│   │   └── file_upload.py
│   │   └── generate_s3_url.py
│   ├── celery.py                 # Celery app
│   ├── config.py                 # Config for env
│   ├── main.py                  # FastAPI app
│   ├── tasks.py
├── database_migrations/         # Track for migrations
├── tests/
├── api.Dockerfile
├── worker.Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### ⚙️ Environment Variables
Create a .env or .envrc.local file in the root directory:
```
# FastAPI
UPLOAD_DIR=./file_upload/data/uploads
BASE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://postgres:password@db:5432/conversion_db

# Redis
REDIS_URL=redis://redis:6379/0

# AWS
S3_BUCKET=<BUCKET_NAME>
USE_S3=true # For using s3 for file upload
```

### 🐳 Running Locally
1. Clone and Configure
```
git clone https://github.com/rishiqwerty/file-upload-task.git
cd file-upload-task
cp .env.example .env
```
2. Start Services
```
docker-compose up -d
```

FastAPI: http://localhost:8088/docs
Redis, Postgres, Celery workers all run via Docker Compose.

### 📥 API Endpoints
- Upload Files:  
**POST /api/v1/jobs/**  
**Content-Type:** multipart/form-data  
**Form Field:** files (multiple .docx files)  

**Response:**
```
{
  "job_id": "uuid",
  "count": 10
}
```
- Check Job Status:  
**GET /status/{job_id}**  
**Response:**  
```
{
  "status": "completed",
  "download_url": "https://.../uuid.zip"
}
```
- Converted .pdf files will be zipped and accessible at:
```
# If hosted on cloud
https://<bucket_name>.s3.amazonaws.com/{job_id}/{job_id}.zip
# Locally
http://localhost:8088/api/v1/{job_id}/download/{job_id}.zip
```

### ☁️ Deploying to AWS
- FastAPI can be deployed using Fargate
- Celery Workers can run on EC2
- Redis running on same EC2 as celery or can be hosted on Elastic cache
- S3 for storing and serving converted files
- IAM Roles
- Ensure EC2 or Fargate task roles have s3:PutObject, s3:GetObject, s3:ListBucket permissions.
- Bucket policy should allow the task role to access the bucket.


### 🛠️ Future Enhancement
- Add retry mechanism in Celery tasks
- Add file size/type validation
- Add expiration or cleanup for old jobs

### Architecture diagram

<img width="641" height="406" alt="Task" src="https://github.com/user-attachments/assets/00a31b4b-db10-463a-9c19-1814bd182ee3" />
