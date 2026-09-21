import { Link } from "react-router-dom";

export function Hero() {
  return (
    <section className="hero">
      <div className="hero-grid" />
      <div className="hero-orb hero-orb-cyan" />
      <div className="hero-orb hero-orb-purple" />

      <div className="hero-content">
        <div className="hero-badge anim-fade-up">
          <span className="status-dot" />
          AI-POWERED HEALTH MONITORING
        </div>

        <h1 className="anim-fade-up delay-1">
          Understand your body
          <span className="gradient-text">before the migraine.</span>
        </h1>

        <p className="hero-description anim-fade-up delay-2">
          A personalized early-warning system combining physiological monitoring,
          Raspberry Pi, machine learning and explainable AI.
        </p>

        <div className="hero-actions anim-fade-up delay-3">
          <Link to="/register" className="btn btn-primary btn-lg btn-shine">
            Start Monitoring <span>→</span>
          </Link>
          <Link to="/how-it-works" className="btn btn-secondary btn-lg">
            Explore System
          </Link>
        </div>

        <div className="hero-trust anim-fade-up delay-4">
          <span>●</span> Personalized <span>•</span> Real-time <span>•</span> Explainable AI
        </div>
      </div>
    </section>
  );
}