import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, CloudUpload, Database, Download, FileJson, FileSpreadsheet, Hammer, RefreshCw, Table } from "lucide-react";
import { API_BASE, api } from "../services/api";

interface DatasetFile {
  name: string;
  size_bytes: number;
  rows: number;
  columns: string[];
  modified: number;
  stored?: boolean;
  storage_bucket?: string;
  storage_key?: string;
}

interface Thresholds {
  calibrated?: boolean;
  source_data?: string;
  band_edges?: { low?: number; high?: number };
  baselines?: Record<string, number | null>;
  deviations?: Record<string, number>;
  demo_presets?: Record<string, { heart_rate: number; systolic_bp: number; diastolic_bp: number; spo2: number; temperature: number }>;
}

interface StorageInfo {
  database?: { url?: string; label?: string; note?: string };
  datasets_dir?: string;
  thresholds_path?: string;
  sms?: {
    provider?: string;
    enabled?: boolean;
    recipient?: string;
    level?: string;
    max_sends?: number;
    sends_used?: number;
  };
  supabase?: {
    enabled?: boolean;
    url?: string;
    project_ref?: string;
    bucket?: string;
    stored_count?: number;
  };
}

interface DatasetsOverview {
  datasets_dir: string;
  files: DatasetFile[];
  thresholds: Thresholds;
  storage?: StorageInfo;
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}

function formatRows(rows: number): string {
  if (rows < 0) return "—";
  return rows.toLocaleString();
}

const SIGNAL_LABELS: Record<string, string> = {
  heart_rate: "Heart rate",
  systolic_bp: "Systolic BP",
  diastolic_bp: "Diastolic BP",
  spo2: "SpO2",
  temperature: "Temperature",
  hrv: "HRV",
  activity: "Activity",
};

const DEVIATION_LABELS: Record<string, string> = {
  hr_trigger_pct: "HR trigger (% rise)",
  hr_weight: "HR weight",
  hrv_trigger_pct: "HRV trigger (% drop)",
  hrv_weight: "HRV weight",
  bp_trigger_pct: "BP trigger (% move)",
  bp_weight: "BP weight",
  spo2_drop: "SpO2 drop threshold",
  spo2_contribution: "SpO2 contribution",
  temp_dev: "Temp deviation",
  temp_weight: "Temp weight",
  static_floor: "Baseline floor",
};

export function DatasetsPage() {
  const [data, setData] = useState<DatasetsOverview | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [logTail, setLogTail] = useState("");
  const [downloading, setDownloading] = useState("");

  const load = useCallback(async () => {
    try {
      setData(await api.get<DatasetsOverview>("/api/datasets"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load datasets");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const run = async (action: () => Promise<{ log_tail?: string }>) => {
    setBusy("busy");
    setError("");
    setLogTail("");
    try {
      const resp = await action();
      if (resp.log_tail) setLogTail(resp.log_tail);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Operation failed");
    } finally {
      setBusy("");
    }
  };

  const download = async (name: string) => {
    setDownloading(name);
    try {
      const token = localStorage.getItem("mg_token");
      const url = `${API_BASE}/api/datasets/download/${encodeURIComponent(name)}`;
      const resp = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!resp.ok) throw new Error(`Download failed (${resp.status})`);
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading("");
    }
  };

  const thresholds = data?.thresholds;
  const storage = data?.storage;
  const sms = storage?.sms;
  const supabase = storage?.supabase;
  const baselines = useMemo(() => {
    if (!thresholds?.baselines) return [];
    return Object.entries(thresholds.baselines).filter(([, v]) => v != null) as [string, number][];
  }, [thresholds]);
  const deviations = useMemo(() => {
    if (!thresholds?.deviations) return [];
    return Object.entries(thresholds.deviations)
      .filter(([k]) => DEVIATION_LABELS[k])
      .map(([k, v]) => [k, v] as [string, number]);
  }, [thresholds]);

  return (
    <div className="page-stack">
      <header className="page-header page-header-actions">
        <div>
          <h1 className="page-title">Datasets &amp; Thresholds</h1>
          <p className="page-subtitle">
            The bundled migraine datasets drive the calibrated deviation thresholds used by both
            the simulation and live monitoring.
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" disabled={busy !== ""} onClick={() => void run(() => api.post("/api/datasets/build"))}>
            <Hammer size={15} /> Rebuild calibration set
          </button>
          <button className="btn btn-primary btn-shine" disabled={busy !== ""} onClick={() => void run(() => api.post("/api/datasets/calibrate"))}>
            <RefreshCw size={15} /> Recalibrate thresholds
          </button>
        </div>
      </header>

      {error && <div className="form-error">{error}</div>}
      {busy && <div className="empty-card"><span>Running pipeline…</span></div>}

      <div className="metric-grid">
        <div className="metric-card">
          <Table size={16} />
          <span>Dataset files</span>
          <strong>{data?.files.length ?? "—"}</strong>
        </div>
        <div className="metric-card">
          <Database size={16} />
          <span>Calibration rows</span>
          <strong>{data?.files.find((f) => f.name === "calibration.csv")?.rows?.toLocaleString() ?? "—"}</strong>
        </div>
        <div className="metric-card">
          <Activity size={16} />
          <span>Calibration status</span>
          <strong>{thresholds?.calibrated ? "CALIBRATED" : "DEFAULTS"}</strong>
        </div>
        <div className="metric-card">
          <FileJson size={16} />
          <span>Origin</span>
          <strong className="metric-tall">{thresholds?.source_data ?? "Built-in heuristics"}</strong>
        </div>
      </div>

      <div className="device-layout">
        <div className="device-main">
          <div className="report-card glass-card">
            <span className="eyebrow">SIGNAL BASELINES</span>
            <h2 className="section-title-sm">
              Baselines from the dataset <em className="section-note">(fallback user baseline)</em>
            </h2>
            <div className="kv-grid">
              {baselines.map(([key, value]) => (
                <div className="kv-row" key={key}>
                  <span>{SIGNAL_LABELS[key] ?? key}</span>
                  <strong>{key === "temperature" ? value.toFixed(1) : Math.round(value).toLocaleString()}</strong>
                </div>
              ))}
              {baselines.length === 0 && <span className="muted">No calibrated baselines — using built-in defaults.</span>}
            </div>
          </div>

          <div className="report-card glass-card">
            <span className="eyebrow">DEVIATION THRESHOLDS</span>
            <h2 className="section-title-sm">Alert cutoffs and weights</h2>
            <div className="kv-grid">
              {deviations.map(([key, value]) => (
                <div className="kv-row" key={key}>
                  <span>{DEVIATION_LABELS[key]}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            {thresholds?.band_edges && (
              <div className="band-note">
                Risk bands &mdash; low &lt; <strong>{thresholds.band_edges.low}</strong> ·
                moderate &lt;= <strong>{thresholds.band_edges.high}</strong> · high above that
              </div>
            )}
          </div>

          <div className="report-card glass-card">
            <span className="eyebrow">DEMO SIMULATION PRESETS</span>
            <h2 className="section-title-sm">Scenario signal vectors used by Demo &amp; Simulation</h2>
            <div className="demo-preset-row">
              {Object.entries(thresholds?.demo_presets ?? {}).map(([scenario, vec]) => (
                <div className={`demo-preset preset-${scenario}`} key={scenario}>
                  <strong className="preset-label">{scenario.toUpperCase()}</strong>
                  <div className="preset-values">
                    <span>HR <b>{vec.heart_rate}</b></span>
                    <span>BP <b>{vec.systolic_bp}/{vec.diastolic_bp}</b></span>
                    <span>SpO2 <b>{vec.spo2}%</b></span>
                    <span>Temp <b>{vec.temperature}°C</b></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {logTail && (
            <div className="device-code">
              <span className="eyebrow">PIPELINE OUTPUT</span>
              <pre className="code-block">{logTail}</pre>
            </div>
          )}
        </div>

        <aside className="device-side">
          <h2 className="section-title-sm">Where your data is stored</h2>
          <div className="report-card glass-card">
            <span className="eyebrow">STORAGE LOCATIONS</span>
            <div className="kv-grid">
              <div className="kv-row">
                <span>Database</span>
                <strong className="storage-path">{storage?.database?.label ?? "App database"}</strong>
              </div>
              <div className="kv-row">
                <span>Database file</span>
                <strong className="storage-path">{storage?.database?.url ?? "—"}</strong>
              </div>
              <div className="kv-row">
                <span>Dataset folder</span>
                <strong className="storage-path">{storage?.datasets_dir ?? data?.datasets_dir ?? "—"}</strong>
              </div>
              <div className="kv-row">
                <span>Thresholds file</span>
                <strong className="storage-path">{storage?.thresholds_path ?? "—"}</strong>
              </div>
            </div>
            <p className="demo-controls-note">
              Users, sensor readings, predictions, alerts and notification logs live in the
              database above; the calibration CSV and thresholds JSON are plain files on disk.
            </p>
          </div>

          {sms && (
            <div className="report-card glass-card">
              <span className="eyebrow">SMS DELIVERY</span>
              <div className="kv-grid">
                <div className="kv-row">
                  <span>Provider</span>
                  <strong>{sms.provider}</strong>
                </div>
                <div className="kv-row">
                  <span>Enabled</span>
                  <strong>{sms.enabled ? "YES" : "NO (mock)"}</strong>
                </div>
                <div className="kv-row">
                  <span>Recipient</span>
                  <strong>{sms.recipient}</strong>
                </div>
                <div className="kv-row">
                  <span>Alert level</span>
                  <strong className="uppercase">{sms.level}</strong>
                </div>
                <div className="kv-row">
                  <span>Real sends used</span>
                  <strong>
                    {sms.sends_used ?? 0} / {sms.max_sends ?? "∞"}
                  </strong>
                </div>
              </div>
            </div>
          )}

          {supabase && (
            <div className="report-card glass-card">
              <span className="eyebrow">SUPABASE</span>
              <div className="kv-grid">
                <div className="kv-row">
                  <span>Configured</span>
                  <strong>{supabase.enabled ? "YES" : "NO"}</strong>
                </div>
                <div className="kv-row">
                  <span>Project</span>
                  <strong className="storage-path">{supabase.project_ref || "—"}</strong>
                </div>
                <div className="kv-row">
                  <span>Storage bucket</span>
                  <strong className="storage-path">{supabase.bucket || "—"}</strong>
                </div>
                <div className="kv-row">
                  <span>Files stored</span>
                  <strong>{supabase.stored_count ?? 0}</strong>
                </div>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                disabled={busy !== ""}
                onClick={() => void run(() => api.post("/api/datasets/supabase-sync"))}
              >
                <CloudUpload size={14} /> Sync datasets to Supabase
              </button>
            </div>
          )}

          <h2 className="section-title-sm">Dataset files</h2>
          {!data || data.files.length === 0 ? (
            <div className="empty-card">
              <Database size={18} />
              <span>No dataset files found.</span>
            </div>
          ) : (
            data.files.map((file) => (
              <div className="device-row" key={file.name}>
                <FileSpreadsheet size={16} />
                <div>
                  <strong>
                    {file.name}
                    {file.stored && <span className="badge badge-success">SUPABASE</span>}
                  </strong>
                  <span>
                    {formatRows(file.rows)} rows · {formatSize(file.size_bytes)}
                    {file.storage_key ? ` · ${file.storage_key}` : ""}
                  </span>
                </div>
                <button
                  className="icon-btn"
                  aria-label={`Download ${file.name}`}
                  title="Download CSV"
                  disabled={downloading === file.name}
                  onClick={() => void download(file.name)}
                >
                  <Download size={16} />
                </button>
              </div>
            ))
          )}
          <div className="device-code">
            <span className="eyebrow">LABEL MAPPING</span>
            <pre className="code-block">{`heart_rate -> hr_abnormal (proxy)
systolic_bp -> episode
diastolic_bp -> episode
spo2        -> episode
temperature -> episode`}</pre>
          </div>
        </aside>
      </div>
    </div>
  );
}