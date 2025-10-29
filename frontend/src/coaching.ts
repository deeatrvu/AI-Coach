import $ from "jquery";
import { CoachingHintType } from "./types";

export class CoachingOverlay {
  private overlay: JQuery<HTMLElement>;
  private hint: JQuery<HTMLElement>;
  private hintText: JQuery<HTMLElement>;
  private hintIcon: JQuery<HTMLElement>;

  constructor() {
    this.overlay = $("#coaching-overlay");
    this.hint = $("#coaching-hint");
    this.hintText = this.hint.find(".hint-text");
    this.hintIcon = this.hint.find(".hint-icon");
  }

  showHint(message: string, type: CoachingHintType = "info", icon: string = "💡"): void {
    this.hintText.text(message);
    this.hintIcon.text(icon);
    
    // Remove existing type classes
    this.overlay.removeClass("warning success info");
    
    // Add new type class
    if (type !== "info") {
      this.overlay.addClass(type);
    }
    
    // Show the overlay
    this.overlay.prop("hidden", false);
    
    // Auto-hide after 5 seconds for non-critical messages
    if (type === "info") {
      setTimeout(() => this.hide(), 5000);
    }
  }

  hide(): void {
    this.overlay.prop("hidden", true);
  }

  // Predefined coaching hints based on common scenarios
  showEvidenceHint(): void {
    this.showHint("💡 Provide specific trial data, patient outcomes, or guideline references", "warning", "📊");
  }

  showDeEscalateHint(): void {
    this.showHint("⚠️ Doctor seems irritated - acknowledge concerns and provide concrete evidence", "warning", "⚠️");
  }

  showEngagementHint(): void {
    this.showHint("✅ Good! Doctor is engaged - continue with evidence-based discussion", "success", "✅");
  }

  showTimePressureHint(): void {
    this.showHint("⏰ Doctor seems pressed for time - be concise and focus on key benefits", "warning", "⏰");
  }

  showObjectionHint(): void {
    this.showHint("🤔 Doctor raised an objection - address it directly with evidence", "info", "🤔");
  }

  showClosureHint(): void {
    this.showHint("🎯 Doctor seems ready to end - summarize key points and next steps", "info", "🎯");
  }

  showStartHint(): void {
    this.showHint("🎤 Start your conversation - introduce yourself and the medication", "info", "🎤");
  }

  showGenericHint(message: string): void {
    this.showHint(message, "info", "💡");
  }

  // Analyze doctor response and show appropriate hint
  analyzeDoctorResponse(response: string, signals: string[] = []): void {
    const responseLower = response.toLowerCase();
    
    // Check for specific signals first
    if (signals.includes("asks for data") || signals.includes("requests evidence")) {
      this.showEvidenceHint();
    } else if (signals.includes("shows impatience") || signals.includes("wants to end call")) {
      this.showDeEscalateHint();
    } else if (signals.includes("expresses interest")) {
      this.showEngagementHint();
    } else if (signals.includes("challenges claim")) {
      this.showObjectionHint();
    } else {
      // Fallback to text analysis
      if (responseLower.includes("evidence") || responseLower.includes("trial") || responseLower.includes("study")) {
        this.showEvidenceHint();
      } else if (responseLower.includes("time") || responseLower.includes("busy") || responseLower.includes("quick")) {
        this.showTimePressureHint();
      } else if (responseLower.includes("objection") || responseLower.includes("concern") || responseLower.includes("worried")) {
        this.showObjectionHint();
      } else if (responseLower.includes("thank you") || responseLower.includes("goodbye") || responseLower.includes("end")) {
        this.showClosureHint();
      } else if (responseLower.includes("interesting") || responseLower.includes("tell me more")) {
        this.showEngagementHint();
      } else {
        this.showGenericHint("Continue the conversation naturally - listen to the doctor's concerns");
      }
    }
  }

  // Show hints based on conversation stage
  showStageHint(stage: string): void {
    switch (stage) {
      case "Introduction":
        this.showHint("👋 Introduce yourself and establish rapport", "info", "👋");
        break;
      case "Discussion":
        this.showHint("💬 Present your medication benefits with evidence", "info", "💬");
        break;
      case "ObjectionDiscussion":
        this.showHint("🛡️ Address objections with data and patient stories", "warning", "🛡️");
        break;
      case "Closure":
        this.showHint("🎯 Summarize key points and propose next steps", "info", "🎯");
        break;
      default:
        this.showGenericHint("Continue the conversation based on doctor's responses");
    }
  }
}
