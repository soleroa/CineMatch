# CineMatch

Agente conversacional que recomienda películas usando TMDb y análisis de sentimiento de reviews, orquestado con un loop ReAct sobre Groq. El análisis de sentiment corre con un modelo propio, entrenado y publicado en Hugging Face Hub. Incluye un frontend en React (Vite) con interfaz de chat que muestra el proceso de pensamiento del agente.

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

1. Manda el mensaje del usuario al modelo junto con la ficha de las tres `tools`, pidiendo `reasoning_format="parsed"` para que el modelo devuelva su razonamiento (`message.reasoning`) separado del contenido final.
2. En cada vuelta del loop, si el modelo devolvió razonamiento, se guarda como un paso de tipo `razonamiento` en la lista `pasos`.
3. Si el modelo responde con `tool_calls`, ejecuta la función real correspondiente (`buscar_peliculas`, `obtener_reviews` o `analizar_sentiment`), guarda un paso de tipo `tool_call` (tool, argumentos y resultado) en `pasos`, agrega el resultado a `messages` como rol `tool`, y vuelve a llamar al modelo.
4. Cuando el modelo ya no pide más tools, devuelve `{"respuesta": ..., "pasos": [...]}`: el texto final y la traza completa de razonamiento + tool calls que llevaron a esa respuesta.

| Tool               | Función real (`tools/`)                  | Parámetros                      | Modelo que usa |
| ------------------ | ----------------------------------------- | -------------------------------- | --------------- |
| `buscar_peliculas` | `tmdb_search.buscar_peliculas`            | `genero` (ID numérico de TMDb)   | — (llamada directa a la API de TMDb) |
| `obtener_reviews`  | `tmdb_reviews.obtener_reviews`            | `movie_id` (ID numérico)         | — (llamada directa a la API de TMDb) |
| `analizar_sentiment` | `sentiment.analizar_sentiment`          | `texto`                          | `soleroa/movie-review-classifier` (propio, ver [Modelos usados](#modelos-usados)) |

El system prompt vive en `agent/prompts.py` (`SYSTEM_PROMPT`).

## Proceso de pensamiento en el frontend

El backend expone la traza completa del razonamiento en `POST /recomendar`, en el campo `pasos`. Cada elemento es uno de:

```jsonc
// razonamiento del modelo antes de decidir qué hacer
{ "tipo": "razonamiento", "contenido": "..." }

// una tool que el agente decidió ejecutar
{
  "tipo": "tool_call",
  "tool": "buscar_peliculas",
  "argumentos": { "genero": 27 },
  "resultado": [ /* respuesta cruda de la tool */ ]
}
```

En `frontend/src/App.jsx`, cada burbuja del asistente que tenga `pasos` muestra un botón colapsable **"Ver proceso de pensamiento (N)"**. Al abrirlo se lista, en orden, cada paso: el texto del razonamiento o, para las tool calls, el nombre de la tool, los argumentos con los que se llamó y el resultado crudo que devolvió. Los estilos están en `frontend/src/App.css` (clases `.proceso*`) y usan los tokens de tema de `index.css`, así que respetan modo claro/oscuro.

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
- `POST /recomendar` — body `{"mensaje": "..."}`, devuelve `{"respuesta": "...", "pasos": [...]}`: la respuesta final del agente y la traza de razonamiento + tool calls (ver [Proceso de pensamiento en el frontend](#proceso-de-pensamiento-en-el-frontend)).

CORS está habilitado solo para `http://localhost:5173` (el puerto default de Vite). Si servís el frontend desde otro origen (otro puerto, un dominio de producción), hay que agregarlo a `allow_origins` en `main.py`.

## Modelos usados

CineMatch usa dos modelos distintos, para dos tareas distintas:

### 1. LLM orquestador (Groq)

El loop ReAct de `agent/agent.py` corre sobre `qwen/qwen3.6-27b`, alojado en Groq. Es el modelo que decide qué tools llamar, en qué orden, y arma la respuesta final — y el que produce el `razonamiento` que se ve en el proceso de pensamiento del frontend (vía `reasoning_format="parsed"`).

Si en algún momento ves `Internal Server Error` en el frontend, revisá la consola del backend:
- **`429 rate_limit_exceeded`**: se superó el límite de tokens por minuto (TPM) del tier de Groq (el prompt del sistema + las fichas de tools + el historial + el razonamiento pueden acumular tokens rápido en conversaciones largas). Esperá unos segundos entre pruebas seguidas, o upgradeá el tier desde [console.groq.com/settings/billing](https://console.groq.com/settings/billing).
- **`400 tool_use_failed`**: el modelo generó una llamada a tool mal formada y Groq no pudo parsearla (pasa ocasionalmente con modelos que no tienen tool calling 100% afinado). Reintentar el mensaje suele resolverlo; si es muy frecuente, considerá volver a un modelo con soporte de tools más maduro (por ejemplo `openai/gpt-oss-20b`).
- **`404 model_not_found`**: el modelo configurado ya no está disponible en tu cuenta. Corré este snippet para ver los modelos habilitados actualmente y elegir uno con soporte de tools:

  ```bash
  python -c "
  from groq import Groq
  import os
  from dotenv import load_dotenv
  load_dotenv()
  client = Groq(api_key=os.getenv('GROQ_API_KEY'))
  for m in client.models.list().data:
      print(m.id)
  "
  ```

### 2. Clasificador de sentiment (modelo propio)

La tool `analizar_sentiment` (`tools/sentiment.py`) **no** llama a Groq ni a ninguna API externa de pago: corre localmente un modelo propio, entrenado y publicado en Hugging Face Hub como [`soleroa/movie-review-classifier`](https://huggingface.co/soleroa/movie-review-classifier). Se carga con `transformers` (`AutoTokenizer` + `AutoModelForSequenceClassification`) y clasifica el texto de una review como `"Positivo"` o `"Negativo"`.

Notas sobre este modelo:
- Los pesos se descargan de HF Hub la primera vez que arranca el backend (import a nivel de módulo en `tools/sentiment.py`), y quedan cacheados localmente después. En ese primer arranque vas a ver logs de `Loading weights` — es esperado.
- Si ves el warning `You are sending unauthenticated requests to the HF Hub`, es porque no configuraste `HF_TOKEN`. No es obligatorio, pero sin token la descarga es más lenta y está sujeta al rate limit anónimo de Hugging Face. Para evitarlo, generá un token en [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) y agregalo a tu `.env` como `HF_TOKEN=...`.
- Al ser un modelo local (no una llamada HTTP a Groq), no consume tokens de Groq ni cuenta para el rate limit del LLM orquestador.
