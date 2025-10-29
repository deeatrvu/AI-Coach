import $ from "jquery";
import { PersonaManager, FeedbackRenderer } from "./modules";
import { RealtimeClient } from "./realtime";
import { CoachingOverlay } from "./coaching";

const personaManager = new PersonaManager();
const feedback = new FeedbackRenderer();
const rtc = new RealtimeClient();
const coaching = new CoachingOverlay();


function appendTranscript(role: "rep" | "doctor", text: string) {
  const el = $("#transcript");
  const div = $("<div>").addClass(`msg ${role}`).text(`${role.toUpperCase()}: ${text}`);
  el.append(div);
  el.scrollTop(el.prop("scrollHeight"));
}

// Persona indicators for text mode removed

async function init() {
  $("#session-status").text("Connecting...");
  await personaManager.loadPersonas();
  $("#session-status").text("Ready");

  // Set up coaching callback
  rtc.setCoachingCallback((content: string, type: string, signals: string[]) => {
    coaching.analyzeDoctorResponse(content, signals);
  });

  // Voice Start
  $("#rt-start").on("click", async () => {
    try {
      $("#session-status").text("Starting voice...");
      coaching.showStartHint();
      await rtc.start();
      $("#rt-start").prop("disabled", true);
      $("#rt-stop").prop("disabled", false);
      $("#session-status").text("Voice connected");
    } catch (e: any) {
      $("#session-status").text("Error");
      alert(e.message || e.toString());
    }
  });

  // Voice Stop
  $("#rt-stop").on("click", async () => {
    try {
      await rtc.stop();
      coaching.hide();
      
      // Run evaluation with sample transcript
      const sampleTranscript = [
        { role: "rep", content: "Hello Dr. Smith, I'd like to discuss our new medication" },
        { role: "doctor", content: "What evidence do you have for its effectiveness?" },
        { role: "rep", content: "Our studies show it's the best treatment available" },
        { role: "doctor", content: "I need to see the trial data, not marketing claims" }
      ];
      
      const evaluation = await rtc.evaluateSession();
      feedback.showFeedback(evaluation);
      
      $("#rt-start").prop("disabled", false);
      $("#rt-stop").prop("disabled", true);
      $("#session-status").text("Voice stopped - Evaluation complete");
    } catch (e: any) {
      alert(e.message || e.toString());
    }
  });

  // Text mode controls removed in voice-only mode
}

init();


