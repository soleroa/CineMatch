import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def obtener_reviews(movie_id: int):
    """
    Trae las reviews de una película específica por su ID de TMDb.
    """
    url = f"{BASE_URL}/movie/{movie_id}/reviews"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["results"]


if __name__ == "__main__":
    # Inception, para probar con algo que sabemos tiene reviews
    reviews = obtener_reviews(27205)
    for r in reviews[:3]:
        print(r["author"], "-", r["content"][:150], "...")
        print("---")