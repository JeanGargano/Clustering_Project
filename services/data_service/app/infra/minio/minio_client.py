import io
import os
import pandas as pd
from minio import Minio

_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
    access_key=os.getenv("MINIO_ROOT_USER", "admin"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "admin1234"),
    secure=False,
)

BUCKET = os.getenv("MINIO_BUCKET_CLEAN", "clean")


async def upload_dataframe(df: pd.DataFrame, job_id: str) -> str:
    if not _client.bucket_exists(BUCKET):
        _client.make_bucket(BUCKET)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    path = f"{job_id}/clean.csv"

    _client.put_object(
        bucket_name=BUCKET,
        object_name=path,
        data=io.BytesIO(csv_bytes),
        length=len(csv_bytes),
        content_type="text/csv",
    )
    return f"{BUCKET}/{path}"