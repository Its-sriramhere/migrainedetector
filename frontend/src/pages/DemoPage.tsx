import { DemoControls } from "../components/demo/DemoControls";
import { DemoInsight } from "../components/demo/DemoInsight";
import { SensorChart } from "../components/dashboard/SensorChart";
import { RiskScore } from "../components/dashboard/RiskScore";
import { useLive } from "../context/LiveContext";

export function DemoPage() {
  const { prediction, sensorHistory } = useLive();

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Demo & Simulation</h1>
          <p className="page-subtitle">
            Push presets or a simulated stream through the exact pipeline used by the Raspberry Pi.
          </p>
        </div>
      </header>

      <div className="demo-page">
        <div className="demo-page-main">
          <DemoControls />
          <SensorChart />
          <div className="demo-counts">
            <span>{sensorHistory.length} readings in session</span>
          </div>
        </div>

        <aside className="demo-page-side">
          <RiskScore score={Math.round(prediction?.risk_score ?? 0)} advice={prediction?.advice} />
          <DemoInsight />
        </aside>
      </div>
    </div>
  );
}