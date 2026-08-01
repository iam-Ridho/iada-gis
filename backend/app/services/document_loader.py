import os
import csv
from langchain_core.documents import Document
from typing import List

class DocumentLoader:
    """Load dokumen dari berbagai sumber"""

    DATA_FOLDER = os.getenv("DATA_FOLDER", r"D:\iada_gis\backend\data")

    @staticmethod
    def load_dummy() -> List[Document]:
        """Data dummy untuk testing"""
        return [
            Document(
                page_content="Budidaya padi di lahan gambut Kalimantan Timur memerlukan drainase khusus. pH tanah harus dijaga antara 4.5-5.5. Varietas Inpari 32 cocok untuk lahan gambut.",
                metadata={"source_type": "pdf", "topic": "padi", "source": "BPS Kaltim 2024"}
            ),
            Document(
                page_content="Kelapa sawit membutuhkan curah hujan 2000-2500 mm per tahun. Tanah latosol dan podsolik merah kuning cocok untuk perkebunan sawit. Panen setiap 10-14 hari.",
                metadata={"source_type": "pdf", "topic": "kelapa_sawit", "source": "Dinas Perkebunan Kaltim"}
            ),
            Document(
                page_content="Jagung hibrida ditanam pada musim hujan. Produksi bisa mencapai 8-10 ton per hektar. Tanah alluvial di dataran rendah sangat cocok.",
                metadata={"source_type": "pdf", "topic": "jagung", "source": "Balitkabi"}
            ),
            Document(
                page_content="Lahan: Lahan Padi Palaran. Koordinat: 117.14, -0.48. Kategori: pertanian. Jenis tanaman: padi. Luas: 50 hektar.",
                metadata={"source_type": "shapefile", "topic": "padi", "location": "Palaran"}
            ),
            Document(
                page_content="Lahan: Perkebunan Sawit Sambutan. Koordinat: 117.12, -0.52. Kategori: perkebunan. Jenis tanaman: kelapa sawit.",
                metadata={"source_type": "shapefile", "topic": "kelapa_sawit", "location": "Sambutan"}
            ),
        ]
    
    # ===================== Shape File =====================
    @staticmethod
    def load_shapefile(shp_path: str, max_features: int = None) -> List[Document]:
        """Load shapefile JIGD"""
        try:
            import geopandas as gpd

            if not os.path.exists(shp_path):
                return []

            base = shp_path.replace('.shp', '')
            for ext in ['.shx', '.dbf']:
                if not os.path.exists(base + ext):
                    print(f"File {ext} not found")
                    return []
            
            gdf = gpd.read_file(shp_path)
            total = len(gdf)
            print(f"Total features: {total}")

            if max_features and total > max_features:
                print(f"Limit to {max_features} features (dari {total})")
                gdf = gdf.head(max_features)

            docs = []

            for idx, row in gdf.iterrows():
                geom = row['geometry']
                attrs = {k: str(v) for k, v in row.items() if k != 'geometry' and v and str(v) != 'nan'}

                lines = [f"{k}: {v}" for k, v in attrs.items()]

                if geom.geom_type == 'Point':
                    lines.append(f"koordinat: {geom.x}, {geom.y}")
                elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                    centroid = geom.centroid
                    lines.append(f"centroid: {centroid.x}, {centroid.y}")
                    lines.append(f"area: {geom.area:.2f}")

                if(len("\n".join(lines)) < 30):
                    continue

                docs.append(Document(
                    page_content="\n".join(lines),
                    metadata={
                        "source_type": "shapefile",
                        "file": os.path.basename(shp_path),
                        "feature_id": int(idx),
                        "geometry_type": geom.geom_type,
                        "total_features": total
                    }
                ))

                if(idx + 1) % 100 == 0:
                    print(f" Progress: {idx+1}/{len(gdf)}")

            return docs
        
        except ImportError:
            print("belum terinstall")
            return []
        except Exception as e:
            print(f"error: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def load_shapefile_for_postgis(shp_path: str, max_features: int = None) -> List[dict]:
        """Load shapefile khusus untuk import ke PostGIS — return WKT + properties, bukan Document"""
        import geopandas as gpd

        if not os.path.exists(shp_path):
            return []

        gdf = gpd.read_file(shp_path)

        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        if max_features and len(gdf) > max_features:
            gdf = gdf.head(max_features)

        layer_type = os.path.splitext(os.path.basename(shp_path))[0]

        records = []
        for idx, row in gdf.iterrows():
            geom = row['geometry']
            if geom is None or not geom.is_valid:
                continue

            attrs = {k: str(v) for k, v in row.items() if k != 'geometry' and v and str(v) != 'nan'}
            name = attrs.get('nama') or attrs.get('name') or f"{layer_type}_{idx}"

            records.append({
                "name": name,
                "layer_type": layer_type,
                "geom_wkt": geom.wkt,
                "properties": attrs
            })

        return records


    # ===================== PDF =====================
    @staticmethod
    def load_pdf(file_path: str) -> List[Document]:
        """Load file PDF"""
        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            if not os.path.exists(file_path):
                print(f"File tidak ditemukan: {file_path}")
                return []

            loader = PyPDFLoader(file_path)
            pages = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = splitter.split_documents(pages)

            for chunk in chunks:
                chunk.metadata.update({
                    "source_type": "pdf",
                    "file": os.path.basename(file_path),
                    "folder": os.path.basename(os.path.dirname(file_path))
                })

            return chunks

        except ImportError as e:
            print(f"Error import library PDF: {e}")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"Error load PDF: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    # ===================== CSV =====================
    @staticmethod
    def load_csv(file_path: str, text_columns: List[str] = None) -> List[Document]:
        """Load File CSV"""

        if not os.path.exists(file_path):
            print(f"File tidak ditemukan: {file_path}")
            return []
        
        documents = []

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                sample = f.read(1024)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                reader = csv.DictReader(f, dialect=dialect)

                if reader.fieldnames is None:
                    print(f"CSV kosong atau tidak memiliki header: {file_path}")
                    return []

                print(f"CSV columns: {reader.fieldnames}")

                for i, row in enumerate(reader):
                    if text_columns:
                        text_parts = [f"{col}: {row.get(col, '')}" for col in text_columns if row.get(col)]
                    else:
                        text_parts = [f"{k}: {v}" for k, v in row.items() if v]

                    content = "\n".join(text_parts)

                    if not content.strip():
                        continue

                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "source_type": "csv",
                            "file": os.path.basename(file_path),
                            "row_id": i
                        }
                    ))

            print(f"CSV loaded: {len(documents)} rows")
            return documents

        except Exception as e:
            print(f"Error load CSV: {e}")
            import traceback
            traceback.print_exc()
            return []

    # ===================== XLSX =====================
    @staticmethod
    def load_excel(file_path: str, text_columns: List[str] = None, sheet_name: str = 0) -> List[Document]:
        """
        Load file Excel (.xlsx, .xls)
    
        text_columns: kolom mana yang digabung jadi teks (None = semua)
        sheet_name: nama atau index sheet (default: 0 = sheet pertama)
        """

        try:
            import pandas as pd

            if not os.path.exists(file_path):
                return []
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            documents = []
            requested_columns = None

            if text_columns:
                actual_cols = {str(col).lower(): col for col in df.columns}
                requested_columns = [actual_cols[col.lower()] for col in text_columns if col.lower() in actual_cols]
                if not requested_columns:
                    print(f"Requested text_columns {text_columns} not found. Available columns: {list(df.columns)}")
                    requested_columns = list(df.columns)

            for i, row in df.iterrows():
                # convert row ke dict (handle NaN)
                row_dict = {k: str(v) if pd.notna(v) else "" for k, v in row.items()}

                # Pilih kolom untuk teks
                if requested_columns is not None:
                    text_parts = [f"{col}: {row_dict.get(col, '')}" for col in requested_columns if row_dict.get(col)]
                else:
                    text_parts = [f"{k}: {v}" for k, v in row_dict.items() if v]

                content = "\n".join(text_parts)

                # skip kosong
                if not content.strip():
                    continue

                documents.append(Document(
                page_content=content,
                metadata={
                    "source_type": "excel",
                    "file": os.path.basename(file_path),
                    "sheet": sheet_name,
                    "row_id": int(i)
                }
            ))
        
            print(f"Excel loaded: {len(documents)} rows")
            return documents
        
        except ImportError:
            print("Install pandas & openpyxl: pip install pandas openpyxl")
            return []
        except Exception as e:
            print(f"Error load Excel: {e}")
            return []
        
    @staticmethod
    def load_by_type(file_path: str, doc_type: str = None) -> List[Document]:
        """Auto-detect type dan load"""
        if doc_type is None:
            ext = os.path.splitext(file_path)[1].lower()
            type_map = {
                '.pdf': 'pdf',
                '.shp': 'shapefile',
                '.csv': 'csv',
                '.xlsx': 'excel',
                '.xls': 'excel',
                '.txt': 'dummy'
            }
            doc_type = type_map.get(ext, 'dummy')

        loaders = {
            'pdf': DocumentLoader.load_pdf,
            'shapefile': DocumentLoader.load_shapefile,
            'csv': DocumentLoader.load_csv,
            'excel': DocumentLoader.load_excel,
            'dummy': DocumentLoader.load_dummy
        }

        loader = loaders.get(doc_type)
        if loader:
            return loader(file_path) if doc_type != 'dummy' else loader()
        
        raise ValueError(f"Unsupported  type: {doc_type}")
    
    @staticmethod
    def list_local_files() -> List[dict]:
        """List Semua file di data folder"""
        import glob

        files = []
        if not os.path.exists(DocumentLoader.DATA_FOLDER):
            return files

        patterns = ['**/*.shp', '**/*.pdf', '**/*.csv', '**/*.xlsx', '**/*.xls']
        for pattern in patterns:
            for path in glob.glob(os.path.join(DocumentLoader.DATA_FOLDER, pattern), recursive=True):
                rel = os.path.relpath(path, DocumentLoader.DATA_FOLDER)
                files.append({
                    "name": os.path.basename(path),
                    "relative_path": rel.replace("\\", "/"),
                    "type": os.path.splitext(path)[1].lower().replace(".", ""),
                    "size_mb": round(os.path.getsize(path) / 1024 / 1024, 2)
                })

        return files