# test_all.py - Comprehensive test untuk IADA-GIS Backend
import httpx
import sys

BASE_URL = "http://localhost:8000"
API_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_result(name, status, detail=""):
    icon = "✅" if status else "❌"
    print(f"  {icon} {name:<40} {detail}")

def test_health():
    print_section("1. HEALTH CHECK")
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=30.0)
        data = r.json()
        
        all_pass = True
        
        ok = data.get("status") == "healthy"
        print_result("Status", ok, str(data.get("version")))
        all_pass = all_pass and ok
        
        services = data.get("services", {})
        for svc in ["parser", "geocoding", "database", "vector_db", "pipeline"]:
            ok = services.get(svc) == "active"
            print_result(svc.capitalize(), ok)
            all_pass = all_pass and ok
        
        return all_pass
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_query_parser():
    print_section("2. QUERY PARSER")
    try:
        from app.services.query_parser import RegexQueryParser
        parser = RegexQueryParser()
        
        tests = [
            ("cari lahan padi dalam 10 km dari Palaran", "spatial_search", "Palaran", "padi"),
            ("bagaimana cara budidaya kelapa sawit", "document_search", None, "kelapa_sawit"),
            ("kebun kopi dekat Samarinda Ulu", "spatial_search", "Samarinda Ulu", "kopi"),
            ("info tentang padi", "document_search", None, "padi"),
            ("dimana lahan jagung di Sungai Kunjang", "spatial_search", "Sungai Kunjang", "jagung"),
        ]
        
        all_pass = True
        for query, exp_type, exp_loc, exp_crop in tests:
            intent = parser.parse(query)
            ok = intent.type == exp_type
            detail = f"type={intent.type}, loc={intent.location}, crop={intent.crop_type}"
            print_result(f"  '{query[:30]}...'", ok, detail)
            all_pass = all_pass and ok
        
        return all_pass
    except Exception as e:
        print_result("Query Parser", False, str(e))
        return False

def test_geocode():
    print_section("3. GEOCODING")
    try:
        all_pass = True
        
        # FIX: parameter 'address' bukan 'q'
        r = httpx.get(f"{API_URL}/geocode", params={"address": "Palaran"}, timeout=30.0)
        print(f"   Status: {r.status_code}")
        data = r.json()
        
        ok = data.get("found") == True and data.get("lat") is not None
        print_result("Geocode Palaran", ok, f"({data.get('lat')}, {data.get('lon')})")
        all_pass = all_pass and ok
        
        r2 = httpx.get(f"{API_URL}/geocode", params={"address": "Samarinda"}, timeout=10.0)
        data2 = r2.json()
        ok = data2.get("found") == True and data2.get("lat") is not None
        print_result("Geocode Samarinda", ok, f"({data2.get('lat')}, {data2.get('lon')})")
        all_pass = all_pass and ok
        
        return all_pass
    except Exception as e:
        print_result("Geocoding", False, str(e))
        return False

def test_spatial():
    print_section("4. SPATIAL / DATABASE")
    try:
        all_pass = True
        
        # FIX: pakai API_URL
        r = httpx.get(f"{API_URL}/places", timeout=30.0)
        data = r.json()
        ok = len(data.get("places", [])) > 0
        print_result("Get All Places", ok, f"{data.get('count')} places")
        all_pass = all_pass and ok
        
        r2 = httpx.get(f"{API_URL}/search-radius", params={
            "lat": -0.48,
            "lon": 117.14,
            "radius_km": 10
        }, timeout=10.0)
        data2 = r2.json()
        ok = data2.get("count", 0) > 0
        print_result("Search Radius", ok, f"{data2.get('count')} places")
        all_pass = all_pass and ok
        
        r3 = httpx.get(f"{API_URL}/db-health", timeout=10.0)
        print_result("DB Health", r3.status_code == 200)
        all_pass = all_pass and (r3.status_code == 200)
        
        return all_pass
    except Exception as e:
        print_result("Spatial", False, str(e))
        return False

def test_vector():
    print_section("5. VECTOR DB / CHROMADB")
    try:
        all_pass = True
        
        # FIX: pakai API_URL
        r = httpx.get(f"{API_URL}/stats", timeout=30.0)
        data = r.json()
        doc_count = data.get("document_count", 0)
        print_result("Vector Stats", True, f"{doc_count} docs")
        
        if doc_count == 0:
            r2 = httpx.post(f"{API_URL}/ingest-dummy", timeout=10.0)
            ok = r2.status_code == 200
            print_result("Ingest Dummy", ok, r2.json().get("message", ""))
            all_pass = all_pass and ok
        
        r3 = httpx.post(f"{API_URL}/search", json={"query": "padi", "top_k": 3}, timeout=10.0)
        data3 = r3.json()
        ok = data3.get("count", 0) > 0
        print_result("Vector Search", ok, f"{data3.get('count')} results")
        all_pass = all_pass and ok
        
        return all_pass
    except Exception as e:
        print_result("Vector", False, str(e))
        return False

def test_pipeline():
    print_section("6. PIPELINE / RAG")
    tests = [
        {
            "name": "Spatial Query",
            "query": "cari lahan padi dalam 50 km dari Palaran",
            "expect_spatial": True,
            "expect_vector": False
        },
        {
            "name": "Document Query",
            "query": "bagaimana cara budidaya kelapa sawit",
            "expect_spatial": False,
            "expect_vector": True
        },
        {
            "name": "Hybrid Query",
            "query": "kebun kopi dekat Samarinda Ulu",
            "expect_spatial": True,
            "expect_vector": False
        },
    ]
    
    all_pass = True
    for test in tests:
        try:
            # FIX: pakai API_URL
            r = httpx.post(f"{API_URL}/ask", json={"query": test["query"]}, timeout=30.0)
            data = r.json()
            
            status = r.status_code == 200
            detail = f"intent={data.get('intent_type')}, spatial={data.get('spatial_count')}, vector={data.get('vector_count')}"
            
            if test["expect_spatial"]:
                ok = data.get("spatial_count", 0) > 0
                if not ok:
                    status = False
                    detail += " [expected spatial > 0]"
            
            if test["expect_vector"]:
                ok = data.get("vector_count", 0) > 0
                if not ok:
                    status = False
                    detail += " [expected vector > 0]"
            
            print_result(test["name"], status, detail)
            all_pass = all_pass and status
            
        except Exception as e:
            print_result(test["name"], False, str(e))
            all_pass = False
    
    # Pipeline debug
    try:
        r = httpx.get(f"{API_URL}/pipeline-debug", timeout=30.0)
        print_result("Pipeline Debug", r.status_code == 200)
    except Exception as e:
        print_result("Pipeline Debug", False, str(e))
    
    return all_pass

def main():
    print(f"\n{'#'*60}")
    print(f"#{'':^58}#")
    print(f"#{'IADA-GIS COMPREHENSIVE TEST':^58}#")
    print(f"#{'':^58}#")
    print(f"{'#'*60}")
    
    results = []
    results.append(("Health", test_health()))
    results.append(("Parser", test_query_parser()))
    results.append(("Geocode", test_geocode()))
    results.append(("Spatial", test_spatial()))
    results.append(("Vector", test_vector()))
    results.append(("Pipeline", test_pipeline()))
    
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"  {icon} {name}")
    
    print(f"\n  Total: {passed}/{total} passed")
    
    if passed == total:
        print(f"\n  🎉 ALL TESTS PASSED! Ready for Tahap 7.")
        return 0
    else:
        print(f"\n  ⚠️  Some tests failed. Please fix before continuing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())