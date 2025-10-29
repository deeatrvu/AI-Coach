// ===================== Core Types =====================

export type ConsultationStyle =
  | "Fast-paced"
  | "Detailed"
  | "Data-driven"
  | "Intuitive"
  | "Empathetic";

export type KnowledgeLevel = "Generalist" | "Specialist" | "Thought Leader";

export type SkepticismLevel = "Low" | "Medium" | "High";

export type Gender = "Male" | "Female" | "Non-binary" | "Other" | "Prefer not to say";

export type ConversationStage = "Introduction" | "Discussion" | "ObjectionDiscussion" | "Closure";

export type DoctorMood = "Neutral" | "Engaged" | "Dismissive";

export type Role = "doctor" | "rep";

// ===================== Behavioral Types =====================

export interface BehavioralTriggers {
  positive: string[];
  negative: string[];
}

export interface SkepticismState {
  scores: number[]; // sliding window of recent scores
}

// ===================== Persona Types =====================

export interface DoctorTraitProfile {
  id: string;
  description: string;
  communication_style: string;
  decision_factors: string[];
  baseline_skepticism_level: SkepticismLevel;
  behavioral_triggers: BehavioralTriggers;
  knowledge_level: KnowledgeLevel;
  consultation_style: ConsultationStyle;
  typical_objections: string[];
  preferred_evidence: string[];
  gender?: Gender;
  availableTimeSeconds: number;
}

// ===================== State Types =====================

export interface DoctorBehaviorState {
  mood: DoctorMood;
  timePressureLevel: number; // 0-5
  conversationStage: ConversationStage;
  secondsElapsed: number;
  trust: number; // 0-100
  skepticismState: SkepticismState;
  currentSkepticismLevel: SkepticismLevel;
  notes?: string;
}

// ===================== Message Types =====================

export interface Message {
  role: Role;
  timestamp?: string;
  content: string;
}

export interface ConversationMessage {
  role: Role;
  timestamp: string; // ISO string
  content: string;
  isLastRepMessage?: boolean;
}

// ===================== API Response Types =====================

export interface StartResponse {
  session_id: string;
  state: DoctorBehaviorState;
  persona: DoctorTraitProfile;
}

export interface TurnResponse {
  state: DoctorBehaviorState;
  doctor_reply: string;
  signals: string[];
  relevancy: -1 | 0 | 1;
  stage: ConversationStage;
  skepticism: SkepticismLevel;
  trust: number;
  time_pressure: number;
  transcript: Message[];
}

export interface EvaluationResponse {
  session_id: string;
  evaluation: EvaluationOutput;
}

// ===================== Evaluation Types =====================

export interface TurnFeedback {
  turnIndex: number;
  speaker: "rep";
  content: string;
  critique: string;
  sentiment: "positive" | "negative" | "neutral";
  couldHaveSaid?: string[];
  justification: string;
}

export interface EvaluationOutput {
  scores: {
    accuracy: number; // 0-100
    empathy: number; // 0-100
    compliance: number; // 0-100
    adaptability: number; // 0-100
  };
  compliance: {
    mustSayMentioned: string[];
    mustSayMissed: string[];
    mustNotSayViolations: string[];
  };
  feedbackSummary: string;
  turnLevelAnalysis: TurnFeedback[];
}

// ===================== Agent Types =====================

export interface DoctorAgentInput {
  persona: DoctorTraitProfile;
  currentMood: DoctorMood;
  timePressureLevel: number;
  conversationStage: ConversationStage;
  secondsElapsed: number;
  currentSkepticismLevel: SkepticismLevel;
  remainingTime: number;
  conversationTranscript: ConversationMessage[];
  repLastMessage: string;
  previousDoctorMessages: string[];
}

export interface DoctorLLMResponse {
  doctorReply: string;
  relevancy: -1 | 0 | 1;
  justification: string;
  nextConversationStage: ConversationStage;
  nextMood: DoctorMood;
  signals?: string[];
}

// ===================== Realtime Types =====================

export interface RealtimeSession {
  client_secret?: { value?: string };
  id?: string;
  model?: string;
}

export interface TranscriptEntry {
  role: string;
  content: string;
  timestamp: string;
}

// ===================== Coaching Types =====================

export type CoachingHintType = "info" | "warning" | "success";

export interface CoachingHint {
  message: string;
  type: CoachingHintType;
  icon: string;
}