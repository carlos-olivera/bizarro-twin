import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL no está configurada en el archivo .env")

# Crear el motor de conexión
# pool_pre_ping=True ayuda a manejar desconexiones silenciosas de la DB
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase Base para los modelos ORM
class Base(DeclarativeBase):
    pass

# Dependencia para obtener una sesión (patrón Context Manager)
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()