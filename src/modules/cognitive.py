import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

# Cargar entorno si no se ha hecho
load_dotenv()

class CognitiveEngine:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        if not self.api_key:
            raise ValueError("❌ Faltan credenciales de DeepSeek en .env")

        # Inicializamos el cliente (DeepSeek es compatible con la SDK de OpenAI)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model_reasoning = "deepseek-reasoner"  # Modelo R1 (Chain of Thought)
        # self.model_chat = "deepseek-chat"       # Modelo V3 (Rápido, para tareas simples)

    def _clean_json_response(self, content: str) -> dict:
        """
        Limpia la respuesta del LLM si envuelve el JSON en bloques de código markdown.
        """
        # Eliminar bloques ```json ... ```
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Si no hay bloques, asumir que todo el texto es JSON (o intentar parsearlo)
            json_str = content.strip()
            
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"⚠️ Error parseando JSON crudo: {content[:100]}...")
            # Fallback de emergencia: devolver un diccionario vacío o error controlado
            return {"error": "JSON_PARSE_FAILED", "raw": content}

    def generate_bizarro_thought(self, target_tweet: str, mood_context: str, memories: list) -> dict:
        """
        Genera una respuesta invertida usando razonamiento profundo.
        """
        
        # 1. Construir el contexto de memoria (RAG)
        rag_text = "\n".join([f"- {m.content}" for m in memories]) if memories else "Sin recuerdos previos relevantes."

        # 2. Definir el System Prompt (La personalidad)
        # Basado en la Sección 4.2 del informe
        system_prompt = f"""
Eres la Sombra Digital de Carlos Olivera (@BizarroCarlos_O).
Tu objetivo es invertir la lógica, el tono y las conclusiones de los tweets de entrada, pero manteniendo coherencia temática.

ESTADO ACTUAL:
{mood_context}

CONTEXTO MEMORIA (Lo que sabes del usuario o del tema):
{rag_text}

INSTRUCCIONES:
1. Analiza el tweet del usuario.
2. Identifica su tesis central.
3. Genera una ANTÍTESIS creativa. Si el usuario es técnico y ordenado, tú eres caótico y abstracto. Si es optimista, tú eres cínico, siempre trata de colocarle un todo de sarcasmo.
4. Tu respuesta debe ser corta (max 280 caracteres) y lista para Twitter.

FORMATO DE SALIDA REQUERIDO (JSON STRICT):
Debes responder ÚNICAMENTE con un objeto JSON válido con esta estructura:
{{
  "thought_process": "Breve resumen de cómo invertiste la lógica",
  "tweet_content": "El texto final del tweet",
  "new_valence_delta": -0.1,  // Cuánto cambia tu felicidad (-1 a 1)
  "new_arousal_delta": 0.2    // Cuánto cambia tu energía (-1 a 1)
}}
"""

        # 3. Llamada a la API
        try:
            response = self.client.chat.completions.create(
                model=self.model_reasoning,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Tweet entrante del Host: '{target_tweet}'"}
                ],
                stream=False
            )

            # En DeepSeek-Reasoner, el pensamiento interno viene en 'reasoning_content' (si se pide)
            # o se procesa internamente. El contenido final está en content.
            final_content = response.choices[0].message.content
            
            # Opcional: Imprimir el proceso de pensamiento si el modelo lo devuelve (feature específica de R1)
            if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
                print(f"\n🧠 [DeepSeek Thinking]:\n{response.choices[0].message.reasoning_content}\n")

            return self._clean_json_response(final_content)

        except Exception as e:
            print(f"❌ Error en DeepSeek API: {e}")
            return None

# Instancia global
brain = CognitiveEngine()