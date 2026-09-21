import { Reveal } from "../components/ui/Reveal";
import { Link } from "react-router-dom";

const steps = [
  {
    n: "01",
    title: "Create your profile",
    body: "Register and answer 14 guided questions about migraine history, sleep, stress, caffeine, hydration and known triggers.",
  },
  {
    n: "02",
    title: "Learn your baseline",
    body: "The system builds a personal baseline — a normal heart-rate band, typical sleep and a deviation profile. Population averages never apply.",
  },
  {
    n: "03",
    title: "Stream physiological data",
    body: "A Raspberry Pi reads heart rate, HRV, blood pressure, SpO₂ and temperature; filters and validates the signal; and uploads it securely.",
  },
  {
    n: "04",
    title: "Extract features",
    body: "Time-windowed features (means, trends, variance, sudden changes) are computed and compared against your baseline.",
  },
  {
    n: "05",
    title: "Predict risk",
    body: "A calibrated ML model estimates the probability of an episode in the next 60 minutes. Low, moderate and high bands are reported.",
  },
  {
    n: "06",
    title: "Explain & act",
    body: "SHAP-style attributions explain which signals drove the estimate. Alerts arrive on the dashboard for you to acknowledge or reject.",
  },
];

export function HowItWorksPage() {
  return (
    <div className="page-wrapper">
      <Reveal>
        <div className="marketing-hero">
          <span className="eyebrow">HOW IT WORKS</span>
          <h1>
            One pipeline from <span className="gradient-text">signal to insight.</span>
          </h1>
          <p className="marketing-hero-sub">
            The same pipeline powers the live demo, the Raspberry Pi, and real ML training.
          </p>
        </div>
      </Reveal>

      <div className="steps-list">
        {steps.map((step) => (
          <Reveal key={step.n} className="step-card glass-card">
            <span className="step-n">{step.n}</span>
            <div>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal>
        <div className="cta-actions marketing-cta">
          <Link to="/register" className="btn btn-primary btn-lg btn-shine">
            Start Personalized Monitoring <span>→</span>
          </Link>
        </div>
      </Reveal>
    </div>
  );
}