from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.pipeline_service import pipeline

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    intent_type: str
    places_found: int
    documents_found: int
    citations: List[dict] = []
    geo_json: Optional[Dict] = None

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint chat conversational
    Ambil pesan terakhir dari user, proses, return jawaban
    """
    last_message = request.messages[-1].content if request.messages else ""

    user_location = None
    if request.user_lat and request.user_lon:
        user_location = {"lat": request.user_lat, "lon": request.user_lon}

    result = await pipeline.process(
        query=last_message,
        user_location=user_location
    )

    return ChatResponse(
        answer=result.answer,
        intent_type=result.intent.type,
        places_found=len(result.spatial_results),
        documents_found=len(result.vector_results),
        citations=result.citations,
        geo_json=result.geo_json
    )