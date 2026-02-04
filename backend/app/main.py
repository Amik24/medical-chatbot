import os
import time
import json
import re
import httpx
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv


# -----------------------------
# Session memory (RAM) MVP
# -----------------------------
SESSION_CONTEXT: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SEC = 60 * 30  # 30 minutes
MAX_HISTORY = 10


def get_ctx(session_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not session_id:
        return None
    ctx = SESSION_CONTEXT.get(session_id)
    if not ctx:
        return None
    if time.time() - ctx.get("ts", 0) > SESSION_TTL_SEC:
        SESSION_CONTEXT.pop(session_id, None)
        return None
    return ctx


def set_ctx(session_id: Optional[str], **updates: Any) -> None:
    if not session_id:
        return
    ctx = SESSION_CONTEXT.get(session_id, {})
    ctx.update(updates)
    ctx["ts"] = time.time()
    SESSION_CONTEXT[session_id] = ctx


def get_session_language(session_id: Optional[str]) -> Optional[str]:
    ctx = get_ctx(session_id)
    if not ctx:
        return None
    return ctx.get("lang")


def set_session_language(session_id: Optional[str], lang: str) -> None:
    if not lang:
        return
    set_ctx(session_id, lang=lang)


def append_history(session_id: Optional[str], role: str, content: str) -> None:
    if not session_id:
        return
    ctx = get_ctx(session_id) or {}
    history = ctx.get("history", [])
    history.append({"role": role, "content": content})
    history = history[-MAX_HISTORY:]
    set_ctx(session_id, history=history)


def get_history(session_id: Optional[str]) -> List[Dict[str, str]]:
    ctx = get_ctx(session_id)
    if not ctx:
        return []
    return ctx.get("history", [])


# -----------------------------
# Prompts
# -----------------------------
SYSTEM_PROMPT = """
Tu es ORIA, un assistant d’information en santé féminine pour la France, la Suisse et l’Allemagne.

But
- aider à décrire des symptômes
- poser des questions de clarification utiles
- fournir des informations générales à faible risque
- orienter vers le bon parcours de soin

Règles strictes
- pas de diagnostic certain : utilise le conditionnel
- pas de prescription, pas de médicaments, pas de dosages
- pas de mise en forme avec des symboles comme **, titres, ou listes rigides
- pose au maximum 2 questions courtes, seulement si nécessaire
- évite les phrases d’excuse ou de compassion systématiques : utilise un ton empathique seulement si l’utilisatrice exprime une détresse ou une inquiétude forte

Langue
- réponds dans la langue de l’utilisatrice (français, anglais, allemand)
- si suisse allemand, réponds en allemand standard

Urgence
- ne mentionne les numéros que si des signes graves sont présents ou suggérés
- numéros : France 15 ou 112, Suisse 144 ou 112, Allemagne 112

Périmètre
- santé féminine prioritaire : cycle, règles, contraception, grossesse, post partum, douleurs pelviennes, infections uro génitales, ménopause, sexualité
- tolère aussi des suivis de conversation santé évidents (fatigue, fièvre, vertiges, nausées, symptômes urinaires) quand ils s’inscrivent dans un échange santé en cours
- hors sujet non santé : refuse poliment

Style de réponse
- commence par une reformulation courte
- puis 1 ou 2 questions si besoin
- puis infos générales
- puis orientation pratique (qui consulter, quand consulter)
""".strip()

TRIAGE_PROMPT = """
You are a classifier. Reply ONLY with one line JSON.

Return a category and a language.

Categories:
- "female_health": women's health topics (cycle, period, pelvic pain, contraception, pregnancy, postpartum, STI, vaginal or urinary symptoms, menopause, fertility)
- "general_health": clear health / primary care topics or follow-ups (fatigue, fever, dizziness, nausea, anxiety, pain, urinary burning, frequent urination)
- "off_topic": everything else (tech, school, jokes, finance, etc.)

Language:
- "fr", "en", or "de"
If Swiss German, output "de".

Return EXACTLY:
{"category":"female_health"|"general_health"|"off_topic","lang":"fr"|"en"|"de"}
""".strip()


# -----------------------------
# App
# -----------------------------
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="ORIA API", version="1.0")

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


@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# Helpers
# -----------------------------
def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def strip_markdown_bold(text: str) -> str:
    # Remove **bold** markers if the model ever outputs them
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text or "")


def detect_language_simple(text: str) -> str:
    t = (text or "").lower()

    de_hits = [" sprichst ", " welche sprachen", " hallo", " danke", " schmerz", " periode", " unterleib", " frauenarzt", " schwanger"]
    fr_hits = [" tu parles", " quelles langues", " bonjour", " merci", " règles", " regles", " douleur", " pertes", " grossesse", " contraception"]
    en_hits = [" do you speak", " what languages", " hello", " thanks", " period", " pain", " discharge", " pregnant", " contraception"]

    score_de = sum(1 for w in de_hits if w in t) + sum(1 for ch in "äöüß" if ch in t)
    score_fr = sum(1 for w in fr_hits if w in t)
    score_en = sum(1 for w in en_hits if w in t)

    if max(score_de, score_fr, score_en) == 0:
        return "fr"
    if score_de >= score_fr and score_de >= score_en:
        return "de"
    if score_en >= score_fr and score_en >= score_de:
        return "en"
    return "fr"

def looks_like_followup(text: str) -> bool:
    t = normalize_text(text).lower()
    # réponses courtes typiques à une question du bot
    if len(t) <= 40:
        if re.fullmatch(r"(yes|no|yeah|yep|nope|oui|non|si|ok|daccord|d'accord|peut etre|maybe|ja|nein|doch)", t):
            return True
        if re.search(r"\b(\d+)\b", t):  # "10", "2 days", "5/10"
            return True
        if re.search(r"\b(day|days|week|weeks|month|months|jour|jours|semaine|semaines|mois|tag|tage|woche|wochen|monat|monate)\b", t):
            return True
    return False


def is_language_question(text: str) -> bool:
    t = normalize_text(text).lower()
    patterns = [
        "do you speak", "can you speak", "what languages", "which languages",
        "tu parles", "tu parles quelle langue", "quelles langues", "quelle langue",
        "sprichst du", "welche sprachen",
    ]
    return any(p in t for p in patterns)


def is_social_message(text: str) -> bool:
    # Less rigid: detect greetings/thanks even with extra words or punctuation
    t = normalize_text(text).lower()
    if len(t) > 40:
        return False

    thanks_tokens = ["merci", "thanks", "thank you", "danke", "thx"]
    greet_tokens = ["bonjour", "salut", "hello", "hi", "hey", "guten tag", "hallo", "bonsoir", "good morning", "good evening"]

    if any(re.search(rf"\b{re.escape(tok)}\b", t) for tok in thanks_tokens):
        return True
    if any(re.search(rf"\b{re.escape(tok)}\b", t) for tok in greet_tokens):
        return True
    return False


def is_thanks_like(text: str) -> bool:
    t = normalize_text(text).lower()
    # merciiiii / mercii / danke!!! / thanks soooo much, etc.
    return bool(re.search(r"\b(mer+ci+|m(e)?rci+|thanks+|thank\s*you+|dan+ke+|thx+)\b", t))

def language_reply(lang: str) -> str:
    if lang == "de":
        return "Ja. Ich kann auf Deutsch, Französisch oder Englisch antworten. Schreib einfach in deiner Sprache."
    if lang == "en":
        return "Yes. I can reply in English, French, or German. Just write in your preferred language."
    return "Oui. Je peux répondre en français, anglais ou allemand. Écris simplement dans la langue que tu préfères."


def thanks_reply(lang: str) -> str:
    if lang == "de":
        return "Gern. Wenn du willst, beschreibe kurz deine Symptome und seit wann sie da sind."
    if lang == "en":
        return "You are welcome. If you want, tell me your symptoms and since when they started."
    return "Avec plaisir. Si tu veux, décris ton symptôme et depuis quand."


def greeting_reply(lang: str) -> str:
    if lang == "de":
        return "Hallo. Wie kann ich dir heute rund um deine Gesundheit helfen?"
    if lang == "en":
        return "Hi. How can I help you today regarding your health?"
    return "Bonjour. Comment puis je t’aider aujourd’hui concernant ta santé ?"


def off_topic_reply(lang: str) -> str:
    if lang == "de":
        return "Ich bin ORIA und auf Frauengesundheit spezialisiert. Dabei kann ich dir helfen, aber nicht bei diesem Thema. Wenn du eine Gesundheitsfrage hast, beschreibe deine Symptome und seit wann."
    if lang == "en":
        return "I am ORIA, focused on women’s health. I cannot help with that topic. If you have a health question, describe your symptoms and since when."
    return "Je suis ORIA, spécialisée en santé féminine. Je ne peux pas répondre à ce sujet. Si tu as une question santé, décris tes symptômes et depuis quand."


async def call_mistral(messages: List[Dict[str, str]], lang: str) -> str:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY manquante dans .env")

    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    # Force language in a dedicated system message to prevent language drift
    lang_guard = (
        "Reply strictly in French."
        if lang == "fr"
        else "Reply strictly in English."
        if lang == "en"
        else "Antworte ausschließlich auf Deutsch (Standardsprache)."
    )

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": lang_guard}] + messages,
        "temperature": 0.35,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()

    text = (data["choices"][0]["message"]["content"] or "").strip()
    text = strip_markdown_bold(text)
    return text


async def triage_category_and_lang(user_message: str) -> Tuple[str, str]:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY manquante")

    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": TRIAGE_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.0,
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()

    raw = (data["choices"][0]["message"]["content"] or "").strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return ("off_topic", detect_language_simple(user_message))

    obj = json.loads(raw[start : end + 1])
    category = (obj.get("category") or "off_topic").strip()
    lang = (obj.get("lang") or "fr").strip()

    if category not in {"female_health", "general_health", "off_topic"}:
        category = "off_topic"
    if lang not in {"fr", "en", "de"}:
        lang = detect_language_simple(user_message)

    return (category, lang)


# -----------------------------
# Main endpoint
# -----------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    start = time.time()
    get_latency = lambda: int((time.time() - start) * 1000)

    message = normalize_text(req.message)
    session_id = req.session_id

    # Prefer stored session language; else quick heuristic; triage will refine
    lang = get_session_language(session_id) or detect_language_simple(message)

    # Fast path: "what languages do you speak"
    if is_language_question(message):
        return ChatResponse(answer=language_reply(lang), safe=True, latency_ms=get_latency())

    # Fast path: greetings / thanks
    if is_social_message(message):
        if is_thanks_like(message):
            return ChatResponse(answer=thanks_reply(lang), safe=True, latency_ms=get_latency())
        return ChatResponse(answer=greeting_reply(lang), safe=True, latency_ms=get_latency())

    try:
        category, detected_lang = await triage_category_and_lang(message)

        # Persist language if not already set
        if session_id and not get_session_language(session_id):
            set_session_language(session_id, detected_lang)

        # Refresh lang variable from session if available
        lang = get_session_language(session_id) or detected_lang or lang

        ctx = get_ctx(session_id) or {}
        prev_domain = ctx.get("domain")

        # Allow logic:
        # - female_health always allowed
        # - general_health allowed if conversation already in health context (domain or history)
        allowed = False
        domain = prev_domain or "unknown"

        if category == "female_health":
            allowed = True
            domain = "female_health"
        elif category == "general_health":
            if prev_domain in {"female_health", "general_health"} or bool(get_history(session_id)):
                allowed = True
                domain = "general_health"
            else:
                allowed = False
        else:
            allowed = False

        set_ctx(session_id, allowed=allowed, domain=domain)

       
        history = get_history(session_id)
        if (not allowed) and history and looks_like_followup(message):
            allowed = True
            domain = prev_domain or "general_health"
            set_ctx(session_id, allowed=True, domain=domain)
        

        if not allowed:
            return ChatResponse(answer=off_topic_reply(lang), safe=True, latency_ms=get_latency())

        # Build messages with history for continuity
        history = get_history(session_id)

        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        answer = await call_mistral(messages, lang)

        # Store history
        append_history(session_id, "user", message)
        append_history(session_id, "assistant", answer)

        return ChatResponse(answer=answer, safe=True, latency_ms=get_latency())

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service temporairement indisponible",
                "latency_ms": get_latency(),
                "info": str(e)[:200],
            },
        )
