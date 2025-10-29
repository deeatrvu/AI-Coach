# backend/app/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.models.doctor_persona import PERSONAS
import httpx 
from app.services.evaluation import evaluate_conversation, evaluate_conversation_structured
from pydantic import BaseModel
from typing import Optional

load_dotenv()  # reads .env

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing. Copy .env.example -> .env and set key.")

app = FastAPI(title="MedRep Coach - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=False,  # Set to False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# (Text-mode transcript and evaluate endpoints removed in voice-only cleanup)

class VoiceEvaluationRequest(BaseModel):
    transcript: list[dict]
    persona_id: str
    must_say: Optional[list[str]] = []
    must_not_say: Optional[list[str]] = []

@app.post("/api/voice/evaluate")
async def evaluate_voice_session(req: VoiceEvaluationRequest):
    """Evaluate a voice session with comprehensive feedback."""
    result = evaluate_conversation(req.transcript, req.persona_id, req.must_say, req.must_not_say)
    return result


@app.post("/api/voice/evaluate2")
async def evaluate_voice_session_v2(req: VoiceEvaluationRequest):
    """Structured evaluator returning summary, scores, highlights, actions, violations."""
    result = evaluate_conversation_structured(req.transcript, req.persona_id, req.must_say, req.must_not_say)
    return result

@app.get("/api/personas")
async def list_personas():
    """Return the full list of doctor personas."""
    return PERSONAS


@app.get("/api/personas/{persona_id}")
async def get_persona(persona_id: str):
    """Return a single doctor persona by ID."""
    for p in PERSONAS:
        if p["id"] == persona_id:
            return p
    raise HTTPException(status_code=404, detail="Persona not found")

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/session-token")
async def session_token():
    """
    Create a short-lived Realtime session with OpenAI. The returned JSON
    contains ephemeral session / client_secret data the frontend will use.
    This server endpoint MUST be protected by your server-side OPENAI_API_KEY.
    """
    url = "https://api.openai.com/v1/realtime/sessions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    # minimal payload - adjust model or voice settings as needed
    payload = {
        "model": "gpt-4o-realtime-preview",
        "voice": os.environ.get("OPENAI_REALTIME_VOICE", "verse"),
    }
    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        resp = await client.post(url, headers=headers, json=payload)

    # async with httpx.AsyncClient(timeout=10.0) as client:
    #     resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code >= 400:
        raise HTTPException(status_code=500, detail=f"OpenAI session creation failed: {resp.text}")

    # Return the session JSON (contains ephemeral token/params). Frontend will read what's needed.
    return resp.json()


# ===== Tone decision API (voice-only helper) =====

class ToneStateIn(BaseModel):
    mood: str  # "Neutral"|"Engaged"|"Dismissive"
    timePressure: int  # 0-5
    skepticism: int  # 0-5
    patience: int = 5
    engagement: int = 5
    hypeCount: int = 0
    evidenceCount: int = 0
    monologueCount: int = 0


class ToneDecideIn(BaseModel):
    current_state: ToneStateIn
    last_doctor: str
    last_mr: str


class ToneDecisionOut(BaseModel):
    mood: str
    timePressure: int
    skepticism: int
    action: str
    pauseReply: bool
    cutNow: bool = False
    patience: int = 5
    engagement: int = 5
    hypeCount: int = 0
    evidenceCount: int = 0
    monologueCount: int = 0


def _clip(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


@app.post("/api/tone-decide", response_model=ToneDecisionOut)
async def tone_decide(payload: ToneDecideIn):
    """
    Enhanced tone decision for realistic busy doctor behavior.
    Returns mood, timePressure, skepticism, action, pauseReply, and cutNow flag.
    """
    # Extract state
    mood = payload.current_state.mood
    time_pressure = payload.current_state.timePressure
    skepticism = payload.current_state.skepticism
    patience = payload.current_state.patience
    engagement = payload.current_state.engagement
    hype_count = payload.current_state.hypeCount
    evidence_count = payload.current_state.evidenceCount
    monologue_count = payload.current_state.monologueCount
    
    # Analyze MR's last message
    mr_lower = (payload.last_mr or "").lower()
    
    # Hard stop triggers (cutNow = True)
    cut_now = False
    if hype_count >= 3:  # 3+ hype phrases
        cut_now = True
    elif monologue_count >= 2 and time_pressure >= 4:  # 2+ long monologues under pressure
        cut_now = True
    elif patience <= 1 and any(word in mr_lower for word in ["best", "revolutionary", "amazing"]):
        cut_now = True
    
    # Evidence recognition (immediate engagement boost) - flexible medical criteria
    evidence_patterns = [
        # Statistical evidence
        "n=", "p=", "p-value", "confidence interval", "ci", "hazard ratio", "hr", "odds ratio", "or",
        # Clinical endpoints
        "primary endpoint", "secondary endpoint", "efficacy", "response rate", "remission rate", 
        "progression-free survival", "pfs", "overall survival", "os", "disease-free survival", "dfs",
        # Trial design
        "randomized", "rct", "double-blind", "placebo-controlled", "phase", "multicenter",
        # Safety data
        "adverse events", "ae", "serious adverse events", "sae", "toxicity", "safety profile",
        # Biomarkers
        "biomarker", "genetic", "mutation", "expression", "receptor", "pathway",
        # Real-world evidence
        "real-world", "registry", "observational", "post-marketing", "surveillance",
        # Guidelines/standards
        "guidelines", "consensus", "recommendation", "standard of care", "treatment algorithm"
    ]
    
    if any(pattern in mr_lower for pattern in evidence_patterns):
        evidence_count += 1
        mood = "Engaged"
        time_pressure = max(1, time_pressure - 2)  # Reduce pressure significantly
        skepticism = max(1, skepticism - 1)
        engagement = min(10, engagement + 2)
        action = "Good. Now tell me about the clinical significance and practical implications."
        pause_reply = False
    else:
        # Hype detection (patience drain)
        if any(word in mr_lower for word in ["best", "revolutionary", "amazing", "unbelievable", "game-changing"]):
            hype_count += 1
            patience = max(0, patience - 2)
            mood = "Dismissive"
            time_pressure = min(5, time_pressure + 1)
            skepticism = min(5, skepticism + 1)
            engagement = max(1, engagement - 1)
            action = "I need specifics, not marketing. What's the actual data?"
            pause_reply = False
        
        # Monologue detection (time pressure increase)
        elif len((payload.last_mr or "").split()) > 25:  # Long message
            monologue_count += 1
            patience = max(0, patience - 1)
            mood = "Dismissive"
            time_pressure = min(5, time_pressure + 1)
            action = "I need the key points, not a presentation. Bottom line?"
            pause_reply = False
        
        # Repetition detection
        elif any(phrase in mr_lower for phrase in ["as i said", "like i mentioned", "again", "repeating"]):
            patience = max(0, patience - 1)
            mood = "Dismissive"
            time_pressure = min(5, time_pressure + 1)
            action = "I heard you the first time. What else do you have?"
            pause_reply = False
        
        # Default busy behavior
        else:
            if time_pressure >= 4:
                mood = "Dismissive"
                action = "I have patients waiting. What's the key point?"
                pause_reply = True
            else:
                mood = "Neutral"
                action = "Continue, but be concise."
                pause_reply = False
    
    # Generate ending phrases for cutNow
    if cut_now:
        ending_phrases = [
            "I'm ending this call. Send me the data sheet.",
            "I don't have time for this. Email me the trial results.",
            "I have patients waiting. This conversation is over.",
            "Send me the evidence, not the sales pitch. Goodbye."
        ]
        action = ending_phrases[hype_count % len(ending_phrases)]
        mood = "Dismissive"
        time_pressure = 5
        patience = 0
    
    return ToneDecisionOut(
        mood=mood,
        timePressure=time_pressure,
        skepticism=skepticism,
        action=action,
        pauseReply=pause_reply,
        cutNow=cut_now,
        patience=patience,
        engagement=engagement,
        hypeCount=hype_count,
        evidenceCount=evidence_count,
        monologueCount=monologue_count
    )
