from fastapi import APIRouter
from pydantic import BaseModel
from app.services.query_parser import parser

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    original: str
    parsed: dict
    status: str

@router.post("/parse", response_model=QueryResponse)
async def parse_query(request: QueryRequest):
    """Endpoint POST untuk parser"""
    result = parser.parse(request.query)

    return QueryResponse(
        original=request.query,
        parsed={
            "location": result.location,
            "radius_km": result.radius_km,
            "keywords": result.keywords
        },
        status="succes"
    )

@router.get("/parse-test")
async def parse_test(query: str):
    """Endpoint GET untuk testing parser"""
    result = parser.parse(query)
    return {
        "input": query,
        "location": result.location,
        "radius_km": result.radius_km,
        "keywords": result.keywords
    }
