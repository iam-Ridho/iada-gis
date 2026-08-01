import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict
import json
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """Koneksi dan query ke PostgreSQL + PostGIS"""

    @staticmethod
    def required_schema_statements() -> List[str]:
        return [
            "CREATE EXTENSION IF NOT EXISTS postgis;",
            """
            CREATE TABLE IF NOT EXISTS public.gis_layers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                layer_type VARCHAR(100) NOT NULL,
                geom GEOMETRY(Geometry, 4326) NOT NULL,
                properties JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_gis_layers_geom ON public.gis_layers USING GIST (geom);",
            "CREATE INDEX IF NOT EXISTS idx_gis_layers_type ON public.gis_layers USING BTREE (layer_type);",
        ]

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
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5, 
            host=self.host, 
            dbname=self.name,
            user=self.user,
            password=self.password,
            port=self.port
        )
        self._ensure_required_schema()
        print("Database ready")

    def _ensure_required_schema(self) -> None:
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                for statement in self.required_schema_statements():
                    cur.execute(statement)
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)
    
    def test_connection(self) -> Dict:
        """Test koneksi"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
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
        finally:
            self.pool.putconn(conn)
        
    def search_places_radius(self, lat: float, lon: float, radius_km: int, category: Optional[str] = None) -> List[Dict]:
        """Cari place dalam radius dari titik lat, lon dengan fungsi sql"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM search_places_radius(%s, %s, %s, %s)",
                    (lat, lon, radius_km, category)
                )
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.pool.putconn(conn)
    
    def get_all_places(self) -> List[Dict]:
        "Ambil semua data places"
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM places ORDER BY id")
                return [dict(row) for row in cur.fetchall()] 
        finally:
            self.pool.putconn(conn)
        
    def insert_places(self, name: str, lat: float, lon: float, category: str = None, description: str = None, crop_type: str = None, soil_type: str = None) -> int:
        """Insert data places baru"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO places (name, description, category, crop_type, soil_type, geom, lat, lon)
                            VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                            RETURNING id
                """, (name, description, category, crop_type, soil_type, lon, lat, lat, lon)
                )
                conn.commit()
                return cur.fetchone()[0]
        finally:
            self.pool.putconn(conn)

    def insert_gis_layer(self, name: str, layer_type: str, geom_wkt: str, properties: dict = None) -> int:
        """Insert atau update layer GIS — cek manual, tidak pakai ON CONFLICT"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                # Cek dulu apakah sudah ada
                cur.execute("""
                    SELECT id FROM public.gis_layers 
                    WHERE name = %s AND layer_type = %s
                """, (name, layer_type))
                existing = cur.fetchone()

                if existing:
                    # Update yang sudah ada
                    cur.execute("""
                        UPDATE public.gis_layers 
                        SET geom = ST_Force2D(ST_GeomFromText(%s, 4326)), properties = %s
                        WHERE id = %s
                        RETURNING id
                    """, (geom_wkt, json.dumps(properties or {}), existing[0]))
                else:
                    # Insert baru
                    cur.execute("""
                        INSERT INTO public.gis_layers (name, layer_type, geom, properties)
                        VALUES (%s, %s, ST_Force2D(ST_GeomFromText(%s, 4326)), %s)
                        RETURNING id
                    """, (name, layer_type, geom_wkt, json.dumps(properties or {})))

                conn.commit()
                return cur.fetchone()[0]
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def query_intersecting_layers(self, lat: float, lon: float, layer_type: Optional[str] = None, radius_km: float = 10, max_results: int = 10) -> List[Dict]:
        """Cari layer GIS dalam radius, dibatasi jumlah & disederhanakan untuk performa"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                base_query = """
                    SELECT id, name, layer_type, properties,
                        ST_AsGeoJSON(ST_Simplify(geom, 0.0001)) as geojson,
                        ST_Distance(
                            geom::geography,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                        ) as distance_meters
                    FROM public.gis_layers
                    WHERE ST_DWithin(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        %s
                    )
                """
                params = [lon, lat, lon, lat, radius_km * 1000]

                if layer_type:
                    base_query += " AND layer_type = %s"
                    params.append(layer_type)

                base_query += " ORDER BY distance_meters ASC LIMIT %s"
                params.append(max_results)

                cur.execute(base_query, params)
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.pool.putconn(conn)

    def list_layer_types(self) -> List[Dict]:
        """Daftar layer GIS yang tersedia beserta jumlah fiturnya (untuk endpoint GET /layers)"""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT layer_type, COUNT(*) as feature_count
                    FROM public.gis_layers
                    GROUP BY layer_type
                """)
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.pool.putconn(conn)
    
    # def insert_shapefile_geometry(self, name: str, category: str, geom_wkt: str, properties: dict = None) -> int:
        """Insert geometri dari shapefile (polygon/point) ke PostGIS"""
        import json
        conn = self.pool.getconn()

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO places (name, category, geom, properties)
                VALUES (%s, %s, ST_GeomFromText(%s, 4326), %s)
                RETURNING id
            """, (name, category, geom_wkt, json.dumps(properties or {})))
            conn.commit()
            return cur.fetchone()[0]

    def close(self):
        self.pool.closeall()

db_service = DatabaseService()

