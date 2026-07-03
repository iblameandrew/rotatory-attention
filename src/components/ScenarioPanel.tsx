import { useAppStore } from '../store/appStore';

export function ScenarioPanel() {
  const scenario = useAppStore((s) => s.scenario);
  const isGenerating = useAppStore((s) => s.isGenerating);
  const isGeneratingPersonas = useAppStore((s) => s.isGeneratingPersonas);
  const personaProgress = useAppStore((s) => s.personaProgress);
  const cells = useAppStore((s) => s.cells);
  const setScenario = useAppStore((s) => s.setScenario);
  const generateScenario = useAppStore((s) => s.generateScenario);

  return (
    <section className="panel scenario-panel">
      <h2>Scenario</h2>
      <p className="hint">
        Describe a closed system. Two cardinalities — verbs &amp; nouns — decompose
        into 50 related and 50 antonym cells, laid out on a semantic gradient where
        similar words sit close and distant words sit far apart.
      </p>
      <textarea
        value={scenario}
        onChange={(e) => setScenario(e.target.value)}
        placeholder="A rain-soaked harbor where forgotten ships whisper contracts to the tide..."
        rows={4}
      />
      <button
        className="primary"
        onClick={generateScenario}
        disabled={(isGenerating || isGeneratingPersonas) || !scenario.trim()}
      >
        {isGenerating
          ? 'Decomposing...'
          : isGeneratingPersonas
            ? `Emanating personas (${personaProgress.completed}/${personaProgress.total})...`
            : 'Decompose Scenario'}
      </button>
      {isGeneratingPersonas && personaProgress.total > 0 && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(personaProgress.completed / personaProgress.total) * 100}%` }}
          />
        </div>
      )}
      {cells.length > 0 && (
        <div className="stats">
          <span className="stat related">{cells.filter((c) => c.polarity === 'related').length} related</span>
          <span className="stat antonym">{cells.filter((c) => c.polarity === 'antonym').length} antonyms</span>
          <span className="stat persona">{cells.filter((c) => c.persona).length} personas</span>
        </div>
      )}
    </section>
  );
}