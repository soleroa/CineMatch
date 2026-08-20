# CineMatch

Conversational agent that recommends movies using TMDb and sentiment analysis of reviews, orchestrated with a ReAct loop over Groq. Sentiment analysis runs on a custom model, trained and published on Hugging Face Hub. Includes a React (Vite) frontend with a chat interface that shows the agent's thinking process.

## Structure

```
CineMatch/
├── .env                      # API keys (Groq, TMDb) — not committed to the repo
├── .env.example               # backend environment variables template
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                    # entry point / FastAPI API
├── agent/
│   ├── __init__.py
│   ├── agent.py                # main ReAct loop (preguntar_agente)
│   └── prompts.py               # agent system prompt
├── tools/
│   ├── __init__.py
│   ├── tmdb_search.py            # tool: search movies (buscar_peliculas)
│   ├── tmdb_reviews.py           # tool: fetch reviews (obtener_reviews)
│   └── sentiment.py               # tool: sentiment classifier (analizar_sentiment)
└── frontend/                   # React chat (Vite)
    ├── .env.example              # frontend environment variables template
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                # chat UI, calls the /recomendar endpoint
        ├── App.css
        └── index.css              # theme tokens (light/dark)
```

## How the agent works

`agent/agent.py` builds a manual ReAct loop with the Groq SDK:

1. Sends the user's message to the model along with the spec of the three `tools`, requesting `reasoning_format="parsed"` so the model returns its reasoning (`message.reasoning`) separate from the final content.
2. On each loop turn, if the model returned reasoning, it's saved as a `razonamiento` (reasoning) step in the `pasos` (steps) list.
3. If the model responds with `tool_calls`, it executes the corresponding real function (`buscar_peliculas`, `obtener_reviews`, or `analizar_sentiment`), saves a `tool_call` step (tool, arguments, and result) in `pasos`, adds the result to `messages` with role `tool`, and calls the model again.
4. When the model no longer requests tools, it returns `{"respuesta": ..., "pasos": [...]}`: the final text and the full trace of reasoning + tool calls that led to that response.

| Tool               | Real function (`tools/`)                  | Parameters                      | Model used |
| ------------------ | ----------------------------------------- | -------------------------------- | --------------- |
| `buscar_peliculas` | `tmdb_search.buscar_peliculas`            | `genero` (numeric TMDb ID)   | — (direct call to the TMDb API) |
| `obtener_reviews`  | `tmdb_reviews.obtener_reviews`            | `movie_id` (numeric ID)         | — (direct call to the TMDb API) |
| `analizar_sentiment` | `sentiment.analizar_sentiment`          | `texto`                          | `soleroa/movie-review-classifier` (custom, see [Models used](#models-used)) |

The system prompt lives in `agent/prompts.py` (`SYSTEM_PROMPT`).

## Thinking process in the frontend

The backend exposes the full reasoning trace in `POST /recomendar`, in the `pasos` field. Each element is one of:

```jsonc
// model reasoning before deciding what to do
{ "tipo": "razonamiento", "contenido": "..." }

// a tool the agent decided to execute
{
  "tipo": "tool_call",
  "tool": "buscar_peliculas",
  "argumentos": { "genero": 27 },
  "resultado": [ /* raw tool response */ ]
}
```

In `frontend/src/App.jsx`, every assistant bubble that has `pasos` shows a collapsible **"View thinking process (N)"** button. Opening it lists, in order, each step: the reasoning text or, for tool calls, the tool name, the arguments it was called with, and the raw result it returned. The styles are in `frontend/src/App.css` (`.proceso*` classes) and use the theme tokens from `index.css`, so they respect light/dark mode.

## Setup — Backend

1. Create the virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate it:

   ```bash
   # macOS / Linux
   source .venv/bin/activate

   # Windows (cmd)
   .venv\Scripts\activate.bat

   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env  # fill in GROQ_API_KEY and TMDB_API_KEY
   ```

5. To exit the virtual environment when you're done:

   ```bash
   deactivate
   ```

## Setup — Frontend

The frontend is in `frontend/`, built with React + Vite. Requires Node.js installed.

1. Install dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. (Optional) configure the backend URL, if you're not using `http://localhost:8000`:

   ```bash
   cp .env.example .env
   # edit VITE_API_URL in frontend/.env
   ```

## Run

You need two terminals running simultaneously: one for the backend, one for the frontend.

```bash
# Terminal 1 — backend (from the project root)
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

Open `http://localhost:5173` in your browser and chat with CineMatch.

## API

The backend (`main.py`) exposes:

- `GET /` — health check, returns `{"status": "CineMatch API funcionando"}`.
- `POST /recomendar` — body `{"mensaje": "..."}`, returns `{"respuesta": "...", "pasos": [...]}`: the agent's final response and the reasoning + tool calls trace (see [Thinking process in the frontend](#thinking-process-in-the-frontend)).

CORS is enabled only for `http://localhost:5173` (Vite's default port). If you serve the frontend from another origin (a different port, a production domain), you need to add it to `allow_origins` in `main.py`.

## Models used

CineMatch uses two different models, for two different tasks:

### 1. Orchestrator LLM (Groq)

The ReAct loop in `agent/agent.py` runs on `qwen/qwen3.6-27b`, hosted on Groq. It's the model that decides which tools to call, in what order, and builds the final response — and the one that produces the `razonamiento` (reasoning) shown in the frontend's thinking process (via `reasoning_format="parsed"`).

If you ever see `Internal Server Error` in the frontend, check the backend console:
- **`429 rate_limit_exceeded`**: the tokens-per-minute (TPM) limit for your Groq tier was exceeded (the system prompt + tool specs + history + reasoning can accumulate tokens quickly in long conversations). Wait a few seconds between consecutive tests, or upgrade your tier at [console.groq.com/settings/billing](https://console.groq.com/settings/billing).
- **`400 tool_use_failed`**: the model generated a malformed tool call and Groq couldn't parse it (happens occasionally with models that don't have tool calling 100% fine-tuned). Retrying the message usually resolves it; if it's very frequent, consider switching back to a model with more mature tool support (e.g. `openai/gpt-oss-20b`).
- **`404 model_not_found`**: the configured model is no longer available on your account. Run this snippet to see the models currently enabled and pick one with tool support:

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

### 2. Sentiment classifier (custom model)

The `analizar_sentiment` tool (`tools/sentiment.py`) **does not** call Groq or any paid external API: it runs a custom model locally, trained and published on Hugging Face Hub as [`soleroa/movie-review-classifier`](https://huggingface.co/soleroa/movie-review-classifier). It's loaded with `transformers` (`AutoTokenizer` + `AutoModelForSequenceClassification`) and classifies a review's text as `"Positivo"` (Positive) or `"Negativo"` (Negative).

Notes about this model:
- The weights are downloaded from HF Hub the first time the backend starts (module-level import in `tools/sentiment.py`), and are cached locally afterward. On that first startup you'll see `Loading weights` logs — this is expected.
- If you see the warning `You are sending unauthenticated requests to the HF Hub`, it's because you haven't configured `HF_TOKEN`. It's not required, but without a token the download is slower and subject to Hugging Face's anonymous rate limit. To avoid it, generate a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and add it to your `.env` as `HF_TOKEN=...`.
- Since it's a local model (not an HTTP call to Groq), it doesn't consume Groq tokens or count toward the orchestrator LLM's rate limit.
