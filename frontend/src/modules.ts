import $ from "jquery";
import { apiGetPersonas } from "./api";
import { DoctorTraitProfile } from "./types";

// Audio management is now handled inside RealtimeClient (realtime.ts)

export class PersonaManager {
  personas: DoctorTraitProfile[] = [];
  current?: DoctorTraitProfile;
  async loadPersonas(): Promise<void> {
    const data = await apiGetPersonas();
    this.personas = data.personas || [];
    this.current = this.personas[0];
    const sel = $("#persona-select");
    sel.empty();
    this.personas.forEach(p => {
      const name = p.description.split(" — ")[0];
      sel.append($("<option>").val(p.id).text(name));
    });
    sel.on("change", () => {
      const id = String(sel.val());
      this.selectPersonaById(id);
    });
  }
  selectPersonaById(id: string) {
    this.current = this.personas.find(p => p.id === id);
  }
}

// Text-mode ConversationEngine removed in voice-only mode

export class FeedbackRenderer {
  showFeedback(evaluation: any): void {
    $("#feedback").prop("hidden", false);
    $("#feedback-json").text(JSON.stringify(evaluation, null, 2));
  }
  renderScores(scores: any): void {
    // Placeholder for richer UI later
  }
}

