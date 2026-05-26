import os
from minio import Minio
from datetime import timedelta

_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
    access_key=os.getenv("MINIO_ROOT_USER", "admin"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "admin1234"),
    secure=False,
)


def generate_presigned_url(result_path: str, expires_hours: int = 1) -> str:
    # result_path viene como "results/abc-111/results.csv"
    bucket, obj_path = result_path.split("/", 1)

    url = _client.presigned_get_object(
        bucket_name=bucket,
        object_name=obj_path,
        expires=timedelta(hours=expires_hours),
    )
    return url