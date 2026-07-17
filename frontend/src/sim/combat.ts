/**
 * Combat resolution: energization × local density.
 * Pure functions for testability.
 */

import {
  AURA_RADIUS,
  COHESION_LOG_K,
  CROWD_SOFT_CAP,
  ENERGY_HIT_COST,
  ENERGY_HIT_GAIN,
  ENERGY_MAX,
  ENERGY_MIN,
  ENERGY_SHOCK,
  FOCUS_K,
  OVERCROWD_K,
  PRESSURE_LOG_K,
  RESIST_SCALE,
} from "./balance";
import type { SimUnit } from "./types";

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

export function dist(a: [number, number], b: [number, number]): number {
  const dx = a[0] - b[0];
  const dy = a[1] - b[1];
  return Math.hypot(dx, dy);
}

export function countNearby(
  unit: SimUnit,
  units: SimUnit[],
  isAlly: (a: SimUnit, b: SimUnit) => boolean,
  isEnemy: (a: SimUnit, b: SimUnit) => boolean,
  radius = AURA_RADIUS
): { alliesNear: number; enemiesNear: number; sameFeatureAllies: number } {
  let alliesNear = 0;
  let enemiesNear = 0;
  let sameFeatureAllies = 0;
  for (const other of units) {
    if (!other.alive || other.id === unit.id) continue;
    if (dist(unit.pos, other.pos) > radius) continue;
    if (isAlly(unit, other)) {
      alliesNear += 1;
      if (other.featureId === unit.featureId) sameFeatureAllies += 1;
    } else if (isEnemy(unit, other)) {
      enemiesNear += 1;
    }
  }
  return { alliesNear, enemiesNear, sameFeatureAllies };
}

/** Soft log cohesion: more allies help, diminishing returns. Same-feature allies weigh extra. */
export function cohesionBonus(alliesNear: number, sameFeatureAllies: number): number {
  const w = alliesNear + sameFeatureAllies * 0.5;
  return COHESION_LOG_K * Math.log1p(w);
}

export function pressureFactor(enemiesNear: number): number {
  return PRESSURE_LOG_K * Math.log1p(enemiesNear);
}

/** Past soft cap, efficiency drops. */
export function overcrowdPenalty(crowd: number): number {
  if (crowd <= CROWD_SOFT_CAP) return 0;
  return clamp(OVERCROWD_K * (crowd - CROWD_SOFT_CAP), 0, 0.45);
}

export function focusFactor(alliesAttackingSame: number): number {
  return 1 / (1 + FOCUS_K * Math.max(0, alliesAttackingSame));
}

export interface ResolveInput {
  attacker: SimUnit;
  defender: SimUnit;
  alliesNearA: number;
  sameFeatureAlliesA: number;
  enemiesNearA: number;
  alliesNearD: number;
  sameFeatureAlliesD: number;
  enemiesNearD: number;
  alliesAttackingSameTarget: number;
  rng: () => number; // 0..1
}

export interface ResolveResult {
  damage: number;
  energyAttacker: number;
  energyDefender: number;
  power: number;
  resist: number;
  variance: number;
}

export function resolveExchange(input: ResolveInput): ResolveResult {
  const {
    attacker: A,
    defender: D,
    alliesNearA,
    sameFeatureAlliesA,
    enemiesNearA,
    alliesNearD,
    sameFeatureAlliesD,
    enemiesNearD,
    alliesAttackingSameTarget,
    rng,
  } = input;

  const E_A = clamp(A.energy, ENERGY_MIN, ENERGY_MAX);
  const E_D = clamp(D.energy, ENERGY_MIN, ENERGY_MAX);

  const cohA = cohesionBonus(alliesNearA, sameFeatureAlliesA);
  const cohD = cohesionBonus(alliesNearD, sameFeatureAlliesD);
  const crowdA = alliesNearA + enemiesNearA;
  const overA = overcrowdPenalty(crowdA);
  const pressure = pressureFactor(enemiesNearD);
  const focus = focusFactor(alliesAttackingSameTarget);

  const skillPower = 1.0; // base auto; skills multiply outside if needed
  const baseDamage = A.attrs.damage * skillPower;

  const power =
    baseDamage *
    (0.5 + 0.5 * E_A) *
    (1 + cohA) *
    (1 - overA) *
    (0.85 + 0.15 * A.attrs.will);

  const resist =
    D.attrs.armor *
    (0.5 + 0.5 * E_D) *
    (1 + cohD) *
    (0.85 + 0.15 * D.attrs.structure);

  const raw = Math.max(1, power - resist * RESIST_SCALE * 0.15);
  // variance rises with contested fields
  const variance = 0.15 + 0.3 * clamp(pressure / 0.6, 0, 1);
  const roll = 1 - variance + rng() * (2 * variance);
  const damage = Math.max(1, raw * roll * focus);

  // Energy updates
  let energyA = E_A - ENERGY_HIT_COST;
  if (damage > 1 && alliesNearA >= 1) {
    energyA += ENERGY_HIT_GAIN; // group momentum
  }
  energyA = clamp(energyA, ENERGY_MIN, ENERGY_MAX);

  const shock = ENERGY_SHOCK * clamp(damage / Math.max(1, D.maxHp), 0, 1) * 4;
  let energyD = E_D - shock;
  // Shared field: allies reduce shock
  if (alliesNearD > 0) {
    energyD += 0.02 * Math.min(alliesNearD, 4);
  }
  energyD = clamp(energyD, ENERGY_MIN, ENERGY_MAX);

  return {
    damage,
    energyAttacker: energyA,
    energyDefender: energyD,
    power,
    resist,
    variance,
  };
}

export function regenEnergy(
  unit: SimUnit,
  dt: number,
  alliesNear: number,
  inCombat: boolean
): number {
  const baseline = unit.baselineEnergy;
  let e = unit.energy;
  const hpRatio = unit.hp / Math.max(1, unit.maxHp);
  // Low HP drains toward lower baseline
  const target = clamp(baseline * (0.55 + 0.45 * hpRatio), ENERGY_MIN, ENERGY_MAX);
  if (!inCombat) {
    e += 0.06 * dt * (target > e ? 1 : -0.3);
  }
  if (alliesNear > 0) {
    e += 0.04 * dt * Math.min(alliesNear, 3) * 0.25;
  }
  // Pull gently toward target
  e += (target - e) * 0.08 * dt;
  return clamp(e, ENERGY_MIN, ENERGY_MAX);
}
