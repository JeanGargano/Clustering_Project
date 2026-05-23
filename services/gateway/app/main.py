import logging
from fastapi import FastAPI
from app.controller.routers import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Clustering IoT — Gateway",
    description="Punto de entrada del sistema de análisis de ciberataques IoT",
    version="2.0.0",
)

app.include_router(router)