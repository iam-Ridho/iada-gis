import httpx
from typing import Tuple, Optional

class NominatimService:
    """Geocoding dengan openstreetmap"""

    BASE_URL = "https://nominatim.openstreetmap.org/search"

    async def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert alamat menjadi langtitude dan longtitude"""

        search_query = f"{address}, East Kalimantan, Indonesia"

        params = {
            "q": search_query,
            "format": "json",
            "limit": 1
        }

        headers = {
            "User-Agent": "IADA-GIS/0.1 (mhdrdh2006@gmail.com)"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    timeout=10.0
                )

                data = response.json()

                if data and len(data) > 0:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return lat,lon
                
                return None
            
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
        
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert koordinat menjadi alamat"""        
        url = "https://nominatim.openstreetmap.org/reverse"

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }

        headers = {"User-Agent": "IADA-GIS/0.1"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            return data.get("display_name")

geocode_service = NominatimService()
