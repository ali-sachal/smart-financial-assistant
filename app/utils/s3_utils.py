# app/utils/s3_utils.py
"""
S3 utilities for the application platform.

Provides async/sync helpers for uploading, downloading, deleting, and
generating presigned URLs for files stored in AWS S3.

Functions:
  upload_resume_to_s3      — upload a resume PDF (bytes) to S3
  upload_video_to_s3       — upload a rendered video MP4 (file path) to S3
  delete_resume_from_s3    — delete a file by key
  delete_file_from_s3      — delete a file by full URL (used by video factory)
  generate_presigned_url   — generate a presigned URL for private file access
  get_resume_content_from_s3 — retrieve file bytes from S3
  extract_file_key_from_url — parse S3 key from a URL string
  validate_file_size        — check file size against max
  validate_pdf_content      — check if bytes represent a PDF
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Local upload directory fallback
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# S3 client factory
# ---------------------------------------------------------------------------

def get_s3_client():
    """Get S3 client with proper configuration."""
    if not settings.FEATURE_S3 or not settings.S3_usage:
        return None

    if not settings.AWS_S3_BUCKET_NAME:
        return None

    try:
        if hasattr(settings, 'AWS_USE_IAM_ROLE') and settings.AWS_USE_IAM_ROLE:
            s3_client = boto3.client(
                's3',
                region_name=settings.AWS_REGION
            )
        else:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return s3_client
    except Exception as e:
        logger.error(f"[S3] Failed to initialize S3 client: {str(e)}")
        raise


# ---------------------------------------------------------------------------
# Upload helpers
# ---------------------------------------------------------------------------

async def upload_resume_to_s3(
    file_content: bytes,
    file_key: str,
    content_type: str = "application/pdf",
) -> Optional[str]:
    """
    Upload resume file to S3 bucket and return the URL.

    Args:
        file_content: Binary content of the file
        file_key: S3 object key (path/filename)
        content_type: MIME type of the file

    Returns:
        str: Public URL of the uploaded file

    Raises:
        Exception: If upload fails
    """
    try:
        s3_client = get_s3_client()

        if not s3_client:
            logger.warning(f"[S3] AWS S3 not configured. Saving file locally: {file_key}")
            local_path = UPLOAD_DIR / file_key
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, "wb") as f:
                f.write(file_content)

            return None

        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
            ACL='private',
            Metadata={
                'uploaded_by': 'eva_api',
                'file_type': 'resume'
            }
        )

        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"
        else:
            file_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"

        logger.info(f"[S3] Successfully uploaded resume: {file_key}")
        return file_url

    except NoCredentialsError:
        logger.error("[S3] AWS credentials not found")
        raise Exception("AWS credentials not configured")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"[S3] ClientError: {error_code} - {str(e)}")

        if error_code == 'NoSuchBucket':
            raise Exception("S3 bucket not found")
        elif error_code == 'AccessDenied':
            raise Exception("Access denied to S3 bucket")
        else:
            raise Exception(f"Failed to upload to S3: {error_code}")
    except Exception as e:
        logger.error(f"[S3] Unexpected error uploading resume: {str(e)}")
        raise Exception("Failed to upload file to storage")



# ---------------------------------------------------------------------------
# Delete helpers
# ---------------------------------------------------------------------------

async def delete_resume_from_s3(file_key: str) -> bool:
    """
    Delete resume file from S3 bucket.

    Args:
        file_key: S3 object key (path/filename)

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        s3_client = get_s3_client()

        if not s3_client:
            local_path = UPLOAD_DIR / file_key
            if local_path.exists():
                try:
                    os.remove(local_path)
                    logger.info(f"[S3] Deleted local file: {file_key}")
                    return True
                except OSError as e:
                    logger.error(f"[S3] Failed to delete local file: {file_key} - {e}")
                    return False
            logger.warning(f"[S3] Local file not found for deletion: {file_key}")
            return False

        s3_client.delete_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_key
        )

        logger.info(f"[S3] Successfully deleted file from S3: {file_key}")
        return True

    except ClientError as e:
        logger.error(f"[S3] Failed to delete file from S3: {file_key} - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[S3] Unexpected error deleting from S3: {str(e)}")
        return False


# ---------------------------------------------------------------------------
# Presigned URL
# ---------------------------------------------------------------------------

def generate_presigned_url(file_key: str, expiration: int = 3600) -> Optional[str]:
    """
    Generate a presigned URL for secure file access.

    Args:
        file_key: S3 object key (path/filename)
        expiration: URL expiration time in seconds (default: 1 hour)

    Returns:
        str: Presigned URL or None if generation fails
    """
    try:
        s3_client = get_s3_client()

        if not s3_client:
            return None

        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_S3_BUCKET_NAME,
                'Key': file_key
            },
            ExpiresIn=expiration
        )

        return presigned_url

    except ClientError as e:
        logger.error(f"[S3] Failed to generate presigned URL: {file_key} - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[S3] Unexpected error generating presigned URL: {str(e)}")
        return None


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

async def get_resume_content_from_s3(file_key: str) -> Optional[bytes]:
    """
    Retrieve the binary content of a resume file from S3.

    Args:
        file_key: S3 object key (path/filename)

    Returns:
        bytes: Binary content of the file, or None if not found or on error.
    """
    try:
        s3_client = get_s3_client()

        if not s3_client:
            local_path = UPLOAD_DIR / file_key
            if local_path.exists():
                try:
                    with open(local_path, "rb") as f:
                        content = f.read()
                    logger.info(f"[S3] Retrieved content for local file: {file_key}")
                    return content
                except Exception as e:
                    logger.error(f"[S3] Failed to read local file: {file_key} - {e}")
                    return None
            else:
                logger.warning(f"[S3] Local file not found: {file_key}")
                return None

        response = s3_client.get_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_key
        )

        file_content = response['Body'].read()
        logger.info(f"[S3] Retrieved content for file from S3: {file_key}")
        return file_content

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"[S3] File not found in S3: {file_key}")
        else:
            logger.error(f"[S3] Failed to retrieve file content: {file_key} - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"[S3] Unexpected error retrieving file content: {str(e)}")
        return None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def extract_file_key_from_url(url: str) -> Optional[str]:
    """
    Extract S3 file key from a full S3 URL.
    """
    try:
        if not url:
            return None

        if url.startswith("local://"):
            return url.replace("local://", "")

        if 'amazonaws.com' in url:
            parts = url.split('amazonaws.com/')
            if len(parts) > 1:
                return parts[1]
        elif hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN in url:
            parts = url.split(f"{settings.AWS_S3_CUSTOM_DOMAIN}/")
            if len(parts) > 1:
                return parts[1]

        return None

    except Exception as e:
        logger.error(f"[S3] Failed to extract file key from URL: {url} - {str(e)}")
        return None


def validate_file_size(file_content: bytes, max_size: int = 5 * 1024 * 1024) -> bool:
    """
    Validate file size against maximum allowed size.

    Args:
        file_content: Binary content of the file
        max_size: Maximum allowed size in bytes (default: 5MB)

    Returns:
        bool: True if file size is valid, False otherwise
    """
    return len(file_content) <= max_size


def validate_pdf_content(file_content: bytes) -> bool:
    """
    Basic validation to check if file content is a PDF.

    Args:
        file_content: Binary content of the file

    Returns:
        bool: True if content appears to be a PDF, False otherwise
    """
    try:
        return file_content[:4] == b'%PDF'
    except Exception:
        return False
