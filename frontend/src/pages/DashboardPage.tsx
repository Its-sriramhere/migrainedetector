import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useLive } from "../context/LiveContext";
import { RiskScore } from "../components/dashboard/RiskScore";
import { SensorCard } from "../components/dashboard/SensorCard";
import { RaspberryPiStatus } from "../components/dashboard/RaspberryPiStatus";
import { FeatureImportance } from "../components/dashboard/FeatureImportance";
import { AlertCard } from "../components/dashboard/AlertCard";
import { Spinner } from "../components/ui/Spinner";

export function DashboardPage() {
  const { prediction, latestReading, alerts, sensorHistory, refresh, connected } = useLive();

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const samples =
    latestReading?.heart_rate != null
      ? [
          { type: "heart_rate", value: `${Math.round(latestReading.heart_rate)} BPM`, timestamp: latestReading.timestamp },
          { type: "hrv", value: latestReading.hrv != null ? `${Math.round(latestReading.hrv)} ms` : "—" },
          {
            type: "blood_pressure",
            value:
              latestReading.systolic_bp && latestReading.diastolic_bp
                ? `${Math.round(latestReading.systolic_bp)}/${Math.round(latestReading.diastolic_bp)}`
                : "—",
          },
          { type: "temperature", value: latestReading.temperature != null ? `${latestReading.temperature}°C` : "—" },
        ]
      : [];

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            {connected ? "Live stream connected." : "Offline — start the demo or connect your Pi."}
          </p>
        </div>
        <Link to="/demo" className="btn btn-secondary btn-sm">
          Open Demo Lab
        </Link>
      </header>

      <div className="dash-grid">
        <div className="dash-col-main">
          <RiskScore score={Math.round(prediction?.risk_score ?? latestReading?.heart_rate ? 30 : 0)} advice={prediction?.advice} />

          {samples.length > 0 ? (
            <div className="sensor-card-grid">
              {samples.map((s) => (
                <SensorCard key={s.type} type={s.type} value={s.value} timestamp={s.timestamp} />
              ))}
            </div>
          ) : (
            <div className="empty-card">
              <Spinner />
              <span>Waiting for sensor data…</span>
            </div>
          )}

          {alerts.length > 0 && (
            <div className="dash-alerts">
              <h2 className="section-title-sm">Recent Alerts</h2>
              {alerts.slice(0, 3).map((a) => (
                <AlertCard key={a.id} alert={a} />
              ))}
            </div>
          )}
        </div>

        <div className="dash-col-side">
          <RaspberryPiStatus />
          <FeatureImportance />
          <div className="dash-quick-links">
            <Link to="/xai">Explain a prediction →</Link>
            <Link to="/history">Log a migraine →</Link>
          </div>
        </div>
      </div>

      {sensorHistory.length > 0 && (
        <p className="dash-count">Stored readings this session: {sensorHistory.length}</p>
      )}
    </div>
  );
}