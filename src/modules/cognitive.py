import os
import json
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Cargar entorno si no se ha hecho
load_dotenv()

class CognitiveEngine:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.system_prompt_path = Path(
            os.getenv("SYSTEM_PROMPT_PATH", "config/system_prompt.txt")
        )
        
        if not self.api_key:
            raise ValueError("❌ Faltan credenciales de DeepSeek en .env")
        
        if not self.system_prompt_path.exists():
            raise FileNotFoundError(
                f"❌ No se encontró el System Prompt en {self.system_prompt_path}. "
                "Define SYSTEM_PROMPT_PATH o crea el archivo con el prompt."
            )

        # Inicializamos el cliente (DeepSeek es compatible con la SDK de OpenAI)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model_reasoning = "deepseek-reasoner"  # Modelo R1 (Chain of Thought)
        # self.model_chat = "deepseek-chat"       # Modelo V3 (Rápido, para tareas simples)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """
        Carga el System Prompt desde un archivo externo.
        Se mantiene fuera del repositorio por seguridad/opsec.
        """
        try:
            return self.system_prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"❌ Error leyendo System Prompt: {e}") from e

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

        # 2. Definir el System Prompt (La personalidad) inyectando contexto dinámico
        system_prompt = self.system_prompt.format(
            mood_context=mood_context,
            rag_text=rag_text,
        )
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
