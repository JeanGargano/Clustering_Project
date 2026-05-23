import json
import os
from aiokafka import AIOKafkaProducer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC     = os.getenv("KAFKA_TOPIC_CLUSTERING_DONE", "clustering.done")


async def publish_clustering_done(
    job_id: str, result_path: str, metrics: dict
) -> None:
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()
    try:
        message = {
            "job_id":      job_id,
            "result_path": result_path,
            "metrics":     metrics,
        }
        await producer.send_and_wait(TOPIC, json.dumps(message).encode())
    finally:
        await producer.stop()