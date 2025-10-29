# backend/app/services/transcript_service.py
import os
import json
import uuid
from datetime import datetime

# Storage directory inside backend (backend/storage/)
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage")
os.makedirs(BASE_DIR, exist_ok=True)


def save_transcript(transcript_payload: dict) -> str:
    """
    Save transcript JSON to disk. Returns session_id used.
    transcript_payload example:
      {
        "session_id": "optional",
        "messages": [{ "role": "rep", "content": "..." , "timestamp": "..." }, ...]
      }
    """
    session_id = transcript_payload.get("session_id") or str(uuid.uuid4())
    out = {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "payload": transcript_payload,
    }
    filename = os.path.join(BASE_DIR, f"{session_id}.json")
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    return session_id


def load_transcript(session_id: str) -> dict | None:
    filename = os.path.join(BASE_DIR, f"{session_id}.json")
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as fh:
        return json.load(fh)
