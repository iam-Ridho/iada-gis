import re
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class IntentType(Enum):
    SPATIAL_SEARCH = "spatial_search"
    DOCUMENT_SEARCH = "document_search"
    HYBRID = "hybrid"
    INFO = "info"
    UNKNOWN = "unknown"

@dataclass
class QueryIntent:
    location: Optional[str] = None
    radius_km: int = 5
    keywords: List[str] = field(default_factory=list)
    raw_query: str = ""

    type: str = "unknown"
    crop_type: Optional[str] = None
    category: Optional[str] = None
    action: Optional[str] = None
    has_spatial: bool = False

    @property
    def keywords_str(self) -> str:
        """Return keyword sebagai string"""
        return ' '.join(self.keywords) if isinstance(self.keywords, list) else str(self.keywords)


class RegexQueryParser:
    """Parser untuk query lokasi"""

    # Database Referensi
    CROP_TYPES = {
        'padi': ['padi', 'beras'],
        'jagung': ['jagung', 'corn'],
        'kelapa_sawit': ['sawit', 'kelapa sawit', 'palm oil'],
        'kopi': ['kopi', 'coffee', 'arabika', 'robusta'],
        'kakao': ['kakao', 'coklat', 'cocoa'],
        'tebu': ['tebu', 'gula'],
        'sayuran': ['sayur', 'sayuran', 'hortikultura'],
    }

    CATEGORIES = {
        'pertanian': ['pertanian', 'tanaman pangan', 'lahan', 'sawah'],
        'perkebunan': ['perkebunan', 'kebun', 'plantation'],
        'peternakan': ['peternakan', 'ternak', 'sapi', 'kambing', 'ayam'],
        'perikanan': ['perikanan', 'ikan', 'kolam', 'budidaya ikan'],
    }

    ACTION_PATTERNS = {
        'cari': [r'\bcari\b', r'\btemukan\b', r'\bcariin\b', r'\bmencari\b'],
        'info': [r'\bapa\b', r'\bbagaimana\b', r'\bgimana\b', r'\bjelaskan\b', r'\binfo\b'],
        'lokasi': [r'\bdimana\b', r'\bdi mana\b', r'\bletak\b', r'\blokasi\b'],
        'cara': [r'\bcara\b', r'\btutorial\b', r'\bpanduan\b', r'\blangkah\b'],
    }

    KNOWN_PLACES = [
        'samarinda ulu', 'samarinda ilir', 'sungai kunjang', 'palaran', 
        'sambutan', 'loa janan', 'bengalon', 'sangatta', 'kutai kartanegara',
        'bontang', 'tanjung redeb', 'sendawar', 'melak', 'barong tongkok',
        'muara badak', 'muara jawa', 'sepinggan', 'balikpapan',
    ]

    SKIP_WORDS = {
        'yang', 'untuk', 'dengan', 'cari', 'dalam', 'radius', 
        'kilometer', 'meter', 'padi', 'sawit', 'jagung', 'kopi',
        'pertanian', 'perkebunan', 'peternakan', 'perikanan',
        'kelapa', 'budidaya', 'cara', 'bagaimana', 'di', 'dekat',
        'dari', 'sekitar', 'sapi', 'kambing', 'ayam', 'ikan',
        'tentang', 'info', 'tentang', 'mau', 'ingin', 'butuh',
        'ada', 'bisa', 'dapat', 'yang', 'juga', 'saja', 'lagi',
        'sudah', 'belum', 'banyak', 'beberapa', 'semua', 'beberapa'
    }

    def parse(self, query: str) -> QueryIntent:
        query_lower = query.lower().strip()

        # Ekstraksi untuk pipeline
        crop_type = self._extract_crop_type(query_lower)
        category = self._extract_category(query_lower)
        action = self._extract_action(query_lower)
        
        # Ekstraksi Dasar
        location = self._extract_location(query_lower, crop_type)
        radius = self._extract_radius(query_lower) or 15
        keywords_list = self._extract_keywords_list(query_lower, location)

        intent_type = self._determine_intent_type(
            location=location,
            crop_type=crop_type,
            category=category,
            action=action,
            query=query_lower
        )
        has_spatial = self._has_spatial_intent(location, query_lower, intent_type)

        return QueryIntent(
            location=location,
            radius_km=radius,
            keywords=keywords_list,
            raw_query=query,

            type=intent_type,
            crop_type=crop_type,
            category=category,
            action=action,
            has_spatial=has_spatial
        )

    
    def _extract_location(self, query: str, crop_type: Optional[str]) -> Optional[str]:
        """Cari pola: di X, dekat X, dari X"""

        for place in self.KNOWN_PLACES:
            if place in query:
                return place.title()

        patterns = [
            # "dari [Lokasi]" - capture sampai akhir atau stopword
            r'dari\s+([a-z]+(?:\s+[a-z]+){0,2})(?=\s+(yang|dengan|untuk|area|radius|km|kilometer|$))',
            
            # "dekat [Lokasi]"
            r'dekat\s+([a-z]+(?:\s+[a-z]+){0,2})(?=\s+(yang|dengan|untuk|area|radius|km|kilometer|$))',
            
            # "sekitar [Lokasi]"
            r'sekitar\s+([a-z]+(?:\s+[a-z]+){0,2})(?=\s+(yang|dengan|untuk|area|radius|km|kilometer|$))',
            
            # "di [Lokasi]" - bisa 1-3 kata
            r'di\s+([a-z]+(?:\s+[a-z]+){0,2})(?=\s+(yang|dengan|untuk|area|radius|km|kilometer|$))',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1).strip()
                location = re.sub(r'\s+(yang|yg|dengan|dgn|untuk|utk)\s+.*$', '', location)

                common_words = {
                    'lahan', 'kebun', 'sawah', 'area', 'tempat', 'lokasi', 
                    'sini', 'sana', 'mana', 'budidaya', 'kelapa', 'cara',
                    'tentang', 'info', 'tentang', 'mau', 'ingin', 'butuh'
                }
                if location.lower() in common_words:
                    continue

                if crop_type and location.lower() in crop_type.replace('_', ' '):
                    continue

                return location.title()
            
        # Fallback
        words = query.split()
        for i in range(len(words) - 1, -1, -1):
            word = words[i]
            clean = re.sub(r'[^\w]', '', word).lower()
            if clean in self.SKIP_WORDS:
                continue

            if i > 0:
                two_words = f"{words[i-1]} {word}".lower().strip()
                if two_words in self.KNOWN_PLACES:
                    return two_words.title()
                
            if len(clean) > 3:
                return word.title()
        return None
            
    def _extract_radius(self, query: str) -> Optional[int]:
        """Cari pola: 10km, 5km, 2 km"""
        patterns = [
            r'(\d+)\s*km',
            r'(\d+)\s*kilometer',
            r'radius\s+(\d+)',
            r'dalam\s+(\d+)\s*(?:km|kilometer)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                radius = int(match.group(1))
                return max(1, min(radius, 100))
        return None
    
    def _extract_keywords_list(self, query: str, location: Optional[str]) -> List[str]:
        """Hapus lokasi, radius, stopwords"""

        if not location:
            location = ""

        # Hapus lokasi
        clean = re.sub(r'\b' + re.escape(location.lower()) + r'\b', '', query)
        # Hapus radius
        clean = re.sub(r'\d+\s*(km|kilometer|m|meter)', '', clean)
        # Hapus angka
        clean = re.sub(r'\d+', '', clean)

        words = clean.split()

        stopWords = {
            'cari', 'yang', 'di', 'dengan', 'untuk', 'dan', 'dekat', 
            'dari', 'ada', 'dalam', 'ke', 'pada', 'adalah', 'ini', 'itu',
            'saya', 'anda', 'kita', 'atau', 'bisa', 'bagaimana', 'apa',
            'dimana', 'kenapa', 'kapan', 'siapa', 'gimana', 'cara', 'info'
        }

        filtered = [w for w in words if w.lower() not in stopWords and len(w) > 2]

        seen = set()
        unique = []
        for w in filtered:
            w_lower = w.lower()
            if w_lower not in seen:
                seen.add(w_lower)
                unique.append(w_lower)

        return unique[:5]
    
    def _extract_crop_type(self, query: str) -> Optional[str]:
        """Ekstrak Jenis Tanaman"""
        all_aliases = []
        for crop, aliases in self.CROP_TYPES.items():
            for alias in aliases:
                all_aliases.append((crop, alias))

        all_aliases.sort(key=lambda x: len(x[1]), reverse=True)

        for crop, alias in all_aliases:
            if alias in query:
                return crop
        return None
    
    def _extract_category(self, query: str) -> Optional[str]:
        """Ekstrak Kategori"""
        for category, aliases in self.CATEGORIES.items():
            for alias in aliases:
                if alias in query:
                    return category
        return None
    
    def _extract_action(self, query: str) -> Optional[str]:
        """Ekstrak Kata Kerja"""
        for action, patterns in self.ACTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return action
        
        # Kalau ada [category/crop] + [preposition] + [place] → "cari"
        if re.search(r'(padi|sawit|jagung|kopi|sapi|ikan|lahan|kebun|peternakan)\s+(di|dekat|dari|sekitar)', query):
            return 'cari'
        
        # Kalau query diawali noun tanpa kata kerja → "cari"
        first_word = query.split()[0] if query.split() else ''
        if first_word in ['kebun', 'lahan', 'peternakan', 'perkebunan', 'pertanian']:
            return 'cari'
        
        return None

    def _determine_intent_type(
        self, location: Optional[str], crop_type: Optional[str], category: Optional[str], action: Optional[str],
        query: str
    ) -> str:
        """Tipe intent"""
        has_location = location is not None
        has_crop = crop_type is not None
        has_category = category is not None

        # Spatial dengan lokasi
        if has_location and (has_crop or has_category):
            return IntentType.SPATIAL_SEARCH.value
        
        # Spatial dengan radius
        if re.search(r'(km|kilometer|radius|jarak|dekat|sekitar|terdekat)', query):
            if has_location:
                return IntentType.SPATIAL_SEARCH.value
            
        # Document: cara/bagaimana/info tanpa lokasi spesifik
        if action in ['info', 'cara'] and not has_location:
            return IntentType.DOCUMENT_SEARCH.value
        
        # Hybrid: ada lokasi juga ada info/cara
        if has_location and action in ['info', 'cara']:
            return IntentType.HYBRID.value
        
        # Default
        if has_location:
            return IntentType.SPATIAL_SEARCH.value
        if has_crop or has_category:
            return IntentType.DOCUMENT_SEARCH.value
        
        return IntentType.INFO.value
    
    def _has_spatial_intent(self, location, query, intent_type):
        """Apakah butuh pencarian spatial"""
        has_radius = re.search(r'(km|kilometer|radius|jarak|dekat|sekitar|terdekat)', query) is not None
        is_spatial_intent = intent_type == IntentType.SPATIAL_SEARCH.value
        return has_radius or is_spatial_intent


parser = RegexQueryParser()