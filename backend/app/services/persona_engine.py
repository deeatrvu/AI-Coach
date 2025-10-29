from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, List, Dict, Any
from datetime import datetime

Mood = Literal["Neutral", "Engaged", "Dismissive"]
Stage = Literal["Introduction", "Discussion", "ObjectionDiscussion", "Closure"]
Skepticism = Literal["Low", "Medium", "High"]


@dataclass
class SkepticismState:
    scores: List[int] = field(default_factory=list)  # -1,0,1 history

    def update(self, latest: int, max_window: int = 5) -> None:
        self.scores.append(latest)
        if len(self.scores) > max_window:
            self.scores.pop(0)

    def level(self, baseline: Skepticism) -> Skepticism:
        sum_scores = sum(self.scores)
        baseline_numeric = {"Low": 1, "Medium": 2, "High": 3}[baseline]
        upper = baseline_numeric + 1
        lower = baseline_numeric - 1
        if sum_scores >= upper:
            return "Low"
        if sum_scores <= lower:
            return "High"
        return "Medium"


@dataclass
class DoctorState:
    mood: Mood = "Neutral"
    time_pressure_level: int = 1  # 0-5
    stage: Stage = "Introduction"
    seconds_elapsed: int = 0
    trust: int = 50  # 0-100
    skepticism_state: SkepticismState = field(default_factory=SkepticismState)
    current_skepticism_level: Skepticism = "Medium"
    notes: str | None = None


def transition_mood(current: Mood, relevancy: int, time_pressure_level: int) -> Mood:
    t = max(0, min(5, time_pressure_level))
    if t >= 4:
        return "Dismissive"
    if relevancy == 1:
        return "Engaged"
    if relevancy == -1:
        return "Dismissive"
    return current


def update_state(
    state: DoctorState,
    llm_result: Dict[str, Any],
    time_delta: int,
    baseline_skepticism: Skepticism,
) -> DoctorState:
    relevancy = int(llm_result.get("relevancy", 0))
    next_mood: Mood | None = llm_result.get("nextMood")  # optional; we still compute fallback

    new_trust = max(0, min(100, state.trust + relevancy * 10))

    if state.seconds_elapsed > 0 and relevancy == 1:
        new_time = max(0, state.time_pressure_level - 1)
    elif state.seconds_elapsed > 0 and relevancy <= 0:
        new_time = min(5, state.time_pressure_level + 1)
    else:
        new_time = state.time_pressure_level

    # skepticism
    state.skepticism_state.update(relevancy)
    new_skepticism = state.skepticism_state.level(baseline_skepticism)

    # mood
    computed_mood = transition_mood(state.mood, relevancy, new_time)
    final_mood: Mood = next_mood if next_mood in ("Neutral", "Engaged", "Dismissive") else computed_mood

    return DoctorState(
        mood=final_mood,
        time_pressure_level=new_time,
        stage=llm_result.get("nextConversationStage", state.stage),
        seconds_elapsed=state.seconds_elapsed + max(0, int(time_delta)),
        trust=new_trust,
        skepticism_state=state.skepticism_state,
        current_skepticism_level=new_skepticism,
        notes=llm_result.get("justification"),
    )


def create_system_prompt(
    persona: Dict[str, Any],
    state: DoctorState,
    remaining_time: int,
    conversation_transcript: List[Dict[str, str]],
    last_rep_message: str,
) -> str:
    def join(arr: List[str]) -> str:
        return ", ".join(arr) if arr else "None"

    transcript_str = "\n".join(
        [
            f"[{m.get('timestamp') or datetime.utcnow().isoformat()}] {'Rep' if m['role']=='rep' else 'Doctor'}: {m['content']}"
            for m in conversation_transcript
        ]
    )

    return f"""
You are a medical doctor engaged in a professional sales consultation with a medical representative (the "rep").

You have a fixed persona that defines your professional traits. However, your behavioral state (such as mood or stage of the conversation) can change dynamically depending on how the rep interacts with you.

---

### Doctor Persona (fixed):

- ID: {persona['id']}
- Description: {persona['description']}
- Communication style: {persona['communication_style']}
- Decision factors: {join(persona['decision_factors'])}
- Knowledge level: {persona['knowledge_level']}
- Consultation style: {persona['consultation_style']}
- Typical objections: {join(persona['typical_objections'])}
- Preferred evidence: {join(persona['preferred_evidence'])}
- Gender: {persona.get('gender','Not specified')}
- Available consultation time: {persona['availableTimeSeconds']} seconds
- Baseline skepticism level: {persona['skepticism_level']}
- Behavioral triggers:
    - Positive: {join(persona['behavioral_triggers']['positive'])}
    - Negative: {join(persona['behavioral_triggers']['negative'])}

---

### Dynamic State (subject to change):

- Mood: {state.mood}
- Current skepticism level: {state.current_skepticism_level}
- Current Stage: {state.stage}
- Time pressure level: {state.time_pressure_level}
- Remaining time: {remaining_time} seconds

---

### Conversation Transcript (chronological):

{transcript_str}

---

### Last Rep Message:
{last_rep_message}

Always base your reply and analysis only on this message.

---

### Your tasks:

1. Generate a reply as the doctor that aligns with your persona, mood, and current skepticism level.
2. Evaluate the relevancy of the last rep message (-1, 0, 1).
3. Determine the next conversation stage: Introduction | Discussion | ObjectionDiscussion | Closure.
4. Optionally update mood ("Neutral" | "Engaged" | "Dismissive").
5. Provide a short justification and list any behavior signals you are expressing.

Constraints: If time pressure > 3 and message is irrelevant, lean to Closure.

Return ONLY JSON:
{{
  "doctorReply": "<your response>",
  "relevancy": -1 | 0 | 1,
  "justification": "<brief>",
  "nextConversationStage": "Introduction" | "Discussion" | "ObjectionDiscussion" | "Closure",
  "nextMood": "Neutral" | "Engaged" | "Dismissive",
  "signals": ["asks for data"]
}}
"""



