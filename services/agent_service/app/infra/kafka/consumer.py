import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer

from app.services.prompt_builder import build_prompt
from services.agent_service.app.infra.llm.llm_client import call_llm
from app.infra.minio_client import download_results
from app.infra.redis_client import get_client

logger = logging.getLogger(__name__)

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC     = os.getenv("KAFKA_TOPIC_CLUSTERING_DONE", "clustering.done")
GROUP_ID  = "agent_service"


async def start_consumer():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    logger.info("Consumer iniciado — escuchando clustering.done")

    try:
        async for msg in consumer:
            asyncio.create_task(_process(msg.value))
    finally:
        await consumer.stop()


async def _process(event: dict):
    job_id      = event["job_id"]
    result_path = event["result_path"]
    metrics     = event["metrics"]
    redis       = get_client()

    try:
        state = json.loads(redis.get(f"job:{job_id}"))
        state["analysis_status"] = "running"
        redis.set(f"job:{job_id}", json.dumps(state))

        df       = await download_results(result_path)
        prompt   = build_prompt(df, metrics)
        analysis = await call_llm(prompt)

        state = json.loads(redis.get(f"job:{job_id}"))
        state["analysis_status"] = "done"
        state["analysis"]        = analysis
        redis.set(f"job:{job_id}", json.dumps(state))

        logger.info(f"Análisis completado — job_id: {job_id}")

    except Exception as e:
        logger.error(f"Error en análisis job {job_id}: {e}")
        state = json.loads(redis.get(f"job:{job_id}"))
        state["analysis_status"] = "failed"
        state["analysis_error"]  = str(e)
        redis.set(f"job:{job_id}", json.dumps(state))