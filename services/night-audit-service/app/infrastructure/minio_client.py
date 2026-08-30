"""Client S3-compatible (MinIO) — archivage des rapports PDF (D12). `boto3`
plutôt que le SDK `minio` officiel : bibliothèque S3 la plus répandue, le
protocole S3 de MinIO est compatible telle quelle (path-style addressing)."""

from __future__ import annotations

import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    return _client


def _ensure_bucket_sync() -> None:
    client = _get_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.minio_bucket)


def _upload_sync(key: str, data: bytes) -> None:
    _ensure_bucket_sync()
    _get_client().put_object(Bucket=settings.minio_bucket, Key=key, Body=data, ContentType="application/pdf")


async def upload_report(establishment_id: str, business_date: str, filename: str, data: bytes) -> str:
    """Chemin spec ligne 623 : `{hotel_id}/audit/{date}/{rapport}.pdf` — UUID
    d'établissement à la place du `hotel_id` littéral (cohérence D12)."""
    key = f"{establishment_id}/audit/{business_date}/{filename}"
    await asyncio.to_thread(_upload_sync, key, data)
    return f"{settings.minio_endpoint_url}/{settings.minio_bucket}/{key}"


def _get_report_sync(key: str) -> bytes:
    return _get_client().get_object(Bucket=settings.minio_bucket, Key=key)["Body"].read()


async def get_report(establishment_id: str, business_date: str, filename: str) -> bytes:
    """Lecture directe (bucket privé, pas d'URL publique) — le bearer token
    de l'utilisateur authentifie déjà `/reports/...`, MinIO n'a pas besoin de
    ses propres credentials exposées au navigateur (cf. D12)."""
    key = f"{establishment_id}/audit/{business_date}/{filename}"
    return await asyncio.to_thread(_get_report_sync, key)
