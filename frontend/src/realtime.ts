import $ from "jquery";
import { RealtimeSession, TranscriptEntry } from "./types";

export class RealtimeClient {
  private pc: RTCPeerConnection | null = null;
  private dc: RTCDataChannel | null = null;
  private micStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private audioEl: HTMLAudioElement | null = null;
  private ephemeralToken: string | null = null;
  private coachingCallback?: (hint: string, type: string, signals: string[]) => void;
  private transcript: TranscriptEntry[] = [];
  private sessionId: string | null = null;

  // ===== Lightweight tone/state for realtime nudging =====
  private mood: "Neutral" | "Engaged" | "Dismissive" = "Neutral";
  private timePressureLevel: number = 4; // start very high: busy senior doctor
  private skepticismLevel: number = 4; // start very skeptical
  private lastToneUpdateAt: number = 0;
  private minToneUpdateMs: number = 900;
  private patienceScore: number = 1; // start with very low patience (0-5)
  private engagementScore: number = 1; // start with very low engagement (0-5)
  private hypeCount: number = 0; // track hype phrases
  private evidenceCount: number = 0; // track evidence provided
  private monologueCount: number = 0; // track long monologues
  private cutNowTriggered: boolean = false; // track if doctor wants to end call
  private hangupTimer: number | null = null; // timer for auto-hangup

  // ===== Mic handling & VAD (barge-in) =====
  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private rafId: number | null = null;
  private isMuted: boolean = false;
  private pushToTalkEnabled: boolean = false;
  private pushToTalkActive: boolean = false;
  private isSpeaking: boolean = false;
  private vadHighThreshold: number = 0.08; // RMS
  private vadLowThreshold: number = 0.03;  // RMS
  private vadHoldMs: number = 250;         // hysteresis
  private vadLastAboveTs: number = 0;
  private remoteVolumeBeforeDuck: number = 1.0;

  constructor(private apiBase: string = (window as any).API_BASE || "http://localhost:8000/api") {}

  setCoachingCallback(callback: (hint: string, type: string, signals: string[]) => void): void {
    this.coachingCallback = callback;
  }

  async start(): Promise<void> {
    // Prepare UI
    this.audioEl = document.getElementById("doctor-audio") as HTMLAudioElement | null;

    // 1) Get ephemeral session token from backend
    const sess = await this.fetchSessionToken();
    this.ephemeralToken = sess?.client_secret?.value || "";
    if (!this.ephemeralToken) throw new Error("Missing ephemeral token from /session-token");

    // 2) Get microphone with improved constraints
    this.micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
      } as any,
    });

    // 3) Create RTCPeerConnection
    this.pc = new RTCPeerConnection({
      iceServers: [
        { urls: ["stun:stun.l.google.com:19302"] },
      ],
    });

    // 4) Prepare remote stream and attach to audio element
    this.remoteStream = new MediaStream();
    if (this.audioEl) {
      this.audioEl.srcObject = this.remoteStream;
      this.audioEl.autoplay = true;
      this.audioEl.muted = false;
      try { await this.audioEl.play(); } catch (_) {}
    }

    // 5) On track from remote, add to remoteStream
    this.pc.ontrack = (event: RTCTrackEvent) => {
      for (const track of event.streams[0].getTracks()) {
        this.remoteStream?.addTrack(track);
      }
    };

    // 6) Create data channel for Realtime events (oai-events)
    this.dc = this.pc.createDataChannel("oai-events");
    this.dc.onopen = () => {
      // Send session.update with dynamic persona/state inference and MR coaching rules
      const instructions = this.buildSessionInstructions();
      this.sendEvent({
        type: "session.update",
        session: {
          instructions,
        },
        tone: {
          mood: this.mood,
          timePressure: this.timePressureLevel,
          skepticism: this.skepticismLevel,
        },
        hint: "You are a VERY busy senior physician with patients waiting. Keep ALL replies under 5 seconds. If MR uses hype words or talks too long, you WILL end the call. Be direct, firm, and impatient. Ask for specific medical evidence (trial data, endpoints, safety profile, guidelines, biomarkers, etc.) immediately when claims are vague.",
      });
      // Setup mic processing & VAD
      this.setupMicProcessing();
      this.attachHotkeys();
    };

    // Listen for messages from the model (doctor responses) and user input
    this.dc.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Debug: Log all message types to understand the API
        console.log("Realtime message received:", data.type, data.item?.type, data.item?.role);
        
        // Handle doctor messages
        if (data.type === "conversation.item.created" && data.item?.type === "message") {
          const content = data.item.content?.[0]?.text || "";
          const signals = data.item.metadata?.signals || [];
          
          // Add to transcript
          this.addToTranscript("doctor", content);
          
          // Trigger coaching callback
          if (this.coachingCallback) {
            this.coachingCallback(content, "info", signals);
          }

          // Update tone heuristically and nudge the session
          this.updateToneAndNudge(signals, content);
          // Also call backend tone-decide with rate limiting
          this.requestBackendToneUpdate(content).catch(() => {});
        }
        
        // Handle MR input messages (for tracking hype/monologue)
        // Note: MR messages might come as "input" or "message" type depending on the API
        if (data.type === "conversation.item.created" && 
            (data.item?.type === "input" || data.item?.type === "message") &&
            data.item?.role === "user") {
          const content = data.item.content?.[0]?.text || "";
          
          console.log("MR message detected:", content);
          
          // Add to transcript
          this.addToTranscript("rep", content);
          
          // Track hype and monologue patterns
          this.trackMrPatterns(content);
        }
      } catch (e) {
        console.warn("Failed to parse data channel message", e);
      }
    };

    // 7) Add mic track to connection
    this.micStream.getAudioTracks().forEach(track => {
      this.pc!.addTrack(track, this.micStream!);
      track.enabled = !this.isMuted && (!this.pushToTalkEnabled || this.pushToTalkActive);
    });

    // 8) Create offer
    const offer = await this.pc.createOffer({ offerToReceiveAudio: true, offerToReceiveVideo: false } as any);
    await this.pc.setLocalDescription(offer);

    // 9) Send SDP offer to OpenAI Realtime to receive answer
    const sdpAnswer = await this.postOfferToOpenAI(offer.sdp || "");
    const answer = {
      type: "answer" as const,
      sdp: sdpAnswer,
    };
    await this.pc.setRemoteDescription(answer);
  }

  async stop(): Promise<void> {
    try {
      this.detachHotkeys();
      if (this.rafId) { cancelAnimationFrame(this.rafId); this.rafId = null; }
      if (this.hangupTimer) { clearTimeout(this.hangupTimer); this.hangupTimer = null; }
      if (this.audioCtx) { try { this.audioCtx.close(); } catch {} this.audioCtx = null; }
      if (this.dc) {
        try { this.dc.close(); } catch {}
      }
      if (this.pc) {
        this.pc.getSenders().forEach(s => { try { s.track && s.track.stop(); } catch {} });
        this.pc.close();
      }
    } finally {
      this.dc = null;
      this.pc = null;
      if (this.micStream) {
        this.micStream.getTracks().forEach(t => t.stop());
        this.micStream = null;
      }
      if (this.audioEl) {
        try { this.audioEl.pause(); } catch {}
        this.audioEl.srcObject = null;
        this.audioEl.volume = 1.0;
      }
      this.remoteStream = null;
    }
  }

  private addToTranscript(role: string, content: string): void {
    this.transcript.push({
      role,
      content,
      timestamp: new Date().toISOString()
    });
    
    // Mirror to backend every 2 messages
    if (this.transcript.length % 2 === 0) {
      this.mirrorTranscriptToBackend();
    }
  }

  private async mirrorTranscriptToBackend(): Promise<void> {
    if (!this.sessionId) return;
    
    try {
      const url = `${this.apiBase}/transcript/${this.sessionId}/add`;
      const latestMessages = this.transcript.slice(-2); // Send last 2 messages
      
      for (const msg of latestMessages) {
        await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            role: msg.role,
            content: msg.content
          })
        });
      }
    } catch (e) {
      console.warn("Failed to mirror transcript to backend", e);
    }
  }

  async evaluateSession(transcript?: any[], personaId: string = "doc_001"): Promise<any> {
    const url = this.apiBase + "/voice/evaluate";
    const transcriptToUse = transcript || this.transcript;
    
    const payload = {
      transcript: transcriptToUse,
      persona_id: personaId,
      must_say: ["evidence", "trial", "study", "patient outcomes"],
      must_not_say: ["best", "revolutionary", "amazing", "unbelievable"]
    };
    
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error(`evaluation failed: ${res.status}`);
    return res.json();
  }

  getTranscript(): TranscriptEntry[] {
    return [...this.transcript];
  }

  private sendEvent(obj: any) {
    try {
      const payload = JSON.stringify(obj);
      this.dc?.send(payload);
    } catch (e) {
      console.warn("failed to send event", e);
    }
  }

  private buildSessionInstructions(): string {
    return [
      "You are a busy, senior medical doctor speaking in realtime via voice.",
      "Persona is not manually selected; infer and adapt dynamically based on the rep's behavior.",
      "Continuously adjust mood, time pressure, skepticism, and stage as the conversation evolves.",
      "Default stance: concise, professional, low patience; prefer replies under ~7 seconds.",
      "MR Coaching rules:",
      "- If rep uses vague claims (e.g., 'best') without proof, express irritation and request evidence.",
      "- If asked for evidence, expect trials, n-sizes, outcomes, guideline mentions.",
      "- If rep is concise and relevant, be engaged and progress the stage.",
      "- Under time pressure, prefer brevity and move to closure when appropriate.",
      "Outputs must be spoken responses; keep them persona-consistent and professional.",
      "Respond in English only.",
    ].join("\n");
  }

  // ===== Tone heuristics and session nudging =====
  private updateToneAndNudge(signals: string[], content: string): void {
    const lower = (content || "").toLowerCase();

    // Adjust mood
    if (signals.includes("shows impatience") || signals.includes("wants to end call")) {
      this.mood = "Dismissive";
      this.timePressureLevel = Math.min(5, this.timePressureLevel + 1);
    } else if (signals.includes("expresses interest")) {
      this.mood = "Engaged";
      this.timePressureLevel = Math.max(0, this.timePressureLevel - 1);
    } else if (signals.includes("asks for data") || signals.includes("requests evidence") || signals.includes("challenges claim")) {
      // Stay firm but professional; if pressure is high, lean dismissive
      this.mood = this.timePressureLevel >= 3 ? "Dismissive" : "Neutral";
    } else {
      // Fallback heuristic by keywords
      if (lower.includes("interesting") || lower.includes("tell me more")) {
        this.mood = "Engaged";
      }
      if (lower.includes("time") || lower.includes("busy") || lower.includes("quick")) {
        this.timePressureLevel = Math.min(5, this.timePressureLevel + 1);
      }
    }

    // Build short guidance snippet and nudge the session
    const guidance = this.buildDynamicGuidance();
    this.sendEvent({
      type: "session.update",
      session: {
        instructions: guidance,
      },
      tone: {
        mood: this.mood,
        timePressure: this.timePressureLevel,
        skepticism: this.skepticismLevel,
      },
    });
  }

  private buildDynamicGuidance(): string {
    const lines: string[] = [];
    lines.push("-- Dynamic Doctor Behavior Hints (do not read verbatim) --");
    lines.push(`Current mood cue: ${this.mood}`);
    lines.push(`Time pressure level: ${this.timePressureLevel} (0-5)`);
    lines.push(`Patience: ${this.patienceScore} (0-5), Engagement: ${this.engagementScore} (0-5)`);
    if (this.mood === "Dismissive") {
      lines.push("Be concise, ask for concrete evidence, and guide towards closure if irrelevancy persists.");
    } else if (this.mood === "Engaged") {
      lines.push("Invite brief but deeper, evidence-based discussion and progress the stage.");
    } else {
      lines.push("Maintain professional neutrality; request relevant, evidence-based points.");
    }
    return lines.join("\n");
  }

  private async requestBackendToneUpdate(lastDoctorMessage: string): Promise<void> {
    const now = Date.now();
    if (now - this.lastToneUpdateAt < this.minToneUpdateMs) return; // rate limit
    this.lastToneUpdateAt = now;

    const lastMr = this.getLastRepUtterance();
    const payload = {
      current_state: {
        mood: this.mood,
        timePressure: this.timePressureLevel,
        skepticism: this.skepticismLevel,
        patience: this.patienceScore,
        engagement: this.engagementScore,
        hypeCount: this.hypeCount,
        evidenceCount: this.evidenceCount,
        monologueCount: this.monologueCount,
      },
      last_doctor: lastDoctorMessage || "",
      last_mr: lastMr || "",
    };

    try {
      const res = await fetch(this.apiBase + "/tone-decide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) return;
      const upd = await res.json();
      const significant = this.isSignificantToneChange(upd);
      if (!significant) return;

      // Update local state with backend response
      this.mood = upd.mood;
      this.timePressureLevel = upd.timePressure;
      this.skepticismLevel = upd.skepticism;
      this.patienceScore = upd.patience || this.patienceScore;
      this.engagementScore = upd.engagement || this.engagementScore;
      this.hypeCount = upd.hypeCount || this.hypeCount;
      this.evidenceCount = upd.evidenceCount || this.evidenceCount;
      this.monologueCount = upd.monologueCount || this.monologueCount;

      // Check for cutNow trigger (doctor wants to end call)
      if (upd.cutNow && !this.cutNowTriggered) {
        this.cutNowTriggered = true;
        console.log("Doctor triggered cutNow - will auto-hangup in 2 seconds");
        
        // Set auto-hangup timer
        this.hangupTimer = window.setTimeout(() => {
          this.handleAutoHangup("Call ended due to patience exhaustion");
        }, 2000); // 2 second delay to let doctor finish speaking
      }

      this.sendEvent({
        type: "session.update",
        tone: {
          mood: this.mood,
          timePressure: this.timePressureLevel,
          skepticism: this.skepticismLevel,
        },
        hint: String(upd.action || "").slice(0, 200),
        pauseReply: Boolean(upd.pauseReply),
      });
    } catch {}
  }

  private trackMrPatterns(content: string): void {
    const contentLower = content.toLowerCase();
    
    // Track hype phrases
    const hypeWords = ["best", "revolutionary", "amazing", "unbelievable", "game-changing", "breakthrough", "incredible"];
    if (hypeWords.some(word => contentLower.includes(word))) {
      this.hypeCount++;
      console.log(`Hype detected (count: ${this.hypeCount}): ${content}`);
    }
    
    // Track evidence phrases - comprehensive medical criteria
    const evidencePatterns = [
      // Statistical evidence
      "n=", "p=", "p-value", "confidence interval", "ci", "hazard ratio", "hr", "odds ratio", "or",
      // Clinical endpoints
      "primary endpoint", "secondary endpoint", "efficacy", "response rate", "remission rate", 
      "progression-free survival", "pfs", "overall survival", "os", "disease-free survival", "dfs",
      // Trial design
      "randomized", "rct", "double-blind", "placebo-controlled", "phase", "multicenter",
      // Safety data
      "adverse events", "ae", "serious adverse events", "sae", "toxicity", "safety profile",
      // Biomarkers
      "biomarker", "genetic", "mutation", "expression", "receptor", "pathway",
      // Real-world evidence
      "real-world", "registry", "observational", "post-marketing", "surveillance",
      // Guidelines/standards
      "guidelines", "consensus", "recommendation", "standard of care", "treatment algorithm"
    ];
    
    if (evidencePatterns.some(pattern => contentLower.includes(pattern))) {
      this.evidenceCount++;
      console.log(`Medical evidence detected (count: ${this.evidenceCount}): ${content}`);
    }
    
    // Track monologues (long messages)
    const wordCount = content.split(/\s+/).length;
    if (wordCount > 25) {
      this.monologueCount++;
      console.log(`Monologue detected (count: ${this.monologueCount}, words: ${wordCount}): ${content}`);
    }
  }

  // Public method to manually track MR patterns (for testing)
  public trackMrMessage(content: string): void {
    console.log("Manually tracking MR message:", content);
    this.trackMrPatterns(content);
  }

  private handleAutoHangup(reason: string): void {
    console.log(`Auto-hangup triggered: ${reason}`);
    
    // Clear any pending hangup timer
    if (this.hangupTimer) {
      clearTimeout(this.hangupTimer);
      this.hangupTimer = null;
    }
    
    // Show notification to user
    if (this.coachingCallback) {
      this.coachingCallback(`Call ended: ${reason}`, "warning", []);
    }
    
    // Stop the session
    this.stop().then(() => {
      // Trigger evaluation with special note about early termination
      this.evaluateSession().then((result) => {
        if (this.coachingCallback) {
          this.coachingCallback("Session ended early due to doctor's patience exhaustion. Review your approach.", "error", []);
        }
      }).catch(console.error);
    }).catch(console.error);
  }

  private isSignificantToneChange(upd: any): boolean {
    if (!upd) return false;
    const moodChanged = upd.mood && upd.mood !== this.mood;
    const tpChanged = typeof upd.timePressure === "number" && Math.abs(upd.timePressure - this.timePressureLevel) >= 1;
    const skChanged = typeof upd.skepticism === "number" && Math.abs(upd.skepticism - this.skepticismLevel) >= 1;
    return Boolean(moodChanged || tpChanged || skChanged);
  }

  private getLastRepUtterance(): string | null {
    for (let i = this.transcript.length - 1; i >= 0; i--) {
      const t = this.transcript[i];
      if (t.role === "rep") return t.content;
    }
    return null;
  }

  // ===== Mic processing, VAD, barge-in, and hotkeys =====
  private setupMicProcessing(): void {
    try {
      if (!this.micStream) return;
      this.audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = this.audioCtx.createMediaStreamSource(this.micStream);
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 1024;
      source.connect(this.analyser);
      const loop = () => {
        const arr = new Uint8Array(this.analyser!.frequencyBinCount);
        this.analyser!.getByteTimeDomainData(arr);
        const rms = this.computeRmsFromTimeDomain(arr);
        // update simple VU meter
        const pct = Math.min(100, Math.round(rms * 200));
        $("#mic-level").text(`${pct}%`);
        this.updateVadState(rms);
        this.rafId = requestAnimationFrame(loop);
      };
      loop();
    } catch (e) {
      console.warn("setupMicProcessing failed", e);
    }
  }

  private computeRmsFromTimeDomain(buf: ArrayLike<number>): number {
    // values are 0..255 centered at 128
    let acc = 0;
    const len = buf.length;
    for (let i = 0; i < len; i++) {
      const v = ((buf[i] as number) - 128) / 128; // -1..1
      acc += v * v;
    }
    return Math.sqrt(acc / Math.max(1, len));
  }

  private updateVadState(rms: number): void {
    const now = performance.now();
    const above = rms >= this.vadHighThreshold;
    const below = rms <= this.vadLowThreshold;

    if (above) this.vadLastAboveTs = now;

    const wasSpeaking = this.isSpeaking;
    if (!this.isSpeaking && above) {
      this.isSpeaking = true;
      this.onLocalSpeechStart();
    } else if (this.isSpeaking && below && now - this.vadLastAboveTs > this.vadHoldMs) {
      this.isSpeaking = false;
      this.onLocalSpeechEnd();
    }
  }

  private onLocalSpeechStart(): void {
    // Barge-in: duck remote audio and hint the model to pause/keep it short
    if (this.audioEl) {
      this.remoteVolumeBeforeDuck = this.audioEl.volume;
      this.audioEl.volume = 0.2;
    }
    this.sendEvent({
      type: "session.update",
      session: {
        instructions: "Rep is speaking now. Pause or keep responses short; resume after the rep finishes.",
      },
    });
    // Enforce mute/PTT gating at track level
    this.applyTrackEnablement();
  }

  private onLocalSpeechEnd(): void {
    if (this.audioEl) {
      this.audioEl.volume = this.remoteVolumeBeforeDuck;
    }
    this.sendEvent({
      type: "session.update",
      session: {
        instructions: "Rep finished speaking. You may respond now; remain concise under time pressure.",
      },
    });
    this.applyTrackEnablement();
  }

  private applyTrackEnablement(): void {
    const enabled = !this.isMuted && (!this.pushToTalkEnabled || this.pushToTalkActive);
    if (this.micStream) {
      this.micStream.getAudioTracks().forEach(t => t.enabled = enabled);
    }
  }

  mute(toggle?: boolean): void {
    if (typeof toggle === "boolean") this.isMuted = toggle; else this.isMuted = !this.isMuted;
    this.applyTrackEnablement();
  }

  setPushToTalk(enabled: boolean): void {
    this.pushToTalkEnabled = enabled;
    this.pushToTalkActive = false;
    this.applyTrackEnablement();
  }

  private attachHotkeys(): void {
    const down = (e: KeyboardEvent) => {
      if (e.repeat) return;
      if (e.code === "Space") {
        this.pushToTalkActive = true;
        this.applyTrackEnablement();
      } else if (e.code === "KeyM") {
        this.mute();
      } else if (e.code === "KeyP") {
        this.setPushToTalk(!this.pushToTalkEnabled);
      }
    };
    const up = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        this.pushToTalkActive = false;
        this.applyTrackEnablement();
      }
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    // store refs for removal
    (this as any)._hkDown = down;
    (this as any)._hkUp = up;
  }

  private detachHotkeys(): void {
    const down = (this as any)._hkDown as (e: KeyboardEvent) => void;
    const up = (this as any)._hkUp as (e: KeyboardEvent) => void;
    if (down) window.removeEventListener("keydown", down);
    if (up) window.removeEventListener("keyup", up);
    (this as any)._hkDown = null;
    (this as any)._hkUp = null;
  }

  private async fetchSessionToken(): Promise<RealtimeSession> {
    const url = this.apiBase.replace(/\/api$/, "") + "/session-token";
    const res = await fetch(url);
    if (!res.ok) throw new Error(`session-token failed: ${res.status}`);
    return res.json();
  }

  private async postOfferToOpenAI(sdp: string): Promise<string> {
    const endpoint = "https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview";
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.ephemeralToken}`,
        "Content-Type": "application/sdp",
      },
      body: sdp,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`OpenAI SDP exchange failed: ${res.status} ${text}`);
    }
    const answerSdp = await res.text();
    return answerSdp;
  }
}
