from fastapi import APIRouter, HTTPException, Query

from app.services.geocode_service import geocode_service

router = APIRouter()

@router.get("/geocode")
async def geocode_address(address: str = Query(..., description="Nama lokasi")):

    """Convert alamat jadi koordinat GPS"""

    result = await geocode_service.geocode(address)

    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Lokasi '{address}' tidak ditemukan")
    
    return {
        "found": True,
        "address": address,
        "lat": result["lat"],
        "lon": result["lon"],
        "display_name": result.get("display_name", address),
        "source": result.get("source", "nominatim"),
        "maps_url": f"https://www.google.com/maps?q={result['lat']},{result['lon']}"
    }

@router.get("/geocode-reverse")
async def reverse_geocode(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):

    """Convert koordinat menjadi alamat"""

    address = await geocode_service.reverse_geocode(lat, lon)

    if address is None:
        raise HTTPException(status_code=404, detail="Koordinat tidak ditemukan")
    
    return {
        "found": True,
        "lat": lat,
        "lon": lon,
        "adrress": address
    }