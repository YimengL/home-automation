import logging
from pathlib import Path
from home_automation import keychain

import boto3

logger = logging.getLogger(__name__)


def _client(account_id: str, key_id_service: str, secret_service: str):
    """Generate a boto3 S3-compatible client for R2."""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=keychain.get_token(key_id_service),
        aws_secret_access_key=keychain.get_token(secret_service),
        region_name="weur"
    )


def upload(pdf_path: Path, doc: dict, account_id: str, bucket_name: str, key_id_service: str, secret_service: str) -> str:
    """Upload proc_*.pdf to R2. Returns the R2 object key."""
    key = f"{doc['date']}/{pdf_path.name}"
    
    _client(account_id, key_id_service, secret_service).upload_file(str(pdf_path), bucket_name, key)
    logger.info("R2 upload OK: %s", key)
    return key


def presign(key: str, account_id: str, bucket_name: str,
            key_id_service: str, secret_service: str, expiry: int = 604800) -> str:
    """Generate a 7-day presigned URL for an R2 object."""
    client = _client(account_id, key_id_service, secret_service)

    return client.generate_presigned_url("get_object",
                                         Params={"Bucket": bucket_name, "Key": key},
                                         ExpiresIn=expiry,)
