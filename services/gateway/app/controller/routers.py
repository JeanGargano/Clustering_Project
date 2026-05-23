import json
import logging
import os
import httpx
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.model.schemas import (
    DocumentUploadResponse,
    JobStatusResponse,
    AnalysisResponse,
    RunClusteringResponse,
)
from services.gateway.app.infra.redis.redis_client import get_client

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
        logger.error(f"Error en data_service: {e.response.text}")
        raise HTTPException(status_code=502, detail="Error al procesar el dataset.")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="data_service no disponible.")


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


# ── 3. Análisis ───────────────────────────────────────────────────────────────
@router.get("/api/jobs/{job_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(job_id: str) -> AnalysisResponse:

    redis = get_client()
    raw   = redis.get(f"job:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Job no encontrado.")

    state = json.loads(raw)

    if state.get("status") != "done":
        raise HTTPException(status_code=400, detail="El clustering aún no ha terminado.")

    if not state.get("analysis"):
        raise HTTPException(status_code=202, detail="Análisis aún no disponible.")

    return AnalysisResponse(
        job_id=job_id,
        status=state.get("analysis_status"),
        analysis=state.get("analysis"),
    )