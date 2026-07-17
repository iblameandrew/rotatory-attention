import { useMatchStore } from "../store/matchStore";

export function FactionPanel() {
  const match = useMatchStore((s) => s.match);
  const sim = useMatchStore((s) => s.sim);
  const selectUnit = useMatchStore((s) => s.selectUnit);
  const selectedUnitId = useMatchStore((s) => s.selectedUnitId);

  if (!match) {
    return (
      <div>
        <h2>Factions</h2>
        <p className="muted">Generate a match to spawn units.</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Relations</h2>
      {match.relations.length === 0 && (
        <p className="muted">Single faction — no partisan matrix.</p>
      )}
      {match.relations.map((r) => (
        <div className="relation-row" key={`${r.chart_a}-${r.chart_b}`}>
          <span>
            {r.name_a} ↔ {r.name_b}
          </span>
          <span className={`stance-${r.stance}`}>
            {r.stance} ({r.score.toFixed(2)})
          </span>
        </div>
      ))}

      <h2>Rosters</h2>
      {match.factions.map((f) => {
        const living =
          sim?.units.filter((u) => u.factionId === f.chart_id && u.alive).length ??
          f.roster.length;
        return (
          <div key={f.chart_id} style={{ marginBottom: "0.75rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                className="dot"
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: f.color,
                  display: "inline-block",
                }}
              />
              <strong>{f.name}</strong>
              <span className="muted">
                {living} alive · {f.mixtures.length} mixtures
              </span>
            </div>
            <ul className="unit-list">
              {(sim?.units.filter((u) => u.factionId === f.chart_id) ?? []).map(
                (u) => (
                  <li
                    key={u.id}
                    className={selectedUnitId === u.id ? "active" : undefined}
                    onClick={() => selectUnit(u.id)}
                  >
                    {u.alive ? "●" : "○"} {u.name}{" "}
                    <span className="muted">
                      E {(u.energy * 100).toFixed(0)}%
                    </span>
                  </li>
                )
              )}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
