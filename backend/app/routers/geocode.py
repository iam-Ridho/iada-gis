from fastapi import APIRouter, HTTPException, Query

from app.services.geocode_service import geocode_service

router = APIRouter()

@router.get("/geocode")
async def geocode_address(address: str = Query(..., description="Nama lokasi")):

    """Convert alamat jadi koordinat GPS"""

    result = await geocode_service.geocode(address)

    if result is None:
        raise HTTPException(status_code=404, detail=f"Lokasi '{address}' tidak ditemukan")
    
    lat, lon = result
    return {
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "source": "nominatim",
        "maps_url": f"https://www.google.com/maps?q={lat},{lon}"
    }

@router.get("/geocode-reverse")
async def reverse_geocode(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):

    """Convert koordinat menjadi alamat"""

    address = await geocode_service.reverse_geocode(lat, lon)

    if address is None:
        raise HTTPException(status_code=404, detail="Koordinat tidak ditemukan")
    
    return {
        "latitude": lat,
        "longitude": lon,
        "adrress": address
    }