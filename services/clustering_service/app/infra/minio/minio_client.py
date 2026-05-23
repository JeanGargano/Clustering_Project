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

BUCKET_CLEAN   = os.getenv("MINIO_BUCKET_CLEAN", "clean")
BUCKET_RESULTS = os.getenv("MINIO_BUCKET_RESULTS", "results")


async def download_dataframe(minio_path: str) -> pd.DataFrame:
    bucket, obj_path = minio_path.split("/", 1)
    response = _client.get_object(bucket, obj_path)
    return pd.read_csv(io.BytesIO(response.read()))


async def upload_results(df: pd.DataFrame, job_id: str) -> str:
    if not _client.bucket_exists(BUCKET_RESULTS):
        _client.make_bucket(BUCKET_RESULTS)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    path = f"{job_id}/results.csv"

    _client.put_object(
        bucket_name=BUCKET_RESULTS,
        object_name=path,
        data=io.BytesIO(csv_bytes),
        length=len(csv_bytes),
        content_type="text/csv",
    )
    return f"{BUCKET_RESULTS}/{path}"