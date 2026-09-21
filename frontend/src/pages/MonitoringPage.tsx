import { useEffect } from "react";
import { SensorChart } from "../components/dashboard/SensorChart";
import { SensorCard } from "../components/dashboard/SensorCard";
import { RaspberryPiStatus } from "../components/dashboard/RaspberryPiStatus";
import { useLive } from "../context/LiveContext";

export function MonitoringPage() {
  const { latestReading, sensorHistory, refresh } = useLive();

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const cards = [
    { type: "heart_rate", value: latestReading?.heart_rate != null ? `${Math.round(latestReading.heart_rate)} BPM` : "—" },
    { type: "hrv", value: latestReading?.hrv != null ? `${Math.round(latestReading.hrv)} ms` : "—" },
    {
      type: "blood_pressure",
      value:
        latestReading?.systolic_bp && latestReading.diastolic_bp
          ? `${Math.round(latestReading.systolic_bp)}/${Math.round(latestReading.diastolic_bp)}`
          : "—",
    },
    { type: "spo2", value: latestReading?.spo2 != null ? `${Math.round(latestReading.spo2)}%` : "—" },
    { type: "temperature", value: latestReading?.temperature != null ? `${latestReading.temperature}°C` : "—" },
    { type: "pi_status", value: sensorHistory.length ? "Active" : "—" },
  ];

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Live Monitoring</h1>
          <p className="page-subtitle">Latest physiological readings from your device or the demo stream.</p>
        </div>
      </header>

      <div className="monitoring-grid">
        <div className="monitoring-main">
          <SensorChart />
          <div className="sensor-card-grid">
            {cards.map((c) => (
              <SensorCard key={c.type} type={c.type} value={c.value} />
            ))}
          </div>
        </div>
        <aside className="monitoring-side">
          <RaspberryPiStatus />
        </aside>
      </div>
    </div>
  );
}