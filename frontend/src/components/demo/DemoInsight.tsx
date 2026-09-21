import { Sparkles } from "lucide-react";
import { useLive } from "../../context/LiveContext";
import "./DemoInsight.css";

export function DemoInsight() {
  const { prediction } = useLive();
  const features = prediction?.features ?? [];

  const top = [...features]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 3);

  return (
    <div className="demo-insight">
      <div className="demo-insight-header">
        <Sparkles size={14} />
        <span>LIVE INSIGHT — WHY THIS RISK</span>
      </div>

      {prediction ? (
        <>
          <div className="demo-insight-score">
            Risk <strong>{prediction.risk_score}%</strong> ({prediction.risk_level})
          </div>
          {top.length > 0 ? (
            <ul className="demo-insight-list">
              {top.map((f) => (
                <li key={f.feature_name}>
                  <span className={f.contribution >= 0 ? "pos" : "neg"}>
                    {f.contribution >= 0 ? "+" : ""}
                    {(f.contribution * 100).toFixed(1)}%
                  </span>
                  <em>{f.feature_name}</em>
                </li>
              ))}
            </ul>
          ) : (
            <p className="demo-insight-empty">Sample this preset to see the explanation.</p>
          )}

          {prediction.advice && prediction.advice.length > 0 && (
            <div className="demo-insight-advice">
              <div className="demo-insight-advice-title">CALMING STEPS</div>
              <ul>
                {prediction.advice.map((tip, i) => (
                  <li key={i}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      ) : (
        <p className="demo-insight-empty">
          No prediction yet. Push a preset or start the stream to generate insights.
        </p>
      )}
    </div>
  );
}