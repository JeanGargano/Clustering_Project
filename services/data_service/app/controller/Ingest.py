import io
import json
import uuid
import logging
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.service.pipeline import run_pipeline
from app.service.kafka_producer import publish_dataset_ready
from app.infra.minio.minio_client import upload_dataframe
from app.infra.redis.redis_client import get_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest")
async def ingest_dataset(file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV.")

    job_id = str(uuid.uuid4())
    redis  = get_client()
    logger.info(f"Job {job_id} — recibido: {file.filename}")

    try:
        contents   = await file.read()
        df         = pd.read_csv(io.BytesIO(contents))
        df_clean   = run_pipeline(df)
        minio_path = await upload_dataframe(df_clean, job_id)

        redis.set(f"job:{job_id}", json.dumps({
            "job_id":          job_id,
            "filename":        file.filename,
            "status_cleaning": "done",
            "minio_path":      minio_path,
            "status":          "queued",
        }))

        await publish_dataset_ready(job_id, minio_path)

        logger.info(f"Job {job_id} publicado en Kafka.")
        return {"job_id": job_id, "filename": file.filename, "status": "queued"}

    except Exception as e:
        logger.error(f"Error en job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))