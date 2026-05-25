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


async def download_results(result_path: str) -> pd.DataFrame:
    bucket, obj_path = result_path.split("/", 1)
    response = _client.get_object(bucket, obj_path)
    return pd.read_csv(io.BytesIO(response.read()))