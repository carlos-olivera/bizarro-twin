import os
from openai import OpenAI
from sqlalchemy import select
from dotenv import load_dotenv
from src.core.database import get_db_session
from src.core.models import SemanticMemory

load_dotenv()

class MemoryService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY requerida para generar embeddings de memoria.")
        
        # Cliente dedicado solo para embeddings
        self.client = OpenAI(api_key=api_key)

    def get_embedding(self, text):
        """Genera vector de 1536 dimensiones usando OpenAI."""
        try:
            text = text.replace("\n", " ") # Normalización básica
            response = self.client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ Error generando embedding: {e}")
            # Retornar vector vacío en caso de fallo crítico para no detener el bot
            return [0.0] * 1536

    def retrieve_context(self, query_text, limit=3):
        """Busca recuerdos semánticamente similares en Postgres."""
        query_vector = self.get_embedding(query_text)
        
        session_gen = get_db_session()
        session = next(session_gen)
        
        try:
            # Búsqueda por similitud de coseno (operador <=>)
            results = session.scalars(
                select(SemanticMemory)
                .order_by(SemanticMemory.embedding.cosine_distance(query_vector))
                .limit(limit)
            ).all()
            
            return results
        except Exception as e:
            print(f"❌ Error recuperando memoria: {e}")
            return []
        finally:
            session.close()

    def save_memory(self, content, source_type, metadata=None):
        """Guarda un nuevo recuerdo (ej. tweet propio o del host)."""
        vector = self.get_embedding(content)
        
        session_gen = get_db_session()
        session = next(session_gen)
        
        try:
            mem = SemanticMemory(
                content=content,
                embedding=vector,
                source_type=source_type,
                metadata_=metadata or {}
            )
            session.add(mem)
            session.commit()
            print(f"💾 Memoria guardada: '{content[:30]}...'")
        except Exception as e:
            print(f"❌ Error guardando memoria: {e}")
            session.rollback()
        finally:
            session.close()

# Instancia global
memory_service = MemoryService()