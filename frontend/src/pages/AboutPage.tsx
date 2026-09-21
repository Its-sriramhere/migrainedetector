import { Reveal } from "../components/ui/Reveal";
import { Link } from "react-router-dom";

export function AboutPage() {
  return (
    <div className="page-wrapper">
      <Reveal>
        <div className="marketing-hero">
          <span className="eyebrow">ABOUT MIGRAINE DETECTOR</span>
          <h1>
            An early-warning system for <span className="gradient-text">your migraine.</span>
          </h1>
          <p className="marketing-hero-sub">
            Migraine Detector is a full-stack research prototype that combines a Raspberry Pi
            sensor station, a FastAPI backend, machine learning, and explainable AI to estimate
            personalized migraine risk from physiological signals.
          </p>
        </div>
      </Reveal>

      <div className="grid-3 min-section">
        <Reveal className="glass-card list-card">
          <h3>Why signals?</h3>
          <p>
            Many migraines are preceded by silent physiological changes — heart rate, HRV,
            blood pressure, activity, temperature. Watching those changes relative to a
            personal baseline creates a prediction window.
          </p>
        </Reveal>
        <Reveal className="glass-card list-card">
          <h3>Built for research</h3>
          <p>
            The system is designed as a study platform: it can log episodes, evaluate
            predictions leakage-safe on real data, and never claims to diagnose anything.
          </p>
        </Reveal>
        <Reveal className="glass-card list-card">
          <h3>Open by design</h3>
          <p>
            The pipeline is modular — sensors → preprocessing → features → model → explanation —
            so you can swap models or add new sensors without rewriting the core.
          </p>
        </Reveal>
      </div>

      <Reveal>
        <div className="cta-actions marketing-cta">
          <Link to="/how-it-works" className="btn btn-primary btn-lg btn-shine">
            See How It Works <span>→</span>
          </Link>
        </div>
      </Reveal>
    </div>
  );
}