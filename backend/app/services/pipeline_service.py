from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from app.services.database import db_service
from app.services.chroma_service import chroma_service
from app.services.geocode_service import geocode_service
from app.services.query_parser import RegexQueryParser, QueryIntent

@dataclass
class Pipelineresult:
    query_original: str
    intent: QueryIntent
    location: Optional[Dict]
    spatial_results: List[Dict]
    vector_results: List[Dict]
    context: str
    answer_ready: bool

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

        # 4) Vector search
        print(f"\nVector search...")
        vector_query = self._build_vector_query(intent)
        vector_results = self.vector_db.search(vector_query, top_k=5)
        print(f"Found: {len(vector_results)} docs")

        # 5) Context
        context = self._build_context(intent, spatial_results, vector_results)
        
        return Pipelineresult(
            query_original=intent.raw_query,
            intent=intent,
            location={"lat": center_lat, "lon": center_lon, "name": intent.location} if center_lat else None,
            spatial_results=spatial_results,
            vector_results=vector_results,
            context=context,
            answer_ready=True
        )


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
            lines.append(f"- [{source}] {str(content)[:100]}...")

        return "\n".join(lines)
    

pipeline = RAGPipeline()
