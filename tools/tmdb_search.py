# TODO: implementar búsqueda de películas contra la API de TMDb (usar TMDB_API_KEY de .env)


import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def buscar_peliculas(genero: str = None, max_duracion: int = None, query: str = None):
    """
    Busca películas en TMDb, opcionalmente filtrando por género o duración.
    """
    url = f"{BASE_URL}/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "sort_by": "popularity.desc",
        "language": "en-US",
    }
    
    if genero:
        params["with_genres"] = genero  # TMDb usa IDs numéricos de género, no texto
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return data["results"]