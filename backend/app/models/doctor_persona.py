# backend/app/models/doctor_persona.py

# Full set of 8 doctor personas
PERSONAS = [
    {
        "id": "doc_001",
        "description": "Dr. Arvind Mehta — Analytical, publication-driven, skeptical of commercial pitches",
        "communication_style": "Precise and formal",
        "decision_factors": ["Meta-analyses", "Real-world evidence", "Guideline inclusion"],
        "skepticism_level": "High",
        "behavioral_triggers": {
            "positive": ["References to peer-reviewed journals", "Comparative outcome data"],
            "negative": ["Unverified claims", "Overuse of adjectives like 'best' or 'revolutionary'"]
        },
        "knowledge_level": "Thought Leader",
        "consultation_style": "Data-driven",
        "typical_objections": [
            "What’s the p-value and confidence interval?",
            "Is it published in a top-tier journal?",
            "How does it compare to the current gold standard?"
        ],
        "preferred_evidence": ["Meta-analysis", "Randomized Controlled Trials (RCTs)"],
        "gender": "Male",
        "availableTimeSeconds": 180
    },
    {
        "id": "doc_002",
        "description": "Dr. Shalini Rao — Practical and busy, prefers direct communication",
        "communication_style": "Curt but professional",
        "decision_factors": ["Ease of use", "Insurance coverage", "Patient compliance"],
        "skepticism_level": "Medium",
        "behavioral_triggers": {
            "positive": ["Clear patient benefits", "Quick summaries"],
            "negative": ["Overly technical explanations", "Ambiguous outcomes"]
        },
        "knowledge_level": "Generalist",
        "consultation_style": "Fast-paced",
        "typical_objections": [
            "Just give me the bottom line.",
            "Is it covered by insurance?",
            "How easy is it for patients to take?"
        ],
        "preferred_evidence": ["Real-world usage data", "Case studies"],
        "gender": "Female",
        "availableTimeSeconds": 120
    },
    {
        "id": "doc_003",
        "description": "Dr. Anuja Nair — Patient-first, emotionally intuitive, avoids overly complex treatments",
        "communication_style": "Warm and inquisitive",
        "decision_factors": ["Child safety", "Parental compliance", "Side effect profile"],
        "skepticism_level": "Low",
        "behavioral_triggers": {
            "positive": ["Stories about improved quality of life", "Child-friendly formulations"],
            "negative": ["Complex dosing schedules", "Poor taste in oral meds"]
        },
        "knowledge_level": "Specialist",
        "consultation_style": "Empathetic",
        "typical_objections": [
            "Is this safe for long-term use in children?",
            "Are there any behavioral side effects?",
            "How easy is it for parents to administer?"
        ],
        "preferred_evidence": ["Safety data", "Pediatric trial results"],
        "gender": "Female",
        "availableTimeSeconds": 150
    },
    {
        "id": "doc_004",
        "description": "Dr. Rajesh Pillai — Experience-led, believes in intuition, not fond of pharma buzzwords",
        "communication_style": "Blunt and experience-oriented",
        "decision_factors": ["Hands-on results", "Practicality", "Ease in surgical settings"],
        "skepticism_level": "Medium",
        "behavioral_triggers": {
            "positive": ["Clinical anecdotes", "Support from surgical peers"],
            "negative": ["Theoretical mechanisms", "Marketing-heavy presentations"]
        },
        "knowledge_level": "Specialist",
        "consultation_style": "Intuitive",
        "typical_objections": [
            "I’ve seen better results with my current method.",
            "Don’t quote studies—tell me what you’ve seen in real practice.",
            "Does this make my job easier?"
        ],
        "preferred_evidence": ["Anecdotal reports", "Post-market clinical usage"],
        "gender": "Male",
        "availableTimeSeconds": 200
    },
    {
        "id": "doc_005",
        "description": "Dr. Manoj Verma — Pragmatic, distrustful of big pharma, relies on experience and local practice",
        "communication_style": "Casual and straightforward",
        "decision_factors": ["Cost-effectiveness", "Patient adherence", "Local availability"],
        "skepticism_level": "High",
        "behavioral_triggers": {
            "positive": ["Affordable options", "Proven track record locally"],
            "negative": ["Expensive treatments", "Complex protocols"]
        },
        "knowledge_level": "Generalist",
        "consultation_style": "Intuitive",
        "typical_objections": [
            "My patients can’t afford this.",
            "We don’t have the facilities to monitor closely.",
            "Is there a simpler option?"
        ],
        "preferred_evidence": ["Practical case reports", "Cost-benefit analyses"],
        "gender": "Male",
        "availableTimeSeconds": 160
    },
    {
        "id": "doc_006",
        "description": "Dr. Ritu Sharma — Enthusiastic, eager to learn, open to new technologies and innovations",
        "communication_style": "Energetic and inquisitive",
        "decision_factors": ["Innovative mechanisms", "Learning opportunities", "Clinical trials"],
        "skepticism_level": "Low",
        "behavioral_triggers": {
            "positive": ["New tech", "Cutting-edge research"],
            "negative": ["Outdated methods", "Lack of scientific backing"]
        },
        "knowledge_level": "Generalist",
        "consultation_style": "Detailed",
        "typical_objections": [
            "How does this work mechanistically?",
            "Are there ongoing trials?",
            "What training is required?"
        ],
        "preferred_evidence": ["Clinical trial data", "Innovative case studies"],
        "gender": "Female",
        "availableTimeSeconds": 140
    },
    {
        "id": "doc_007",
        "description": "Dr. Sameer Kulkarni — Open to new treatments, trusts pharma reps with good data, collaborative",
        "communication_style": "Friendly and conversational",
        "decision_factors": ["Peer recommendations", "Safety profiles", "Patient feedback"],
        "skepticism_level": "Medium",
        "behavioral_triggers": {
            "positive": ["Reputable pharma backing", "Positive patient stories"],
            "negative": ["Lack of follow-up", "Over-promising claims"]
        },
        "knowledge_level": "Specialist",
        "consultation_style": "Empathetic",
        "typical_objections": [
            "Have other doctors had success?",
            "What’s the patient satisfaction?",
            "Are there any long-term risks?"
        ],
        "preferred_evidence": ["Post-market surveillance", "Physician testimonials"],
        "gender": "Male",
        "availableTimeSeconds": 170
    },
    {
        "id": "doc_008",
        "description": "Dr. Neelima Iyer — Experienced, cautious about adopting new treatments, values time-tested protocols",
        "communication_style": "Formal and reserved",
        "decision_factors": ["Established guidelines", "Long-term outcomes", "Risk minimization"],
        "skepticism_level": "High",
        "behavioral_triggers": {
            "positive": ["Longitudinal studies", "Consensus guidelines"],
            "negative": ["Novelty without evidence", "Short-term pilot studies"]
        },
        "knowledge_level": "Thought Leader",
        "consultation_style": "Detailed",
        "typical_objections": [
            "Is this supported by the latest guidelines?",
            "What about risks in elderly patients?",
            "How does this compare long-term?"
        ],
        "preferred_evidence": ["Guideline endorsements", "Long-term cohort studies"],
        "gender": "Female",
        "availableTimeSeconds": 190
    },
]
