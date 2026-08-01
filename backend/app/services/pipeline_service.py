from typing import List, Dict, Optional
from dataclasses import dataclass, field
import time

from app.services.database import db_service
from app.services.chroma_service import chroma_service
from app.services.geocode_service import geocode_service
from app.services.query_parser import RegexQueryParser, QueryIntent
from app.services.llm_service import llm_service

@dataclass
class Pipelineresult:
    query_original: str
    intent: QueryIntent
    location: Optional[Dict]
    spatial_results: List[Dict]
    vector_results: List[Dict]
    context: str
    answer: str
    answer_ready: bool
    model_used: str = "unknown"
    processing_time_ms: int = 0
    citations: List[Dict] = field(default_factory=list)
    geo_json: Optional[Dict] = None

class RAGPipeline:
    """Pipeline: Query -> parse -> geocode -> search(spatial + vector) -> context"""

    def __init__(self):
        self.parser = RegexQueryParser()
        self.geocoder = geocode_service
        self.spatial_db = db_service
        self.vector_db = chroma_service
    
    async def process(self, query: str, user_location: Optional[Dict] = None) -> Pipelineresult:
        """
        Proses query dari user sampai jadi context untuk LLM
        
        Args:
            query: Pertanyaan user dalam bahasa alami
            user_location: Lokasi user (opsional), format {"lat": x, "lon": y}
        """
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"Pipeline: '{query}'")
        print(f"{'='*60}")

        # 1) Parse Query
        print("\n 1: Parsing Query...")
        intent = self.parser.parse(query)
        print(f"\n Parsed: {intent.type} | loc={intent.location} | crop={intent.crop_type}")

        # 2) Geocode (kalau ada lokasi)
        center_lat, center_lon = None, None

        if intent.location:
            print(f"\n Geocoding '{intent.location}'...")
            geo_result = await self.geocoder.geocode(intent.location)
            
            if geo_result.get("lat") is not None and geo_result.get("lon") is not None:
                center_lat, center_lon = geo_result["lat"], geo_result["lon"]
                src = "Nominatim" if geo_result.get("found") else geo_result.get("source", "fallback")
                print(f" Coords ({src}): ({center_lat}, {center_lon})")
            elif user_location:
                center_lat, center_lon = user_location["lat"], user_location["lon"]
                print(f" Fallback to user location")

        # 3) Spatial Search
        spatial_results = []
        if intent.has_spatial and center_lat and center_lon:
            print(f"\nSpatial search...")
            spatial_results = self.spatial_db.search_places_radius(
                lat=center_lat,
                lon=center_lon,
                radius_km=intent.radius_km,
                category=intent.category
            )
            print(f"Found: {len(spatial_results)} places")

        # 4) Query Polygon layer GIS
        geo_json = None
        if center_lat and center_lon:
            print(f"\nQuerying GIS layers (polygon)...")
            geo_query_start = time.time()
            
            preferred_layer_type = self._match_layer_type(intent.location) if intent.location else None
            layer_results = self.spatial_db.query_intersecting_layers(
                center_lat, center_lon, 
                layer_type=preferred_layer_type,
                radius_km=intent.radius_km,
                max_results=10
            )

            if not layer_results and preferred_layer_type:
                print(f"Tidak ada hasil untuk layer '{preferred_layer_type}', coba tanpa filter...")
                layer_results = self.spatial_db.query_intersecting_layers(
                    center_lat, center_lon, radius_km=intent.radius_km, max_results=10
                )

            geo_query_ms = int((time.time() - geo_query_start) * 1000)
            print(f"Found: {len(layer_results)} intersecting layers ({geo_query_ms}ms)") 
            if layer_results:
                geo_json = self._build_geojson(layer_results)


        # 5) Vector search
        print(f"\nVector search...")
        vector_query = self._build_vector_query(intent)
        vector_results = self.vector_db.search(vector_query, top_k=5)
        print(f"Found: {len(vector_results)} docs")

        # 5) Context
        context = self._build_context(intent, spatial_results, vector_results)

        # 6) LLM generate
        print(f"\n Generating Answer....")
        llm_start = time.time() 
        llm_result = await llm_service.generate_answer(context, query)
        llm_ms = int((time.time() - llm_start) * 1000)
        answer = llm_result["answer"]
        print(f" Answer generate ({len(answer)} chars, {llm_ms}ms)")

        citations = self._extract_citations(vector_results)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return Pipelineresult(
            query_original=intent.raw_query,
            intent=intent,
            location={"lat": center_lat, "lon": center_lon, "name": intent.location} if center_lat else None,
            spatial_results=spatial_results,
            vector_results=vector_results,
            context=context,
            answer=answer,
            answer_ready=True,
            model_used=llm_result.get("model", "unknown"),
            processing_time_ms=elapsed_ms,
            citations=citations,
            geo_json=geo_json
        )

    def _match_layer_type(self, location: str) -> Optional[str]:
        """Cocokkan nama lokasi dengan layer_type yang ada (berdasarkan konvensi nama file shapefile)"""
        if not location:
            return None
        
        location_lower = location.lower().replace(' ', '_')
        
        # Mapping manual — sesuaikan dengan layer_type yang benar-benar ada di database
        location_to_layer = {
            'samarinda': 'kawasan_pertanian_kota_samarinda',
            'kutai_barat': 'kawasan_pertanian_kutai_barat',
            'kutai_kartanegara': 'kawasan_pertanian_kutai_kartanegara',
            'kutai_timur': 'kawasan_pertanian_kutai_timur',
        }
        
        for key, layer_type in location_to_layer.items():
            if key in location_lower:
                return layer_type
        
        return None

    def _build_geojson(self, layer_results: List[Dict]) -> Dict:
        """Gabungkan hasil query_intersecting_layers jadi FeatureCollection standar"""
        import json

        features = []
        for row in layer_results:
            try:
                geometry = json.loads(row["geojson"])
            except (KeyError, json.JSONDecodeError):
                continue
            
            features.append({
                "type" : "Feature",
                "geometry" : geometry,
                "properties" : {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "layer_type": row.get("layer_type"),
                    **(row.get("properties") or {})
                }
            })
        return {
            "type": "FeatureCollection",
            "features": features
        }

    def _build_vector_query(self, intent: QueryIntent) -> str:
        """Build query untuk vector search dari intent"""
        parts = []

        if intent.crop_type:
            parts.append(str(intent.crop_type.replace('_', ' ')))
        if intent.category:
            parts.append(str(intent.category))
        if intent.keywords:
            for kw in intent.keywords:
                if isinstance(kw, str):
                    parts.append(kw)
                elif isinstance(kw, list):
                    parts.extend([str(k) for k in kw])
                else:
                    parts.append(str(kw))
        if intent.action:
            parts.append(str(intent.action))

        if not parts:
            return str(intent.raw_query)

        return " ".join(parts)

    def _extract_citations(self, vector_results: List[Dict]) -> List[Dict]:
        """ Ekstrak sumber unik dari hasil vector search """
        citations = []
        seen = set()

        for d in vector_results:
            meta = d.get('metadata', {}) if isinstance(d, dict) else {}
            source = meta.get('source') or meta.get('file') or "Sumber tidak diketahui"
            if source not in seen:
                citations.append({
                    "source": source,
                    "type": meta.get("source_type", "unknown")
                })
                seen.add(source)

        return citations

    def _build_context(self, intent: QueryIntent, spatial: List[Dict], vector: List[Dict]) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append(f"Query: {intent.raw_query}")
        lines.append(f"Intent: {intent.type}")

        if intent.location:
            lines.append(f"Location: {intent.location}")
            lines.append(f"Radius: {intent.radius_km} km")

        keywords_str = ", ".join([str(k) for k in intent.keywords]) if intent.keywords else "None"
        lines.append(f"Keywords: {keywords_str}")

        lines.append(f"\n-- Spatial ({len(spatial)} result) --")
        for p in spatial:
            name = p.get('name', 'Unknown')
            dist = p.get('distance_meters', 0)
            lines.append(f"- {name} ({dist:.0f}m)")

        lines.append(f"\n--- Documents ({len(vector)} results) ---")
        for d in vector:
            meta = d.get('metadata', {}) if isinstance(d, dict) else {}
            source = meta.get('source_type', '?') if isinstance(meta, dict) else '?'
            content = d.get('content', '') if isinstance(d, dict) else str(d)
            lines.append(f"- [{source}] {str(content)[:500]}...")

        return "\n".join(lines)
    

pipeline = RAGPipeline()
