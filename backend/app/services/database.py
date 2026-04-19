import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """Koneksi dan query ke PostgreSQL + PostGIS"""

    def __init__(self):
        # var
        self.host = os.getenv("DB_HOST")
        self.name = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT", "5432")

        # check if available
        if not all([self.host, self.name, self.user, self.password]):
            missing = []
            if not self.host: missing.append("DB_HOST")
            if not self.name: missing.append("DB_NAME")
            if not self.user: missing.append("DB_USER")
            if not self.password: missing.append("DB_PASSWORD")
            
            raise ValueError(
                f"Database configuration missing: {', '.join(missing)}. "
            )
        
        # koneksi
        self.conn = psycopg2.connect(
            host=self.host,
            dbname=self.name,
            user=self.user,
            password=self.password,
            port=self.port
        )
        print("Database connect")
    
    def test_connection(self) -> Dict:
        """Test koneksi"""
        with self.conn.cursor() as cur:
            # postgre check version
            cur.execute("SELECT version();")
            pg_version = cur.fetchone()[0]

            # postgis check version
            cur.execute("SELECT PostGIS_Version();")
            postgis_version = cur.fetchone()[0]

            return {
                "postgresql": pg_version,
                "postgis": postgis_version,
                "status": "connected"
            }
        
    def search_places_radius(self, lat: float, lon: float, radius_km: int, category: Optional[str] = None) -> List[Dict]:
        """Cari place dalam radius dari titik lat, lon dengan fungsi sql"""

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM search_places_radius(%s, %s, %s, %s)",
                (lat, lon, radius_km, category)
            )
            return [dict(row) for row in cur.fetchall()]
    
    def get_all_places(self) -> List[Dict]:
        "Ambil semua data places"

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM places ORDER BY id")
            return [dict(row) for row in cur.fetchall()] 
        
    def insert_places(self, name: str, lat: float, lon: float, category: str = None, description: str = None, crop_type: str = None, soil_type: str = None) -> int:
        """Insert data places baru"""

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO places (name, description, category, crop_type, soil_type, geom, lat, lon)
                        VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                        RETURNING id
            """, (name, description, category, crop_type, soil_type, lon, lat, lat, lon)
            )
            self.conn.commit()
            return cur.fetchone()[0]
        
    def close(self):
        self.conn.close()

db_service = DatabaseService()

