import { useState } from "react";
import type { FormEvent } from "react";
import { Reveal } from "../components/ui/Reveal";
import { Loader2, Mail, MapPin } from "lucide-react";

const TO_EMAIL = "sriram.efx@gmail.com";

export function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [result, setResult] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (honeypot) return;
    setError("");
    setResult("sending");
    try {
      const res = await fetch(`https://formsubmit.co/ajax/${TO_EMAIL}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          name,
          email,
          message,
          _subject: "Migraine Detector — website contact",
          _captcha: "false",
          _template: "table",
        }),
      });
      if (!res.ok) throw new Error(`FormSubmit returned HTTP ${res.status}`);
      setResult("sent");
    } catch (err) {
      setResult("error");
      setError(err instanceof Error ? err.message : "Could not send your message. Please try again.");
    }
  };

  return (
    <div className="page-wrapper">
      <Reveal>
        <div className="marketing-hero">
          <span className="eyebrow">CONTACT</span>
          <h1>
            Questions, ideas, <span className="gradient-text">collaboration.</span>
          </h1>
          <p className="marketing-hero-sub">
            Migraine Detector is a research prototype. We welcome feedback from patients,
            clinicians and engineers.
          </p>
        </div>
      </Reveal>

      <div className="contact-layout">
        <Reveal className="glass-card contact-card">
          <span className="eyebrow">SEND A MESSAGE</span>
          <h2 className="section-title-sm">Start a conversation</h2>
          {result === "sent" ? (
            <div className="form-success">
              Thanks! Your message is on its way.
              <span>
                If it does not arrive in a few minutes, check the FormSubmit activation email for{" "}
                {TO_EMAIL} and click the confirmation link once.
              </span>
            </div>
          ) : (
            <form onSubmit={submit}>
              <label>
                Name
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                />
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
                Message
                <textarea
                  required
                  rows={5}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Tell us about your idea or question…"
                />
              </label>
              <div className="honeypot" aria-hidden="true">
                <input
                  tabIndex={-1}
                  autoComplete="off"
                  name="_honeypot"
                  value={honeypot}
                  onChange={(e) => setHoneypot(e.target.value)}
                />
              </div>
              {result === "error" && <div className="form-error">{error}</div>}
              <button className="btn btn-primary btn-shine" disabled={result === "sending"}>
                {result === "sending" ? (
                  <>
                    <Loader2 size={16} className="spin" /> Sending…
                  </>
                ) : (
                  "Send message"
                )}
              </button>
            </form>
          )}
        </Reveal>

        <Reveal className="glass-card contact-card">
          <span className="eyebrow">DETAILS</span>
          <h2 className="section-title-sm">Other ways to reach us</h2>
          <div className="contact-item">
            <Mail size={16} />
            <span>{TO_EMAIL}</span>
          </div>
          <div className="contact-item">
            <MapPin size={16} />
            <span>Built as a personal research project — not a registered medical device.</span>
          </div>
          <p className="cell-muted contact-note">
            For medical emergencies or advice, always contact your healthcare provider.
          </p>
        </Reveal>
      </div>
    </div>
  );
}