import json
import logging
import os
import httpx
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from app.infra.minio.minio_client import generate_presigned_url

from app.model.schemas import (
    DocumentUploadResponse,
    JobStatusResponse,
    AnalysisResponse,
    RunClusteringResponse,
)
from app.infra.redis.redis_client import get_client

logger = logging.getLogger(__name__)
router = APIRouter()

DATA_SERVICE_URL       = os.getenv("DATA_SERVICE_URL", "http://data_service:8002")



# ── 1. Ingesta ────────────────────────────────────────────────────────────────
@router.post("/api/ingest", response_model=DocumentUploadResponse)
async def ingest_dataset(file: UploadFile = File(...)) -> DocumentUploadResponse:

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV.")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{DATA_SERVICE_URL}/ingest",
                files={"file": (file.filename, await file.read(), "text/csv")},
            )
            response.raise_for_status()

        data = response.json()
        logger.info(f"Ingesta completada — job_id: {data['job_id']}")
        return DocumentUploadResponse(**data)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTPStatusError: {e.response.status_code}")
        logger.error(f"Response: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"RequestError: {repr(e)}")
        raise HTTPException(status_code=503, detail=str(e))


# ── 2. Polling ────────────────────────────────────────────────────────────────
@router.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:

    redis = get_client()
    raw   = redis.get(f"job:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Job no encontrado.")

    data = json.loads(raw)
    logger.info(f"Polling job {job_id} — status: {data['status']}")
    return JobStatusResponse(**data)



# ── 3. Resultados del clustering ──────────────────────────────────────────────
@router.get("/api/jobs/{job_id}/results")
async def get_results(job_id: str):

    redis = get_client()
    raw   = redis.get(f"job:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Job no encontrado.")

    state   = json.loads(raw)
    gmm_run = state.get("runs", {}).get("gmm")

    if not gmm_run:
        raise HTTPException(status_code=404, detail="Run GMM no encontrado.")

    if gmm_run.get("status") != "done":
        raise HTTPException(status_code=400, detail="El clustering aún no ha terminado.")

    result_path = gmm_run.get("result_path")
    if not result_path:
        raise HTTPException(status_code=404, detail="Ruta de resultados no encontrada.")

    url = generate_presigned_url(result_path)

    return {
        "job_id":       job_id,
        "download_url": url,
        "expires_in":   "1 hora",
        "metrics":      gmm_run.get("metrics"),
        "centroids":    gmm_run.get("centroids"),
    }