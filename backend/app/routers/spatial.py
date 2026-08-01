from fastapi import HTTPException, APIRouter, Query
from typing import Optional
import os

from app.services.database import db_service
from app.services.document_loader import DocumentLoader

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
        ("Lahan Padi Palaran", -0.6239, 117.1963, "pertanian", "padi", "Lahan padi 50ha", "alluvial"),
        ("Perkebunan Sawit Sambutan", -0.52, 117.12, "perkebunan", "kelapa_sawit", "Sawit mature", "latosol"),
        ("Lahan Jagung Sungai Kunjang", -0.50, 117.16, "pertanian", "jagung", "Jagung hibrida", "podsolik"),
        ("Kebun Kopi Samarinda Ulu", -0.55, 117.15, "perkebunan", "kopi", "Kopi arabika", "andosol"),
        ("Peternakan Sapi Palaran", -0.47, 117.13, "peternakan", None, "Sapi perah", None),
    ]

    inserted = []
    for place in dummy_places:
        pid = db_service.insert_places(*place)
        inserted.append({"id": pid, "name": place[0]})

    return {
        "message": "Data dummy berhasil dibuat",
        "inserted": inserted,
        "count": len(inserted)
    }

@router.post("/ingest-shapefile-postgis")
async def ingest_shapefile_to_postgis(file_path: str, max_features: int = 500):
    """"Import satu shapefile langsung ke postgis"""
    records = DocumentLoader.load_shapefile_for_postgis(file_path, max_features)

    if not records:
        raise HTTPException(status_code=404, detail="Tidak ada data valid untuk diimport")

    inserted, failed = 0, 0
    for r in records:
        try:
            db_service.insert_gis_layer(r["name"], r["layer_type"], r["geom_wkt"], r["properties"])
            inserted += 1
        except Exception as e:
            failed += 1
            print(f"Skip record error: {e}")

    return {
        "file": file_path,
        "total_records": len(records),
        "inserted": inserted,
        "failed": failed
    }

@router.post("/batch-ingest-shapefile-postgis")
async def batch_ingest_shapefiles_to_postgis(max_features: int = 500):
    files = DocumentLoader.list_local_files()
    shp_files = [f for f in files if f["type"] == "shp"]

    if not shp_files:
        raise HTTPException(status_code=404, detail="Tidak ada file .shp ditemukan")

    results = []
    total_inserted = 0

    for f in shp_files:
        file_path = os.path.join(DocumentLoader.DATA_FOLDER, f["relative_path"])
        try:
            records = DocumentLoader.load_shapefile_for_postgis(file_path, max_features)
            inserted = 0
            for r in records:
                try:
                    db_service.insert_gis_layer(r["name"], r["layer_type"], r["geom_wkt"], r["properties"])
                    inserted += 1
                except Exception as e:
                    print(f"Insert error untuk {r['name']}: {e}")  # ← tambahkan ini
                    continue

            total_inserted += inserted
            results.append({"file": f["name"], "status": "success", "inserted": inserted})
        except Exception as e:
            results.append({"file": f["name"], "status": "error", "error": str(e)})

    return {
        "total_files": len(shp_files),
        "total_inserted": total_inserted,
        "details": results
    }

@router.get("/layers")
async def list_layers():
    """List layer gis yang tersedia"""
    layers = db_service.list_layer_types()
    return {"count": len(layers), "layers": layers}

@router.get("/layers/query")
async def query_layers_at_point(
    lat: float = Query(...), lon: float = Query(...),
    layer_type: Optional[str] = Query(None),
    radius_km: float = Query(10, description="Radius pencarian dalam km")
):
    """Cari layer GIS dalam radius dari titik lokasi tertentu"""
    result = db_service.query_intersecting_layers(lat, lon, layer_type, radius_km)
    return {
        "point": {"lat": lat, "lon": lon},
        "layer_type_filter": layer_type,
        "radius_km": radius_km,
        "count": len(result),
        "layers": result
    }
