import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import type { MigraineEpisode } from "../types";

const SYMPTOMS = [
  "throbbing",
  "light_sensitivity",
  "sound_sensitivity",
  "nausea",
  "aura",
  "dizziness",
  "neck_pain",
  "visual_disturbance",
];

export function HistoryPage() {
  const [episodes, setEpisodes] = useState<MigraineEpisode[]>([]);
  const [startTime, setStartTime] = useState("");
  const [severity, setSeverity] = useState("mild");
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [trigger, setTrigger] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void load();
  }, []);

  const load = async () => {
    try {
      setEpisodes(await api.get<MigraineEpisode[]>("/api/migraine/history"));
    } catch {
      /* ignore */
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = {
        start_time: startTime ? new Date(startTime).toISOString() : new Date().toISOString(),
        severity,
        symptoms: selectedSymptoms,
        trigger: trigger || undefined,
        notes: notes || undefined,
      };
      await api.post("/api/migraine", body);
      setTrigger("");
      setNotes("");
      setSelectedSymptoms([]);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save episode");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Migraine History</h1>
          <p className="page-subtitle">Log episodes to build richer ground truth for the model.</p>
        </div>
      </header>

      <div className="history-layout">
        <form className="glass-card log-card" onSubmit={submit}>
          <span className="eyebrow">NEW EPISODE</span>
          <h2 className="section-title-sm">Log today's episode</h2>

          <label>
            Start time
            <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          </label>

          <span className="field-label">Severity</span>
          <div className="segmented">
            {["mild", "moderate", "severe"].map((s) => (
              <button
                type="button"
                key={s}
                className={`segment ${severity === s ? "active" : ""}`}
                onClick={() => setSeverity(s)}
              >
                {s.toUpperCase()}
              </button>
            ))}
          </div>

          <span className="field-label">Symptoms</span>
          <div className="chip-group">
            {SYMPTOMS.map((symptom) => (
              <button
                type="button"
                key={symptom}
                className={`chip ${selectedSymptoms.includes(symptom) ? "active" : ""}`}
                onClick={() =>
                  setSelectedSymptoms((prev) =>
                    prev.includes(symptom) ? prev.filter((x) => x !== symptom) : [...prev, symptom],
                  )
                }
              >
                {symptom.replace(/_/g, " ")}
              </button>
            ))}
          </div>

          <label>
            Trigger
            <input
              value={trigger}
              onChange={(e) => setTrigger(e.target.value)}
              placeholder="e.g. missed sleep, bright screens"
            />
          </label>
          <label>
            Notes
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
          </label>

          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary btn-big btn-shine" disabled={busy}>
            {busy ? "Saving…" : "Log episode"}
          </button>
        </form>

        <div className="history-list">
          {episodes.length === 0 ? (
            <div className="empty-card">
              <span>No episodes logged yet.</span>
            </div>
          ) : (
            episodes.map((episode) => (
              <div className="episode-card" key={episode.id}>
                <div className="episode-top">
                  <span className={`badge badge-${episode.severity ?? "mild"}`}>
                    {(episode.severity ?? "mild").toUpperCase()}
                  </span>
                  <time>{new Date(episode.start_time).toLocaleString()}</time>
                </div>
                <p className="episode-symptoms">
                  {episode.symptoms?.length ? episode.symptoms.join(", ") : "No symptoms recorded"}
                </p>
                {episode.trigger && <p className="episode-trigger">Trigger: {episode.trigger}</p>}
                {episode.notes && <p className="episode-notes">{episode.notes}</p>}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}