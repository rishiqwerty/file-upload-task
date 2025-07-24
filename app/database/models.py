from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from datetime import datetime
import uuid
from app.database.base import Base
import enum


class JobStatusEnum(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.pending)
    created_at = Column(DateTime, default=datetime.now)
    download_url = Column(String, nullable=True)
    file_conversions = relationship(
        "FileConversion", back_populates="job", cascade="all, delete-orphan"
    )


class FileConversion(Base):
    __tablename__ = "file_conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job = relationship("Job", back_populates="file_conversions")
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    file_name = Column(String, nullable=False)
    output_file_path = Column(String, nullable=True)
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.pending)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
