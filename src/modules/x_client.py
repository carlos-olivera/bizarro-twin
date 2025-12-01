import os
import json
import asyncio
import inspect
from twikit import Client
from tenacity import retry, stop_after_attempt, wait_exponential

# Rutas de archivos
COOKIES_PATH = "data/cookies/cookies.json"

class XClient:
    def __init__(self):
        # Inicializamos el cliente simulando ser Chrome en Windows o Linux
        self.client = Client(language="es-MX")
        self.user = None
        # Cacheamos la firma de create_tweet para compatibilidad de versiones
        try:
            self._create_tweet_params = set(inspect.signature(self.client.create_tweet).parameters.keys())
        except Exception:
            self._create_tweet_params = set()

    async def login(self):
        """
        Intenta iniciar sesión usando cookies guardadas.
        Si fallan, NO intenta login con password (por seguridad),
        sino que pide intervención humana.
        """
        if not os.path.exists(COOKIES_PATH):
            raise FileNotFoundError(
                f"❌ No se encontró {COOKIES_PATH}. Debes exportar las cookies manualmente primero."
            )

        print(f"🍪 Cargando cookies desde {COOKIES_PATH}...")
        self.client.load_cookies(COOKIES_PATH)

        try:
            # Verificamos si la sesión es válida obteniendo datos del usuario actual
            self.user = await self.client.user()
            print(f"✅ Login exitoso como: @{self.user.screen_name} (ID: {self.user.id})")
            
            # Guardamos las cookies actualizadas (Twikit refresca tokens internamente)
            self.client.save_cookies(COOKIES_PATH)
            
        except Exception as e:
            print(f"❌ Error de autenticación: {e}")
            print("⚠️ SUGERENCIA: Tus cookies pueden haber expirado. Extrae unas nuevas del navegador.")
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def post_tweet(self, text, reply_to_id=None, quote_to_id=None):
        """
        Publica un tweet con manejo de reintentos.
        Soporta responder o quotear dependiendo de los IDs provistos.
        """
        if not self.user:
            await self.login()

        if quote_to_id:
            print(f"🚀 Publicando QUOTE a {quote_to_id}: {text[:30]}...")
            tweet = await self._create_with_quote(text, quote_to_id)
        elif reply_to_id:
            print(f"🚀 Publicando RESPUESTA a {reply_to_id}: {text[:30]}...")
            tweet = await self._create_with_reply(text, reply_to_id)
        else:
            print(f"🚀 Publicando TWEET NUEVO: {text[:30]}...")
            tweet = await self.client.create_tweet(text)
            
        return tweet

    async def _create_with_quote(self, text: str, quote_to_id: str):
        """
        Maneja compatibilidad de parámetros para quotear según la versión de Twikit.
        """
        params = self._create_tweet_params
        # Modo preferido si existe
        if "quote_tweet_id" in params:
            return await self.client.create_tweet(text, quote_tweet_id=quote_to_id)
        if "quote" in params:
            return await self.client.create_tweet(text, quote=quote_to_id)
        # Último recurso: adjuntar la URL manualmente en el texto (sin attachment_url para evitar BadRequest)
        url = f"https://x.com/i/web/status/{quote_to_id}"
        return await self.client.create_tweet(f"{text} {url}")

    async def _create_with_reply(self, text: str, reply_to_id: str):
        """
        Maneja compatibilidad de parámetros para replies según la versión de Twikit.
        """
        params = self._create_tweet_params
        if "reply_to" in params:
            return await self.client.create_tweet(text, reply_to=reply_to_id)
        if "reply_to_tweet_id" in params:
            return await self.client.create_tweet(text, reply_to_tweet_id=reply_to_id)
        # Último recurso: menciona manualmente al usuario al responder
        return await self.client.create_tweet(text)

    async def get_my_latest_mentions(self, limit=10, notif_type="all"):
        """
        Obtiene menciones para el ciclo de respuesta.
        Twikit requiere el parámetro 'type' en get_notifications (ej. 'all', 'mention').
        """
        if not self.user:
            await self.login()
        
        # Nota: Twikit recupera notificaciones, hay que filtrar menciones
        # Esta es una implementación simplificada para prueba
        return await self.client.get_notifications(type=notif_type, count=limit)

# Instancia global para importar en otros lados
x_bot = XClient()
