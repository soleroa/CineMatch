# CineMatch

Agente conversacional que recomienda películas usando TMDb y análisis de sentimiento de reviews, orquestado con un loop ReAct sobre Groq.

## Estructura

```
cine-agent/
├── .env                    # API keys (Groq, TMDb)
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                 # entry point / API con FastAPI
├── agent/
│   ├── __init__.py
│   ├── agent.py             # loop ReAct principal
│   └── prompts.py           # system prompt del agente
└── tools/
    ├── __init__.py
    ├── tmdb_search.py        # tool: buscar películas
    ├── tmdb_reviews.py       # tool: traer reviews
    └── sentiment.py          # tool: tu clasificador
```

## Setup

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

## Run

```bash
uvicorn main:app --reload
```
