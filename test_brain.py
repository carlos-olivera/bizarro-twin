import sys
from src.modules.cognitive import brain

# Simulamos un objeto de memoria simple (Mock)
class MockMemory:
    def __init__(self, content):
        self.content = content

def test_thinking():
    print("🧠 Despertando a DeepSeek-Reasoner...")
    
    # 1. Simulación de Input (Un tweet típico de un CEO Tech)
    input_tweet = "La inteligencia artificial descentralizada es el futuro de la soberanía digital. Debemos construir sistemas robustos y transparentes."
    print(f"\n📢 Tweet del Host: '{input_tweet}'")

    # 2. Simulación de Contexto
    mock_memories = [
        MockMemory("Carlos valora la estructura y la lógica."),
        MockMemory("En el pasado, critiqué la centralización de datos.")
    ]
    
    current_mood = "Valencia: -0.2 (Ligeramente irritado), Arousal: 0.6 (Alerta/Tenso)"

    # 3. Ejecutar el Cerebro
    result = brain.generate_bizarro_thought(input_tweet, current_mood, mock_memories)

    if result:
        print("\n⚡ RESULTADO GENERADO (JSON):")
        print("-" * 40)
        print(f"🤔 Lógica Invertida: {result.get('thought_process')}")
        print(f"🐦 Tweet Bizarro:    {result.get('tweet_content')}")
        print(f"📉 Cambio Emocional: V={result.get('new_valence_delta')}, A={result.get('new_arousal_delta')}")
        print("-" * 40)
        
        # Validación de longitud de Twitter
        if len(result.get('tweet_content', '')) > 280:
            print("⚠️ ADVERTENCIA: El tweet excede 280 caracteres.")
        else:
            print("✅ Longitud de tweet válida.")
    else:
        print("❌ Falló la generación del pensamiento.")

if __name__ == "__main__":
    test_thinking()