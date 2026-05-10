import httpx
import json
import urllib.parse

# Path shapefile Anda
SHP_PATH = r"D:\iada_gis\data\jigd\pertanian\kawasan_pertanian_kota_samarinda.shp"

# 1. Ingest Shapefile
print("=" * 60)
print("STEP 1: Ingest Shapefile")
print("=" * 60)

encoded_path = urllib.parse.quote(SHP_PATH, safe='')

try:
    response = httpx.post(
        f"http://localhost:8000/api/v1/ingest-shapefile?file_path={encoded_path}",
        timeout=30.0
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    exit()

# 2. Cek Stats
print("\n" + "=" * 60)
print("STEP 2: Check Stats")
print("=" * 60)

response = httpx.get("http://localhost:8000/api/v1/stats")
print(json.dumps(response.json(), indent=2))

# 3. Search
print("\n" + "=" * 60)
print("STEP 3: Semantic Search")
print("=" * 60)

queries = [
    "lahan pertanian samarinda",
    "kawasan padi",
    "pertanian kota samarinda",
    "lahan subur",
]

for query in queries:
    print(f"\n--- Query: '{query}' ---")
    
    response = httpx.post(
        "http://localhost:8000/api/v1/search",
        json={"query": query, "top_k": 5}
    )
    
    data = response.json()
    
    for result in data.get('results', []):
        meta = result['metadata']
        
        # Hanya tampilkan shapefile results
        if meta.get('source_type') == 'shapefile':
            print(f"\n  ID       : {result['id']}")
            print(f"  Distance : {result['distance']:.4f}")
            print(f"  File     : {meta.get('file', 'N/A')}")
            print(f"  Feature  : {meta.get('feature_id', 'N/A')}")
            print(f"  Geometry : {meta.get('geometry_type', 'N/A')}")
            print(f"  Content  : {result['content'][:200]}...")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)