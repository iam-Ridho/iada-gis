# 🗺️ Arsitektur Frontend — IADA GIS

> **IADA GIS** adalah aplikasi Flutter yang memungkinkan pengguna bertanya tentang
> pertanian di Kalimantan Timur melalui chat berbasis AI, lalu hasilnya ditampilkan
> di peta interaktif jika ada data spasial yang relevan.

---

## 1. Gambaran Besar Sistem

```
┌──────────────────────────────────────────────────────┐
│                  Flutter App (Frontend)               │
│                                                      │
│   [User ngetik pertanyaan]                           │
│          ↓                                           │
│   ChatInputBar ──→ ChatNotifier (Riverpod)           │
│                         ↓                           │
│                    ApiService (Dio)                  │
│                         ↓  HTTP POST /api/v1/chat    │
│              ┌──────────────────────┐                │
│              │   Backend (FastAPI)   │                │
│              │   + AI / RAG Engine  │                │
│              └──────────────────────┘                │
│                         ↓ JSON Response              │
│                    ChatNotifier                      │
│                    ↙         ↘                       │
│           chatProvider    mapProvider                │
│                ↓                ↓                    │
│           ChatBubble       (GeoJSON tersimpan)       │
│         (teks + badge)          ↓                   │
│                         MapBottomSheet               │
│                              ↓                       │
│                          MapView                     │
│                     (flutter_map + polygon)          │
└──────────────────────────────────────────────────────┘
```

---

## 2. Struktur Folder

```
lib/
├── main.dart                    # Entry point aplikasi
│
├── app/
│   ├── app.dart                 # Root widget (kosong, belum dipakai)
│   └── theme.dart               # Tema global (kosong, belum dipakai)
│
├── core/                        # Infrastruktur lintas-fitur
│   ├── constants/
│   │   └── api_constants.dart   # URL base + endpoint
│   └── network/
│       └── api_service.dart     # HTTP client (Dio) + method sendMessages()
│
├── features/                    # Fitur-fitur aplikasi (dipisah per domain)
│   ├── chat/
│   │   ├── models/
│   │   │   └── chat_message.dart    # Data class: ChatMessage, ChatResponse, UIMessage
│   │   ├── providers/
│   │   │   └── chat_providers.dart  # State management: ChatNotifier, isLoadingProvider
│   │   └── screens/
│   │       ├── chat_screens.dart    # Layar utama chat
│   │       └── widgets/
│   │           ├── chat_bubble.dart     # Bubble pesan (user & bot)
│   │           ├── chat_input_bar.dart  # TextField + tombol kirim
│   │           └── citations_chip.dart  # Chip sumber dokumen
│   │
│   ├── map/
│   │   ├── providers/
│   │   │   └── map_provider.dart    # State management: MapNotifier (menyimpan GeoJSON)
│   │   └── screens/
│   │       ├── map_screen.dart      # (Kosong, belum dipakai)
│   │       └── widgets/
│   │           ├── map_view.dart        # Widget peta (flutter_map + polygon layer)
│   │           └── map_bottom_sheet.dart # Fungsi showMapBottomSheet()
│   │
│   └── home/
│       └── screens/
│           └── home_screen.dart    # (Kosong, belum dipakai)
│
└── shared/                      # Widget yang dipakai lebih dari 1 fitur
    └── widgets/
        └── loading_indicator.dart  # CircularProgressIndicator kecil
```

---

## 3. Layer Arsitektur

Proyek ini mengikuti pola **Feature-first + layered architecture** yang dibagi menjadi:

| Layer | Folder | Tanggung Jawab |
|---|---|---|
| **Core** | `core/` | Infrastruktur global: HTTP client, konstanta API |
| **Feature** | `features/` | Logika bisnis, state, dan UI per domain fitur |
| **Shared** | `shared/` | Widget reusable yang tidak milik satu fitur saja |
| **App** | `app/` | Konfigurasi root app (routing, tema) — *belum terisi* |

---

## 4. State Management — Riverpod

Proyek menggunakan **flutter_riverpod** dengan tiga provider utama:

### `chatProvider` — `NotifierProvider<ChatNotifier, List<UIMessage>>`
- Menyimpan **seluruh riwayat pesan** di layar chat
- Method `sendMessage()` mengelola full lifecycle:
  1. Tambah pesan user ke state
  2. Set `isLoading = true`
  3. Kirim HTTP via `ApiService`
  4. Tambah respons bot ke state
  5. Update `mapProvider` dengan GeoJSON dari respons
  6. Set `isLoading = false`

### `mapProvider` — `NotifierProvider<MapNotifier, Map<String,dynamic>?>`
- Menyimpan **data GeoJSON terakhir** dari respons bot
- State awal `null` (tidak ada peta)
- Di-update oleh `ChatNotifier` setelah setiap respons bot yang memiliki data spasial

### `isLoadingProvider` — `StateProvider<bool>`
- Flag sederhana untuk menampilkan/menyembunyikan `LoadingIndicator`

---

## 5. Data Model

```
ChatMessage          →  dikirim ke backend (role + content)
     ↓
  API POST
     ↓
ChatResponse         ←  diterima dari backend
  ├── answer          : String  (teks jawaban AI)
  ├── intentType      : String  (tipe intent: spatial / document / general)
  ├── placesFound     : int
  ├── documentsFound  : int
  ├── citations       : List<Map>  (daftar sumber dokumen)
  └── geoJson         : Map?   (null jika tidak ada data spasial)

UIMessage            →  representasi pesan untuk ditampilkan di UI
  ├── text            : String
  ├── isUser          : bool
  ├── timestamp       : DateTime
  └── botData         : ChatResponse?  (null untuk pesan user)
```

> **Kenapa ada dua model pesan (ChatMessage vs UIMessage)?**
>
> `ChatMessage` adalah kontrak dengan backend — hanya berisi `role` dan `content`
> sesuai format OpenAI/LLM standard. `UIMessage` adalah model UI yang lebih kaya:
> menyimpan timestamp, data bot lengkap, dan flag `isUser` agar bubble bisa
> dirender berbeda untuk user vs bot.

---

## 6. Alur Data End-to-End (Flow Lengkap)

```
Step 1: User mengetik & tap kirim
        ChatInputBar._handleSend()
              ↓
Step 2: Panggil notifier
        ref.read(chatProvider.notifier).sendMessage(text)
              ↓
Step 3: ChatNotifier.sendMessage()
        ├── Tambah UIMessage(isUser: true) ke state
        ├── Set isLoadingProvider = true
        └── Buat payload: [ChatMessage(role:'user', content:text)]
              ↓
Step 4: ApiService.sendMessages()
        POST http://localhost:8000/api/v1/chat
        Body: { messages: [...], user_lat: null, user_lon: null }
              ↓
Step 5: Backend merespons JSON
        {
          "answer": "Di Kutai Kartanegara terdapat...",
          "intent_type": "spatial",
          "places_found": 3,
          "documents_found": 5,
          "citations": [{"source": "data-pertanian.csv"}],
          "geo_json": { "type": "FeatureCollection", "features": [...] }
        }
              ↓
Step 6: ChatResponse.fromJson() parsing respons
              ↓
Step 7: ChatNotifier
        ├── Tambah UIMessage(isUser: false, botData: response) ke state
        └── mapProvider.notifier.updateGeoJson(response.geoJson)
              ↓
Step 8: UI rebuild otomatis (Riverpod)
        ├── ChatScreens rebuild → ListView menampilkan ChatBubble baru
        └── ChatBubble deteksi hasSpatialData = (geoJson != null)
              ↓
Step 9: Jika hasSpatialData = true
        ChatBubble menampilkan _buildSpatialBadge() di atas teks
        Badge bisa di-tap → showMapBottomSheet(context, geoJson)
              ↓
Step 10: MapBottomSheet muncul (85% tinggi layar)
         Berisi MapView(geoJson: geoJson)
              ↓
Step 11: MapView._processGeoJson()
         ├── Parse coordinates → List<LatLng>
         ├── Hitung centroid → _mapCenter
         ├── Buat List<Polygon>
         └── MapController.move(_mapCenter, 14.0)
              ↓
Step 12: flutter_map render peta OSM + polygon biru di atas tile
```

---

## 7. Dependency Graph Antar Komponen

```
main.dart
  └── ChatScreens (ConsumerStatefulWidget)
        ├── watch: chatProvider       ← list pesan
        ├── watch: isLoadingProvider  ← loading state
        ├── ChatBubble (per pesan)
        │     ├── UIMessage (data)
        │     ├── CitationsChip (jika ada citations)
        │     └── showMapBottomSheet() (jika ada geoJson)
        │           └── MapView (flutter_map)
        ├── LoadingIndicator (jika isLoading)
        └── ChatInputBar (ConsumerStatefulWidget)
              └── read: chatProvider.notifier.sendMessage()

ChatNotifier
  ├── read: apiServiceProvider   ← HTTP
  └── read: mapProvider.notifier ← update GeoJSON

ApiService
  └── ApiConstants (baseUrl, endpoint)
```

---

## 8. Mengapa Arsitektur Ini?

### Feature-first folder structure
Semua yang berkaitan dengan `chat` ada di `features/chat/`, semua tentang `map`
ada di `features/map/`. Ini memudahkan ketika tim berkembang — developer bisa
fokus di satu fitur tanpa takut konflik.

### Riverpod bukan setState / Provider biasa
- **Compile-safe**: error ketika provider tidak ada terdeteksi saat compile, bukan runtime
- **Tidak perlu BuildContext untuk baca state** dari dalam notifier (berguna di `ChatNotifier` yang perlu baca `mapProvider`)
- **`ref.listen`** di `ChatScreens` digunakan untuk auto-scroll saat pesan baru masuk — ini pattern reactive yang bersih

### Dio bukan http package
Dio dipakai karena sudah ada di `pubspec.yaml` dan memiliki `LogInterceptor`
bawaan yang memudahkan debugging request/response tanpa kode tambahan.

### GeoJSON sebagai format data spasial
Backend mengembalikan GeoJSON langsung. Frontend tidak perlu library parsing
tambahan — cukup `Map<String, dynamic>` dan ekstrak koordinat manual.
`MapView` kemudian mengkonversi ke `LatLng` dan `Polygon` dari `flutter_map`.

---

## 9. Hal yang Belum Selesai / WIP

| File/Fitur | Status | Catatan |
|---|---|---|
| `app/app.dart` | 🔴 Kosong | Harusnya jadi root widget + routing |
| `app/theme.dart` | 🔴 Kosong | Theme global belum dipindah dari `main.dart` |
| `features/home/screens/home_screen.dart` | 🔴 Kosong | Layar home belum dibuat |
| `features/map/screens/map_screen.dart` | 🔴 Kosong | Layar peta standalone belum dibuat |
| `chat_bubble.dart` line 92 | ⚠️ Bug | `if ()` kosong — syntax error/incomplete code |
| `chat_input_bar.dart` | ⚠️ WIP | `lat` dan `lon` selalu `null`, geolokasi belum diintegrasikan |
| `citations_chip.dart` onTap | ⚠️ WIP | `onTap: () {}` — aksi ketika tap citation belum diimplementasi |
| Routing (go_router) | 🔴 Belum | `go_router` ada di `pubspec.yaml` tapi belum dipakai |
| Multi-turn conversation | ⚠️ WIP | `requestPayload` hanya kirim 1 pesan terakhir, bukan seluruh history |

---

## 10. File Referensi Cepat

| Mau ngerjain apa? | File yang harus dibuka |
|---|---|
| Ubah tampilan bubble chat | [chat_bubble.dart](file:///d:/iada_gis/frontend/lib/features/chat/screens/widgets/chat_bubble.dart) |
| Ubah logika kirim pesan / handle respons | [chat_providers.dart](file:///d:/iada_gis/frontend/lib/features/chat/providers/chat_providers.dart) |
| Ubah tampilan/logika peta | [map_view.dart](file:///d:/iada_gis/frontend/lib/features/map/screens/widgets/map_view.dart) |
| Ubah tampilan bottom sheet peta | [map_bottom_sheet.dart](file:///d:/iada_gis/frontend/lib/features/map/screens/widgets/map_bottom_sheet.dart) |
| Ubah URL API / endpoint | [api_constants.dart](file:///d:/iada_gis/frontend/lib/core/constants/api_constants.dart) |
| Ubah konfigurasi HTTP (timeout, headers) | [api_service.dart](file:///d:/iada_gis/frontend/lib/core/network/api_service.dart) |
| Tambah field baru di respons bot | [chat_message.dart](file:///d:/iada_gis/frontend/lib/features/chat/models/chat_message.dart) |
| Tambah state global baru | Buat `NotifierProvider` baru di folder `providers/` fitur terkait |
