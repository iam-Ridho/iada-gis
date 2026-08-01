from fastapi import APIRouter
from app.services.batch_ingest import BatchIngestion

router = APIRouter()

@router.post("/batch-ingest")
async def batch_ingest_all(max_features_shp: int = 500):
    """Ingest semua file di folder data/ sekaligus"""
    result = BatchIngestion.ingest_all(max_features_shp=max_features_shp)
    return result

@router.get("/list-files")
async def list_available_files():
    """Lihat semua file yang tersedia di folder data/ sebelum ingest"""
    from app.services.document_loader import DocumentLoader
    files = DocumentLoader.list_local_files()
    return {
        "count": len(files),
        "files": files
    }