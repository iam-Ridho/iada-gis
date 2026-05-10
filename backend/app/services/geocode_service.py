# pyrefly: ignore [missing-import]
import httpx
from typing import Dict, Optional

class NominatimService:
    """Geocoding dengan openstreetmap"""

    BASE_URL = "https://nominatim.openstreetmap.org/search"

    # Fallback koordinat
    KNOWN_COORDINATES = {
        'palaran': (-0.6239518, 117.1962968),
        'samarinda': (-0.4917013, 117.1458991),
        'samarinda ulu': (-0.45, 117.15),
        'sungai kunjang': (-0.50, 117.16),
        'sambutan': (-0.52, 117.12),
        'bontang': (0.12, 117.50),
        'balikpapan': (-1.27, 116.83),
        'kutai kartanegara': (-0.13, 116.60),
        'tenggarong': (-0.40, 117.00),
    }

    async def geocode(self, address: str) -> Dict:
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
                response.raise_for_status()

                data = response.json()

                if data and len(data) > 0:
                    return {
                        "found": True,
                        "lat": float(data[0]["lat"]),
                        "lon": float(data[0]["lon"]),
                        "display_name": data[0].get("display_name", address)
                    }
                
                return self._fallback(address)
            
        except Exception as e:
            print(f"Geocoding error: {e}")
            return self._fallback(address)
        
    def _fallback(self, address: str) -> Dict:
        key = address.lower().strip()
        if key in self.KNOWN_COORDINATES:
            lat, lon = self.KNOWN_COORDINATES[key]
            print(f"Using fallback for '{address}': {lat}, {lon}")
            return {
                "found": False,
                "lat": lat,
                "lon": lon,
                "display_name": address,
                "source": 'fallback'
            }

        return {
            "found": False,
            "lat": None,
            "lon": None,
            "display_name": None,
            "source": "none"
        }
        
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert koordinat menjadi alamat"""        
        url = "https://nominatim.openstreetmap.org/reverse"

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }

        headers = {"User-Agent": "IADA-GIS/0.1"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return data.get("display_name")
        except Exception as e:
            print(f"Reverse geocode error: {e}")
            return None


geocode_service = NominatimService()
