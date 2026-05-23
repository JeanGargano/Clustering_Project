import asyncio
import logging
from fastapi import FastAPI
from app.infra.kafka.consumer import start_consumer

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Agent Service")

@app.on_event("startup")
async def startup():
    asyncio.create_task(start_consumer())