import os
import time
import random
import asyncio
import traceback
from datetime import datetime, timezone, date
from dotenv import load_dotenv

# Importar nuestros módulos
from src.modules.x_client import x_bot
from src.modules.cognitive import brain
from src.modules.mood_engine import mood_engine
from src.modules.memory_service import memory_service
from src.modules.state_machine import state_machine
from src.core.database import get_db_session
from src.core.models import InteractionLog, MoodLog

# Cargar configuración
load_dotenv()
TARGET_HOST = os.getenv("X_USERNAME") # El usuario al que hacemos "Sombra"

# Configuración de Tiempos (Desde variables de entorno con fallback)
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", 300))
CHECK_INTERVAL_MAX = int(os.getenv("CHECK_INTERVAL_MAX", 900))

def interaction_exists(tweet_id: str) -> bool:
    """Verifica si ya reaccionamos a un tweet específico."""
    if not tweet_id:
        return False
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        return session.query(InteractionLog).filter_by(tweet_id=tweet_id).first() is not None
    except Exception as e:
        print(f"❌ Error verificando DB: {e}")
        return False
    finally:
        session.close()

def last_daily_post_date() -> date | None:
    """Devuelve la fecha del último daily_post registrado."""
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        last_daily = (
            session.query(InteractionLog)
            .filter_by(action_type="daily_post")
            .order_by(InteractionLog.created_at.desc())
            .first()
        )
        if last_daily:
            return last_daily.created_at.date()
        return None
    except Exception as e:
        print(f"❌ Error consultando último daily: {e}")
        return None
    finally:
        session.close()

def extract_text(tweet) -> str:
    """Obtiene el texto de un tweet de forma segura."""
    if tweet is None:
        return ""
    if hasattr(tweet, "text"):
        return tweet.text
    if isinstance(tweet, dict):
        return tweet.get("text", "")
    return str(tweet)

async def run_autonomy_cycle():
    print(f"\n🌀 --- INICIANDO CICLO DE AUTONOMÍA ---")
    
    # ---------------------------------------------------------
    # 1. PERCEPCIÓN: Obtener contexto (host, menciones, daily)
    # ---------------------------------------------------------
    now = datetime.now(timezone.utc)

    # Host: buscar último tweet no respondido
    host_tweet = None
    try:
        print(f"👁️ Escaneando perfil de @{TARGET_HOST}...")
        tweets = await x_bot.client.search_tweet(f"from:{TARGET_HOST}", product="Latest")
        if tweets:
            candidate = tweets[0]
            if not interaction_exists(getattr(candidate, "id", None)):
                host_tweet = candidate
    except Exception as e:
        print(f"❌ Error leyendo X (host): {e}")

    # Menciones: obtener notificaciones y filtrar no respondidas
    mentions = []
    try:
        notifications = await x_bot.get_my_latest_mentions(limit=10)
        for n in notifications:
            tid = getattr(n, "id", None)
            if tid and not interaction_exists(tid):
                mentions.append(n)
    except Exception as e:
        print(f"⚠️ Error obteniendo menciones: {e}")

    allow_daily = last_daily_post_date() != now.date()

    plan = state_machine.decide_action(
        host_tweet=host_tweet,
        mentions=mentions,
        allow_daily=allow_daily,
        current_time=now,
    )

    if not plan:
        print("💤 Sin acciones pendientes en este ciclo.")
        return

    target_text = extract_text(plan.target_tweet) if plan.target_tweet else plan.target_text
    target_id = getattr(plan.target_tweet, "id", None) if plan.target_tweet else None

    # ---------------------------------------------------------
    # 2. ESTADO INTERNO: Consultar Mood y RAG
    # ---------------------------------------------------------
    current_mood = mood_engine.get_current_mood()
    print(f"🌡️ Mood Actual: {current_mood['description']} (V:{current_mood['valence']}, A:{current_mood['arousal']})")

    relevant_memories = memory_service.retrieve_context(target_text)
    print(f"📚 Recuerdos recuperados: {len(relevant_memories)}")
    
    # ---------------------------------------------------------
    # 3. COGNICIÓN: Generar Inversión Bizarra con DeepSeek
    # ---------------------------------------------------------
    print(f"🧠 Pensando respuesta invertida ({plan.reason})...")
    decision = brain.generate_bizarro_thought(
        target_tweet=target_text,
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

    if not final_content or len(final_content) > 280:
        print("⚠️ Tweet inválido (vacío o muy largo). Abortando.")
        return

    # ---------------------------------------------------------
    # 4. ACCIÓN: Publicar en X
    # ---------------------------------------------------------
    action_log_type = "daily_post" if plan.action_type == "daily" else "shadow_quote" if plan.should_quote else "shadow_reply"
    try:
        if plan.action_type == "daily":
            print("🗓️ Publicando DAILY POST")
            await x_bot.post_tweet(final_content)
        else:
            if plan.should_quote:
                print("🎲 Decisión: Publicar como QUOTE TWEET")
                await x_bot.post_tweet(final_content, quote_to_id=target_id)
            else:
                print("🎲 Decisión: Publicar como RESPUESTA (REPLY)")
                await x_bot.post_tweet(final_content, reply_to_id=target_id)
            
        print("🚀 TWEET PUBLICADO EXITOSAMENTE")
        
        # ---------------------------------------------------------
        # 5. PERSISTENCIA: Guardar Log y Actualizar Mood
        # ---------------------------------------------------------
        session_gen_save = get_db_session() 
        session_save = next(session_gen_save)
        
        try:
            log = InteractionLog(
                tweet_id=target_id,
                action_type=action_log_type,
                input_context=target_text,
                generated_content=final_content,
                mood_state=current_mood,
                reward_score=0.0 
            )
            session_save.add(log)
            
            delta_v = decision.get('new_valence_delta', 0)
            delta_a = decision.get('new_arousal_delta', 0)

            new_valence = max(-1.0, min(1.0, current_mood['valence'] + delta_v))
            new_arousal = max(-1.0, min(1.0, current_mood['arousal'] + delta_a))
            
            mood_log = MoodLog(
                valence=new_valence,
                arousal=new_arousal,
                stimulus_type="tweet_posted",
                description=f"Reacción ({action_log_type}) a {target_id or 'daily_post'}"
            )
            session_save.add(mood_log)
            
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
