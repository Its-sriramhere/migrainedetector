import { BrainCircuit, Fingerprint, ShieldCheck } from "lucide-react";
import { Fragment } from "react";
import { Reveal } from "../ui/Reveal";

const features = [
  {
    icon: <Fingerprint size={20} />,
    title: "14-question profile",
    body: "A guided assessment captures your migraine history, sleep, stress, activity and known triggers.",
  },
  {
    icon: <BrainCircuit size={20} />,
    title: "Learns your baseline",
    body: "The system learns what is normal for you from your own physiological measurements — not population averages.",
  },
  {
    icon: <ShieldCheck size={20} />,
    title: "Personalized risk",
    body: "Current signals are compared against your own baseline to estimate deviation and migraine risk.",
  },
];

const chain = ["QUESTIONNAIRE", "PERSONAL PROFILE", "BASELINE", "CURRENT SIGNAL", "DEVIATION", "MODEL", "RISK"];

export function Personalization() {
  return (
    <section className="section">
      <div className="container">
        <Reveal>
          <span className="eyebrow">03 — Personalization</span>
          <h2 className="section-title">
            The system learns what is <span className="gradient-text">normal for you.</span>
          </h2>
          <p className="section-subtitle">
            A generic "high heart rate" rule cannot detect your migraine. Comparing
            today's signals against <em>your own</em> baseline can.
          </p>
        </Reveal>

        <div className="grid-3 personalization-grid">
          {features.map((feature) => (
            <Reveal key={feature.title} className="glass-card glass-purple personal-card">
              <div className="personal-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
            </Reveal>
          ))}
        </div>

        <Reveal>
          <div className="chain">
            {chain.map((step, index) => (
              <Fragment key={step}>
                <span className="chain-node">{step}</span>
                {index !== chain.length - 1 && <span className="chain-arrow">→</span>}
              </Fragment>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}