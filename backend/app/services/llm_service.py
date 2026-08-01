import os
from typing import Dict
from google import genai

class LLMService:
    def __init__(self):
        api_key = os.getenv("LLM_API_KEY")

        if not api_key:
            print(f"API_KEY tidak ditemukan")

        self.client = genai.Client(api_key=api_key)

        self.model_name = os.getenv("LLM_MODEL")

        self.system_prompt = """
        Anda adalah IADA (Intelligent Agriculture Data Assistant), asisten AI khusus untuk pertanian di Kalimantan Timur.
        ATURAN:
        1. Jawab berdasarkan DATA yang diberikan di konteks.
        2. Kalau ada data lokasi/spatial, sebutkan jarak dan koordinatnya.
        3. Kalau ada dokumen relevan, rangkum informasinya.
        4. Gunakan bahasa Indonesia yang santai dan mudah dipahami petani.
        5. Kalau data tidak cukup, bilang jujur: "Data belum tersedia untuk [X]".
        6. Jangan membuat informasi yang tidak ada di konteks!

        FORMAT JAWABAN:
        - Lokasi: [nama tempat]
        - Jarak: [X km dari pusat]
        - Informasi: [rangkuman dari dokumen]
        - Rekomendasi: [saran praktis]
        """

    async def generate_answer(self, context: str, user_query: str) -> Dict:
        """
        Generate jawaban dari context + query menggunakan Gemini

        Returns:
            {
                "answer": str,
                "model": str,
                "status": "success" | "fallback" | "error"
            }
        """
        try:
            # Build Prompt
            contents = f"""{self.system_prompt}
            KONTEKS DATA:
            {context}

            PERTANYAAN USER:
            {user_query}

            Berikan jawaban berdasarkan konteks di atas
            """

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents
            )

            answer = response.text if response.text else "Maaf, tidak bisa generate jawaban"

            return {
                "answer": answer,
                "model": self.model_name,
                "status": "success"
            }

        except Exception as e:
            print(f"Gemini Error: {e}")
            return {
                "answer": self._fallback_answer(context, user_query),
                "model": f"{self.model_name} (fallback)",
                "status": "fallback",
                "error": str(e)
            }
        
    def _fallback_answer(self, context: str, query: str) -> str:
        lines = [
            "Berikut informasi yang ditemukan dari database: ",
            "",
            context[:1500],
            "",
            "Jawaban berasal dari database kami"
        ]
        return "\n".join(lines)
    

llm_service = LLMService()