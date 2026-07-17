import type { BirthInput, MatchManifest } from "../sim/types";

export async function createMatch(
  people: BirthInput[],
  options?: { max_units_per_faction?: number; include_mixtures?: boolean }
): Promise<MatchManifest> {
  const res = await fetch("/api/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ people, options: options ?? {} }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Match failed");
  }
  return res.json();
}

export async function healthCheck(): Promise<{ ok: boolean; agent_mode: string }> {
  const res = await fetch("/health");
  if (!res.ok) throw new Error("API offline");
  return res.json();
}
