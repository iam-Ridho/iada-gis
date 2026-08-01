import httpx
import time

API = "http://localhost:8000/api/v1"

tests = [
    "cari lahan padi dalam 50 km dari Palaran",
    "bagaimana cara budidaya kelapa sawit",
    "kebun kopi dekat Samarinda Ulu",
    "info tentang jagung hibrida",
    "peternakan sapi terdekat dari Sambutan",
]

print("=" * 70)
print("🎉 FINAL RAG TEST - IADA-GIS")
print("=" * 70)

for q in tests:
    print(f"\n📝 Query: {q}")
    start = time.time()
    
    r = httpx.post(f"{API}/ask", json={"query": q}, timeout=60.0)
    elapsed = (time.time() - start) * 1000
    
    data = r.json()
    
    print(f"   ⏱️  Time: {elapsed:.0f}ms")
    print(f"   🎯 Intent: {data['intent_type']}")
    print(f"   📍 Spatial: {data['spatial_count']} | 📚 Vector: {data['vector_count']}")
    print(f"   🤖 Model: {data.get('model_used', 'unknown')}")
    print(f"   💬 Answer: {data['answer'][:200]}...")
    print("-" * 70)

print("\n✅ ALL TESTS COMPLETE!")