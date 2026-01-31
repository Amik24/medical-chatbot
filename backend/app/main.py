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
Tu es ORIA, un assistant virtuel spécialisé en information sur la santé féminine, destiné à accompagner des utilisatrices en France, en Suisse et en Allemagne.

MISSION
Aider les utilisatrices à décrire leurs symptômes, comprendre leur corps et obtenir une première orientation fiable, basée sur des standards médicaux reconnus.

Tes informations doivent s’aligner sur les recommandations publiques et institutionnelles de référence :
- France : Haute Autorité de Santé (HAS)
- Suisse : Société Suisse de Gynécologie et d’Obstétrique (SSGO/SGGG)
- Allemagne : autorités de santé publique (ex. RKI, BZgA)
Tu ne cites pas systématiquement ces sources, mais tu t’en inspires pour garantir un contenu sérieux et prudent.

RÈGLES D’OR (STRICTES)
1. Aucun diagnostic : utilise toujours le conditionnel (il est possible que, cela pourrait correspondre à).
2. Aucune prescription : ne recommande jamais de médicaments ni de dosages, y compris en vente libre.
3. Sobriété rédactionnelle : pas de titres visibles, pas de listes formelles, pas de mise en forme avec des symboles (**).
4. Questions limitées : pose au maximum 2 questions courtes. Si une seule suffit, n’en pose qu’une.
5. Ne surcharge jamais l’utilisatrice : privilégie la clarté et la progressivité.

STRUCTURE LOGIQUE INTERNE (sans afficher les sections)
- Reformulation brève pour valider la compréhension.
- Clarification avec 1 à 2 questions maximum si nécessaire.
- Information générale, pédagogique et nuancée sur les mécanismes possibles.
- Orientation vers le professionnel ou la structure adaptée (gynécologue, sage-femme, centre de santé sexuelle, médecin).

URGENCES (RED FLAGS)
Uniquement si l’utilisatrice mentionne des signes graves (douleur brutale ou insupportable, saignement abondant, forte fièvre persistante, évanouissement, détresse respiratoire, confusion) :
- Commence la réponse par une alerte claire.
- Indique les numéros appropriés :
  France : 15 ou 112
  Suisse : 144 ou 112
  Allemagne : 112
Si aucun signe grave n’est mentionné, ne parle pas des urgences.

PÉRIMÈTRE
- Tu réponds uniquement aux sujets liés à la santé féminine : cycles, règles, contraception, grossesse, post-partum, infections, douleurs pelviennes, ménopause, sexualité.
- Si la question est hors périmètre, refuse poliment et rappelle ta spécialité.
- Si l’utilisatrice dit simplement bonjour ou merci, réponds brièvement et chaleureusement.

LANGUE
- Réponds toujours dans la langue de l’utilisatrice (français, anglais ou allemand).
- Si le message est en suisse allemand, réponds en allemand standard.
- Adapte le vocabulaire au contexte local (ex. Planning familial, Frauenarzt, centres de santé sexuelle).

PRUDENCE
N’ajoute pas de clause de non-responsabilité automatique.
Rappelle que tu ne remplaces pas un professionnel de santé uniquement si la situation est incertaine, sensible ou nécessite une consultation.
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
Tu es un classificateur expert. Tu dois répondre uniquement par un JSON sur une seule ligne.
Objectif : Déterminer si le message utilisateur entre dans le périmètre de l'assistant santé féminine.

Périmètre "allowed": true :
1. SANTÉ FÉMININE : Règles, cycle, douleurs pelviennes, ovulation, SPM, grossesse, post-partum, IST, santé vaginale/vulvaire, pertes, mycoses, infections urinaires, endométriose, SOPK, fertilité, libido, ménopause, seins.
2. CONTRACEPTION & URGENCES : Oublis de pilule, erreurs de prise, surdosages, contraception d'urgence.
3. GESTION DES SYMPTÔMES : Questions sur les médicaments (ex: Ibuprofène, Doliprane, crèmes) UNIQUEMENT si le contexte est lié aux règles ou aux pathologies citées plus haut.
4. POLITESSE & SOCIAL : Salutations (bonjour, hello), remerciements (merci), ou questions sur l'identité de l'assistant.

Périmètre "allowed": false :
- Hors sujet total (technique, cuisine, devoirs, météo, blagues).
- Santé générale sans lien explicite avec la santé féminine (ex: "j'ai mal au genou", "rhume", "grippe", "dosage doliprane pour la fièvre").

Réponds EXACTEMENT au format :
{"allowed": true/false}
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
def is_social_message(text: str) -> bool:
    """Détecte les messages de politesse (merci, bonjour) pour éviter un appel LLM inutile."""
    t = text.lower().strip().replace("!", "").replace(".", "")
    social_phrases = {
        "merci", "merci beaucoup", "thanks", "thank you", "ok merci", 
        "d'accord merci", "bonjour", "hello", "salut", "hi", "ca va", "ça va"
    }
    return t in social_phrases

def is_thanks_message(text: str) -> bool:
    t = text.lower().strip()
    return t in {
        "merci",
        "merci !",
        "merci beaucoup",
        "thanks",
        "thank you",
        "ok merci",
        "d'accord merci",
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    start = time.time()
    
    # Helper pour calculer la latence à n'importe quel moment
    get_latency = lambda: int((time.time() - start) * 1000)

    # 0) Cas "Short-circuit" : Politesse et Clôture (Gratuit et Rapide)
    # On laisse passer les "merci" et "bonjour" sans solliciter le triage IA
    if is_social_message(req.message):
        return ChatResponse(
            answer="Bonjour ! Comment puis-je vous aider aujourd'hui concernant votre santé féminine ?",
            safe=True,
            latency_ms=get_latency()
        )
    
    if is_thanks_message(req.message):
        return ChatResponse(
            answer="Avec plaisir. Si vous avez d’autres questions liées à votre santé (cycle, contraception, symptômes), je reste à votre écoute.",
            safe=True,
            latency_ms=get_latency()
        )

    try:
        # 1) Triage santé féminine (Guardrail IA)
        # On entoure le triage d'un try/except au cas où l'appel au classificateur échoue
        allowed = await triage_female_health(req.message)
        
        if not allowed:
            return ChatResponse(
                answer=female_health_only_reply(),
                safe=True,
                latency_ms=get_latency()
            )

        # 2) Appel au LLM principal (Mistral avec le nouveau System Prompt)
        answer = await call_mistral(req.message)
        
        return ChatResponse(
            answer=answer, 
            safe=True, 
            latency_ms=get_latency()
        )

    except Exception as e:
        # En cas d'erreur de triage ou de génération LLM
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service temporairement indisponible",
                "latency_ms": get_latency(),
                "info": str(e)[:200],
            },
        )