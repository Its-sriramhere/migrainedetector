import { Reveal } from "../components/ui/Reveal";
import { Link } from "react-router-dom";

const stack = [
  { tech: "Frontend", detail: "React 18 + TypeScript + Vite, Recharts, Tailwind-driven design tokens" },
  { tech: "Backend", detail: "FastAPI, SQLAlchemy, SQLite (PostgreSQL-ready via DATABASE_URL)" },
  { tech: "Edge device", detail: "Raspberry Pi with MAX30102, BP module, MPU6050, MAX30205" },
  { tech: "ML", detail: "scikit-learn, XGBoost, SHAP; baseline models first, user-level CV" },
  { tech: "Realtime", detail: "WebSocket (prediction_update / alert_update), async demo stream" },
  { tech: "Security", detail: "bcrypt password hashing, JWT auth, CORS, HTTPS-ready" },
];

export function ResearchPage() {
  return (
    <div className="page-wrapper">
      <Reveal>
        <div className="marketing-hero">
          <span className="eyebrow">RESEARCH & TECHNOLOGY</span>
          <h1>
            A rigorous, <span className="gradient-text">explainable</span> foundation.
          </h1>
          <p className="marketing-hero-sub">
            Evaluation, privacy and reproducibility are first-class concerns across the whole
            stack.
          </p>
        </div>
      </Reveal>

      <div className="stack-grid">
        {stack.map((item) => (
          <Reveal key={item.tech} className="glass-card stack-card">
            <h3>{item.tech}</h3>
            <p>{item.detail}</p>
          </Reveal>
        ))}
      </div>

      <Reveal className="glass-card metrics-card">
        <h2 className="section-title-sm">Evaluation metrics</h2>
        <p className="cell-muted">
          Precision, recall, specificity, ROC-AUC, PR-AUC, false-alarm rate and prediction lead
          time — computed on leakage-safe user-level splits.
        </p>
      </Reveal>

      <Reveal>
        <div className="cta-actions marketing-cta">
          <Link to="/demo" className="btn btn-primary btn-lg btn-shine">
            Try the Demo Lab <span>→</span>
          </Link>
        </div>
      </Reveal>
    </div>
  );
}