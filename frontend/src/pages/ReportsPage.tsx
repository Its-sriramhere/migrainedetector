import { useEffect, useState } from "react";
import { Database, Download, Printer } from "lucide-react";
import { API_BASE, api } from "../services/api";
import type { ReportOverview } from "../types";
import { Spinner } from "../components/ui/Spinner";

const zero: ReportOverview = {
  total_readings: 0,
  total_predictions: 0,
  total_alerts: 0,
  total_episodes: 0,
  days_monitored: 0,
  risk_band_counts: { low: 0, moderate: 0, high: 0 },
};

export function ReportsPage() {
  const [report, setReport] = useState<ReportOverview>(zero);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<ReportOverview>("/api/reports/overview")
      .then((r) => setReport(r))
      .catch(() => setReport(zero))
      .finally(() => setLoading(false));
  }, []);

  const downloadCsv = async (path: string, filename: string) => {
    const token = localStorage.getItem("mg_token");
    const res = await fetch(`${API_BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloads = [
    { path: "/api/reports/predictions.csv", file: "predictions.csv", label: "Predictions CSV", icon: <Download size={14} /> },
    { path: "/api/reports/episodes.csv", file: "episodes.csv", label: "Episodes CSV", icon: <Download size={14} /> },
    { path: "/api/dataset/export.csv", file: "migraine_dataset.csv", label: "Full dataset", icon: <Database size={14} /> },
  ];

  if (loading) {
    return (
      <div className="page-wrapper page-center">
        <Spinner />
      </div>
    );
  }

  const stats = [
    { label: "Readings", value: report.total_readings },
    { label: "Predictions", value: report.total_predictions },
    { label: "Alerts", value: report.total_alerts },
    { label: "Episodes", value: report.total_episodes },
    { label: "Days monitored", value: report.days_monitored },
  ];

  const bands = report.risk_band_counts ?? {};

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Overview of everything the system has captured for you.</p>
        </div>
        <div className="page-actions">
          {downloads.map((d) => (
            <button key={d.path} className="btn btn-secondary btn-sm" onClick={() => void downloadCsv(d.path, d.file)}>
              {d.icon} {d.label}
            </button>
          ))}
          <button className="btn btn-primary btn-sm" onClick={() => window.print()}>
            <Printer size={14} /> Print / Save as PDF
          </button>
        </div>
      </header>

      <div className="stat-tiles">
        {stats.map((stat) => (
          <div className="stat-tile" key={stat.label}>
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
          </div>
        ))}
      </div>

      <div className="reports-layout">
        <div className="report-card glass-card">
          <span className="eyebrow">RISK BANDS</span>
          <h2 className="section-title-sm">Prediction distribution</h2>
          <div className="band-bars">
            {["low", "moderate", "high"].map((band) => {
              const count = bands[band] ?? 0;
              const total = report.total_predictions || 1;
              const pct = (count / total) * 100;
              return (
                <div className="band-row" key={band}>
                  <span className="band-label">{band.toUpperCase()}</span>
                  <div className="band-track">
                    <div className={`band-fill ${band}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="band-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="report-card glass-card">
          <span className="eyebrow">LATEST</span>
          <h2 className="section-title-sm">Current status</h2>
          <div className="latest-summary">
            <div>
              <span>Latest risk</span>
              <strong>
                {report.latest_risk_score != null ? `${Math.round(report.latest_risk_score)}%` : "—"}
              </strong>
            </div>
            <div>
              <span>Level</span>
              <strong>{(report.latest_risk_level ?? "—").toUpperCase()}</strong>
            </div>
            <div>
              <span>Average risk</span>
              <strong>{report.average_risk != null ? `${report.average_risk}%` : "—"}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}