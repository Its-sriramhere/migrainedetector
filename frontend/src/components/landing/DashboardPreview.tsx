import { Activity, HeartPulse, Wind } from "lucide-react";
import { Reveal } from "../ui/Reveal";

export function DashboardPreview() {
  return (
    <section className="section">
      <div className="container">
        <Reveal>
          <span className="eyebrow">07 — Dashboard</span>
          <h2 className="section-title">
            One calm screen for <span className="gradient-text">everything live.</span>
          </h2>
          <p className="section-subtitle">
            Current risk, Raspberry Pi status, live sensor values, trends, SHAP
            explanation and recent alerts — designed to be read at a glance.
          </p>
        </Reveal>

        <Reveal>
          <div className="dashboard-preview glass-card">
            <div className="preview-top">
              <div className="preview-headline">
                <span className="risk-dot high" />
                CURRENT MIGRAINE RISK
              </div>
              <span className="badge badge-warning">● DEMO MODE</span>
            </div>
            <div className="preview-body">
              <div className="preview-risk">
                <div className="preview-ring">72%<small>MODERATE</small></div>
                <div className="preview-risk-meta">
                  <strong>Next 60 minutes</strong>
                  <span>Based on your current pattern vs your personal baseline.</span>
                </div>
              </div>
              <div className="preview-sensors">
                {[
                  { icon: <HeartPulse size={16} />, label: "HR", value: "84 BPM" },
                  { icon: <Activity size={16} />, label: "HRV", value: "34 ms" },
                  { icon: <Activity size={16} />, label: "BP", value: "128/82" },
                  { icon: <Wind size={16} />, label: "SpO₂", value: "98%" },
                ].map((sensor) => (
                  <div className="preview-chip" key={sensor.label}>
                    {sensor.icon}
                    <span>{sensor.label}</span>
                    <strong>{sensor.value}</strong>
                  </div>
                ))}
              </div>
            </div>
            <div className="preview-chart">
              <div className="chart-lines" />
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}