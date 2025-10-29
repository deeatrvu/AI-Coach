# Busy Doctor Demo Script

## What's New: Realistic Busy Doctor Behavior

The system now simulates a **truly busy senior physician** who will actually hang up on you if you waste their time, just like calling a real busy doctor.

## Key Features

### 1. **Hard Stop Triggers** (Auto-Hangup)
- **3+ hype phrases** ("revolutionary", "amazing", "best") → Doctor ends call
- **2+ long monologues** under time pressure → Doctor cuts off
- **Patience exhaustion** + more hype → Immediate hangup

### 2. **Real-Time Emotional Responses**
- **Vague claims**: "I need specifics, not marketing. What's the actual data?"
- **Long monologues**: "I need the key points, not a presentation. Bottom line?"
- **Repetition**: "I heard you the first time. What else do you have?"
- **Evidence provided**: "Good. Now tell me about the clinical significance and practical implications."

### 3. **Flexible Medical Criteria Recognition**
The doctor now recognizes **any** of these medical evidence types:
- **Statistical**: n=, p-value, confidence interval, hazard ratio, odds ratio
- **Clinical endpoints**: primary/secondary endpoint, efficacy, response rate, PFS, OS, DFS
- **Trial design**: randomized, RCT, double-blind, placebo-controlled, phase, multicenter
- **Safety data**: adverse events, SAE, toxicity, safety profile
- **Biomarkers**: genetic, mutation, expression, receptor, pathway
- **Real-world evidence**: registry, observational, post-marketing, surveillance
- **Guidelines**: consensus, recommendation, standard of care, treatment algorithm

### 4. **Auto-Hangup Flow**
1. Doctor says ending phrase (e.g., "I'm ending this call. Send me the data sheet.")
2. System waits 2 seconds for doctor to finish
3. Call automatically disconnects
4. Shows evaluation with "Call ended due to patience exhaustion"

## Demo Scenarios

### Scenario 1: MR Gets Hanged Up On (Bad Approach)
```
MR: "Hi Dr. Smith, I have this revolutionary new drug that's absolutely amazing..."
Doctor: "I need specifics, not marketing. What's the actual data?"
MR: "It's the best treatment available, truly game-changing..."
Doctor: "I don't have time for this. Email me the trial results."
[2 seconds later - AUTO HANGUP]
```

### Scenario 2: MR Provides Evidence (Good Approach)
```
MR: "Hi Dr. Smith, I'd like to discuss our Phase 3 trial results."
Doctor: "What's the trial size and primary endpoint?"
MR: "It was a randomized trial with n=500 patients, primary endpoint was..."
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Conversation continues - Doctor becomes engaged]
```

### Scenario 2b: MR Provides Safety Data
```
MR: "The safety profile shows adverse events in 15% of patients..."
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor becomes engaged - recognizes safety data as valid evidence]
```

### Scenario 2c: MR References Guidelines
```
MR: "This aligns with the latest treatment guidelines and consensus recommendations..."
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor recognizes guidelines as valid medical criteria]
```

### Scenario 3: MR Talks Too Long
```
MR: "So this drug works by targeting the specific mechanism of action in the cellular pathway, and what we found in our comprehensive analysis was that patients showed significant improvement across multiple domains including quality of life measures, functional outcomes, and biomarker changes..."
Doctor: "I need the key points, not a presentation. Bottom line?"
MR: "Well, as I was saying, the results were really quite remarkable..."
Doctor: "I have patients waiting. This conversation is over."
[2 seconds later - AUTO HANGUP]
```

## How to Test

1. **Start the application** (backend + frontend)
2. **Select a doctor persona** (any will work)
3. **Try these approaches**:
   - Use hype words repeatedly → Get hanged up on
   - Talk in long monologues → Get cut off
   - Provide specific trial data → Get engaged response
   - Be concise and evidence-based → Successful conversation

## Technical Implementation

- **Backend**: Enhanced `tone_decide()` function with `cutNow` flag
- **Frontend**: Auto-hangup governor with 2-second delay
- **Real-time tracking**: Hype count, evidence count, monologue count
- **Stricter defaults**: High time pressure, low patience, high skepticism

## Result

The doctor now behaves like a real busy senior physician who:
- ✅ Will actually hang up on you if you waste their time
- ✅ Gets immediately engaged when you provide real evidence
- ✅ Shows realistic emotional responses to poor communication
- ✅ Has zero tolerance for marketing speak without proof

This creates a much more realistic and challenging training environment for medical representatives.
