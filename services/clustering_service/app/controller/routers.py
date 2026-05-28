import io
import json
import uuid
import logging
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.process import process
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
        minio_path = await upload_dataframe(df, job_id)

        state = {
            "job_id":     job_id,
            "filename":   file.filename,
            "minio_path": minio_path,
            "status":     "queued",
        }
        redis.set(f"job:{job_id}", json.dumps(state))

        await process(df, state)

        logger.info(f"Job {job_id} procesado.")
        return {"job_id": job_id, "filename": file.filename, "status": "queued"}

    except Exception as e:
        logger.error(f"Error en job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))