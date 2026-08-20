# CineMatch

Agente conversacional que recomienda películas usando TMDb y análisis de sentimiento de reviews, orquestado con un loop ReAct sobre Groq. Incluye un frontend en React (Vite) con interfaz de chat.

## Estructura

```
CineMatch/
├── .env                      # API keys (Groq, TMDb) — no se sube al repo
├── .env.example               # plantilla de variables de entorno del backend
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                    # entry point / API con FastAPI
├── agent/
│   ├── __init__.py
│   ├── agent.py                # loop ReAct principal (preguntar_agente)
│   └── prompts.py               # system prompt del agente
├── tools/
│   ├── __init__.py
│   ├── tmdb_search.py            # tool: buscar películas (buscar_peliculas)
│   ├── tmdb_reviews.py           # tool: traer reviews (obtener_reviews)
│   └── sentiment.py               # tool: clasificador de sentiment (analizar_sentiment)
└── frontend/                   # chat en React (Vite)
    ├── .env.example              # plantilla de variables de entorno del frontend
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                # UI de chat, llama al endpoint /recomendar
        ├── App.css
        └── index.css              # tokens de tema (claro/oscuro)
```

## Cómo funciona el agente

`agent/agent.py` arma un loop ReAct manual con el SDK de Groq:

1. Manda el mensaje del usuario al modelo junto con la ficha de las tres `tools`.
2. Si el modelo responde con `tool_calls`, ejecuta la función real correspondiente (`buscar_peliculas`, `obtener_reviews` o `analizar_sentiment`), agrega el resultado a `messages` como rol `tool`, y vuelve a llamar al modelo.
3. Cuando el modelo ya no pide más tools, devuelve `respuesta.content` como texto final.

| Tool               | Función real (`tools/`)                  | Parámetros                      |
| ------------------ | ----------------------------------------- | -------------------------------- |
| `buscar_peliculas` | `tmdb_search.buscar_peliculas`            | `genero` (ID numérico de TMDb)   |
| `obtener_reviews`  | `tmdb_reviews.obtener_reviews`            | `movie_id` (ID numérico)         |
| `analizar_sentiment` | `sentiment.analizar_sentiment`          | `texto`                          |

El system prompt vive en `agent/prompts.py` (`SYSTEM_PROMPT`).

## Setup — Backend

1. Crear el entorno virtual:

   ```bash
   python -m venv .venv
   ```

2. Activarlo:

   ```bash
   # macOS / Linux
   source .venv/bin/activate

   # Windows (cmd)
   .venv\Scripts\activate.bat

   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Configurar las variables de entorno:

   ```bash
   cp .env.example .env  # completar GROQ_API_KEY y TMDB_API_KEY
   ```

5. Para salir del entorno virtual cuando termines:

   ```bash
   deactivate
   ```

## Setup — Frontend

El frontend está en `frontend/`, hecho con React + Vite. Requiere Node.js instalado.

1. Instalar las dependencias:

   ```bash
   cd frontend
   npm install
   ```

2. (Opcional) configurar la URL del backend, si no vas a usar `http://localhost:8000`:

   ```bash
   cp .env.example .env
   # editar VITE_API_URL en frontend/.env
   ```

## Run

Necesitás dos terminales corriendo en simultáneo: una para el backend, otra para el frontend.

```bash
# Terminal 1 — backend (desde la raíz del proyecto)
source .venv/bin/activate
uvicorn main:app --reload
# → http://localhost:8000
```

```bash
# Terminal 2 — frontend
cd frontend
npm run dev
# → http://localhost:5173
```

Abrí `http://localhost:5173` en el navegador y chateá con CineMatch.

## API

El backend (`main.py`) expone:

- `GET /` — health check, devuelve `{"status": "CineMatch API funcionando"}`.
- `POST /recomendar` — body `{"mensaje": "..."}`, devuelve `{"respuesta": "..."}` con la respuesta del agente.

CORS está habilitado solo para `http://localhost:5173` (el puerto default de Vite). Si servís el frontend desde otro origen (otro puerto, un dominio de producción), hay que agregarlo a `allow_origins` en `main.py`.

## Problema conocido: rate limit de Groq

El modelo configurado en `agent/agent.py` (`openai/gpt-oss-120b`) tiene, en el tier gratuito/on-demand de Groq, un límite de **8000 tokens por minuto**. El prompt del sistema + las tres fichas de tools + el historial de conversación pueden superar ese límite y Groq responde `413 rate_limit_exceeded`, que en la API se ve como `Internal Server Error`.

Opciones para evitarlo:
- Cambiar a un modelo con mayor límite de TPM en el tier gratuito (ej. `llama-3.1-8b-instant`).
- Upgradear el tier de Groq (Dev Tier) desde [console.groq.com/settings/billing](https://console.groq.com/settings/billing).
- Esperar a que se libere la ventana de un minuto entre pruebas seguidas.
