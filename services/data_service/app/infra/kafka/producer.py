import json
import os
from aiokafka import AIOKafkaProducer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC     = os.getenv("KAFKA_TOPIC_DATASET_READY", "dataset.ready")


async def publish_dataset_ready(job_id: str, minio_path: str) -> None:
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()
    try:
        message = {"job_id": job_id, "minio_path": minio_path}
        await producer.send_and_wait(TOPIC, json.dumps(message).encode())
    finally:
        await producer.stop()