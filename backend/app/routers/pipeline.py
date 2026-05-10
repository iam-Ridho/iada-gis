from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.services.pipeline_service import pipeline, Pipelineresult

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None

class QueryResponse(BaseModel):
    query: str
    intent_type: str
    location: Optional[Dict]
    spatial_count: int
    vector_count: int
    context: str
    places: List[Dict]
    documents: List[Dict]


@router.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    """
    Endpoint utama: User kirim query natural language, 
    sistem proses penuh dan kembalikan context + hasil
    
    Contoh query:
    - "cari lahan padi dalam 10 km dari Palaran"
    - "bagaimana cara budidaya kelapa sawit di Samarinda"
    - "peternakan sapi terdekat dari lokasi saya"
    """

    try:
        # Build user location
        user_location = None
        if request.user_lat and request.user_lon:
            user_location = {"lat": request.user_lat, "lon": request.user_lon}

        # Jalankan Pipeline
        result = await pipeline.process(
            query=request.query,
            user_location=user_location
        )

        # Format response
        return QueryResponse(
            query=result.query_original,
            intent_type=result.intent.type,
            location=result.location,
            spatial_count=len(result.spatial_results),
            vector_count=len(result.vector_results),
            context=result.context,
            places=result.spatial_results,
            documents=result.vector_results
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/ask-simple")
async def ask_simple(query: str, user_lat: Optional[float] = None, user_lon: Optional[float] = None):
    """
    Versi simple untuk testing dari browser/query params
    
    Contoh: /api/v1/ask-simple?query=cari+lahan+padi+dekat+Palaran
    """
    request = QueryRequest(query=query, user_lat=user_lat, user_lon=user_lon)
    return await ask(request)

@router.get("/pipeline-debug")
async def pipeline_debug():
    return {
        "pipeline_status": "active",
        "components": {
            "parser": "active",
            "geocoder": "active",
            "spatial_db": "active",
            "vector_db": "active"
        },
        "sample_queries": [
            "cari lahan padi dalam 10 km dari Palaran",
            "bagaimana cara budidaya kelapa sawit",
            "peternakan sapi terdekat dari Samarinda Ulu"
        ]
    }