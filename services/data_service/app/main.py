from fastapi import FastAPI
from app.controller.Ingest import router

app = FastAPI(title="Data Service")
app.include_router(router)