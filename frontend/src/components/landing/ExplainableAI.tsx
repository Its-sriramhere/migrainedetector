import { Sparkles } from "lucide-react";
import { Reveal } from "../ui/Reveal";

const factors = [
  { label: "HRV decrease", width: 92, tone: "danger" },
  { label: "Sleep deviation", width: 74, tone: "cyan" },
  { label: "HR increase", width: 60, tone: "cyan" },
  { label: "BP variation", width: 42, tone: "cyan" },
  { label: "Activity change", width: 26, tone: "cyan" },
];

export function ExplainableAI() {
  return (
    <section className="xai-section section">
      <div className="container">
        <div className="xai-wrap">
          <Reveal>
            <div className="xai-copy">
              <span className="eyebrow">06 — Explainable AI</span>
              <h2 className="section-title">
                Why is your risk <span className="gradient-text">elevated?</span>
              </h2>
              <p className="section-subtitle">
                SHAP-style feature attribution shows which physiological changes
                contributed most to the current risk estimate.
              </p>
              <div className="xai-sample">
                <span className="xai-title">Sample prediction · 81%</span>
                <div className="xai-bars">
                  {factors.map((factor) => (
                    <div className="xai-bar-row" key={factor.label}>
                      <span className="xai-bar-label">{factor.label}</span>
                      <div className="xai-bar">
                        <div
                          className={`xai-bar-fill ${factor.tone}`}
                          style={{ width: `${factor.width}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal>
            <div className="xai-token">
              <Sparkles size={26} />
              <strong>✦ AI ANALYSIS</strong>
              <p>
                Every elevated risk estimate comes with an explanation you can read.
              </p>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}