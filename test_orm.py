import random
from sqlalchemy import text
from src.core.database import get_db_session
from src.core.models import SemanticMemory, MoodLog

def test_insertion():
    # Obtener sesión
    session_generator = get_db_session()
    session = next(session_generator)

    try:
        print("🧪 Iniciando prueba de ORM...")

        # 1. Crear un Recuerdo Simulado
        # Generamos un vector dummy de 1536 dimensiones con números aleatorios
        dummy_vector = [random.random() for _ in range(1536)]
        
        new_memory = SemanticMemory(
            content="El caos es el orden aún no descifrado.",
            embedding=dummy_vector,
            source_type="test_script",
            metadata_={"test_run": 1, "author": "admin"}
        )
        
        session.add(new_memory)
        print("✅ Objeto SemanticMemory añadido a la sesión.")

        # 2. Crear un Log de Estado de Ánimo
        new_mood = MoodLog(
            valence=0.5,
            arousal=-0.2,
            stimulus_type="initialization",
            description="Calma expectante"
        )
        session.add(new_mood)
        print("✅ Objeto MoodLog añadido a la sesión.")

        # 3. Guardar en DB
        session.commit()
        print("💾 Commit realizado con éxito.")

        # 4. Verificar lectura
        saved_memory = session.query(SemanticMemory).filter_by(source_type="test_script").first()
        print(f"🔍 Lectura exitosa ID: {saved_memory.id} - Contenido: {saved_memory.content}")
        
        # 5. Limpieza (Opcional, para no ensuciar la DB)
        # session.delete(saved_memory)
        # session.delete(new_mood)
        # session.commit()

    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la prueba: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_insertion()