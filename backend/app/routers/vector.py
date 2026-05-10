from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from app.services.chroma_service import chroma_service
from app.services.document_loader import DocumentLoader

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/ingest-dummy")
async def ingest_dummy():
    docs = DocumentLoader.load_dummy()
    result = chroma_service.add_documents(docs)
    return {
        "message": "Data dummy success ingest",
        "count": result["count"]
    }

@router.post("/ingest-shapefile")
async def ingest_shapefile(file_path: str, max_features: int = 500):

    loop = asyncio.get_event_loop()
    docs = await loop.run_in_executor(
        None,
        lambda: DocumentLoader.load_shapefile(file_path, max_features)
    )
    if not docs:
        raise HTTPException(status_code=404, detail="Tidak ada dokumen yang bisa diload")
    
    result = chroma_service.add_documents(docs)
    return {
        "file": file_path,
        "count": result["count"],
        "limit_applied": max_features,
        "sample": docs[0].metadata if docs else None
    }

# PDF Skip untuk baca file gambar, belum implementasi
@router.post("/ingest-pdf")
async def ingest_pdf(file_path: str):
    import asyncio
    loop = asyncio.get_event_loop()
    docs = await loop.run_in_executor(
        None,
        lambda: DocumentLoader.load_pdf(file_path)
    )
    if not docs:
        raise HTTPException(status_code=404, detail="Tidak ada PDF diload")
    
    result = chroma_service.add_documents(docs)

    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["message"])
    
    return {
        "file": file_path,
        "type": "pdf",
        "pages": len(docs),
        "count": result["count"]
    }

@router.post("/ingest-csv")
async def ingest_csv(file_path: str, text_columns: str = None):
    cols = text_columns.split(",") if text_columns else None
    docs = DocumentLoader.load_csv(file_path, cols)

    print(f"Path: {file_path}")
    print(f"Docs loaded: {len(docs)}")
    if docs:
        print(f"Sample: {docs[0].page_content[:100]}")

    if not docs:
        raise HTTPException(status_code=404, detail="CSV tidak dapat diload")
    
    result = chroma_service.add_documents(docs)
    return {
        "file_path": file_path,
        "type": "csv",
        "rows": len(docs),
        "count": result["count"]
    }

@router.post("/ingest-excel")
async def ingest_excel(file_path: str, text_columns: str = None, sheet_name: str = "0"):
    cols = text_columns.split(",") if text_columns else None

    try:
        sheet = int(sheet_name)
    except ValueError:
        sheet = sheet_name

    docs = DocumentLoader.load_excel(file_path, cols, sheet)

    if not docs:
        raise HTTPException(status_code=404, detail="Excel tidak bisa diload")
    
    result = chroma_service.add_documents(docs)
    return {
        "file": file_path,
        "type": "excel",
        "rows": len(docs),
        "count": result["count"]
    }

@router.post("/search")
async def search(request: SearchRequest):
    """Semantci search"""
    result = chroma_service.search(request.query, request.top_k)
    return {
        "query": request.query,
        "results": result,
        "count": len(result)
    }

@router.get("/stats")
async def stats():
    """Statistik ChromaDB"""
    return chroma_service.get_stats()
