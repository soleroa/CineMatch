# 1. Lo que ya tenías: imports, client, tools
import os
import json
from groq import Groq
from dotenv import load_dotenv

from tools.tmdb_search import buscar_peliculas
from tools.tmdb_reviews import obtener_reviews
from tools.sentiment import analizar_sentiment

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

tools = [
    {
        "type": "function",
        "function": {
            "name": "buscar_peliculas",
            "description": "Busca películas según género y otros filtros",
            "parameters": {
                "type": "object",
                "properties": {
                    "genero": {
                        "type": ["string", "integer"],
                        "description": "ID numérico del género de TMDb (ej: 27 para terror)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_reviews",
            "description": "Obtiene reviews de películas según ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {
                        "type": ["string", "integer"],
                        "description": "ID numérico de la película"
                    }
                },
                "required": ["movie_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_sentiment",
            "description": "Analiza el sentiment de un texto",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Texto a analizar"
                    }
                },
                "required": ["texto"]
            }
        }
    }
]

# 2. NUEVO: la función que arma y corre el loop
def preguntar_agente(mensaje_usuario: str):
    messages = [
        {"role": "system", "content": "Sos un asistente que recomienda películas usando TMDb y análisis de sentiment."},
        {"role": "user", "content": mensaje_usuario}
    ]

    funciones_disponibles = {
        "buscar_peliculas": buscar_peliculas,
        "obtener_reviews": obtener_reviews,
        "analizar_sentiment": analizar_sentiment,
    }

    pasos = []

    while True:
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=600,
            reasoning_format="parsed",
        )

        respuesta = response.choices[0].message

        razonamiento = getattr(respuesta, "reasoning", None)
        if razonamiento:
            pasos.append({"tipo": "razonamiento", "contenido": razonamiento})

        if not respuesta.tool_calls:
            return {"respuesta": respuesta.content, "pasos": pasos}

        messages.append(respuesta)

        for tool_call in respuesta.tool_calls:
            nombre_funcion = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments)

            funcion_real = funciones_disponibles[nombre_funcion]
            resultado = funcion_real(**argumentos)

            pasos.append({
                "tipo": "tool_call",
                "tool": nombre_funcion,
                "argumentos": argumentos,
                "resultado": resultado,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(resultado)
            })

# 3. NUEVO: para probarlo corriendo el archivo directo
if __name__ == "__main__":
    resultado = preguntar_agente("Quiero ver una película de terror, ¿qué me recomendás?")
    print(resultado["respuesta"])
    print(json.dumps(resultado["pasos"], ensure_ascii=False, indent=2))