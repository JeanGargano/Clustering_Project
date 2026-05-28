import json
import logging
import pandas as pd

from app.services.clustering import run_clustering
from app.infra.kafka.producer import publish_clustering_done
from app.infra.minio.minio_client import upload_results
from app.infra.redis.redis_client import get_client

logger = logging.getLogger(__name__)


async def process(df: pd.DataFrame, event: dict):

    job_id = event["job_id"]
    redis  = get_client()

    try:
        # Marcar como running
        raw   = redis.get(f"job:{job_id}")
        state = json.loads(raw)
        state["status"] = "running"
        redis.set(f"job:{job_id}", json.dumps(state))

        # Clustering
        result = run_clustering(df)

        # Persistir resultados en MinIO
        result_path = await upload_results(result["df_with_labels"], job_id)

        # Actualizar estado
        raw   = redis.get(f"job:{job_id}")
        state = json.loads(raw)
        state["status"] = "done"
        state.setdefault("runs", {})["kmeans"] = {
            "status":      "done",
            "metrics":     result["metrics"],
            "centroids":   result["centroids"],
            "result_path": result_path,
            "analysis":    None,
        }
        redis.set(f"job:{job_id}", json.dumps(state))

        # Publicar evento Kafka
        await publish_clustering_done(job_id, result_path, result["metrics"])

        logger.info(f"Job {job_id} — clustering done.")

    except Exception as e:
        logger.error(f"Job {job_id} fallido: {e}")
        try:
            raw = redis.get(f"job:{job_id}")
            if raw:
                state = json.loads(raw)
                state["status"] = "failed"
                state["error"]  = str(e)
                redis.set(f"job:{job_id}", json.dumps(state))
        except Exception as redis_error:
            logger.error(f"Error actualizando Redis en fallo: {redis_error}")

        raise  