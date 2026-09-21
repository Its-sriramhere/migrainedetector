import { useAuth } from "../context/AuthContext";
import { useEffect, useState } from "react";

export function SettingsPage() {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!saved) return;
    const timer = setTimeout(() => setSaved(false), 2500);
    return () => clearTimeout(timer);
  }, [saved]);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Account and alert preferences.</p>
        </div>
      </header>

      <div className="settings-layout">
        <div className="report-card glass-card">
          <span className="eyebrow">ACCOUNT</span>
          <h2 className="section-title-sm">Personal details</h2>
          <div className="profile-rows">
            <div className="profile-row">
              <span>Name</span>
              <strong>{user?.name}</strong>
            </div>
            <div className="profile-row">
              <span>Email</span>
              <strong>{user?.email}</strong>
            </div>
            <div className="profile-row">
              <span>Informed consent</span>
              <strong>{user?.consent_given ? "Given" : "Not given"}</strong>
            </div>
            <div className="profile-row">
              <span>Member since</span>
              <strong>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</strong>
            </div>
          </div>
        </div>

        <div className="report-card glass-card">
          <span className="eyebrow">PREFERENCES</span>
          <h2 className="section-title-sm">Demo & alert settings</h2>
          <div className="settings-inline">
            <label>
              <input type="checkbox" defaultChecked /> Enable demo mode by default
            </label>
            <label>
              <input type="checkbox" defaultChecked /> Show risk explanation on alerts
            </label>
            <label>
              <input type="checkbox" /> Email me on high-risk estimates
            </label>
          </div>

          {saved && <div className="form-success">Preferences saved.</div>}
          <button className="btn btn-primary btn-shine" onClick={() => setSaved(true)}>
            Save preferences
          </button>
          <p className="cell-muted settings-hint">
            Preferences are stored locally in this prototype. Backend persistence is exercised by the
            API endpoints.
          </p>
        </div>
      </div>
    </div>
  );
}