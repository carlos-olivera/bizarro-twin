from sqlalchemy import select, desc
from src.core.database import get_db_session
from src.core.models import MoodLog

class MoodEngine:
    def __init__(self):
        self.decay_factor = 0.95  # Factor de retorno al equilibrio (0.0)

    def get_current_mood(self):
        """Recupera el último estado emocional y aplica decaimiento temporal."""
        session_gen = get_db_session()
        session = next(session_gen)
        
        try:
            # Obtener el último log registrado
            last_log = session.query(MoodLog).order_by(desc(MoodLog.id)).first()
            
            if not last_log:
                # Estado inicial por defecto
                return {
                    "valence": 0.0, 
                    "arousal": 0.0, 
                    "description": "Neutral (Inicio de sistema)"
                }

            # Aplicar inercia: el tiempo suaviza las emociones extremas
            current_valence = last_log.valence * self.decay_factor
            current_arousal = last_log.arousal * self.decay_factor
            
            return {
                "valence": round(current_valence, 3),
                "arousal": round(current_arousal, 3),
                "description": self._describe_mood(current_valence, current_arousal)
            }
        finally:
            session.close()

    def _describe_mood(self, v, a):
        """Traduce coordenadas numéricas (Valence, Arousal) a instrucciones de texto para el LLM."""
        if v > 0.3 and a > 0.3: return "Eufórico y Maníaco. Usa signos de exclamación, sé intenso."
        if v > 0.3 and a < -0.3: return "Relajado y Zen. Sé benevolente y pacífico."
        if v < -0.3 and a > 0.3: return "Iracundo y Agresivo. Busca conflicto, sé cortante."
        if v < -0.3 and a < -0.3: return "Depresivo y Nihilista. Sé oscuro, breve y desesperanzado."
        return "Analítico y Distante (Neutral)."

# Instancia global
mood_engine = MoodEngine()