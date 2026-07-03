export type WordType = 'verb' | 'noun';
export type WordPolarity = 'related' | 'antonym';

export interface WordCell {
  id: string;
  word: string;
  type: WordType;
  polarity: WordPolarity;
  gridX: number;
  gridZ: number;
  semanticX: number;
  semanticY: number;
  persona?: Persona;
  isListening: boolean;
  isReacting: boolean;
  reactionIntensity: number;
  cliqueId?: string;
}

export interface MemoryLayer {
  id: string;
  timestamp: number;
  title: string;
  narrative: string;
  emotionalTone: string;
}

export interface Persona {
  id: string;
  sourceWord: string;
  name: string;
  verbs: string[];
  nouns: string[];
  systemPrompt: string;
  memoryRegistry: MemoryLayer[];
  traits: string[];
}

export interface SuperCell {
  id: string;
  memberIds: string[];
  name: string;
  combinedPrompt: string;
  centerX: number;
  centerZ: number;
}

export interface GeneratedWord {
  word: string;
  type: WordType;
  semanticX: number;
  semanticY: number;
}

export interface GeneratedWords {
  related: GeneratedWord[];
  antonyms: GeneratedWord[];
}

export interface AppSettings {
  apiKey: string;
  modelSlug: string;
}