import { useCallback, useEffect, useState } from "react";
import { MessageSquareWarning, PhoneCall, PhoneOff, Clock3, ShieldOff, CheckCircle2 } from "lucide-react";
import { useLive } from "../context/LiveContext";
import { AlertCard } from "../components/dashboard/AlertCard";
import { Spinner } from "../components/ui/Spinner";
import { api } from "../services/api";

interface NotificationEntry {
  id: number;
  risk_level: string | null;
  provider: string;
  status: string;
  detail: string | null;
  recipient: string | null;
  created_at: string | null;
}

interface NotificationsInfo {
  sms_enabled: boolean;
  sms_provider: string;
  sms_max_sends: number;
  logs: NotificationEntry[];
}

const STATUS_META: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
  sent: { label: "SENT", icon: <CheckCircle2 size={12} />, cls: "success" },
  skipped: { label: "SKIPPED", icon: <ShieldOff size={12} />, cls: "muted" },
  failed: { label: "FAILED", icon: <PhoneOff size={12} />, cls: "danger" },
  quota_exceeded: { label: "QUOTA", icon: <Clock3 size={12} />, cls: "warning" },
};

function statusMeta(status: string) {
  return STATUS_META[status] ?? { label: status.toUpperCase(), icon: <Clock3 size={12} />, cls: "muted" };
}

export function AlertsPage() {
  const { alerts, refreshAlerts } = useLive();
  const [notifications, setNotifications] = useState<NotificationsInfo | null>(null);

  const loadNotifications = useCallback(async () => {
    try {
      setNotifications(await api.get<NotificationsInfo>("/api/alerts/notifications?limit=20"));
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void refreshAlerts();
    void loadNotifications();
  }, [refreshAlerts, loadNotifications]);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Alerts</h1>
          <p className="page-subtitle">High and moderate risk estimates with optional feedback.</p>
        </div>
      </header>

      {alerts.length === 0 ? (
        <div className="empty-card">
          <Spinner />
          <span>No alerts yet. They are created when risk crosses a threshold.</span>
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      )}

      <div className="report-card glass-card">
        <div className="notification-head">
          <span className="eyebrow">SMS DELIVERY</span>
          <span className={`badge badge-${notifications?.sms_enabled ? "success" : "muted"}`}>
            <PhoneCall size={12} /> {notifications?.sms_enabled ? "SMS ENABLED" : "SMS OFF"}
          </span>
          {notifications && (
            <span className="badge badge-muted">
              <MessageSquareWarning size={12} /> {notifications.sms_provider.toUpperCase()} · CAP{" "}
              {notifications.sms_max_sends}
            </span>
          )}
        </div>
        <h2 className="section-title-sm">Notification log</h2>
        <p className="page-subtitle">Who was texted, when, and whether delivery succeeded.</p>

        {!notifications ? (
          <div className="empty-card">
            <Spinner />
            <span>Loading notification log…</span>
          </div>
        ) : notifications.logs.length === 0 ? (
          <div className="empty-card">
            <MessageSquareWarning size={18} />
            <span>No SMS notifications recorded yet.</span>
          </div>
        ) : (
          <div className="sms-log">
            {notifications.logs.map((entry) => {
              const meta = statusMeta(entry.status);
              return (
                <div className="sms-log-row" key={entry.id}>
                  <div className="sms-log-main">
                    <span className={`badge badge-${meta.cls}`}>
                      {meta.icon} {meta.label}
                    </span>
                    <span className="sms-log-level">
                      {entry.risk_level ? entry.risk_level.toUpperCase() : "—"} RISK
                    </span>
                    <span className="sms-log-recipient">{entry.recipient ?? "no recipient"}</span>
                  </div>
                  <span className="sms-log-time">
                    {entry.created_at ? new Date(entry.created_at).toLocaleString() : ""}
                  </span>
                  {entry.detail && <span className="sms-log-detail">{entry.detail}</span>}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}