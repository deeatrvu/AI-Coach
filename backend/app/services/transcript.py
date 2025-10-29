# backend/app/services/transcript.py

from typing import List, Dict

# In-memory storage for now (later can use DB)
TRANSCRIPTS: Dict[str, List[dict]] = {}

def save_message(session_id: str, role: str, content: str):
    """
    Save a message to the transcript for a given session.
    role = "user" (MR) or "doctor"
    """
    if session_id not in TRANSCRIPTS:
        TRANSCRIPTS[session_id] = []
    TRANSCRIPTS[session_id].append({"role": role, "content": content})


def get_transcript(session_id: str) -> List[dict]:
    """
    Return all messages for a session.
    """
    return TRANSCRIPTS.get(session_id, [])


def clear_transcript(session_id: str):
    """
    Clear transcript for a session.
    """
    if session_id in TRANSCRIPTS:
        del TRANSCRIPTS[session_id]
