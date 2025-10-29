import { EvaluationResponse } from "./types";

const API_BASE = (window as any).API_BASE || "http://localhost:8000/api";

export async function apiGetPersonas() {
  const res = await fetch(`${API_BASE}/personas`);
  if (!res.ok) throw new Error(`personas failed: ${res.status}`);
  return res.json();
}

