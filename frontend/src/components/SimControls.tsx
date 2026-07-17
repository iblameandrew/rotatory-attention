import { useMatchStore } from "../store/matchStore";

export function SimControls() {
  const playing = useMatchStore((s) => s.playing);
  const speed = useMatchStore((s) => s.speed);
  const setPlaying = useMatchStore((s) => s.setPlaying);
  const setSpeed = useMatchStore((s) => s.setSpeed);
  const match = useMatchStore((s) => s.match);
  const sim = useMatchStore((s) => s.sim);

  if (!match || !sim) return null;

  const alive = sim.units.filter((u) => u.alive).length;

  return (
    <div className="overlay-bar">
      <button type="button" onClick={() => setPlaying(!playing)}>
        {playing ? "Pause" : "Play"}
      </button>
      {[1, 2, 4].map((s) => (
        <button
          key={s}
          type="button"
          className={speed === s ? "primary" : undefined}
          onClick={() => setSpeed(s)}
        >
          ×{s}
        </button>
      ))}
      <span className="badge">
        t={sim.time.toFixed(1)}s · {alive}/{sim.units.length} alive
      </span>
      {match.factions.map((f) => (
        <span className="badge" key={f.chart_id}>
          <span className="dot" style={{ background: f.color }} />
          {f.name} ({f.roster.length})
        </span>
      ))}
    </div>
  );
}
