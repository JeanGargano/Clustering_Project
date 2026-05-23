import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer

from app.services.clustering import run_clustering
from services.clustering_service.app.infra.minio.minio_client import download_dataframe, upload_results
from services.clustering_service.app.infra.redis.redis_client import get_client
from app.infra.kafka.producer import publish_clustering_done

logger = logging.getLogger(__name__)

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC     = os.getenv("KAFKA_TOPIC_DATASET_READY", "dataset.ready")
GROUP_ID  = "clustering_service"


async def start_consumer():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    logger.info("Consumer iniciado — escuchando dataset.ready")

    try:
        async for msg in consumer:
            asyncio.create_task(_process(msg.value))
    finally:
        await consumer.stop()


async def _process(event: dict):
    job_id     = event["job_id"]
    minio_path = event["minio_path"]
    redis      = get_client()

    try:
        # Marcar como running
        state = json.loads(redis.get(f"job:{job_id}"))
        state["status"] = "running"
        redis.set(f"job:{job_id}", json.dumps(state))

        # Descargar, clustering, subir resultados
        df          = await download_dataframe(minio_path)
        result      = run_clustering(df)
        result_path = await upload_results(result["df_with_labels"], job_id)

        # Actualizar Redis con resultados
        state["status"]      = "done"
        state["metrics"]     = result["metrics"]
        state["centroids"]   = result["centroids"]
        state["result_path"] = result_path
        redis.set(f"job:{job_id}", json.dumps(state))

        # Publicar clustering.done
        await publish_clustering_done(job_id, result_path, result["metrics"])

        logger.info(f"Job {job_id} — clustering done.")

    except Exception as e:
        logger.error(f"Job {job_id} fallido: {e}")
        state = json.loads(redis.get(f"job:{job_id}"))
        state["status"] = "failed"
        state["error"]  = str(e)
        redis.set(f"job:{job_id}", json.dumps(state))