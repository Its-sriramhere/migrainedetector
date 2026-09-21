import { Reveal } from "../ui/Reveal";

const nodes = [
  "14 Questions",
  "Personal Baseline",
  "Raspberry Pi",
  "Physiological Data",
  "ML Model",
  "SHAP / XAI",
  "Risk Score",
  "Alert",
];

export function DataFlow() {
  return (
    <section className="data-flow">
      <div className="container">
        <Reveal>
          <div className="data-flow-heading">
            <span className="eyebrow">02 — How It Works</span>
            <h2 className="section-title">
              From signals to <em className="gradient-text">insight.</em>
            </h2>
            <p className="section-subtitle">
              Your Raspberry Pi streams physiological data into a single pipeline
              shared by the live demo and real hardware.
            </p>
          </div>
        </Reveal>

        <div className="flow-track">
          {nodes.map((node, index) => (
            <div className="flow-item" key={node}>
              <div className="flow-node">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{node}</strong>
              </div>
              {index !== nodes.length - 1 && (
                <div className="flow-connector">
                  <i />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}