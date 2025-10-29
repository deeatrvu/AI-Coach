# backend/app/api/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services import transcript_service
from app.models import doctor_persona
from app.services.persona_engine import DoctorState, update_state, create_system_prompt
from app.models.doctor_persona import PERSONAS
import os
import httpx
from datetime import datetime

router = APIRouter()


class Message(BaseModel):
    role: str  # "rep" or "doctor"
    timestamp: Optional[str] = None
    content: str


class TranscriptIn(BaseModel):
    session_id: Optional[str] = None
    messages: List[Message]


class EvaluateIn(BaseModel):
    session_id: Optional[str] = None
    messages: List[Message]
    must_say: Optional[List[str]] = []
    must_not_say: Optional[List[str]] = []
    persona_id: Optional[str] = None


@router.post("/transcripts")
async def save_transcript(payload: TranscriptIn):
    """
    Persist the transcript (simple file storage). Returns session_id.
    """
    sid = transcript_service.save_transcript(payload.dict())
    return {"session_id": sid}


@router.post("/evaluate")
async def evaluate(payload: EvaluateIn):
    """
    Placeholder endpoint: for now just saves transcript and returns a stub.
    We'll wire the evaluation logic (LLM + compliance) in the next step.
    """
    # Save transcript (ensures we have a session id and stored file)
    sid = transcript_service.save_transcript(payload.dict())

    # Minimal response — evaluation service will replace this logic later
    return {
        "session_id": sid,
        "status": "queued",
        "message": "Transcript saved. Evaluation will be provided by evaluation-service (coming next)."
    }


@router.get("/personas")
async def list_personas():
    """
    Return available doctor personas (static). See app/models/doctor_persona.py
    """
    return {"personas": doctor_persona.PERSONAS}


# ===== Conversation lifecycle (REST) =====

class StartConversationIn(BaseModel):
    persona_id: str


@router.post("/conversation/start")
async def start_conversation(payload: StartConversationIn):
    persona = next((p for p in PERSONAS if p["id"] == payload.persona_id), None)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # initialize state using persona baseline
    baseline = persona.get("skepticism_level", "Medium")
    state = DoctorState(
        mood="Neutral",
        time_pressure_level=1,
        stage="Introduction",
        seconds_elapsed=0,
        trust=50,
        current_skepticism_level=baseline,
    )

    session_id = transcript_service.save_transcript({
        "messages": [],
        "persona_id": payload.persona_id,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "state": state.__dict__,
    })

    return {"session_id": session_id, "state": state.__dict__, "persona": persona}


class TurnIn(BaseModel):
    session_id: str
    persona_id: str
    rep_message: Message
    state: dict  # serialized DoctorState from client or last response


@router.post("/conversation/turn")
async def process_turn(payload: TurnIn):
    persona = next((p for p in PERSONAS if p["id"] == payload.persona_id), None)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Load transcript file to append
    record = transcript_service.load_transcript(payload.session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")

    transcript = record["payload"].get("messages", [])
    # append rep message
    rep_msg = payload.rep_message.dict()
    if not rep_msg.get("timestamp"):
        rep_msg["timestamp"] = datetime.utcnow().isoformat() + "Z"
    transcript.append({"role": "rep", "content": rep_msg["content"], "timestamp": rep_msg["timestamp"]})

    # Build prompt and call OpenAI Responses API (text) for JSON tool-free output
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # reconstruct state
    state = DoctorState(**{
        "mood": payload.state.get("mood", "Neutral"),
        "time_pressure_level": payload.state.get("time_pressure_level", 1),
        "stage": payload.state.get("stage", "Introduction"),
        "seconds_elapsed": payload.state.get("seconds_elapsed", 0),
        "trust": payload.state.get("trust", 50),
        "current_skepticism_level": payload.state.get("current_skepticism_level", persona.get("skepticism_level", "Medium")),
    })

    remaining = max(0, int(persona["availableTimeSeconds"]) - int(state.seconds_elapsed))
    system_prompt = create_system_prompt(
        persona=persona,
        state=state,
        remaining_time=remaining,
        conversation_transcript=transcript,
        last_rep_message=rep_msg["content"],
    )

    completion = client.chat.completions.create(
        model=os.environ.get("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Respond in strict JSON as instructed."},
        ],
    )

    content = completion.choices[0].message.content or "{}"
    try:
        import json
        llm_json = json.loads(content)
    except Exception:
        llm_json = {"doctorReply": "Please clarify.", "relevancy": 0, "nextConversationStage": state.stage, "nextMood": state.mood, "signals": []}

    # append doctor reply
    transcript.append({
        "role": "doctor",
        "content": llm_json.get("doctorReply", ""),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    # update state
    new_state = update_state(
        state,
        llm_result=llm_json,
        time_delta=30,
        baseline_skepticism=persona.get("skepticism_level", "Medium"),
    )

    # persist back
    record["payload"]["messages"] = transcript
    record["payload"]["state"] = new_state.__dict__
    transcript_service.save_transcript(record["payload"])  # re-save same session id

    return {
        "state": new_state.__dict__,
        "doctor_reply": llm_json.get("doctorReply"),
        "signals": llm_json.get("signals", []),
        "relevancy": llm_json.get("relevancy", 0),
        "stage": new_state.stage,
        "skepticism": new_state.current_skepticism_level,
        "trust": new_state.trust,
        "time_pressure": new_state.time_pressure_level,
        "transcript": transcript,
    }


class EndConversationIn(BaseModel):
    session_id: str
    persona_id: str


@router.post("/conversation/end")
async def end_conversation(payload: EndConversationIn):
    # For now, just load transcript and return simple evaluation stub
    from app.services.evaluation import evaluate_conversation
    record = transcript_service.load_transcript(payload.session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Map to simple transcript shape expected by evaluator
    simple = [
        {"role": ("user" if m["role"] == "rep" else "doctor"), "content": m["content"]}
        for m in record["payload"].get("messages", [])
    ]
    result = evaluate_conversation(simple, payload.persona_id)
    return {"session_id": payload.session_id, "evaluation": result}


# ===== Tone decision API (heuristic controller) =====

class ToneStateIn(BaseModel):
    mood: str  # "Neutral"|"Engaged"|"Dismissive"
    timePressure: int  # 0-5
    skepticism: int  # 0-5


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


def _clip(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


@router.post("/tone-decide", response_model=ToneDecisionOut)
async def tone_decide(payload: ToneDecideIn):
    state = payload.current_state
    mood = state.mood
    time_pressure = int(state.timePressure)
    skepticism = int(state.skepticism)

    last_mr = (payload.last_mr or "").lower()
    last_doc = (payload.last_doctor or "").lower()

    # Rule 1: vague hype words
    hype = any(w in last_mr for w in ["best", "revolutionary", "amazing"])
    if hype:
        skepticism += 2
        time_pressure += 1
        if mood != "Dismissive":
            mood = "Dismissive"

    # Rule 2: concrete RCT markers (rough heuristic)
    mentions_trial = any(w in last_mr for w in ["trial", "rct", "randomized"]) 
    mentions_stats = any(w in last_mr for w in ["p=", "p-value", "p value", "%", "n="])
    if mentions_trial and mentions_stats:
        skepticism -= 1
        if mood != "Dismissive":
            mood = "Engaged"

    # Rule 3: interruptions under pressure (approx: if doctor asked to be brief and MR is long)
    long_mr = len(last_mr.split()) > 25
    doc_pressure_keywords = any(w in last_doc for w in ["quick", "time", "brief", "short"])
    if long_mr and (time_pressure >= 3 or doc_pressure_keywords):
        time_pressure += 1

    # Clip values
    time_pressure = _clip(time_pressure, 0, 5)
    skepticism = _clip(skepticism, 0, 5)

    # Action prompt
    action: str
    pause = False
    if mood == "Dismissive" or time_pressure >= 4:
        action = "Be brief and firm; ask for RCT size and primary endpoint; consider moving to closure."
    elif mentions_trial and mentions_stats:
        action = "Acknowledge evidence; ask one follow-up about endpoint or safety, keep it concise."
    elif hype:
        action = "Request specific evidence: trial size, outcomes, and p-value; avoid marketing language."
    else:
        action = "Maintain professional tone; request relevant, evidence-based points."

    return ToneDecisionOut(
        mood=mood,
        timePressure=time_pressure,
        skepticism=skepticism,
        action=action[:200],
        pauseReply=pause,
    )
