CREATE EXTENSION IF NOT EXISTS postgis;

-- table places untuk pertanian
CREATE TABLE IF NOT EXISTS places (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- Nama Lokasi
    description TEXT,           -- Deskripsi
    category VARCHAR(50),       -- Kategori: pertanian, perkebunan, peternakan
    crop_type VARCHAR(50),      -- Jenis tanaman: padi, jagung
    soil_type VARCHAR(50),      -- Jenis tanah
    ph_min DECIMAL(3, 1),       -- ph minimal
    ph_max DECIMAL(3, 1),       -- ph maksimal

    -- Untuk kolom spatial
    geom GEOMETRY(Point, 4326), -- Format: POINT
    lat DECIMAL(10, 8),         -- latitude
    lon DECIMAL(11, 8),         -- longitude

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- index untuk query
CREATE INDEX IF NOT EXISTS idx_places_geom ON places USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_places_category ON places(category);
CREATE INDEX IF NOT EXISTS idx_places_crop ON places(crop_type);

-- fungsi untuk mencari dalam radius
CREATE OR REPLACE FUNCTION search_places_radius(
    center_lat DECIMAL,         -- latitude pusat pencarian
    center_lon DECIMAL,         -- longitude pusat pencarian
    radius_km integer,          -- Radius dalam km
    p_category VARCHAR DEFAULT NULL -- Filter kategori
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    category VARCHAR,
    crop_type VARCHAR,
    distance_meters DOUBLE PRECISION,
    lat DECIMAL,
    lon DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.category,
        p.crop_type,
        ST_Distance(
            p.geom::geography,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        ) as distance_meters,
        p.lat,
        p.lon
    FROM places p
    WHERE ST_DWithin(
        p.geom::geography,
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography,
        radius_km * 1000
    )
    AND (p_category IS NULL OR p.category = p_category)
    ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql;

-- insert data dummy untuk testing
INSERT INTO places (name, description, category, crop_type, soil_type, geom, lat, lon)
VALUES
    ('Lahan Padi Palaran', 'Lahan padi seluas 50ha', 'pertanian', 'padi', 'alluvial',
    ST_SetSRID(ST_MakePoint(117.14, -0.48), 4326), -0.48, 117.14),

    ('Perkebunan Sawit Sambutan', 'Sawit mature 100ha', 'perkebunan', 'kelapa sawit', 'latosol',
    ST_SetSRID(ST_MakePoint(117.12, -0.52), 4326), -0.52, 117.12),

    ('Lahan Jagung Sungai Kunjang', 'Jagung hibrida', 'pertanian', 'jagung', 'podsolik',
    ST_SetSRID(ST_MakePoint(117.16, -0.50), 4326), -0.50, 117.16),

    ('Kebun Kopi Samarinda Ulu', 'Kopi arabika', 'perkebunan', 'kopi', 'andosol',
     ST_SetSRID(ST_MakePoint(117.15, -0.55), 4326), -0.55, 117.15),
    
    ('Peternakan Sapi Palaran', 'Sapi perah 50 ekor', 'peternakan', NULL, NULL,
     ST_SetSRID(ST_MakePoint(117.13, -0.47), 4326), -0.47, 117.13);

SELECT 'Data berhasil diinsert: ' || COUNT(*) || ' rows' as status FROM places;


