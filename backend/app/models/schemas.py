from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
class Citation(BaseModel):
    source: str
    url: Optional[str] = None
    
class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    geo_json: Optional[dict] = None