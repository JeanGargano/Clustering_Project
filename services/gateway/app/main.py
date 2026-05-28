import logging
from fastapi import FastAPI
from app.controller.routers import router
from fastapi.middleware.cors import CORSMiddleware





# ... (aquí abajo continúan las rutas que ya tienes, como app.include_router(...))

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Clustering IoT — Gateway",
    description="Punto de entrada del sistema de análisis de ciberataques IoT",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Permite el origen de tu React
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Permite todos los headers
)

app.include_router(router)