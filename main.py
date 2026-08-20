from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import preguntar_agente

app = FastAPI(title="CineMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreguntaRequest(BaseModel):
    mensaje: str


@app.post("/recomendar")
def recomendar(request: PreguntaRequest):
    resultado = preguntar_agente(request.mensaje)
    return {"respuesta": resultado["respuesta"], "pasos": resultado["pasos"]}


@app.get("/")
def root():
    return {"status": "CineMatch API funcionando"}