import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DeepSeekEmbeddingTester:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("❌ Error: DEEPSEEK_API_KEY no encontrada en .env")
            
        # URL basada en la documentación/snippet encontrado
        self.api_url = "https://api.deepseek.com/v1/embeddings"
        # Usaremos el modelo por defecto sugerido
        self.model = "deepseek-embedding" 
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_embedding(self, text):
        print(f"📡 Conectando a {self.api_url} con modelo '{self.model}'...")
        
        payload = {
            "model": self.model,
            "input": text 
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️ Error HTTP {response.status_code}")
                print(f"Respuesta: {response.text}")
                return None
            
            result = response.json()
            
            # Extraer el primer embedding
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0]["embedding"]
                return embedding
            else:
                print(f"⚠️ Estructura de respuesta inesperada: {result}")
                return None

        except Exception as e:
            print(f"❌ Excepción durante la petición: {str(e)}")
            return None

def main():
    print("🧪 Iniciando prueba de DeepSeek Embeddings...")
    
    try:
        tester = DeepSeekEmbeddingTester()
        
        test_text = "El caos es el orden aún no descifrado."
        vector = tester.get_embedding(test_text)
        
        if vector:
            dim = len(vector)
            print("\n✅ ¡ÉXITO! Se generó el embedding correctamente.")
            print(f"📊 Dimensión del vector: {dim}")
            print(f"🔢 Primeros 5 valores: {vector[:5]}...")
            
            if dim == 1536:
                print("🟢 Compatible con configuración actual de Postgres (VECTOR(1536)).")
            else:
                print(f"⚠️ ATENCIÓN: La dimensión es {dim}. Debes ajustar la tabla 'semantic_memory' en Postgres.")
                print(f"   SQL Sugerido: ALTER TABLE semantic_memory ALTER COLUMN embedding TYPE vector({dim});")
        else:
            print("\n❌ FALLO: No se pudo obtener el embedding. Revisa la API Key o el nombre del modelo.")

    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()