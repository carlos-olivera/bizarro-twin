"""
Script de prueba manual para publicar un reply y/o quote al último tweet del host.
No guarda historial en DB; solo valida la funcionalidad de publicación.

Uso:
    python manual_post_test.py --mode both
Opciones:
    --mode reply    -> solo reply
    --mode quote    -> solo quote
    --mode both     -> reply y luego quote

Requiere:
    - Cookies válidas en data/cookies/cookies.json
    - Variable de entorno X_USERNAME con el usuario host (o --host)
"""

import argparse
import asyncio
import os
from dotenv import load_dotenv

from src.modules.x_client import x_bot

load_dotenv()


async def run_test(mode: str, host: str):
    print(f"🔧 Modo de prueba: {mode} | Host: {host}")

    # Login
    await x_bot.login()

    # Obtener último tweet del host
    tweets = await x_bot.client.search_tweet(f"from:{host}", product="Latest")
    if not tweets:
        print("❌ No se encontraron tweets del host.")
        return

    latest = tweets[0]
    tweet_id = getattr(latest, "id", None)
    tweet_text = getattr(latest, "text", "")
    print(f"🎯 Último tweet del host ({tweet_id}): {tweet_text[:80]}...")

    # Mensajes de prueba
    reply_text = "Test REPLY automático (se debe borrar)."
    quote_text = "Test QUOTE automático (se debe borrar)."

    # Ejecutar acciones según modo
    if mode in ("reply", "both"):
        print(f"🚀 Enviando REPLY a {tweet_id}: {reply_text}")
        await x_bot.post_tweet(reply_text, reply_to_id=tweet_id)

    if mode in ("quote", "both"):
        print(f"🚀 Enviando QUOTE a {tweet_id}: {quote_text}")
        await x_bot.post_tweet(quote_text, quote_to_id=tweet_id)

    print("✅ Prueba finalizada (no se guardó historial).")


def main():
    parser = argparse.ArgumentParser(description="Prueba manual de reply/quote al último tweet del host.")
    parser.add_argument("--mode", choices=["reply", "quote", "both"], default="both", help="Acciones a ejecutar")
    parser.add_argument("--host", default=os.getenv("X_USERNAME", "@carlos_olivera"), help="Usuario host (sin @ opcional)")
    args = parser.parse_args()

    # Normalizar host: quitar doble arroba si viene con @
    host = args.host.lstrip("@")

    asyncio.run(run_test(args.mode, host))


if __name__ == "__main__":
    main()
