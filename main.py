from fastapi import FastAPI
from pydantic import BaseModel

from agent.agent import preguntar_agente

app = FastAPI(title="CineMatch API")


class PreguntaRequest(BaseModel):
    mensaje: str


@app.post("/recomendar")
def recomendar(request: PreguntaRequest):
    respuesta = preguntar_agente(request.mensaje)
    return {"respuesta": respuesta}


@app.get("/")
def root():
    return {"status": "CineMatch API funcionando"}