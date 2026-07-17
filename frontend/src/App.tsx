import { ChartForm } from "./components/ChartForm";
import { FactionPanel } from "./components/FactionPanel";
import { SimControls } from "./components/SimControls";
import { UnitInspector } from "./components/UnitInspector";
import { Battlefield } from "./scene/Battlefield";

export default function App() {
  return (
    <div className="app">
      <aside className="panel">
        <ChartForm />
      </aside>
      <main className="viewport">
        <SimControls />
        <Battlefield />
      </main>
      <aside className="panel right">
        <FactionPanel />
        <UnitInspector />
      </aside>
    </div>
  );
}
