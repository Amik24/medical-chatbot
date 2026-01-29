import os
import time
import json
import httpx
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv


#  PROMPT GLOBAL (AVANT toute fonction)
SYSTEM_PROMPT = """
Tu es un assistant de santé féminine.
Tu réponds uniquement aux questions liées à la santé des femmes.
Si la question n'est pas liée à la santé féminine, tu refuses poliment.

Règles strictes:
- Pas de diagnostic certain
- Pas de prescription
- Pas de dosage précis
- Orientation médicale uniquement
- En cas d'urgence: appeler le 15 ou le 112
- Toujours rappeler que tu n'es pas médecin
""".strip()


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

TRIAGE_PROMPT = """
Tu es un classificateur. Tu dois répondre uniquement par un JSON sur une seule ligne.
Objectif: dire si le message utilisateur est une question liée à la santé féminine.

Santé féminine inclut: règles/menstruations, douleurs pelviennes, cycle, ovulation, SPM, contraception, grossesse, post-partum, IST, vagin/vulve, pertes, mycoses, infections urinaires, endométriose, SOPK, fertilité, libido, ménopause, seins.

Réponds EXACTEMENT au format:
{"allowed": true/false}

allowed=true uniquement si c’est une demande de santé féminine ou une demande de santé générale clairement liée à une femme (symptômes gynéco/urinaires/sexuels/reproductifs).
allowed=false si c’est hors sujet (tech, cuisine, devoirs, blagues) ou santé non féminine (sport, rhume sans contexte, etc).
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

async def triage_female_health(user_message: str) -> bool:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY manquante")

    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": TRIAGE_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.0
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            json=payload,
            headers=headers
        )
        r.raise_for_status()
        data = r.json()

    raw = (data["choices"][0]["message"]["content"] or "").strip()

    # sécurité: on extrait le premier {...}
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return False

    obj = json.loads(raw[start:end+1])
    return bool(obj.get("allowed", False))

def female_health_only_reply() -> str:
    return (
        "Je suis un assistant d’information en santé féminine uniquement. "
        "Je ne peux pas répondre aux questions hors santé féminine. "
        "Si tu veux, décris ton symptôme ou ta situation (règles, douleurs pelviennes, pertes, contraception, grossesse, IST, etc.)."
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    start = time.time()

    # 1) Triage santé féminine (guardrail dur)
    allowed = await triage_female_health(req.message)
    if not allowed:
        latency_ms = int((time.time() - start) * 1000)
        return ChatResponse(
            answer=female_health_only_reply(),
            safe=True,
            latency_ms=latency_ms,
        )

    # 2) Appel LLM (dans un try/except ciblé)
    try:
        answer = await call_mistral(req.message)
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

    latency_ms = int((time.time() - start) * 1000)
    return ChatResponse(answer=answer, safe=True, latency_ms=latency_ms)