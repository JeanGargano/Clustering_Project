import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer
from app.services.process import process    

logger = logging.getLogger(__name__)

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC     = os.getenv("KAFKA_TOPIC_CLUSTERING_DONE", "clustering.done")
GROUP_ID  = "agent_service"


async def _safe_process(event: dict):
    try:
        await process(event)
    except Exception as e:
        logger.error(f"Error no capturado en task: {e}")


async def start_consumer():
    while True:
        try:
            consumer = AIOKafkaConsumer(
                TOPIC,
                bootstrap_servers=BOOTSTRAP,
                group_id=GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            await consumer.start()
            logger.info(f"Consumer iniciado — escuchando {TOPIC}")
            break 
        except Exception as e:
            logger.warning(f"Kafka no disponible, reintentando en 5s... ({e})")
            await asyncio.sleep(5)

    try:
        async for msg in consumer:
            asyncio.create_task(_safe_process(msg.value))
    finally:
        await consumer.stop()