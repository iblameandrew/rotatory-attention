import { create } from "zustand";
import { createMatch } from "../api/client";
import { createSimFromMatch, stepSim, type SimState } from "../sim/engine";
import type { BirthInput, MatchManifest, SimUnit } from "../sim/types";

export const PRESETS: BirthInput[] = [
  {
    name: "Ada",
    year: 1990,
    month: 7,
    day: 15,
    hour: 10,
    minute: 30,
    lat: 41.9028,
    lng: 12.4964,
    tz_str: "Europe/Rome",
  },
  {
    name: "Niko",
    year: 1988,
    month: 12,
    day: 3,
    hour: 18,
    minute: 15,
    lat: 40.7128,
    lng: -74.006,
    tz_str: "America/New_York",
  },
  {
    name: "Mira",
    year: 1995,
    month: 3,
    day: 21,
    hour: 8,
    minute: 5,
    lat: 35.6762,
    lng: 139.6503,
    tz_str: "Asia/Tokyo",
  },
];

interface Store {
  people: BirthInput[];
  match: MatchManifest | null;
  sim: SimState | null;
  playing: boolean;
  speed: number;
  selectedUnitId: string | null;
  loading: boolean;
  error: string | null;
  setPeople: (p: BirthInput[]) => void;
  addPerson: () => void;
  removePerson: (index: number) => void;
  updatePerson: (index: number, patch: Partial<BirthInput>) => void;
  loadPresets: (count?: number) => void;
  generate: () => Promise<void>;
  setPlaying: (v: boolean) => void;
  setSpeed: (v: number) => void;
  selectUnit: (id: string | null) => void;
  tick: (dt: number) => void;
  selectedUnit: () => SimUnit | null;
}

const emptyPerson = (): BirthInput => ({
  name: "Person",
  year: 1992,
  month: 6,
  day: 15,
  hour: 12,
  minute: 0,
  lat: 51.5074,
  lng: -0.1278,
  tz_str: "Europe/London",
});

export const useMatchStore = create<Store>((set, get) => ({
  people: PRESETS.slice(0, 2),
  match: null,
  sim: null,
  playing: true,
  speed: 1,
  selectedUnitId: null,
  loading: false,
  error: null,

  setPeople: (p) => set({ people: p }),
  addPerson: () =>
    set((s) => ({
      people: [
        ...s.people,
        { ...emptyPerson(), name: `Person ${s.people.length + 1}` },
      ],
    })),
  removePerson: (index) =>
    set((s) => ({ people: s.people.filter((_, i) => i !== index) })),
  updatePerson: (index, patch) =>
    set((s) => ({
      people: s.people.map((p, i) => (i === index ? { ...p, ...patch } : p)),
    })),
  loadPresets: (count = 2) => set({ people: PRESETS.slice(0, count) }),

  generate: async () => {
    set({ loading: true, error: null });
    try {
      const match = await createMatch(get().people, {
        max_units_per_faction: 18,
        include_mixtures: true,
      });
      const sim = createSimFromMatch(match);
      set({ match, sim, loading: false, playing: true, selectedUnitId: null });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : String(e),
      });
    }
  },

  setPlaying: (v) => set({ playing: v }),
  setSpeed: (v) => set({ speed: v }),
  selectUnit: (id) => set({ selectedUnitId: id }),

  tick: (dt) => {
    const { sim, match, playing, speed } = get();
    if (!playing || !sim || !match) return;
    stepSim(sim, match, dt * speed);
    // trigger re-render
    set({ sim: { ...sim, units: [...sim.units] } });
  },

  selectedUnit: () => {
    const { sim, selectedUnitId } = get();
    if (!sim || !selectedUnitId) return null;
    return sim.units.find((u) => u.id === selectedUnitId) ?? null;
  },
}));
