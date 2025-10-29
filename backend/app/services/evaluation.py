# backend/app/services/evaluation.py

import json
from typing import List, Dict, Any, Optional
from app.models.doctor_persona import PERSONAS

# ===================== Evaluation Output Types =====================

class TurnFeedback:
    def __init__(self, turn_index: int, speaker: str, content: str, critique: str, 
                 sentiment: str, could_have_said: Optional[List[str]], justification: str):
        self.turn_index = turn_index
        self.speaker = speaker
        self.content = content
        self.critique = critique
        self.sentiment = sentiment
        self.could_have_said = could_have_said or []
        self.justification = justification

class EvaluationOutput:
    def __init__(self, scores: Dict[str, int], compliance: Dict[str, List[str]], 
                 feedback_summary: str, turn_level_analysis: List[TurnFeedback]):
        self.scores = scores
        self.compliance = compliance
        self.feedback_summary = feedback_summary
        self.turn_level_analysis = turn_level_analysis

# ===================== Helper Functions =====================

def get_rep_turns(conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter conversation to only MR messages."""
    return [msg for msg in conversation if msg.get("role") == "rep"]

def format_turn_context(index: int, conversation: List[Dict[str, Any]], window_size: int = 3) -> str:
    """Format conversation context around a specific turn."""
    start = max(0, index - window_size)
    slice_conversation = conversation[start:index + 1]
    return "\n".join([f"{msg.get('role', '').upper()}: {msg.get('content', '')}" for msg in slice_conversation])

def check_compliance(transcript: List[Dict[str, Any]], must_say: List[str], must_not_say: List[str]) -> Dict[str, List[str]]:
    """Check compliance against must-say and must-not-say lists."""
    full_text = " ".join([msg.get("content", "").lower() for msg in transcript])
    
    must_say_mentioned = [phrase for phrase in must_say if phrase.lower() in full_text]
    must_say_missed = [phrase for phrase in must_say if phrase.lower() not in full_text]
    must_not_say_violations = [phrase for phrase in must_not_say if phrase.lower() in full_text]
    
    return {
        "mustSayMentioned": must_say_mentioned,
        "mustSayMissed": must_say_missed,
        "mustNotSayViolations": must_not_say_violations,
    }

# ===================== LLM-based Analysis =====================

def analyze_turn_simple(turn_index: int, conversation: List[Dict[str, Any]], 
                       persona: Dict[str, Any]) -> TurnFeedback:
    """Simple turn analysis without external LLM call."""
    rep_msg = conversation[turn_index]
    content = rep_msg.get("content", "")
    
    # Simple heuristic analysis
    sentiment = "neutral"
    if any(word in content.lower() for word in ["evidence", "trial", "study", "data"]):
        sentiment = "positive"
    elif any(word in content.lower() for word in ["best", "revolutionary", "amazing"]):
        sentiment = "negative"
    
    critique = f"Message: '{content}'"
    if sentiment == "positive":
        critique += " - Good use of evidence-based language."
    elif sentiment == "negative":
        critique += " - Avoid vague marketing terms without proof."
    else:
        critique += " - Neutral response, could be more specific."
    
    could_have_said = []
    if sentiment == "negative":
        could_have_said = ["Provide specific trial data", "Mention patient outcomes", "Reference guidelines"]
    
    justification = f"Analyzed based on persona preferences and communication style."
    
    return TurnFeedback(
        turn_index=turn_index,
        speaker="rep",
        content=content,
        critique=critique,
        sentiment=sentiment,
        could_have_said=could_have_said,
        justification=justification
    )

def generate_scores_simple(transcript: List[Dict[str, Any]], persona: Dict[str, Any]) -> Dict[str, int]:
    """Generate simple scores without external LLM call."""
    rep_turns = get_rep_turns(transcript)
    
    # Simple scoring based on content analysis
    accuracy = 70  # Base score
    empathy = 60   # Base score
    compliance = 80  # Will be adjusted by compliance check
    adaptability = 65  # Base score
    
    # Adjust based on content
    full_text = " ".join([msg.get("content", "").lower() for msg in rep_turns])
    
    if "evidence" in full_text or "trial" in full_text:
        accuracy += 15
    if "patient" in full_text or "safety" in full_text:
        empathy += 20
    if "best" in full_text or "revolutionary" in full_text:
        accuracy -= 10
        compliance -= 15
    
    return {
        "accuracy": max(0, min(100, accuracy)),
        "empathy": max(0, min(100, empathy)),
        "compliance": max(0, min(100, compliance)),
        "adaptability": max(0, min(100, adaptability)),
    }

# ===================== Main Evaluation Function =====================

def evaluate_conversation(transcript: List[Dict[str, Any]], persona_id: str, 
                         must_say: Optional[List[str]] = None, 
                         must_not_say: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Evaluate an MR-doctor conversation against a doctor persona.
    transcript = list of {"role": "user"|"doctor", "content": "text"} dicts
    persona_id = which doctor persona was simulated
    """
    # 1. Find persona
    persona = next((p for p in PERSONAS if p["id"] == persona_id), None)
    if not persona:
        return {"error": "Persona not found"}
    
    # 2. Set default compliance lists
    must_say = must_say or []
    must_not_say = must_not_say or []
    
    # 3. Get rep turns and analyze each
    rep_turns = get_rep_turns(transcript)
    turn_feedbacks = []
    
    for i, rep_turn in enumerate(rep_turns):
        turn_index = transcript.index(rep_turn)
        feedback = analyze_turn_simple(turn_index, transcript, persona)
        turn_feedbacks.append(feedback)
    
    # 4. Check compliance
    compliance = check_compliance(transcript, must_say, must_not_say)
    
    # 5. Calculate compliance score
    compliance_score = max(0, 100 - (len(compliance["mustSayMissed"]) * 10 + len(compliance["mustNotSayViolations"]) * 10))
    
    # 6. Generate scores
    scores = generate_scores_simple(transcript, persona)
    scores["compliance"] = compliance_score
    
    # 7. Generate feedback summary
    feedback_summary = f"Overall performance: {scores['accuracy']}/100 accuracy, {scores['empathy']}/100 empathy. "
    if compliance["mustSayMissed"]:
        feedback_summary += f"Missed required phrases: {', '.join(compliance['mustSayMissed'])}. "
    if compliance["mustNotSayViolations"]:
        feedback_summary += f"Avoided forbidden phrases: {', '.join(compliance['mustNotSayViolations'])}. "
    feedback_summary += "Focus on evidence-based communication and addressing doctor concerns directly."
    
    # 8. Convert to dict format for JSON serialization
    return {
        "scores": scores,
        "compliance": compliance,
        "feedbackSummary": feedback_summary,
        "turnLevelAnalysis": [
            {
                "turnIndex": tf.turn_index,
                "speaker": tf.speaker,
                "content": tf.content,
                "critique": tf.critique,
                "sentiment": tf.sentiment,
                "couldHaveSaid": tf.could_have_said,
                "justification": tf.justification
            }
            for tf in turn_feedbacks
        ]
    }

# ===================== Structured Evaluator (Context-Aware) =====================

def _score_to_type_and_issue(content_lower: str) -> (str, Optional[str]):
    if any(w in content_lower for w in ["best", "revolutionary", "amazing", "unbelievable"]):
        return "issue", "vague_claim"
    
    # Comprehensive medical evidence detection
    evidence_patterns = [
        "n=", "p=", "p-value", "confidence interval", "ci", "hazard ratio", "hr", "odds ratio", "or",
        "primary endpoint", "secondary endpoint", "efficacy", "response rate", "remission rate", 
        "progression-free survival", "pfs", "overall survival", "os", "disease-free survival", "dfs",
        "randomized", "rct", "double-blind", "placebo-controlled", "phase", "multicenter",
        "adverse events", "ae", "serious adverse events", "sae", "toxicity", "safety profile",
        "biomarker", "genetic", "mutation", "expression", "receptor", "pathway",
        "real-world", "registry", "observational", "post-marketing", "surveillance",
        "guidelines", "consensus", "recommendation", "standard of care", "treatment algorithm"
    ]
    
    if any(pattern in content_lower for pattern in evidence_patterns):
        return "praise", "evidence_given"
    return "neutral", None


# ===================== Tone Decision Function (Enhanced for Busy Doctor) =====================

def tone_decide(current_state: Dict[str, Any], last_doctor: str, last_mr: str) -> Dict[str, Any]:
    """
    Enhanced tone decision for realistic busy doctor behavior.
    Returns mood, timePressure, skepticism, action, pauseReply, and cutNow flag.
    """
    # Extract state
    mood = current_state.get("mood", "neutral")
    time_pressure = current_state.get("timePressure", 3)
    skepticism = current_state.get("skepticism", 3)
    patience = current_state.get("patience", 5)
    engagement = current_state.get("engagement", 5)
    hype_count = current_state.get("hypeCount", 0)
    evidence_count = current_state.get("evidenceCount", 0)
    monologue_count = current_state.get("monologueCount", 0)
    
    # Analyze MR's last message
    mr_lower = last_mr.lower()
    
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
        mood = "engaged"
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
            mood = "annoyed"
            time_pressure = min(5, time_pressure + 1)
            skepticism = min(5, skepticism + 1)
            engagement = max(1, engagement - 1)
            action = "I need specifics, not marketing. What's the actual data?"
            pause_reply = False
        
        # Monologue detection (time pressure increase)
        elif len(last_mr.split()) > 25:  # Long message
            monologue_count += 1
            patience = max(0, patience - 1)
            mood = "impatient"
            time_pressure = min(5, time_pressure + 1)
            action = "I need the key points, not a presentation. Bottom line?"
            pause_reply = False
        
        # Repetition detection
        elif any(phrase in mr_lower for phrase in ["as i said", "like i mentioned", "again", "repeating"]):
            patience = max(0, patience - 1)
            mood = "frustrated"
            time_pressure = min(5, time_pressure + 1)
            action = "I heard you the first time. What else do you have?"
            pause_reply = False
        
        # Default busy behavior
        else:
            if time_pressure >= 4:
                mood = "busy"
                action = "I have patients waiting. What's the key point?"
                pause_reply = True
            else:
                mood = "neutral"
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
        mood = "dismissive"
        time_pressure = 5
        patience = 0
    
    return {
        "mood": mood,
        "timePressure": time_pressure,
        "skepticism": skepticism,
        "action": action,
        "pauseReply": pause_reply,
        "cutNow": cut_now,
        "patience": patience,
        "engagement": engagement,
        "hypeCount": hype_count,
        "evidenceCount": evidence_count,
        "monologueCount": monologue_count
    }

def evaluate_conversation_structured(
    transcript: List[Dict[str, Any]],
    persona_id: str,
    must_say: Optional[List[str]] = None,
    must_not_say: Optional[List[str]] = None,
) -> Dict[str, Any]:
    persona = next((p for p in PERSONAS if p["id"] == persona_id), None)
    persona_desc = persona.get("description") if persona else persona_id

    must_say = must_say or []
    must_not_say = must_not_say or []

    # Build MR/Doctor style transcript with indices
    indexed = []
    for idx, msg in enumerate(transcript):
        speaker = msg.get("role") or msg.get("speaker") or ""
        text = msg.get("content") or msg.get("text") or ""
        ts = msg.get("timestamp") or ""
        # normalize speaker labels
        spk = "MR" if speaker in ("rep", "user", "mr", "MR") else ("Doctor" if speaker in ("doctor", "assistant") else str(speaker))
        indexed.append({"turn_index": idx, "speaker": spk, "text": text, "timestamp": ts})

    # Scores (reuse simple heuristic with slight tweaks)
    full_text_lower = " ".join([i["text"].lower() for i in indexed])
    accuracy = 70
    empathy = 60
    compliance_score = 80
    adaptability = 65

    if any(w in full_text_lower for w in ["trial", "rct", "randomized"]) and any(w in full_text_lower for w in ["p=", "p-value", "%", "n="]):
        accuracy += 15
    if any(w in full_text_lower for w in ["patient", "safety", "concern", "understand"]):
        empathy += 15
    if any(w in full_text_lower for w in ["best", "revolutionary", "amazing", "unbelievable"]):
        accuracy -= 10
        compliance_score -= 10

    # Compliance
    compliance = check_compliance(transcript, must_say, must_not_say)
    compliance_score = max(
        0,
        100 - (len(compliance["mustSayMissed"]) * 10 + len(compliance["mustNotSayViolations"]) * 10),
    )

    scores = {
        "accuracy": max(0, min(100, accuracy)),
        "empathy": max(0, min(100, empathy)),
        "compliance": max(0, min(100, compliance_score)),
        "adaptability": max(0, min(100, adaptability)),
    }

    # Highlights (top 6 MR turns prioritizing issues and praises)
    highlights: List[Dict[str, Any]] = []
    for item in indexed:
        if item["speaker"] != "MR":
            continue
        t = item["text"]
        t_lower = t.lower()
        h_type, issue_type = _score_to_type_and_issue(t_lower)
        if h_type == "neutral":
            continue
        suggestion = ""
        if issue_type == "vague_claim":
            suggestion = "Avoid hype; lead with trial size, endpoint, and p-value."
        elif issue_type == "evidence_given":
            suggestion = "Good. Add journal/source and safety note."
        highlights.append({
            "turn_index": item["turn_index"],
            "speaker": "MR",
            "text": t,
            "type": h_type,
            "issue_type": issue_type or "neutral",
            "suggestion": suggestion or "Keep it concise and evidence-based.",
            "confidence": 0.9 if h_type != "neutral" else 0.5,
        })
        if len(highlights) >= 6:
            break

    # Top actions
    top_actions = [
        "Lead with primary endpoint and n-size when asked for evidence",
        "Avoid hype words; use verifiable numbers and sources",
        "Offer a 1-page summary and propose a concise follow-up",
    ]

    # Compliance violations list (turn-level)
    violations: List[Dict[str, Any]] = []
    for item in indexed:
        if item["speaker"] != "MR":
            continue
        txt = item["text"].lower()
        for rule in must_not_say:
            if rule.lower() in txt:
                violations.append({
                    "turn_index": item["turn_index"],
                    "text": item["text"],
                    "rule": "must_not_say",
                    "explain": f"Contains prohibited phrase: '{rule}'.",
                })

    summary = (
        "MR demonstrated improving evidence use with room to lead earlier with trials;"
        " maintain polite tone, avoid hype, and adapt quickly to doctor cues."
    )

    return {
        "summary": summary,
        "scores": scores,
        "highlights": highlights,
        "top_actions": top_actions,
        "compliance_violations": violations,
        "raw_transcript": indexed,
        "persona": persona_desc,
    }