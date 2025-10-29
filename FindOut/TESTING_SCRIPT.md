# Testing Script: What to Say to the Busy Doctor

## 🎯 Purpose
This script shows **exactly what to say** to test the new realistic busy doctor behavior and get different emotional responses.

## 🚀 How to Use
1. Start the application (backend + frontend)
2. Select any doctor persona
3. Click "Start Voice Session"
4. **Open Browser Console (F12)** to see debug messages
5. Use the phrases below to test different scenarios

## 🔍 What You'll See in Console
- `Realtime message received: conversation.item.created message assistant`
- `MR message detected: [your message]`
- `Hype detected (count: X): [your message]`
- `Medical evidence detected (count: X): [your message]`
- `Doctor triggered cutNow - will auto-hangup in 2 seconds`

---

## 📋 Testing Scenarios

### ❌ SCENARIO 1: Get Hanged Up On (Bad Approach)
**Goal**: Trigger auto-hangup by using too much hype

**What to say:**
```
"Hi Dr. Smith, I have this revolutionary new drug that's absolutely amazing and game-changing for your patients."
```

**Console Output:**
```
Hype detected (count: 1): Hi Dr. Smith, I have this revolutionary...
```

**Expected Response:**
```
Doctor: "I need specifics, not marketing. What's the actual data?"
```

**Then say:**
```
"It's the best treatment available, truly unbelievable results, breakthrough therapy..."
```

**Console Output:**
```
Hype detected (count: 2): It's the best treatment available...
Hype detected (count: 3): [if you say more hype]
Doctor triggered cutNow - will auto-hangup in 2 seconds
```

**Expected Result:**
```
Doctor: "I don't have time for this. Email me the trial results."
[2 seconds later - AUTO HANGUP with "Call ended due to patience exhaustion"]
```

---

### ❌ SCENARIO 2: Get Cut Off for Long Monologue
**Goal**: Trigger hangup by talking too long

**What to say:**
```
"Hi Dr. Smith, I'd like to discuss our new treatment option. So this drug works by targeting the specific mechanism of action in the cellular pathway, and what we found in our comprehensive analysis was that patients showed significant improvement across multiple domains including quality of life measures, functional outcomes, and biomarker changes, and the data really demonstrates the clinical benefit across different patient populations..."
```

**Console Output:**
```
Monologue detected (count: 1, words: 45): Hi Dr. Smith, I'd like to discuss...
```

**Expected Response:**
```
Doctor: "I need the key points, not a presentation. Bottom line?"
```

**Then say:**
```
"Well, as I was saying, the results were really quite remarkable and we saw improvements in multiple endpoints and the safety profile was excellent and the patients really benefited from this treatment approach..."
```

**Console Output:**
```
Monologue detected (count: 2, words: 38): Well, as I was saying...
Doctor triggered cutNow - will auto-hangup in 2 seconds
```

**Expected Result:**
```
Doctor: "I have patients waiting. This conversation is over."
[2 seconds later - AUTO HANGUP with "Call ended due to patience exhaustion"]
```

---

### ✅ SCENARIO 3: Get Engaged with Statistical Evidence
**Goal**: Make doctor interested with real data

**What to say:**
```
"Hi Dr. Smith, I'd like to discuss our Phase 3 trial results."
```

**Expected Response:**
```
Doctor: "What's the trial size and primary endpoint?"
```

**Then say:**
```
"It was a randomized controlled trial with n=500 patients, primary endpoint was progression-free survival with a p-value of 0.003, hazard ratio of 0.65."
```

**Console Output:**
```
Medical evidence detected (count: 1): It was a randomized controlled trial...
```

**Expected Response:**
```
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor becomes engaged - mood changes to "Engaged", time pressure decreases]
```

---

### ✅ SCENARIO 4: Get Engaged with Safety Data
**Goal**: Show doctor recognizes safety as valid evidence

**What to say:**
```
"Hi Dr. Smith, I'd like to discuss our safety profile data."
```

**Expected Response:**
```
Doctor: "What's the trial size and primary endpoint?"
```

**Then say:**
```
"The safety profile shows adverse events in 15% of patients, serious adverse events in 3%, with no grade 4 toxicities observed."
```

**Console Output:**
```
Medical evidence detected (count: 1): The safety profile shows adverse events...
```

**Expected Response:**
```
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor becomes engaged - mood changes to "Engaged"]
```

---

### ✅ SCENARIO 5: Get Engaged with Guidelines
**Goal**: Show doctor recognizes guidelines as valid criteria

**What to say:**
```
"Hi Dr. Smith, I'd like to discuss our treatment approach."
```

**Expected Response:**
```
Doctor: "What's the trial size and primary endpoint?"
```

**Then say:**
```
"This aligns with the latest treatment guidelines and consensus recommendations from the medical society."
```

**Console Output:**
```
Medical evidence detected (count: 1): This aligns with the latest treatment guidelines...
```

**Expected Response:**
```
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor becomes engaged - mood changes to "Engaged"]
```

---

### ✅ SCENARIO 6: Get Engaged with Biomarkers
**Goal**: Show doctor recognizes biomarkers as valid evidence

**What to say:**
```
"Hi Dr. Smith, I'd like to discuss our biomarker analysis."
```

**Expected Response:**
```
Doctor: "What's the trial size and primary endpoint?"
```

**Then say:**
```
"The biomarker analysis showed genetic mutations in 60% of responders, with receptor expression correlating with efficacy."
```

**Console Output:**
```
Medical evidence detected (count: 1): The biomarker analysis showed genetic mutations...
```

**Expected Response:**
```
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor becomes engaged - mood changes to "Engaged"]
```

---

### ✅ SCENARIO 7: Get Engaged with Real-World Evidence
**Goal**: Show doctor recognizes real-world data as valid

**What to say:**
```
"Hi Dr. Smith, I'd like to discuss our real-world evidence."
```

**Expected Response:**
```
Doctor: "What's the trial size and primary endpoint?"
```

**Then say:**
```
"Our real-world registry data shows consistent efficacy across 1000+ patients in post-marketing surveillance."
```

**Console Output:**
```
Medical evidence detected (count: 1): Our real-world registry data shows...
```

**Expected Response:**
```
Doctor: "Good. Now tell me about the clinical significance and practical implications."
[Doctor becomes engaged - mood changes to "Engaged"]
```

---

## 🎭 Testing Different Doctor Moods

### Test Patience Levels
**Start with hype, then provide evidence:**
```
1. "This is revolutionary and amazing..." (patience drops)
2. "But the trial data shows n=300, p<0.001..." (patience recovers)
```

### Test Time Pressure
**Talk slowly and vaguely:**
```
"I'd like to discuss... um... our treatment... which is... you know... really good..."
```
**Expected**: Doctor gets impatient, time pressure increases

### Test Skepticism
**Make vague claims:**
```
"This drug is really effective for most patients..."
```
**Expected**: Doctor asks for specifics, skepticism increases

---

## 🔍 What to Watch For

### Console Logs (Open Developer Tools - F12)
- `Realtime message received: conversation.item.created message assistant`
- `MR message detected: [your message]`
- `Hype detected (count: X): [your message]`
- `Medical evidence detected (count: X): [your message]`
- `Monologue detected (count: X, words: Y): [your message]`
- `Doctor triggered cutNow - will auto-hangup in 2 seconds`

### Doctor's Emotional Responses (Now Working!)
- **Hype words** → Doctor becomes "Dismissive" and says "I need specifics, not marketing"
- **Evidence provided** → Doctor becomes "Engaged" and says "Good. Now tell me about..."
- **Long monologues** → Doctor becomes "Dismissive" and says "I need the key points, not a presentation"
- **Repetition** → Doctor becomes "Dismissive" and says "I heard you the first time"

### Auto-Hangup Triggers (Now Working!)
- **3+ hype phrases** → Doctor says ending phrase and auto-hangup
- **2+ long monologues** under pressure → Doctor cuts off and auto-hangup
- **Patience exhaustion** + more hype → Immediate hangup

### Specific Doctor Phrases You'll Hear
- **"I need specifics, not marketing. What's the actual data?"** (hype detected)
- **"I need the key points, not a presentation. Bottom line?"** (monologue detected)
- **"I heard you the first time. What else do you have?"** (repetition detected)
- **"I have patients waiting. What's the key point?"** (time pressure high)
- **"Good. Now tell me about the clinical significance and practical implications."** (evidence provided)
- **"I'm ending this call. Send me the data sheet."** (cutNow triggered)

---

## 🎯 Success Criteria

### ✅ Good Session (Doctor Engaged)
- Doctor asks follow-up questions
- Mood stays "engaged" or "neutral"
- No auto-hangup
- Conversation continues naturally

### ❌ Bad Session (Doctor Hangs Up)
- Doctor becomes "dismissive"
- Auto-hangup triggered
- Call ends with "patience exhaustion" message
- Evaluation shows early termination

---

## 💡 Pro Tips

1. **Start with evidence** - Lead with trial data, not marketing
2. **Be concise** - Keep responses under 25 words
3. **Avoid hype words** - No "revolutionary", "amazing", "best"
4. **Use medical terms** - Endpoints, biomarkers, guidelines, safety
5. **Watch the doctor's mood** - Adjust approach based on responses

---

## 🚨 Common Mistakes to Avoid

- ❌ "This is the best drug ever"
- ❌ Long monologues without evidence
- ❌ Repeating the same vague claims
- ❌ Ignoring doctor's requests for specifics
- ❌ Using marketing language instead of medical data

---

## ✅ Good Phrases to Use

- ✅ "The trial showed n=500, p<0.001"
- ✅ "Primary endpoint was progression-free survival"
- ✅ "Safety profile shows 15% adverse events"
- ✅ "This aligns with treatment guidelines"
- ✅ "Biomarker analysis showed genetic mutations"
- ✅ "Real-world registry data demonstrates efficacy"

## 🚨 Troubleshooting

### If Doctor Isn't Getting Frustrated
1. **Check console logs** - You should see `Hype detected (count: X)` messages
2. **Restart backend** - Make sure the new tone-decide function is loaded
3. **Clear browser cache** - Refresh the page completely
4. **Check backend logs** - Look for `POST /api/tone-decide HTTP/1.1" 200 OK`

### If Auto-Hangup Isn't Working
1. **Check console** - You should see `Doctor triggered cutNow - will auto-hangup in 2 seconds`
2. **Wait 2 seconds** - There's a 2-second delay before hangup
3. **Check patience count** - Make sure you've used 3+ hype phrases

### If Evidence Detection Isn't Working
1. **Check console** - You should see `Medical evidence detected (count: X)`
2. **Use exact phrases** - Try "n=500", "p-value", "primary endpoint", "adverse events"
3. **Check spelling** - Make sure you're using the exact medical terms

### Manual Testing (If Automatic Detection Fails)
Open browser console and type:
```javascript
// Get the realtime client instance
const client = window.realtimeClient;

// Manually track a hype message
client.trackMrMessage("This is revolutionary and amazing!");

// Manually track evidence
client.trackMrMessage("The trial showed n=500, p<0.001");
```

## 🎯 Expected Results Now

The doctor should now behave like a **real busy senior physician**:
- ✅ Gets frustrated with hype words
- ✅ Becomes engaged with medical evidence
- ✅ Actually hangs up on you if you waste their time
- ✅ Shows realistic emotional responses
- ✅ Provides specific feedback based on your approach

This script will help you test all the new busy doctor behaviors and see exactly how the system responds to different approaches!
