# 📋 IADA-GIS — Project Summary (AI Reference)

> **Dokumen ini adalah acuan untuk AI** agar dapat memahami progress, arsitektur, dan status implementasi project IADA-GIS secara akurat.
> Diperbarui terakhir: 2026-08-14

---

## 🧭 Gambaran Umum

**IADA-GIS** (Intelligent Agriculture Data Assistant — Geographic Information System) adalah aplikasi asisten pertanian berbasis AI untuk wilayah **Kalimantan Timur**. Pengguna bisa bertanya dalam Bahasa Indonesia tentang pertanian, dan sistem akan menjawab dengan data spasial (peta), data dokumen, dan jawaban natural language dari LLM.

**Target pengguna:** Petani, penyuluh pertanian, dan instansi dinas pertanian di Kaltim.

---

## 🏗️ Arsitektur Sistem

```
Flutter App (Android/Web)
        │  HTTP (Dio)
        ▼
FastAPI Backend (Python)
        │
   ┌────┴────┐
   ▼         ▼
PostGIS   ChromaDB
(Spatial)  (Vector/RAG)
        │
        ▼
  Google Gemini LLM
```

### Alur Query Utama:
1. User ketik pertanyaan di chat Flutter
2. Frontend kirim ke `POST /api/v1/chat`
3. Backend: **Query Parser** (regex NLP) → ekstrak intent, lokasi, jenis tanaman, radius
4. **Geocoding** via Nominatim (OSM) + fallback hardcoded Kaltim
5. **Spatial Search** di PostGIS (radius-based, filter kategori)
6. **GIS Layer Query** → ambil polygon dari tabel `gis_layers` → serialize ke GeoJSON
7. **Vector Search** di ChromaDB (semantic search dokumen)
8. **LLM** (Gemini) generate jawaban dari context gabungan
9. Response JSON dikirim balik ke Flutter
10. Flutter tampilkan chat bubble + peta (bottom sheet) jika ada GeoJSON

---

## 🛠️ Tech Stack

### Backend
| Komponen | Teknologi | Status |
|---|---|---|
| Web Framework | FastAPI + Uvicorn | ✅ Running |
| Database Spatial | PostgreSQL 15 + PostGIS 3.3 | ✅ Connected |
| Vector DB | ChromaDB (persistent) | ✅ Running |
| Embedding Model | paraphrase-multilingual-MiniLM-L12-v2 | ✅ Active |
| LLM | Google Gemini (via google-genai) | ⚠️ Terintegrasi (health check hardcoded) |
| Geocoding | Nominatim OSM + fallback hardcoded | ✅ Active |
| GIS Processing | GeoPandas, Shapely | ✅ Active |
| Document Loader | LangChain + PyPDF + OpenPyXL | ✅ Active |
| OCR | Pytesseract + pdf2image | ⚠️ Terinstall, belum diintegrasikan |
| Containerization | Docker Compose (hanya PostgreSQL) | ⚠️ Parsial |

### Frontend
| Komponen | Teknologi | Status |
|---|---|---|
| Framework | Flutter (Dart, SDK ^3.10.7) | ✅ Running |
| State Management | Riverpod v2 (flutter_riverpod) | ✅ Active |
| HTTP Client | Dio v5 | ✅ Active |
| Routing | go_router v13 | ✅ Installed, belum dipakai |
| Map | flutter_map v8 + latlong2 | ✅ Active |
| Tile Layer | OpenStreetMap | ✅ Active |
| Location | geolocator v11 | ✅ Installed, belum dipakai di UI |
| Env Config | flutter_dotenv | ✅ Active |
| Target Platform | Android + Web (web folder ada) | ✅ Android running |

---

## 📁 Struktur File Project

```
iada_gis/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry, CORS, register 7 routers
│   │   ├── core/config.py
│   │   ├── models/schemas.py
│   │   ├── routers/
│   │   │   ├── pipeline.py            # /ask, /ask-simple, /pipeline-debug
│   │   │   ├── chat.py                # /chat (endpoint utama frontend)
│   │   │   ├── vector.py
│   │   │   ├── spatial.py
│   │   │   ├── geocode.py
│   │   │   ├── query.py
│   │   │   └── ingestion.py           # batch-ingest, list-files
│   │   └── services/
│   │       ├── pipeline_service.py    # ✅ Orchestrator RAG pipeline lengkap
│   │       ├── query_parser.py        # ✅ NLP regex parser
│   │       ├── geocode_service.py     # ✅ Nominatim + fallback Kaltim
│   │       ├── database.py            # ✅ PostgreSQL + PostGIS (connection pool)
│   │       ├── chroma_service.py      # ✅ ChromaDB vector service
│   │       ├── document_loader.py     # ✅ PDF, SHP, CSV, XLSX loader
│   │       ├── llm_service.py         # ✅ Google Gemini generate answer
│   │       └── batch_ingest.py        # ✅ Batch ingest semua file di /data
│   ├── data/documents/ + data/jigd/
│   ├── chroma_db/
│   └── test_all.py, test_integration.py, test_shapefile.py
│
├── frontend/
│   ├── lib/
│   │   ├── main.dart                  # Entry → ChatScreens
│   │   ├── core/
│   │   │   ├── network/api_service.dart       # ✅ Dio ApiService
│   │   │   └── constants/api_constants.dart   # ✅ baseUrl, endpoint
│   │   ├── features/
│   │   │   ├── chat/
│   │   │   │   ├── models/chat_message.dart   # ✅ ChatMessage, ChatResponse, UIMessage
│   │   │   │   ├── providers/chat_providers.dart # ✅ ChatNotifier, isLoadingProvider
│   │   │   │   └── screens/
│   │   │   │       ├── chat_screens.dart       # ✅ Chat screen utama
│   │   │   │       └── widgets/
│   │   │   │           ├── chat_bubble.dart    # ✅ Bubble + spatial badge
│   │   │   │           ├── chat_input_bar.dart # ✅ Input bar
│   │   │   │           └── citations_chip.dart # ✅ Chip sumber dokumen
│   │   │   └── map/
│   │   │       ├── providers/map_provider.dart # ✅ MapNotifier
│   │   │       ├── screens/
│   │   │       │   ├── map_screen.dart         # ❌ File kosong
│   │   │       │   └── widgets/
│   │   │       │       ├── map_view.dart       # ✅ FlutterMap + polygon render
│   │   │       │       └── map_bottom_sheet.dart # ✅ Modal bottom sheet
│   │   │       └── utils/
│   │   │           └── geojson_parser.dart     # ❌ Hanya komentar
│   │   └── shared/widgets/loading_indicator.dart # ✅
│   └── test/features/map/                        # ⚠️ Minimal
│
├── docker-compose.yml                 # ⚠️ Hanya PostgreSQL
├── init.sql                           # SQL init schema
└── docs/                              # ❌ Kosong
```

---

## ✅ Fitur yang Sudah Selesai (Backend)

| Fitur | File | Keterangan |
|---|---|---|
| FastAPI setup + CORS | main.py | 7 router terdaftar |
| Query Parser NLP | query_parser.py | Regex: intent, lokasi, tanaman, radius, kategori |
| Geocoding | geocode_service.py | Nominatim + 20+ kota Kaltim hardcoded |
| Spatial Search (PostGIS) | database.py | search_places_radius() |
| GIS Layer Query → GeoJSON | database.py + pipeline_service.py | query_intersecting_layers() + _build_geojson() |
| Vector DB (ChromaDB) | chroma_service.py | Embedding + semantic search |
| Multi-format Document Loader | document_loader.py | PDF, SHP, CSV, XLSX, XLS |
| Batch Ingest | batch_ingest.py + ingestion.py | Ingest semua file di /data |
| RAG Pipeline Orchestrator | pipeline_service.py | Parse → Geocode → Spatial → GIS → Vector → LLM |
| LLM Integration | llm_service.py | Google Gemini, fallback jika gagal |
| Chat Endpoint | routers/chat.py | POST /api/v1/chat |
| Citations Extraction | pipeline_service.py | _extract_citations() dari vector results |

## ✅ Fitur yang Sudah Selesai (Frontend)

| Fitur | File | Keterangan |
|---|---|---|
| Chat Screen | chat_screens.dart | ListView + auto-scroll ke bawah |
| Chat Bubble | chat_bubble.dart | Bubble user/bot, spatial badge tap-to-map |
| Chat Input Bar | chat_input_bar.dart | Send message ke provider |
| Citations Chip | citations_chip.dart | Tampilkan sumber dokumen |
| Chat Provider (Riverpod) | chat_providers.dart | State management chat + API call |
| API Service (Dio) | api_service.dart | HTTP client ke backend, 30s/60s timeout |
| Map View (FlutterMap) | map_view.dart | Render Polygon + MultiPolygon GeoJSON |
| Auto-center peta | map_view.dart | _mapController.move() ke centroid polygon |
| Map Bottom Sheet | map_bottom_sheet.dart | Modal 85% screen tinggi dengan peta |
| Map State Provider | map_provider.dart | MapNotifier simpan GeoJSON terkini |
| Loading Indicator | loading_indicator.dart | Tampil saat fetch API |
| Empty State | chat_screens.dart | Tampilan awal sebelum ada pesan |

---

## ⚠️ Yang Belum Selesai / In-Progress

| Item | Status | Prioritas |
|---|---|---|
| geojson_parser.dart | ❌ File ada tapi hanya komentar kosong | Medium |
| map_screen.dart | ❌ File kosong (0 bytes) | Medium |
| Routing dengan go_router | ❌ Package terinstall tapi belum dipakai | Low |
| GPS/Geolocator di UI | ❌ Package terinstall, belum ada tombol lokasi user | Medium |
| Home Screen | ❌ Direktori features/home ada, tidak ada file | Low |
| OCR untuk PDF gambar | ⚠️ Library terinstall, belum di-integrate | Low |
| Autentikasi & API Key | ❌ Belum ada | Low |
| Rate Limiting | ❌ Belum ada | Low |
| Docker full stack | ⚠️ Hanya PostgreSQL ter-containerize | Low |
| Dokumentasi /docs | ❌ Folder kosong | Low |
| Widget/Unit Tests | ⚠️ Direktori test ada, test sangat minimal | Low |
| LLM status di health check | ⚠️ Health check hardcode "not_connected_yet" | Medium |

---

## 🐛 Known Issues & Catatan Teknis

1. **Health check LLM status salah** — GET /health mengembalikan "llm": "not_connected_yet" padahal LLM sudah terintegrasi. Status hardcoded di main.py.
2. **database.py raise error saat startup** — Jika env var DB tidak ada, langsung throw ValueError. Tidak ada lazy initialization.
3. **geojson_parser.dart kosong** — Parsing GeoJSON dilakukan langsung di map_view.dart (_processGeoJson()), bukan di utility class terpisah.
4. **CORS terlalu terbuka** — allow_origins=["*"] harus direstriksi sebelum production.
5. **go_router belum dipakai** — Navigasi via Navigator langsung, routing belum terstruktur.
6. **map_screen.dart kosong** — Peta hanya tampil via bottom sheet, belum ada halaman peta dedicated.
7. **API version inkonsisten** — main.py pakai env default "0.6.0" tapi health check hardcode "0.8.0".

---

## 🔄 Alur Data Lengkap (Chat → Peta)

```
User ketik query
  → ChatInputBar.send()
  → ChatNotifier.sendMessage()
  → ApiService.sendMessages() → POST /api/v1/chat
  → RAGPipeline.process()
      → RegexQueryParser.parse()             ← intent, lokasi, tanaman, radius
      → geocode_service.geocode()            ← lat/lon dari Nominatim/fallback
      → db_service.search_places_radius()   ← PostGIS point search
      → db_service.query_intersecting_layers() ← GIS polygon layers
      → _build_geojson()                     ← FeatureCollection JSON
      → chroma_service.search()              ← vector semantic search
      → llm_service.generate_answer()       ← Gemini generate
  ← ChatResponse { answer, geo_json, citations, places_found, documents_found }
  → MapProvider.updateGeoJson(geoJson)
  → ChatBubble tampil dengan spatial badge (jika ada geo_json)
  → User tap badge → showMapBottomSheet()
  → MapView._processGeoJson() → render Polygon di FlutterMap OSM tiles
```

---

## 📊 Estimasi Progress Keseluruhan

| Area | Progress | Catatan |
|---|---|---|
| Backend Core (API + Pipeline) | ~90% | Hampir lengkap, minor polish |
| Backend Data Layer (DB + Vector) | ~85% | OCR belum terintegrasi |
| Frontend Chat Feature | ~85% | Fungsional end-to-end |
| Frontend Map Feature | ~65% | MapView ada, screen dedicated kosong |
| Frontend Routing & Navigation | ~20% | go_router belum dipakai |
| Testing | ~15% | Test files sangat minimal |
| DevOps / Deployment | ~20% | Docker parsial, belum full stack |
| Dokumentasi | ~30% | README backend bagus, docs/ kosong |

**Overall: ~65% selesai** — Fitur inti (chat + peta + RAG pipeline) sudah berjalan end-to-end. Yang tersisa: refinement, fitur tambahan (GPS, routing), testing, dan deployment.

---

## 🎯 Prioritas Next Steps (Saran)

### Jangka Pendek
1. Fix health check endpoint agar status LLM akurat
2. Implementasi geojson_parser.dart sebagai utility class terpisah
3. Tambah tombol "Gunakan Lokasi Saya" di chat input (pakai geolocator)
4. Implementasi map_screen.dart sebagai halaman peta full

### Jangka Menengah
5. Setup go_router untuk navigasi antar halaman (Chat ↔ Map ↔ Home)
6. Integrasi OCR ke document_loader.py
7. Tambah widget test untuk ChatBubble dan MapView
8. Docker Compose full stack (backend + frontend web)

### Jangka Panjang
9. Autentikasi pengguna (JWT atau API Key)
10. Rate limiting di backend
11. Deploy ke cloud (GCP/AWS/VPS)
12. Isi folder docs/ dengan dokumentasi API dan arsitektur
