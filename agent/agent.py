from agent.prompts import SYSTEM_PROMPT
from tools.tmdb_search import buscar_peliculas
from tools.tmdb_reviews import get_reviews
from tools.sentiment import classify_sentiment

# TODO: instanciar cliente Groq (usar GROQ_API_KEY de .env)

TOOLS = {
    "buscar_peliculas": buscar_peliculas,
    "get_reviews": get_reviews,
    "classify_sentiment": classify_sentiment,
}


def run_agent(user_message: str) -> str:
    """Loop ReAct principal: piensa, elige tool, actúa, observa, repite hasta responder."""
    # TODO: implementar el loop ReAct (thought -> action -> observation -> ... -> final answer)
    raise NotImplementedError
