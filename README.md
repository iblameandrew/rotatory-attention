# Causality

A Three.js semantic decomposition system. Given a scenario description, the closed system breaks down into two cardinalities — **verbs** and **nouns** — generating 50 related words and 50 antonyms via OpenRouter LLM.

Each word lives as a voxel cell on a Conway-inspired isometric grid. After decomposition, every cell automatically emanates a full persona (5 verbs, 5 nouns, system prompt, layered memory registry). Cells listen and react to uttered words, and can form cliques into super cells.

## Setup

```bash
npm install
npm run dev
```

## Usage

1. Enter your [OpenRouter](https://openrouter.ai) API key and select a model slug
2. Describe a scenario and click **Decompose Scenario**
3. Explore the isometric voxel grid — related cells on top, antonyms below
4. Watch personas emanate across all cells automatically
5. **Click** a cell to inspect its persona
6. **Utter** words to make cells react; neighboring cells resonate
7. Select multiple cells and **Form Super Cell** to create cliques

## Stack

- React + TypeScript + Vite
- Three.js via @react-three/fiber + @react-three/drei
- OpenAI SDK → OpenRouter backend
- Zustand state management