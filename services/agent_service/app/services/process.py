import json
import logging

from app.services.prompt_builder import build_prompt
from app.infra.llm.llm_client import call_llm
from app.infra.minio.minio_client import download_results
from app.infra.redis.redis_client import get_client

logger = logging.getLogger(__name__)


async def process(event: dict):

    job_id = event["job_id"]
    result_path = event["result_path"]
    metrics = event["metrics"]

    redis = get_client()

    try:

        # Obtener estado actual 
        raw = redis.get(f"job:{job_id}")

        if not raw:
            raise ValueError(
                f"Job {job_id} no encontrado en Redis."
            )

        state = json.loads(raw)

        # Inicializar runs si no existe 
        if "runs" not in state or state["runs"] is None:
            state["runs"] = {}

        if "gmm" not in state["runs"]:
            state["runs"]["gmm"] = {}

        # Marcar análisis como running
        state["runs"]["gmm"]["analysis_status"] = "running"

        redis.set(
            f"job:{job_id}",
            json.dumps(state)
        )

        # Descargar resultados clustering
        df = await download_results(result_path)

        # Construir prompt
        prompt = build_prompt(df, metrics)

        # Llamada al LLM
        analysis = await call_llm(prompt)

        # Leer estado fresco nuevamente
        raw = redis.get(f"job:{job_id}")

        state = json.loads(raw)

        # Guardar análisis
        state["runs"]["gmm"]["analysis_status"] = "done"

        state["runs"]["gmm"]["analysis"] = analysis

        redis.set(
            f"job:{job_id}",
            json.dumps(state)
        )

        logger.info(
            f"Análisis completado — job_id: {job_id}"
        )

    except Exception as e:

        logger.error(
            f"Error en análisis job {job_id}: {e}"
        )

        try:

            raw = redis.get(f"job:{job_id}")

            if raw:

                state = json.loads(raw)

                if "runs" not in state or state["runs"] is None:
                    state["runs"] = {}

                if "gmm" not in state["runs"]:
                    state["runs"]["gmm"] = {}

                state["runs"]["gmm"]["analysis_status"] = "failed"

                state["runs"]["gmm"]["analysis_error"] = str(e)

                redis.set(
                    f"job:{job_id}",
                    json.dumps(state)
                )

        except Exception as redis_error:

            logger.error(
                f"Error actualizando Redis en fallo: {redis_error}"
            )