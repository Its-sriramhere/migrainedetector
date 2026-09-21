import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import type { RiskProfile, BaselineEstimates } from "../types";
import { Spinner } from "../components/ui/Spinner";

export function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<RiskProfile | null>(null);
  const [baseline, setBaseline] = useState<BaselineEstimates | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [prof, base] = await Promise.allSettled([
          api.get<RiskProfile>("/api/assessment/profile").catch(() => null),
          api.get<BaselineEstimates>("/api/assessment/baseline").catch(() => null),
        ]);
        if (prof.status === "fulfilled") setProfile(prof.value);
        if (base.status === "fulfilled") setBaseline(base.value);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  if (loading) {
    return (
      <div className="page-wrapper page-center">
        <Spinner />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="page-stack">
        <header className="page-header">
          <div>
            <h1 className="page-title">Profile</h1>
            <p className="page-subtitle">Your personalization profile.</p>
          </div>
        </header>
        <div className="empty-card">
          <span>You have not created a profile yet.</span>
          <Link to="/onboarding" className="btn btn-primary btn-sm btn-shine">
            Take the 14-question assessment
          </Link>
        </div>
      </div>
    );
  }

  const rows: { label: string; value: string | number | undefined }[] = [
    { label: "Migraine history score", value: profile.migraine_history_score },
    { label: "Sleep profile", value: profile.sleep_profile },
    { label: "Stress profile", value: profile.stress_profile },
    { label: "Activity profile", value: profile.activity_profile },
    { label: "Hydration profile", value: profile.hydration_profile },
    { label: "Caffeine profile", value: profile.caffeine_profile },
    { label: "Resting HR", value: profile.resting_hr },
  ];

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Profile</h1>
          <p className="page-subtitle">
            Signed in as <strong>{user?.email}</strong> · profile version {profile.profile_version}
          </p>
        </div>
      </header>

      <div className="profile-layout">
        <div className="report-card glass-card">
          <span className="eyebrow">PERSONAL FACTORS</span>
          <h2 className="section-title-sm">Your risk profile</h2>
          <div className="profile-rows">
            {rows.map((row) => (
              <div className="profile-row" key={row.label}>
                <span>{row.label}</span>
                <strong>{row.value ?? "—"}</strong>
              </div>
            ))}
          </div>

          <div className="profile-triggers">
            <span className="field-label">Triggers</span>
            <div className="chip-group">
              {profile.trigger_profile.length === 0 ? (
                <span className="cell-muted">None recorded</span>
              ) : (
                profile.trigger_profile.map((trigger) => (
                  <span className="chip active" key={trigger}>
                    {trigger.replace(/_/g, " ")}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="report-card glass-card">
          <span className="eyebrow">LEARNED BASELINE</span>
          <h2 className="section-title-sm">What is normal for you</h2>
          <div className="profile-rows">
            <div className="profile-row">
              <span>Heart rate band</span>
              <strong>
                {baseline ? `${baseline.heart_rate_low}–${baseline.heart_rate_high} BPM` : "—"}
              </strong>
            </div>
            <div className="profile-row">
              <span>Typical sleep</span>
              <strong>{baseline?.sleep_hours != null ? `${baseline.sleep_hours} h` : "—"}</strong>
            </div>
            <div className="profile-row">
              <span>Source</span>
              <strong>{baseline?.resting_note ?? "—"}</strong>
            </div>
          </div>
          <p className="cell-muted profile-note">
            The heuristic engine compares incoming signals against this baseline to estimate
            personal deviation.
          </p>
        </div>
      </div>
    </div>
  );
}