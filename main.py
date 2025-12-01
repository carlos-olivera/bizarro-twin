import os
import time
import random
import asyncio
import traceback
from dotenv import load_dotenv

# Importar nuestros módulos
from src.modules.x_client import x_bot
from src.modules.cognitive import brain
from src.modules.mood_engine import mood_engine
from src.modules.memory_service import memory_service
from src.core.database import get_db_session
from src.core.models import InteractionLog, MoodLog

# Cargar configuración
load_dotenv()
TARGET_HOST = os.getenv("X_USERNAME") # El usuario al que hacemos "Sombra"

# Configuración de Tiempos (Desde variables de entorno con fallback)
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", 300))
CHECK_INTERVAL_MAX = int(os.getenv("CHECK_INTERVAL_MAX", 900))

async def run_autonomy_cycle():
    print(f"\n🌀 --- INICIANDO CICLO DE AUTONOMÍA ---")
    
    # ---------------------------------------------------------
    # 1. PERCEPCIÓN: Obtener el último tweet del Host
    # ---------------------------------------------------------
    try:
        print(f"👁️ Escaneando perfil de @{TARGET_HOST}...")
        tweets = await x_bot.client.search_tweet(f"from:{TARGET_HOST}", product="Latest")
        
        if not tweets:
            print("💤 No se encontraron tweets recientes.")
            return

        latest_tweet = tweets[0]
        tweet_text = latest_tweet.text
        tweet_id = latest_tweet.id
        print(f"🎯 Tweet detectado ({tweet_id}): {tweet_text[:50]}...")

    except Exception as e:
        print(f"❌ Error leyendo X: {e}")
        return

    # ---------------------------------------------------------
    # 2. MEMORIA: ¿Ya reaccionamos a este ID?
    # ---------------------------------------------------------
    session_gen_check = get_db_session()
    session_check = next(session_gen_check)
    
    try:
        exists = session_check.query(InteractionLog).filter_by(tweet_id=tweet_id).first()
        if exists:
            print("⏭️ Ya reaccioné a este tweet. Ignorando.")
            return
    except Exception as e:
         print(f"❌ Error verificando DB: {e}")
         return
    finally:
        session_check.close()

    # ---------------------------------------------------------
    # 3. ESTADO INTERNO: Consultar Mood y RAG
    # ---------------------------------------------------------
    current_mood = mood_engine.get_current_mood()
    print(f"🌡️ Mood Actual: {current_mood['description']} (V:{current_mood['valence']}, A:{current_mood['arousal']})")

    # Recuperar recuerdos relevantes (RAG)
    relevant_memories = memory_service.retrieve_context(tweet_text)
    print(f"📚 Recuerdos recuperados: {len(relevant_memories)}")
    
    # ---------------------------------------------------------
    # 4. COGNICIÓN: Generar Inversión Bizarra con DeepSeek
    # ---------------------------------------------------------
    print("🧠 Pensando respuesta invertida...")
    decision = brain.generate_bizarro_thought(
        target_tweet=tweet_text,
        mood_context=f"Estado: {current_mood['description']}",
        memories=relevant_memories
    )

    if not decision:
        print("❌ El cerebro no produjo respuesta (JSON inválido o error API).")
        return

    final_content = decision.get('tweet_content')
    thought_process = decision.get('thought_process')
    
    print(f"💡 Pensamiento: {thought_process}")
    print(f"🗣️ Decisión: {final_content}")

    # Validaciones de seguridad antes de postear
    if not final_content or len(final_content) > 280:
        print("⚠️ Tweet inválido (vacío o muy largo). Abortando.")
        return

    # ---------------------------------------------------------
    # 5. ACCIÓN: Publicar en X
    # ---------------------------------------------------------
    action_log_type = "shadow_reply" # Default action changed to reply
    
    try:
        # Lógica de Quote Probabilística
        is_quote_candidate = (random.random() < (1 / 3))
        should_quote = is_quote_candidate and (random.random() < 0.5)

        if should_quote:
            print("🎲 Decisión Aleatoria: Publicar como QUOTE TWEET")
            # CORRECCIÓN: Twikit 2.x usa 'quote' en lugar de 'quote_tweet_id'
            await x_bot.client.create_tweet(final_content, quote=tweet_id)
            action_log_type = "shadow_quote"
        else:
            print("🎲 Decisión Aleatoria: Publicar como RESPUESTA (REPLY)")
            # Nota: x_bot.post_tweet ya fue corregido para usar 'reply_to' internamente
            await x_bot.post_tweet(final_content, reply_to_id=tweet_id)
            
        print("🚀 TWEET PUBLICADO EXITOSAMENTE")
        
        # ---------------------------------------------------------
        # 6. PERSISTENCIA: Guardar Log y Actualizar Mood
        # ---------------------------------------------------------
        session_gen_save = get_db_session() 
        session_save = next(session_gen_save)
        
        try:
            # 6.1 Guardar Log de Interacción
            log = InteractionLog(
                tweet_id=tweet_id,
                action_type=action_log_type,
                input_context=tweet_text,
                generated_content=final_content,
                mood_state=current_mood,
                reward_score=0.0 
            )
            session_save.add(log)
            
            # 6.2 Calcular nuevo estado de ánimo
            delta_v = decision.get('new_valence_delta', 0)
            delta_a = decision.get('new_arousal_delta', 0)

            # Clamping
            new_valence = max(-1.0, min(1.0, current_mood['valence'] + delta_v))
            new_arousal = max(-1.0, min(1.0, current_mood['arousal'] + delta_a))
            
            mood_log = MoodLog(
                valence=new_valence,
                arousal=new_arousal,
                stimulus_type="tweet_posted",
                description=f"Reacción ({action_log_type}) a {tweet_id}"
            )
            session_save.add(mood_log)
            
            # 6.3 Guardar memoria propia
            memory_service.save_memory(
                content=f"Dije: {final_content}", 
                source_type="self_reflection"
            )
            
            session_save.commit()
            print("💾 Persistencia completada correctamente.")
            
        except Exception as db_e:
            print(f"❌ Error guardando en DB: {db_e}")
            session_save.rollback()
        finally:
            session_save.close()
        
    except Exception as e:
        print(f"❌ Error crítico en fase de Acción/Persistencia: {type(e).__name__}: {e}")
        traceback.print_exc()

async def main_loop():
    """Bucle infinito con Jitter y manejo de errores"""
    print("🤖 SISTEMA 'GEMELO BIZARRO' ONLINE")
    print("-----------------------------------")
    print(f"⏱️ Configuración de Intervalos: {CHECK_INTERVAL_MIN}s - {CHECK_INTERVAL_MAX}s")
    
    # Intento de login inicial
    try:
        await x_bot.login()
    except Exception as e:
        print("🚨 Error crítico en login inicial. Verifica cookies.json.")
        return

    while True:
        try:
            await run_autonomy_cycle()
        except Exception as e:
            print(f"💥 Error no manejado en el ciclo principal: {e}")
            traceback.print_exc()
        
        # Dormir aleatoriamente
        sleep_time = random.randint(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
        next_run = time.strftime('%H:%M:%S', time.localtime(time.time() + sleep_time))
        print(f"💤 Durmiendo {sleep_time} segundos (próximo ciclo: {next_run})...")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido manualmente.")