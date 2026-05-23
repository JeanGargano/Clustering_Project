import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer
from app.services.clustering import run_clustering
from services.clustering_service.app.infra.minio.minio_client import download_dataframe, upload_results
from services.clustering_service.app.infra.redis.redis_client import get_client

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
    logger.info("Consumer Kafka iniciado — escuchando dataset.ready")

    try:
        async for msg in consumer:
            event = msg.value
            job_id     = event["job_id"]
            minio_path = event["minio_path"]
            model_type = event["model_type"] 
            logger.info(f"Job {job_id} recibido — modelo: {model_type}")
            asyncio.create_task(_process(job_id, minio_path, model_type))
    finally:
        await consumer.stop()


async def _process(job_id: str, minio_path: str, model_type: str):
    redis = get_client()
    try:
        # 1. Marcar como running
        redis.set(f"job:{job_id}", json.dumps({"status": "running", "job_id": job_id}))

        # 2. Descargar dataset limpio desde MinIO
        df = await download_dataframe(minio_path)

        # 3. Ejecutar clustering con el modelo elegido
        result = run_clustering(df, model_type)

        # 4. Subir resultados a MinIO
        result_path = await upload_results(result["df_with_labels"], job_id)

        # 5. Actualizar Redis con resultados completos
        redis.set(f"job:{job_id}", json.dumps({
            "job_id":      job_id,
            "status":      "done",
            "model_type":  model_type,
            "result_path": result_path,
            "metrics":     result["metrics"],
            "centroids":   result["centroids"],
        }))

        logger.info(f"Job {job_id} completado.")

    except Exception as e:
        logger.error(f"Job {job_id} fallido: {e}")
        redis.set(f"job:{job_id}", json.dumps({
            "job_id":  job_id,
            "status":  "failed",
            "error":   str(e),
        }))