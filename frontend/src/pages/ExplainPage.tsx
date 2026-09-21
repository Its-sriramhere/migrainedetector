import { useLive } from "../context/LiveContext";
import { FeatureImportance } from "../components/dashboard/FeatureImportance";
import { RiskScore } from "../components/dashboard/RiskScore";
import { DemoInsight } from "../components/demo/DemoInsight";

export function ExplainPage() {
  const { prediction } = useLive();
  const features = prediction?.features ?? [];

  const summary =
    !prediction
      ? "No prediction yet. Generate one in the Demo Lab to see the SHAP-style explanation."
      : prediction.risk_level === "high"
        ? "Several features are pushing your risk upward. Review each contribution below."
        : "Your current pattern is near baseline. The contributions below are small in magnitude.";

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Explainable AI</h1>
          <p className="page-subtitle">
            Why did the model estimate this risk? SHAP-style feature attribution per prediction.
          </p>
        </div>
      </header>

      <div className="xai-page-grid">
        <div className="xai-main">
          <div className="explain-card glass-card">
            <span className="eyebrow">CURRENT PREDICTION</span>
            <h2 className="section-title-sm">{summary}</h2>
            {prediction && (
              <p className="cell-muted">
                Model {prediction.model_version} · window {prediction.prediction_window} min ·{" "}
                {prediction.source === "demo" ? "demo source" : prediction.source}
              </p>
            )}
          </div>
          <FeatureImportance />
          {features.length > 0 && (
            <div className="explain-card glass-card">
              <span className="eyebrow">FEATURE VALUES</span>
              <div className="feature-values">
                {features.map((f) => (
                  <div className="feature-value-row" key={f.feature_name}>
                    <span>{f.feature_name}</span>
                    <strong>{f.feature_value ?? "—"}</strong>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <aside className="xai-side">
          <RiskScore score={Math.round(prediction?.risk_score ?? 0)} advice={prediction?.advice} />
          <DemoInsight />
        </aside>
      </div>
    </div>
  );
}