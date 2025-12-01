import asyncio
from src.modules.x_client import x_bot

async def main():
    print("🕵️ Iniciando prueba de conexión con X...")
    try:
        # Intentar login
        await x_bot.login()
        
        # Prueba de lectura: Buscar un tweet popular (ej. Elon Musk o una cuenta de noticias)
        # Esto valida que podemos leer el timeline
        print("\n🔍 Probando lectura de timeline...")
        tweets = await x_bot.client.search_tweet("Elon Musk", product="Top")
        
        if tweets:
            print(f"✅ Lectura exitosa. Tweet encontrado: {tweets[0].text[:50]}...")
        else:
            print("⚠️ Login ok, pero no se encontraron tweets (¿Shadowban?).")

    except Exception as e:
        print(f"\n❌ PRUEBA FALLIDA: {e}")

if __name__ == "__main__":
    asyncio.run(main())