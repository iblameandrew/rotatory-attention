import { AURA_RADIUS, PATROL_SPEED_SCALE } from "./balance";
import { dist } from "./combat";
import type { PartisanRelation, SimUnit, Stance } from "./types";

export function stanceBetween(
  relations: PartisanRelation[],
  a: string,
  b: string
): Stance {
  if (a === b) return "affiliation";
  for (const r of relations) {
    if (
      (r.chart_a === a && r.chart_b === b) ||
      (r.chart_a === b && r.chart_b === a)
    ) {
      return r.stance;
    }
  }
  return "neutrality";
}

export function isAlly(
  relations: PartisanRelation[],
  a: SimUnit,
  b: SimUnit
): boolean {
  return stanceBetween(relations, a.factionId, b.factionId) === "affiliation";
}

export function isEnemy(
  relations: PartisanRelation[],
  a: SimUnit,
  b: SimUnit
): boolean {
  return stanceBetween(relations, a.factionId, b.factionId) === "conflict";
}

export function pickTarget(
  unit: SimUnit,
  units: SimUnit[],
  relations: PartisanRelation[]
): string | null {
  const stancePref: Stance =
    // Prefer conflict targets; if none, affiliation for support; else null
    "conflict";

  let bestEnemy: SimUnit | null = null;
  let bestEnemyD = Infinity;
  let bestAlly: SimUnit | null = null;
  let bestAllyNeed = -1;

  for (const other of units) {
    if (!other.alive || other.id === unit.id) continue;
    const st = stanceBetween(relations, unit.factionId, other.factionId);
    const d = dist(unit.pos, other.pos);
    if (st === "conflict" && d < bestEnemyD) {
      bestEnemyD = d;
      bestEnemy = other;
    }
    if (st === "affiliation") {
      const need = 1 - other.hp / Math.max(1, other.maxHp);
      if (need > 0.05 && need > bestAllyNeed && d < AURA_RADIUS * 3) {
        bestAllyNeed = need;
        bestAlly = other;
      }
    }
  }

  if (bestEnemy) return bestEnemy.id;
  if (bestAlly) return bestAlly.id;
  return null;
}

export function seek(
  unit: SimUnit,
  target: SimUnit,
  dt: number,
  mode: "attack" | "support" | "patrol"
): [number, number] {
  const dx = target.pos[0] - unit.pos[0];
  const dy = target.pos[1] - unit.pos[1];
  const d = Math.hypot(dx, dy) || 1;
  const range = unit.attrs.range;
  let desired = unit.attrs.speed * (mode === "patrol" ? PATROL_SPEED_SCALE : 1);

  // Stop inside range for attack
  if (mode === "attack" && d <= range * 0.95) {
    return [0, 0];
  }
  // Support: approach but not on top
  if (mode === "support" && d < 1.2) {
    return [0, 0];
  }

  return [(dx / d) * desired * dt, (dy / d) * desired * dt];
}

export function wander(unit: SimUnit, dt: number, t: number): [number, number] {
  const angle = Math.sin(t * 0.7 + unit.pos[0] * 0.1) * Math.PI * 2;
  const sp = unit.attrs.speed * 0.35 * dt;
  return [Math.cos(angle) * sp, Math.sin(angle) * sp];
}

export function softSeparation(
  unit: SimUnit,
  units: SimUnit[],
  dt: number
): [number, number] {
  let sx = 0;
  let sy = 0;
  for (const other of units) {
    if (!other.alive || other.id === unit.id) continue;
    const d = dist(unit.pos, other.pos);
    if (d > 1.1 || d < 1e-4) continue;
    const push = (1.1 - d) / 1.1;
    sx += ((unit.pos[0] - other.pos[0]) / d) * push;
    sy += ((unit.pos[1] - other.pos[1]) / d) * push;
  }
  return [sx * 1.5 * dt, sy * 1.5 * dt];
}
