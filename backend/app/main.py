import os
import time
from typing import Optional
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Medical Chatbot API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None, max_length=80)

class ChatResponse(BaseModel):
    answer: str
    safe: bool = True
    latency_ms: int

SYSTEM_PROMPT = """
Tu es un assistant d'information santé. Tu ne remplaces pas un médecin.
- Ne jamais diagnostiquer avec certitude.
- Pas de prescription, pas de dosage précis.
- Si urgence possible (douleur thoracique, détresse respiratoire, confusion, faiblesse d'un côté, saignement important, réaction allergique sévère, convulsions, aggravation rapide): recommander 15 ou 112.
- Si manque d'infos: poser 2 à 4 questions.
- Donner conseils à faible risque: repos, hydratation, surveillance, consulter si aggravation.
- Terminer par: "Je ne suis pas un médecin..."
""".strip()

@app.get("/health")
def health():
    return {"status": "ok"}

async def call_mistral(user_message: str) -> str:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY manquante dans .env")

    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message.strip()},
        ],
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()

    return data["choices"][0]["message"]["content"].strip()

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    start = time.time()
    try:
        answer = await call_mistral(req.message)
        latency_ms = int((time.time() - start) * 1000)
        return ChatResponse(answer=answer, safe=True, latency_ms=latency_ms)
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM unavailable or timeout",
                "latency_ms": latency_ms,
                "info": str(e)[:200],
            },
        )
