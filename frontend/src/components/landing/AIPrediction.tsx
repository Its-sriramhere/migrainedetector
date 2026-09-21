import { BrainCircuit, TrendingDown, TrendingUp, Timer } from "lucide-react";
import { Reveal } from "../ui/Reveal";

const steps = [
  {
    icon: <Timer size={18} />,
    title: "Time-windowed features",
    body: "The last 30 minutes are turned into means, trends, variance and sudden changes — never a single isolated reading.",
  },
  {
    icon: <TrendingUp size={18} />,
    title: "Deviation from baseline",
    body: "Current pattern vs your own baseline is converted into a personal deviation profile.",
  },
  {
    icon: <BrainCircuit size={18} />,
    title: "ML prediction",
    body: "A calibrated model estimates the probability of an episode within the configured window.",
  },
  {
    icon: <TrendingDown size={18} />,
    title: "Non-diagnostic output",
    body: "The result is an estimated risk level — low, moderate or high — never a diagnosis.",
  },
];

export function AIPrediction() {
  return (
    <section className="section">
      <div className="container">
        <Reveal>
          <span className="eyebrow">05 — AI Prediction</span>
          <h2 className="section-title">
            Machine learning on <span className="gradient-text">your time series.</span>
          </h2>
          <p className="section-subtitle">
            Baseline models first — Logistic Regression, Random Forest, XGBoost — with
            SHAP explaining every prediction.
          </p>
        </Reveal>

        <div className="grid-4 ai-grid">
          {steps.map((step, index) => (
            <Reveal key={step.title} className="ai-card glass-card">
              <div className="ai-card-top">
                <span className="ai-icon">{step.icon}</span>
                <span className="ai-index">0{index + 1}</span>
              </div>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}