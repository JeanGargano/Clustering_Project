import json
import logging

from app.services.clustering import run_clustering
from app.infra.kafka.producer import publish_clustering_done
from app.infra.minio.minio_client import (
    download_dataframe,
    upload_results
)
from app.infra.redis.redis_client import get_client

logger = logging.getLogger(__name__)


async def process(event: dict):

    job_id = event["job_id"]
    minio_path = event["minio_path"]

    redis = get_client()

    try:

        # Estado inicial
        raw = redis.get(f"job:{job_id}")

        state = json.loads(raw)

        state["status"] = "running"

        redis.set(
            f"job:{job_id}",
            json.dumps(state)
        )

        # Descargar dataset
        df = await download_dataframe(minio_path)

        # Clustering
        result = run_clustering(df)

        # Guardar resultados
        result_path = await upload_results(
            result["df_with_labels"],
            job_id
        )
        #logger.info(result_path)

        # Recuperar estado actualizado
        raw = redis.get(f"job:{job_id}")

        state = json.loads(raw)

        state["status"] = "done"

        # Inicializar runs
        if "runs" not in state or state["runs"] is None:
            state["runs"] = {}

        # Resultado GMM
        state["runs"]["gmm"] = {
            "status": "done",
            "metrics": result["metrics"],
            "centroids": result["centroids"],
            "result_path": result_path,
            "analysis": None
        }

        # Persistir estado 
        redis.set(
            f"job:{job_id}",
            json.dumps(state)
        )

        # Evento Kafka
        await publish_clustering_done(
            job_id,
            result_path,
            result["metrics"]
        )

        logger.info(
            f"Job {job_id} — clustering done."
        )

    except Exception as e:

        logger.error(
            f"Job {job_id} fallido: {e}"
        )

        try:

            raw = redis.get(f"job:{job_id}")

            if raw:

                state = json.loads(raw)

                state["status"] = "failed"

                state["error"] = str(e)

                redis.set(
                    f"job:{job_id}",
                    json.dumps(state)
                )

        except Exception as redis_error:

            logger.error(
                f"Error actualizando Redis en fallo: {redis_error}"
            )