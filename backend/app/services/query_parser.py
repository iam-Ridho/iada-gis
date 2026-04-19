import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedQuery:
    location: str
    radius_km: int
    keywords: str
    raw_query: str

class RegexQueryParser:
    """"Parser untuk query lokasi"""

    def parse(self, query: str) -> ParsedQuery:
        query_lower = query.lower()

        location = self._extract_location(query_lower)

        radius = self._extract_radius(query_lower) or 5

        keywords = self._clean_keywords(query_lower, location)

        return ParsedQuery(
            location=location,
            radius_km=radius,
            keywords=keywords,
            raw_query=query
        )

    
    def _extract_location(self, query: str) -> str:
        """Cari pola: di X, dekat X, dari X"""

        patterns = [
            r'di\s+([a-z\s]+?)(?=\s+(yang|dengan|untuk|area|radius|$))',
            r'dari\s+([a-z\s]+?)(?=\s+(yang|dengan|untuk|area|radius|$))',
            r'dekat\s+([a-z\s]+?)(?=\s+(yang|dengan|untuk|area|radius|$))',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
            
        # Fallback
        words = query.split()
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 4 and clean_word not in ['yang', 'untuk', 'dengan', 'cari']:
                return word
        return "unknown"
            
    def _extract_radius(self, query: str) -> Optional[int]:
        """Cari pola: 10km, 5km, 2 km"""
        patterns = [
            r'(\d+)\s*km',
            r'(\d+)\s*kilometer',
            r'radius\s+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        return None
    
    def _clean_keywords(self, query: str, location: str) -> str:
        """Hapus lokasi, radius, stopwords"""

        clean = re.sub(r'\b' + re.escape(location) + r'\b', '', query)
        clean = re.sub(r'\d+\s*(km|kilometer|m|meter)', '', clean)

        words = clean.split()

        stopWords = {'cari', 'yang', 'di', 'dengan', 'untuk', 'dan', 'dekat', 'dari', 'ada', 'dalam'}

        filtered = [w for w in words if w.lower() not in stopWords]

        return ' '.join(filtered)
    
parser = RegexQueryParser()