import { chatCompletion } from './openrouter';
import type { GeneratedWord, GeneratedWords } from '../types';

const SYSTEM = `You are a semantic decomposition engine. Given a scenario description, you break it into a closed system with exactly two cardinalities: VERBS (actions, processes) and NOUNS (entities, objects, concepts).

Return valid JSON with this exact structure:
{
  "related": [{"word": "string", "type": "verb"|"noun", "semanticX": 0.0, "semanticY": 0.0}, ...],
  "antonyms": [{"word": "string", "type": "verb"|"noun", "semanticX": 0.0, "semanticY": 0.0}, ...]
}

Rules:
- "related" must contain exactly 50 entries (mix of verbs and nouns deeply tied to the scenario)
- "antonyms" must contain exactly 50 entries (semantic opposites/contrasts to the scenario)
- Each half should have roughly equal verbs and nouns
- Words should be evocative, specific, and scenario-grounded
- No duplicates across both lists

SEMANTIC GRADIENT COORDINATES (critical):
- Every word MUST have semanticX and semanticY (floats from 0.0 to 1.0)
- These coordinates define a semantic distance field — words are placed in space proportional to meaning
- Semantically adjacent/similar words MUST have coordinates within 0.03–0.08 of each other
- Semantically distant words MUST be far apart (Euclidean distance 0.35+ in coordinate space)
- Build a continuous gradient manifold: if word A is close to B in meaning, and B is close to C, then A and C should also be relatively near
- Related words form one gradient cluster; antonyms form a separate gradient cluster with their own internal proximity rules
- Verbs and nouns can interleave in the gradient based on semantic affinity, not separated by type`;

export async function generateWords(
  model: string,
  scenario: string,
): Promise<GeneratedWords> {
  const raw = await chatCompletion(
    model,
    SYSTEM,
    `Scenario: "${scenario}"\n\nDecompose this closed system into 50 related verbs/nouns and 50 antonym verbs/nouns. Assign semanticX/semanticY coordinates so similar words are spatially close and distant words are far apart.`,
  );

  const parsed = JSON.parse(raw) as GeneratedWords;
  return {
    related: normalizeList(parsed.related),
    antonyms: normalizeList(parsed.antonyms),
  };
}

function normalizeList(
  items: { word: string; type: string; semanticX?: number; semanticY?: number }[] | undefined,
): GeneratedWord[] {
  if (!Array.isArray(items)) return [];
  return items
    .filter((i) => i?.word)
    .map((i) => ({
      word: String(i.word).trim(),
      type: i.type === 'verb' ? 'verb' : 'noun',
      semanticX: clamp(i.semanticX),
      semanticY: clamp(i.semanticY),
    }));
}

function clamp(v: unknown): number {
  const n = Number(v);
  if (Number.isNaN(n)) return 0.5;
  return Math.max(0, Math.min(1, n));
}