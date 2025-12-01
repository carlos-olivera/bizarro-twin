import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Cargar entorno
load_dotenv()
print(f"✅ Entorno cargado para agente: {os.getenv('AGENT_NAME')}")

# 2. Verificar DeepSeek Key (sin mostrarla toda)
key = os.getenv("DEEPSEEK_API_KEY")
if key:
    print(f"✅ API Key detectada: {key[:5]}...")
else:
    print("❌ Faltan credenciales de DeepSeek")

# 3. Probar conexión a Base de Datos
db_url = os.getenv("DATABASE_URL")
try:
    engine = create_engine(db_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print(f"✅ Conexión exitosa a DB: {result.fetchone()[0]}")
        
        # Verificar extensión vector
        vec_check = connection.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector';"))
        if vec_check.fetchone():
             print(f"✅ Extensión pgvector activa.")
        else:
             print(f"❌ pgvector NO detectado.")
             
except Exception as e:
    print(f"❌ Error de conexión a DB: {e}")

print("\nListo para comenzar el desarrollo de módulos.")