from fastapi import FastAPI
from pydantic import BaseModel

from agent.agent import run_agent

app = FastAPI(title="CineMatch")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # TODO: invocar run_agent(request.message) y devolver la respuesta
    reply = run_agent(request.message)
    return ChatResponse(reply=reply)
