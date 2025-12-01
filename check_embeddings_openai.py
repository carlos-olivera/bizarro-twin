import os
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_openai_embedding():
    print("🧪 Probando Embeddings con OpenAI (Modelo text-embedding-3-small)...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: Falta OPENAI_API_KEY en el archivo .env")
        print("ℹ️  Agrega: OPENAI_API_KEY=sk-...")
        return

    # Cliente específico para OpenAI (separado de DeepSeek)
    client = OpenAI(api_key=api_key)

    try:
        text = "El caos es el orden aún no descifrado."
        
        # Llamada estándar a OpenAI
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        vector = response.data[0].embedding
        dim = len(vector)
        
        print("\n✅ ¡ÉXITO! OpenAI generó el vector.")
        print(f"📊 Dimensión: {dim}")
        
        if dim == 1536:
            print("🟢 COMPATIBLE: Coincide perfectamente con tu tabla Postgres (VECTOR(1536)).")
            print("   Podemos proceder a ensamblar el sistema híbrido.")
        else:
            print(f"⚠️ DIFIERE: La tabla espera 1536, recibimos {dim}.")

    except Exception as e:
        print(f"\n❌ FALLO: {e}")

if __name__ == "__main__":
    test_openai_embedding()