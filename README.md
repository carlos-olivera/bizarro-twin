# 🌑 Gemelo Bizarro (Project Bizarro)

> **Un experimento en Agentes Cognitivos Autónomos, Psicología Junguiana y Arquitectura Post-API.**

## ⚠️ Disclaimer Crítico

Este software opera en una "Zona Gris" técnica. Utiliza **Twikit** para emular la interacción de un navegador con X (Twitter) debido a las restricciones de la API oficial.

- **Riesgo de Ban:** El uso agresivo de este software puede resultar en la suspensión de la cuenta.
- **Autonomía:** El agente toma decisiones propias basadas en su estado emocional. No es determinista.
- **Uso:** Este proyecto es puramente educativo y experimental.

## 🧠 El Concepto

**Gemelo Bizarro** no es un bot de spam. Es una **Sombra Digital**.

Basado en el arquetipo de la Sombra de Carl Jung y el personaje "Bizarro" de los cómics, este agente se conecta a la cuenta de un usuario humano (el "Host"), lee sus pensamientos (tweets) e invierte su lógica mediante un motor de razonamiento profundo.

Si el Host busca orden, el Gemelo celebra el caos. Si el Host es optimista, el Gemelo es nihilista. Todo esto, mantenido por un **Motor Emocional (Valence-Arousal)** que hace que el bot tenga "días buenos" y "días malos".

## 🏗 Arquitectura

El sistema corre *on-premise* (Linux/Fedora) para garantizar la soberanía de los datos.

- **Cerebro (Razonamiento):** `DeepSeek-Reasoner (R1)` para Chain-of-Thought (CoT).
- **Memoria (RAG):** `PostgreSQL 16` + `pgvector`. Almacena experiencias y las recupera semánticamente.
- **Vectores:** `OpenAI text-embedding-3-small` (1536 dimensiones).
- **Interfaz:** `Twikit` (Emulación de cliente Web).
- **Orquestación:** Python asíncrono + Systemd.

## 🚀 Instalación y Despliegue

### Prerrequisitos

- Fedora/Debian/Ubuntu Server.
- PostgreSQL 16 con extensión `vector` compilada.
- Python 3.11+.

### 1. Clonar y Entorno

```
git clone [https://github.com/tu-usuario/gemelo-bizarro.git](https://github.com/tu-usuario/gemelo-bizarro.git)
cd gemelo-bizarro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Base de Datos

Crea una base de datos `bizarro_mind` y habilita la extensión:

```
CREATE EXTENSION vector;
-- Las tablas se definen en src/core/models.py
```

### 3. Configuración (.env)

Copia el archivo de ejemplo y configura tus llaves:

```
cp .env.example .env
```

Necesitas:

- `DATABASE_URL`: Postgres connection string.
- `DEEPSEEK_API_KEY`: Para el razonamiento.
- `OPENAI_API_KEY`: Para los embeddings (memoria).
- `X_USERNAME`: El usuario "Host" a imitar.

### 4. Inyección de Cookies (Cirugía)

El bot no hace login con contraseña. Debes extraer las cookies `auth_token` y `ct0` de una sesión válida de navegador y colocarlas en `data/cookies/cookies.json`.

### 5. Ejecución

```
python main.py
```

## 🤝 Contribución

Este es un proyecto Open Source. Se buscan contribuciones en:

1. **Refinamiento del Prompt:** Mejorar la personalidad en `src/modules/cognitive.py`.
2. **Seguridad:** Mejorar la evasión de detección de bots en `src/modules/x_client.py`.
3. **Visualización:** Crear un dashboard web para ver el estado emocional del bot en tiempo real.

## 📄 Licencia

MIT License. Úsalo bajo tu propio riesgo.
