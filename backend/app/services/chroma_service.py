import chromadb
import hashlib
import uuid
from chromadb.config import Settings
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import Dict, List

class ChromaService:
    """Vector database untuk semantic search"""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path= "./chroma_db",
            settings= Settings(anonymized_telemetry=False)
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name="agri_documents",
            metadata={"hnsw:space": "cosine"}
        )

        print("Chroma service ready")

    def add_documents(self, documents: List[Document]) -> Dict:
        """Masukkan dokumen ke ChromaDb"""

        if not documents:
            return {"status": "error", "message": "No Documents"}
        
        documents = [d for d in documents if d.page_content.strip()]

        if not documents:
            return {"status": "error", "message": "Semua dokumen kosong"}
        
        texts = [d.page_content for d in documents]
        metadatas = [d.metadata for d in documents]
        ids = []
        seen = set()
        for i, d in enumerate(documents):
            base_id = hashlib.md5(d.page_content.encode()).hexdigest()

            # tambahkan index kalau hash masih sama
            unique_id = base_id
            counter = 0
            while unique_id in seen:
                counter += 1
                unique_id = f"{base_id}_{counter}"

            seen.add(unique_id)
            ids.append(unique_id)

        self.collection.upsert(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        return {
            "status": "success", "count": len(documents)
        }
    
    def search(self, query: str, top_k: int = 5, max_distance: float = 1.5) -> List[Dict]:
        """Semantic search"""
        result = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        for i in range(len(result["ids"][0])):
            distance = result["distances"][0][i]
            if distance < max_distance:
                output.append({
                    "id": result["ids"][0][i],
                    "metadata": result["metadatas"][0][i],
                    "content": result["documents"][0][i],
                    "distance": distance
                })
        return output
    
    def get_stats(self) -> Dict:
        """Statistik Collection"""
        return {
            "collection": "agri_documents",
            "document_count": self.collection.count()
        }
        

chroma_service = ChromaService()