from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.routers import query, geocode, spatial, vector, pipeline

load_dotenv()

app = FastAPI(
    title="IADA-GIS",
    description="IADA with GIS",
    version=os.getenv("API_VERSION", "0.6.0")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(geocode.router, prefix="/api/v1", tags=["Geocoding"])
app.include_router(spatial.router, prefix="/api/v1", tags=["Spatial"])
app.include_router(vector.router, prefix="/api/v1", tags=["Vector"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["Pipeline"])

@app.get("/")
async def root():
    return {"message": "IADA-GIS Backend Running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.6.0",
        "services": {
            "parser": "active",
            "geocoding": "active",
            "database": "active",
            "vector_db": "active",
            "pipeline": "active",
            "llm": "not_connected_yet"
        }
    }
