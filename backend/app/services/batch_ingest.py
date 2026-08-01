import os
from typing import List, Dict
from tqdm import tqdm

from app.services.document_loader import DocumentLoader
from app.services.chroma_service import chroma_service

class BatchIngestion:
    """Batch ingest semua file dari folder data/"""

    @staticmethod
    def ingest_all(max_features_shp: int = 500) -> Dict:
        """Ingest SEMUA file yang ditemukan di DATA_FOLDER"""

        files = DocumentLoader.list_local_files()

        print(f"Found {len(files)} files")

        results = []
        total_ingested = 0

        for f in tqdm(files, desc="Ingesting"):
            try:
                file_path = os.path.join(DocumentLoader.DATA_FOLDER, f["relative_path"])

                # route ke loader yang sesuai
                if f["type"] == "shp":
                    docs = DocumentLoader.load_shapefile(file_path, max_features=max_features_shp)
                elif f["type"] == "pdf":
                    docs = DocumentLoader.load_pdf(file_path)
                elif f["type"] == "csv":
                    docs = DocumentLoader.load_csv(file_path)
                elif f["type"] in ["xlsx", "xls"]:
                    docs = DocumentLoader.load_excel(file_path)
                else:
                    continue

                if docs:
                    ingest_result = chroma_service.add_documents(docs)
                    total_ingested += ingest_result["count"]
                    results.append({
                        "file": f["name"],
                        "type": f["type"],
                        "status": "success",
                        "count": ingest_result["count"]
                    })
                else:
                    results.append({
                        "file": f["name"],
                        "type": f["type"],
                        "status": "empty",
                        "count": 0
                    })
            
            except Exception as e:
                results.append({
                    "file": f["name"],
                    "type": f["type"],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "total_files": len(files),
            "total_ingested": total_ingested,
            "details": results
        }

    @staticmethod
    def ingest_file(file_path: str, doc_type: str = None) -> Dict:
        """Ingest satu file spesifik berdasarkan path"""
        try:
            docs = DocumentLoader.load_by_type(file_path, doc_type)
            
            if not docs:
                return {
                    "file": os.path.basename(file_path),
                    "status": "empty",
                    "count": 0
                }
            
            result = chroma_service.add_documents(docs)
            return {
                "file": os.path.basename(file_path),
                "status": "success",
                "count": result["count"]
            }
        
        except Exception as e:
            return {
                "file": os.path.basename(file_path),
                "status": "error",
                "count": str(e)
            }
