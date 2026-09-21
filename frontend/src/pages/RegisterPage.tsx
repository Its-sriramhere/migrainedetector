import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { FormEvent } from "react";
import { useAuth } from "../context/AuthContext";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!consent) {
      setError("Please accept the informed-consent statement.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      await register({ name, email, password, consent_given: true });
      navigate("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card glass-card" onSubmit={submit}>
        <span className="eyebrow">JOIN MIGRAINE DETECTOR</span>
        <h1>Create your account</h1>
        <p className="auth-sub">
          A research early-warning system. Take the 14-question profile afterwards.
        </p>

        <label>
          Full name
          <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" />
        </label>
        <label>
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
        </label>

        <label className="consent-box">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          <span>
            I understand this is a research prototype. Predictions are not a medical
            diagnosis and do not replace professional care.
          </span>
        </label>

        {error && <div className="form-error">{error}</div>}

        <button className="btn btn-primary btn-big btn-shine" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>

        <p className="auth-alt">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}