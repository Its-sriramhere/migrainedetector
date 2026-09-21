import { FlaskConical, LineChart, Microscope, ShieldCheck } from "lucide-react";
import { Reveal } from "../ui/Reveal";

const items = [
  {
    icon: <LineChart size={18} />,
    title: "Evaluation, not just accuracy",
    body: "Precision, recall, specificity, ROC-AUC, PR-AUC, false-alarm rate and prediction lead time.",
  },
  {
    icon: <FlaskConical size={18} />,
    title: "Leakage-safe evaluation",
    body: "Train, validation and test splits are performed at the user level to avoid optimistic results.",
  },
  {
    icon: <Microscope size={18} />,
    title: "Research prototype",
    body: "Designed as a prediction early-warning study, not a clinically validated diagnostic device.",
  },
  {
    icon: <ShieldCheck size={18} />,
    title: "Privacy-first",
    body: "Password hashing, JWT authentication, HTTPS and data minimization throughout.",
  },
];

export function Research() {
  return (
    <section className="section">
      <div className="container">
        <Reveal>
          <span className="eyebrow">09 — Research & Technology</span>
          <h2 className="section-title">
            Built as a <span className="gradient-text">research system.</span>
          </h2>
        </Reveal>
        <div className="grid-2 research-grid">
          {items.map((item) => (
            <Reveal key={item.title} className="glass-card research-card">
              <div className="personal-icon">{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}