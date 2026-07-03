import type { WordType } from '../types';

export interface SemanticWord {
  word: string;
  type: WordType;
  semanticX: number;
  semanticY: number;
}

interface LayoutPoint {
  x: number;
  z: number;
  anchorX: number;
  anchorZ: number;
}

const MIN_DIST = 1.35;
const SPREAD = 11;

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

function fallbackCoord(index: number, total: number, axis: 'x' | 'y'): number {
  const t = total <= 1 ? 0.5 : index / (total - 1);
  if (axis === 'x') return clamp01(t);
  const row = Math.floor(t * Math.sqrt(total));
  const col = index % Math.ceil(Math.sqrt(total));
  const cols = Math.ceil(Math.sqrt(total));
  return clamp01(col / Math.max(cols - 1, 1) * 0.6 + row / Math.max(Math.ceil(total / cols) - 1, 1) * 0.4);
}

function normalizeSemantic(words: SemanticWord[]): SemanticWord[] {
  return words.map((w, i) => ({
    ...w,
    semanticX: clamp01(w.semanticX ?? fallbackCoord(i, words.length, 'x')),
    semanticY: clamp01(w.semanticY ?? fallbackCoord(i, words.length, 'y')),
  }));
}

function relaxOverlaps(points: LayoutPoint[], iterations = 60): void {
  for (let iter = 0; iter < iterations; iter++) {
    for (let i = 0; i < points.length; i++) {
      for (let j = i + 1; j < points.length; j++) {
        const dx = points[j].x - points[i].x;
        const dz = points[j].z - points[i].z;
        const dist = Math.sqrt(dx * dx + dz * dz) || 0.01;
        if (dist < MIN_DIST) {
          const push = (MIN_DIST - dist) / 2;
          const nx = dx / dist;
          const nz = dz / dist;
          points[i].x -= nx * push;
          points[i].z -= nz * push;
          points[j].x += nx * push;
          points[j].z += nz * push;
        }
      }
    }

    const anchorPull = 0.25 - iter * 0.003;
    if (anchorPull > 0) {
      for (const p of points) {
        p.x += (p.anchorX - p.x) * anchorPull;
        p.z += (p.anchorZ - p.z) * anchorPull;
      }
    }
  }
}

function layoutField(words: SemanticWord[], offsetZ: number): { x: number; z: number }[] {
  const normalized = normalizeSemantic(words);
  const points: LayoutPoint[] = normalized.map((w) => {
    const x = w.semanticX * SPREAD;
    const z = w.semanticY * SPREAD + offsetZ;
    return { x, z, anchorX: x, anchorZ: z };
  });

  relaxOverlaps(points);
  return points.map((p) => ({ x: p.x, z: p.z }));
}

export function layoutSemanticGradient(
  related: SemanticWord[],
  antonyms: SemanticWord[],
): { positions: { x: number; z: number }[]; centerX: number; centerZ: number } {
  const relatedPos = layoutField(related, 0);
  const antonymPos = layoutField(antonyms, SPREAD + 3);
  const positions = [...relatedPos, ...antonymPos];

  const centerX = positions.reduce((s, p) => s + p.x, 0) / positions.length;
  const centerZ = positions.reduce((s, p) => s + p.z, 0) / positions.length;

  return { positions, centerX, centerZ };
}

export function semanticDistance(
  ax: number,
  az: number,
  bx: number,
  bz: number,
): number {
  return Math.sqrt((ax - bx) ** 2 + (az - bz) ** 2);
}