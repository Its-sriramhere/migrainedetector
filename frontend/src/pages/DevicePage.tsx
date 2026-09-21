import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Cable, Cpu, Plus, Wifi } from "lucide-react";
import { api } from "../services/api";
import type { Device } from "../types";
import { RaspberryPiStatus } from "../components/dashboard/RaspberryPiStatus";

function timeAgo(iso?: string): string {
  if (!iso) return "never";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

const GUIDE = [
  {
    title: "1. Flash the image",
    body: "Write Raspberry Pi OS (64-bit) to an SD card and connect your sensors to the GPIO pins (MAX30102, BMP180, MPU6050).",
  },
  {
    title: "2. Install the app",
    body: "Clone this repo, copy the raspberry-pi folder to the Pi, and install dependencies with pip install -r raspberry-pi/requirements.txt.",
  },
  {
    title: "3. Configure credentials",
    body: "Set BACKEND_URL, DEVICE_ID (matching this page) and AUTH_TOKEN (donated to the Pi) as environment variables in the app's systemd unit or .env.",
  },
  {
    title: "4. Run + verify",
    body: "Launch with python main.py. It registers once, uploads readings every 10s, and sends a heartbeat every 60s — this page flips to ONLINE when a heartbeat arrives.",
  },
];

export function DevicePage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [identifier, setIdentifier] = useState("");
  const [name, setName] = useState("Raspberry Pi");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void load();
    const interval = setInterval(() => void load(), 8000);
    return () => clearInterval(interval);
  }, []);

  const load = async () => {
    try {
      const list = await api.get<Device[]>("/api/devices");
      setDevices(list);
    } catch {
      /* ignore */
    }
  };

  const register = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/devices/register", { device_identifier: identifier, device_name: name });
      identifier && setIdentifier("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register device");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Device</h1>
          <p className="page-subtitle">
            Simulate the Raspberry Pi onboarding: register a device identity like your Pi would.
          </p>
        </div>
      </header>

      <div className="device-layout">
        <div className="device-main">
          <RaspberryPiStatus />

          <div className="report-card glass-card">
            <span className="eyebrow">REGISTER A DEVICE</span>
            <h2 className="section-title-sm">Pair your Raspberry Pi</h2>
            <form onSubmit={register}>
              <label>
                Device identifier
                <input
                  required
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="mg-pi-001"
                />
              </label>
              <label>
                Display name
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              {error && <div className="form-error">{error}</div>}
              <button className="btn btn-primary btn-shine" disabled={busy}>
                <Plus size={15} /> {busy ? "Registering…" : "Register device"}
              </button>
            </form>
          </div>

          <div className="device-code">
            <span className="eyebrow">HOW IT CONNECTS</span>
            <h2 className="section-title-sm">Raspberry Pi connection guide</h2>
            <ol className="guide-list">
              {GUIDE.map((step) => (
                <li key={step.title}>
                  <strong>{step.title}</strong>
                  <span>{step.body}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="device-code">
            <span className="eyebrow">HEARTBEAT</span>
            <h2 className="section-title-sm">The Pi announces itself like this</h2>
            <pre className="code-block">{`POST /api/devices/heartbeat
Authorization: Bearer <device-token>

{ "device_identifier": "mg-pi-001", "device_name": "Raspberry Pi" }

→ 200 { "status": "online", "last_seen": "2026-09-12T10:00:00Z" }`}</pre>
          </div>
        </div>

        <aside className="device-side">
          <h2 className="section-title-sm">Known devices</h2>
          {devices.length === 0 ? (
            <div className="empty-card">
              <Cpu size={18} />
              <span>No devices registered yet.</span>
            </div>
          ) : (
            devices.map((device) => (
              <div className="device-row" key={device.id}>
                <Cpu size={16} />
                <div>
                  <strong>{device.device_name}</strong>
                  <span>
                    {device.device_identifier} · last seen {timeAgo(device.last_seen)}
                  </span>
                </div>
                <span className={`badge badge-${device.status === "online" ? "success" : "muted"}`}>
                  {device.status === "online" ? <Wifi size={12} /> : <Cable size={12} />}{" "}
                  {device.status.toUpperCase()}
                </span>
              </div>
            ))
          )}
        </aside>
      </div>
    </div>
  );
}