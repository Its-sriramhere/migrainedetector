import { useLive } from "../../context/LiveContext";
import "./FeatureImportance.css";

export function FeatureImportance() {
  const { prediction } = useLive();
  const latest = prediction;
  const features = latest?.features ?? [];

  if (!features.length) {
    return (
      <div className="feature-card empty">
        <span className="feature-title">FEATURE IMPORTANCE</span>
        <p>No prediction data yet. Start monitoring to see explanations.</p>
      </div>
    );
  }

  const sorted = [...features].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  return (
    <div className="feature-card">
      <div className="feature-header">
        <span className="feature-title">FEATURE IMPORTANCE</span>
        <span className="badge badge-ai">SHAP</span>
      </div>
      <div className="feature-bars">
        {sorted.slice(0, 6).map((f) => {
          const pct = Math.min(Math.abs(f.contribution) * 100, 100);
          const isPositive = f.contribution > 0;
          return (
            <div className="feature-row" key={f.feature_name}>
              <span className="feature-label">{f.feature_name}</span>
              <div className="feature-bar">
                <div
                  className={`feature-fill ${isPositive ? "danger" : "safe"}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className={`feature-value ${isPositive ? "danger" : "safe"}`}>
                {isPositive ? "+" : ""}
                {(f.contribution * 100).toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}