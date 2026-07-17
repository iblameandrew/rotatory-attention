import { useMatchStore } from "../store/matchStore";

export function ChartForm() {
  const people = useMatchStore((s) => s.people);
  const updatePerson = useMatchStore((s) => s.updatePerson);
  const addPerson = useMatchStore((s) => s.addPerson);
  const removePerson = useMatchStore((s) => s.removePerson);
  const loadPresets = useMatchStore((s) => s.loadPresets);
  const generate = useMatchStore((s) => s.generate);
  const loading = useMatchStore((s) => s.loading);
  const error = useMatchStore((s) => s.error);

  return (
    <div>
      <h1>Rotatory Attention</h1>
      <p className="muted">
        Each birth chart becomes a faction. Units are hierarchical children of
        role/style features; fights resolve by energization and local density.
      </p>

      <div className="actions">
        <button type="button" onClick={() => loadPresets(2)}>
          2 presets
        </button>
        <button type="button" onClick={() => loadPresets(3)}>
          3 presets
        </button>
        <button type="button" onClick={addPerson}>
          Add chart
        </button>
      </div>

      {people.map((p, i) => (
        <div className="person-card" key={i}>
          <header>
            <span>Faction {i + 1}</span>
            <button
              type="button"
              disabled={people.length <= 1}
              onClick={() => removePerson(i)}
            >
              Remove
            </button>
          </header>
          <div className="field">
            <label>Name</label>
            <input
              value={p.name}
              onChange={(e) => updatePerson(i, { name: e.target.value })}
            />
          </div>
          <div className="row">
            <div className="field">
              <label>Year</label>
              <input
                type="number"
                value={p.year}
                onChange={(e) => updatePerson(i, { year: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Month</label>
              <input
                type="number"
                value={p.month}
                onChange={(e) => updatePerson(i, { month: Number(e.target.value) })}
              />
            </div>
          </div>
          <div className="row">
            <div className="field">
              <label>Day</label>
              <input
                type="number"
                value={p.day}
                onChange={(e) => updatePerson(i, { day: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Hour</label>
              <input
                type="number"
                value={p.hour}
                onChange={(e) => updatePerson(i, { hour: Number(e.target.value) })}
              />
            </div>
          </div>
          <div className="row">
            <div className="field">
              <label>Minute</label>
              <input
                type="number"
                value={p.minute}
                onChange={(e) =>
                  updatePerson(i, { minute: Number(e.target.value) })
                }
              />
            </div>
            <div className="field">
              <label>Timezone</label>
              <input
                value={p.tz_str}
                onChange={(e) => updatePerson(i, { tz_str: e.target.value })}
              />
            </div>
          </div>
          <div className="row">
            <div className="field">
              <label>Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={p.lat}
                onChange={(e) => updatePerson(i, { lat: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={p.lng}
                onChange={(e) => updatePerson(i, { lng: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>
      ))}

      {error && <div className="error">{error}</div>}

      <div className="actions">
        <button
          type="button"
          className="primary"
          disabled={loading || people.length < 1}
          onClick={() => void generate()}
        >
          {loading ? "Spawning…" : "Generate match"}
        </button>
      </div>
    </div>
  );
}
