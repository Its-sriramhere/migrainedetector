import { Link } from "react-router-dom";
import { Reveal } from "../ui/Reveal";
import { useAuth } from "../../context/AuthContext";

export function CTA() {
  const { user } = useAuth();
  return (
    <section className="cta-section">
      <div className="container">
        <Reveal>
          <div className="cta-card">
            <span className="eyebrow">Start Today</span>
            <h2>
              Know your body
              <span className="gradient-text">before the migraine.</span>
            </h2>
            <p>
              Create your personal profile, connect your Raspberry Pi and let the
              system learn what normal means for you.
            </p>
            <div className="cta-actions">
              {user ? (
                <Link to="/dashboard" className="btn btn-primary btn-lg btn-shine">
                  Go to Dashboard <span>→</span>
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary btn-lg btn-shine">
                    Start Personalized Monitoring <span>→</span>
                  </Link>
                  <Link to="/how-it-works" className="btn btn-secondary btn-lg">
                    How It Works
                  </Link>
                </>
              )}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}