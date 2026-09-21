import { Cpu, Wifi, WifiOff, Clock, Shield } from "lucide-react";
import { useLive } from "../../context/LiveContext";
import { useReveal } from "../../hooks/useReveal";
import "./RaspberryPiStatus.css";

export function RaspberryPiStatus() {
  const { prediction } = useLive();
  const [ref, visible] = useReveal<HTMLDivElement>();
  const latest = prediction;

  const isOnline = !!latest;
  const statusLabel = isOnline ? "CONNECTED" : "OFFLINE";
  const statusClass = isOnline ? "online" : "offline";

  return (
    <div className={`pi-status-card ${statusClass}`} ref={ref}>
      <div className={`reveal ${visible ? "is-visible" : ""}`}>
        <div className="pi-status-header">
          <div className="pi-status-icon">
            <Cpu size={20} />
          </div>
          <div className="pi-status-info">
            <span className="pi-status-label">RASPBERRY PI</span>
            <span className={`pi-status-badge ${statusClass}`}>
              {isOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
              {statusLabel}
            </span>
          </div>
        </div>

        <div className="pi-status-grid">
          <div className="pi-stat">
            <Clock size={14} />
            <span>Uptime: {isOnline ? "4h 23m" : "—"}</span>
          </div>
          <div className="pi-stat">
            <Shield size={14} />
            <span>Health: {isOnline ? "Normal" : "N/A"}</span>
          </div>
        </div>

        {isOnline && (
          <div className="pi-status-details">
            <div className="pi-detail">
              <span>SD Card</span>
              <div className="pi-detail-bar">
                <div className="pi-detail-fill" style={{ width: "42%" }} />
              </div>
              <span>42%</span>
            </div>
            <div className="pi-detail">
              <span>Temp</span>
              <div className="pi-detail-bar">
                <div className="pi-detail-fill temp" style={{ width: "38%" }} />
              </div>
              <span>48°C</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}