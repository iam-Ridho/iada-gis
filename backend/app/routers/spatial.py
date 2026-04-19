from fastapi import HTTPException, APIRouter, Query
from typing import Optional

from app.services.database import db_service

router = APIRouter()

@router.get("/db-health")
async def database_health():
    """Cek koneksi database"""
    try:
        result = db_service.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@router.get("/places")
async def get_all_places():
    """Ambil data places"""
    places = db_service.get_all_places()
    return {
        "count": len(places),
        "places": places
    }

@router.get("/search-radius")
async def search_radius(lat: float = Query(..., description="Latitude pusat pencarian"), lon: float = Query(..., description="Longitude pusat pencarian"), radius_km: int = Query(5, description="Radius dalam km,"), category: Optional[str] = Query(None, description="Filter Kategori") ):
    """cari lokasi radius dalam titik tertentu"""
    result = db_service.search_places_radius(lat, lon, radius_km, category)
    return {
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "category_filter": category,
        "count": len(result),
        "places": result       
    }

@router.post("/seed-data")
async def seed_dummy_data():
    """Insert data dummy untuk testing"""
    dummy_places = [
        ("Lahan Padi Palaran", -0.48, 117.14, "pertanian", "padi", "Lahan padi 50ha", "alluvial"),
        ("Perkebunan Sawit Sambutan", -0.52, 117.12, "perkebunan", "kelapa_sawit", "Sawit mature", "latosol"),
        ("Lahan Jagung Sungai Kunjang", -0.50, 117.16, "pertanian", "jagung", "Jagung hibrida", "podsolik"),
        ("Kebun Kopi Samarinda Ulu", -0.55, 117.15, "perkebunan", "kopi", "Kopi arabika", "andosol"),
        ("Peternakan Sapi Palaran", -0.47, 117.13, "peternakan", None, "Sapi perah", None),
    ]

    inserted = []
    for place in dummy_places:
        pid = db_service.insert_place(*place)
        inserted.append({"id": pid, "name": place[0]})

    return {
        "message": "Data dummy berhasil dibuat",
        "inserted": inserted,
        "count": len(inserted)
    }