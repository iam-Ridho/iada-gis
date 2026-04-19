import asyncio
from app.services.query_parser import parser
from app.services.geocode_service import geocode_service

async def test_chain():
    # parse query
    query = "cari padi di samarinda dalam 10km"
    parsed = parser.parse(query)
    print(f"Parsed: {parsed}")

    # geocode lokasi
    coords = await geocode_service.geocode(parsed.location)
    if coords:
        lat, lon = coords
        print(f"Koordinat {parsed.location}: lat={lat}, lon={lon}")
        print(f"Siap query database dengan radius {parsed.radius_km}km")
    else:
        print("lokasi tidak ditemukan")

if __name__ == "__main__":
    asyncio.run(test_chain())