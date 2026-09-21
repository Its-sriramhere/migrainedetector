import { Link } from "react-router-dom";
import { Reveal } from "../ui/Reveal";

const pipeline = ["DATA INPUT", "PREPROCESSING", "FEATURE EXTRACTION", "ML MODEL", "SHAP", "RISK", "ALERT"];

export function DemoSection() {
  return (
    <section className="demo-section section">
      <div className="container">
        <Reveal>
          <span className="eyebrow">08 — Demo Lab</span>
          <h2 className="section-title">
            See the pipeline <span className="gradient-text">in action.</span>
          </h2>
          <p className="section-subtitle">
            Push NORMAL, MODERATE or HIGH-RISK presets — or a live simulated stream —
            through the exact same pipeline used by the Raspberry Pi.
          </p>
        </Reveal>

        <Reveal>
          <div className="demo-pipeline">
            {pipeline.map((stage, index) => (
              <div className="demo-stage" key={stage}>
                <span className="demo-stage-node">{stage}</span>
                {index !== pipeline.length - 1 && (
                  <span className="demo-stage-connector"><i /></span>
                )}
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal>
          <div className="demo-cta">
            <Link to="/register" className="btn btn-primary btn-lg btn-shine">
              Try the Demo Lab <span>→</span>
            </Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}