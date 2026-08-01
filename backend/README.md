# 🌾 IADA-GIS Backend

**IADA (Intelligent Agriculture Data Assistant)** — Sistem AI untuk membantu petani di Kalimantan Timur mencari informasi pertanian dengan teknologi GIS, Vector Search, dan LLM.

---

## 📋 Daftar Isi

- [Deskripsi](#-deskripsi)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Fitur](#-fitur)
- [Tech Stack](#-tech-stack)
- [Struktur Proyek](#-struktur-proyek)
- [Prasyarat](#-prasyarat)
- [Instalasi](#-instalasi)
- [Konfigurasi Environment](#-konfigurasi-environment)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [API Endpoints](#-api-endpoints)
- [Cara Ingest Data](#-cara-ingest-data)
- [Contoh Query](#-contoh-query)
- [Status Progress](#-status-progress)

---

## 📖 Deskripsi

IADA-GIS adalah backend API yang menggabungkan:
- **GIS (Geographic Information System)** — Pencarian lokasi pertanian berbasis koordinat dan radius
- **RAG (Retrieval-Augmented Generation)** — Pencarian dokumen semantik menggunakan vector database
- **LLM (Gemini AI)** — Generate jawaban natural language dari konteks data yang ditemukan

Pengguna cukup mengetik pertanyaan dalam bahasa Indonesia seperti *"cari lahan padi dalam 10 km dari Palaran"* dan sistem akan secara otomatis melakukan geocoding, spatial search, vector search, lalu menghasilkan jawaban yang mudah dipahami.

---

## 🏗️ Arsitektur Sistem

```
User Query (Bahasa Indonesia)
        │
        ▼
┌─────────────────┐
│  Query Parser   │  ← Regex NLP: ekstrak lokasi, radius, crop, intent
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────────┐
│Geocode│  │Vector Query│
│Nominatim  │Builder    │
└───┬───┘  └─────┬──────┘
    │             │
    ▼             ▼
┌──────────┐  ┌──────────────┐
│PostGIS   │  │ChromaDB      │
│Spatial   │  │Semantic      │
│Search    │  │Search        │
└────┬─────┘  └──────┬───────┘
     │                │
     └────────┬────────┘
              ▼
       ┌─────────────┐
       │Context Build│
       └──────┬──────┘
              ▼
       ┌─────────────┐
       │ Gemini LLM  │  ← Generate jawaban akhir
       └──────┬──────┘
              ▼
       JSON Response
```

---

## ✨ Fitur

### 🔍 Query Parser (NLP Berbasis Regex)
- Deteksi otomatis **tipe intent**: `spatial_search`, `document_search`, `hybrid`, `info`
- Ekstraksi **lokasi** dari query natural language
- Ekstraksi **jenis tanaman**: padi, jagung, kelapa sawit, kopi, kakao, dll
- Ekstraksi **kategori**: pertanian, perkebunan, peternakan, perikanan
- Ekstraksi **radius** pencarian (dalam km)
- Fallback ke known places Kalimantan Timur

### 🗺️ Geocoding
- Integrasi **Nominatim / OpenStreetMap** untuk konversi alamat ke koordinat
- Fallback koordinat hardcoded untuk kota-kota utama Kaltim
- Reverse geocoding (koordinat ke alamat)

### 📍 Spatial Search (PostGIS)
- Pencarian lokasi pertanian berdasarkan **radius dari titik pusat**
- Filter berdasarkan **kategori** (pertanian, perkebunan, dll)
- Query langsung ke fungsi PostgreSQL `search_places_radius()`

### 📚 Vector Search (ChromaDB)
- Embedding dokumen menggunakan **HuggingFace Multilingual MiniLM**
- Semantic search dokumen pertanian (PDF, Shapefile, CSV, Excel)
- Ingest multi-format: `.pdf`, `.shp`, `.csv`, `.xlsx`, `.xls`
- Deduplikasi dokumen via MD5 hash

### 🤖 LLM Integration (Google Gemini)
- Generate jawaban dalam **bahasa Indonesia** yang ramah petani
- System prompt khusus domain pertanian Kaltim
- Fallback graceful jika API tidak tersedia

### 💬 Chat API
- Endpoint conversational untuk integrasi frontend
- Support user location untuk personalisasi hasil

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|---|---|
| Web Framework | FastAPI |
| Database Spatial | PostgreSQL + PostGIS |
| Vector Database | ChromaDB |
| Embedding Model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| LLM | Google Gemini (via `google-genai`) |
| Geocoding | Nominatim (OpenStreetMap) |
| GIS Processing | GeoPandas, Shapely |
| PDF Loader | LangChain + PyPDF |
| OCR (opsional) | Pytesseract + pdf2image |
| HTTP Client | httpx |
| Env Config | python-dotenv |

---

## 📁 Struktur Proyek

```
backend/
├── app/
│   ├── main.py                    # Entry point FastAPI, CORS, router register
│   ├── core/
│   │   └── config.py              # Konfigurasi Pydantic Settings
│   ├── models/
│   │   └── schemas.py             # Pydantic schemas
│   ├── routers/
│   │   ├── pipeline.py            # Endpoint utama: /ask, /ask-simple
│   │   ├── chat.py                # Endpoint chat conversational
│   │   ├── vector.py              # Ingest & search dokumen
│   │   ├── spatial.py             # PostGIS: places, radius search
│   │   ├── geocode.py             # Forward & reverse geocoding
│   │   └── query.py               # Query parser standalone
│   └── services/
│       ├── pipeline_service.py    # Orchestrator RAG pipeline
│       ├── query_parser.py        # NLP regex parser
│       ├── geocode_service.py     # Nominatim service
│       ├── database.py            # PostgreSQL + PostGIS service
│       ├── chroma_service.py      # ChromaDB vector service
│       ├── document_loader.py     # Multi-format document loader
│       ├── llm_service.py         # Google Gemini LLM service
│       └── batch_ingest.py        # Batch ingest semua file di /data
├── data/
│   ├── documents/                 # Simpan file PDF, CSV, Excel di sini
│   └── jigd/                      # Simpan Shapefile JIGD di sini
├── chroma_db/                     # ChromaDB persistent storage (auto-generated)
├── .env                           # Environment variables (jangan di-commit!)
├── requirements.txt               # Python dependencies
├── test_all.py                    # Test suite lengkap
├── test_integration.py            # Integration tests
└── test_shapefile.py              # Shapefile-specific tests
```

---

## ✅ Prasyarat

Pastikan sudah terinstall:
- **Python 3.10+**
- **PostgreSQL 14+** dengan ekstensi **PostGIS**
- **Tesseract OCR** (opsional, untuk PDF berbasis gambar)
- **Poppler** (opsional, untuk `pdf2image`)

---

## 📦 Instalasi

### 1. Clone & Setup Virtual Environment

```bash
# Clone repository
git clone <repo-url>
cd backend

# Buat virtual environment
python -m venv venv

# Aktifkan (Windows)
venv\Scripts\Activate.ps1

# Aktifkan (Linux/Mac)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Database PostgreSQL

```sql
-- Buat database
CREATE DATABASE iada_gis;

-- Aktifkan PostGIS
\c iada_gis
CREATE EXTENSION postgis;

-- Buat tabel places
CREATE TABLE places (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    crop_type VARCHAR(100),
    soil_type VARCHAR(100),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326)
);

-- Buat index spatial
CREATE INDEX idx_places_geom ON places USING GIST(geom);

-- Buat fungsi pencarian radius
CREATE OR REPLACE FUNCTION search_places_radius(
    p_lat DOUBLE PRECISION,
    p_lon DOUBLE PRECISION,
    p_radius_km INTEGER,
    p_category VARCHAR DEFAULT NULL
)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    category VARCHAR,
    crop_type VARCHAR,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pl.id, pl.name, pl.category, pl.crop_type,
        pl.lat, pl.lon,
        ST_Distance(
            pl.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
        ) AS distance_meters
    FROM places pl
    WHERE
        ST_DWithin(
            pl.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
            p_radius_km * 1000
        )
        AND (p_category IS NULL OR pl.category = p_category)
    ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql;
```

---

## ⚙️ Konfigurasi Environment

Buat file `.env` di root folder `backend/`:

```env
# Database PostgreSQL + PostGIS
DB_HOST=localhost
DB_NAME=iada_gis
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432

# Google Gemini LLM
LLM_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-2.0-flash

# App
API_VERSION=0.8.0

# Path data folder
DATA_FOLDER=D:\iada_gis\data
```

> **Dapatkan Gemini API Key:** https://aistudio.google.com/app/apikey

---

## 🚀 Menjalankan Aplikasi

```bash
# Aktifkan venv terlebih dahulu
venv\Scripts\Activate.ps1

# Jalankan server development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Akses di browser:
- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 📡 API Endpoints

### 🔑 Pipeline (Endpoint Utama)

| Method | Path | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/ask` | Query utama: natural language ke jawaban lengkap |
| `POST` | `/api/v1/ask-simple` | Versi simple via query params |
| `GET` | `/api/v1/pipeline-debug` | Status komponen pipeline |

**Contoh request `/api/v1/ask`:**
```json
{
  "query": "cari lahan padi dalam 10 km dari Palaran",
  "user_lat": -0.49,
  "user_lon": 117.14
}
```

**Response:**
```json
{
  "query": "cari lahan padi dalam 10 km dari Palaran",
  "intent_type": "spatial_search",
  "location": {"lat": -0.6239, "lon": 117.1963, "name": "Palaran"},
  "spatial_count": 3,
  "vector_count": 5,
  "context": "...",
  "answer": "Ditemukan 3 lahan padi di sekitar Palaran...",
  "model_used": "gemini-2.0-flash",
  "places": [...],
  "documents": [...]
}
```

---

### 💬 Chat

| Method | Path | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/chat` | Chat conversational |

---

### 🗺️ Geocoding

| Method | Path | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/geocode?address=Palaran` | Alamat ke koordinat |
| `GET` | `/api/v1/geocode-reverse?lat=-0.62&lon=117.19` | Koordinat ke alamat |

---

### 📍 Spatial (PostGIS)

| Method | Path | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/db-health` | Cek koneksi database |
| `GET` | `/api/v1/places` | Ambil semua data places |
| `GET` | `/api/v1/search-radius` | Cari places dalam radius |
| `POST` | `/api/v1/seed-data` | Insert data dummy untuk testing |

---

### 📚 Vector / Dokumen

| Method | Path | Deskripsi |
|---|---|---|
| `POST` | `/api/v1/ingest-dummy` | Ingest data dummy ke ChromaDB |
| `POST` | `/api/v1/ingest-shapefile?file_path=...` | Ingest shapefile `.shp` |
| `POST` | `/api/v1/ingest-pdf?file_path=...` | Ingest file PDF |
| `POST` | `/api/v1/ingest-csv?file_path=...` | Ingest file CSV |
| `POST` | `/api/v1/ingest-excel?file_path=...` | Ingest file Excel |
| `POST` | `/api/v1/search` | Semantic search dokumen |
| `GET` | `/api/v1/stats` | Statistik ChromaDB |

---

## 📂 Cara Ingest Data

### Ingest Data Dummy (untuk testing awal)
```bash
curl -X POST http://localhost:8000/api/v1/ingest-dummy
curl -X POST http://localhost:8000/api/v1/seed-data
```

### Ingest Shapefile JIGD
```bash
curl -X POST "http://localhost:8000/api/v1/ingest-shapefile?file_path=D:/iada_gis/data/jigd/lahan.shp&max_features=500"
```

### Ingest PDF
```bash
curl -X POST "http://localhost:8000/api/v1/ingest-pdf?file_path=D:/iada_gis/data/documents/panduan_padi.pdf"
```

### Ingest CSV
```bash
curl -X POST "http://localhost:8000/api/v1/ingest-csv?file_path=D:/iada_gis/data/documents/data_lahan.csv"
```

---

## 💡 Contoh Query

| Query | Intent | Yang Terjadi |
|---|---|---|
| `cari lahan padi dalam 10 km dari Palaran` | `spatial_search` | Geocode "Palaran" lalu spatial search radius 10km |
| `bagaimana cara budidaya kelapa sawit` | `document_search` | Vector search dokumen budidaya sawit |
| `peternakan sapi terdekat dari Samarinda Ulu` | `spatial_search` | Geocode + filter kategori peternakan |
| `info lahan jagung di Sungai Kunjang` | `hybrid` | Geocode + Spatial + Vector search |

---

## 📊 Status Progress

| Fitur | Status |
|---|---|
| ✅ FastAPI setup + CORS | Selesai |
| ✅ PostgreSQL + PostGIS koneksi | Selesai |
| ✅ Query Parser (Regex NLP) | Selesai |
| ✅ Geocoding (Nominatim + fallback) | Selesai |
| ✅ Spatial search radius (PostGIS) | Selesai |
| ✅ ChromaDB vector database | Selesai |
| ✅ Document Loader (PDF, SHP, CSV, Excel) | Selesai |
| ✅ RAG Pipeline Orchestrator | Selesai |
| ✅ LLM Integration (Google Gemini) | Selesai |
| ✅ Chat endpoint | Selesai |
| ⚠️ Batch ingest | Sebagian — ada bug variabel `results` vs `result` |
| ⏳ OCR untuk PDF berbasis gambar | Library terinstall, belum diimplementasi |
| ⏳ Frontend / Dashboard | Belum dimulai |
| ⏳ Autentikasi & API Key | Belum dimulai |
| ⏳ Rate limiting | Belum dimulai |
| ⏳ Docker / Deployment | Belum dimulai |

---

## 🐛 Known Issues

1. **`batch_ingest.py`** — Variabel tidak konsisten (`result` vs `results`), fungsi `ingest_file()` belum selesai
2. **`chat.py`** — Field `places_found` dan `documents_found` tipe `str` tapi return nilai `int`
3. **PDF berbasis gambar** — Pytesseract & pdf2image sudah terinstall, belum diintegrasikan ke loader
4. **DB init** — `database.py` raise error saat startup jika env vars tidak ada (bukan lazy initialization)

---

## 🤝 Kontribusi

Proyek ini dalam tahap pengembangan aktif. Untuk kontribusi:
1. Fork repository
2. Buat branch fitur: `git checkout -b feature/nama-fitur`
3. Commit perubahan: `git commit -m "feat: tambah fitur X"`
4. Push dan buat Pull Request

---

## 📄 Lisensi

Proyek ini dikembangkan untuk keperluan pertanian Kalimantan Timur.
