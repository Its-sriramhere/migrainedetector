import { AlertTriangle, BellRing, Check, ThumbsDown, ThumbsUp, X } from "lucide-react";
import { useLive } from "../../context/LiveContext";
import type { Alert } from "../../types";
import "./AlertCard.css";

export function AlertCard({ alert }: { alert: Alert }) {
  const { acknowledgeAlert, alertFeedback } = useLive();
  const level = alert.risk_level;

  return (
    <div className={`alert-card alert-${level}`}>
      <div className="alert-icon">
        {level === "high" ? <BellRing size={18} /> : <AlertTriangle size={18} />}
      </div>

      <div className="alert-body">
        <div className="alert-top">
          <span className={`badge badge-${level}`}>{level.toUpperCase()} RISK</span>
          <span className="alert-time">{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ""}</span>
        </div>
        <p className="alert-message">{alert.message}</p>

        {alert.advice && alert.advice.length > 0 && (
          <div className="alert-advice">
            <span className="alert-advice-title">WHAT TO DO NOW</span>
            <ul>
              {alert.advice.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          </div>
        )}

        {alert.acknowledged ? (
          <div className="alert-feedback-done">
            {alert.feedback ? (
              <span>Acknowledged · Feedback: {alert.feedback.replace("_", " ")}</span>
            ) : (
              <span>Acknowledged</span>
            )}
          </div>
        ) : (
          <div className="alert-actions">
            <button className="btn btn-mini" onClick={() => void acknowledgeAlert(alert.id)}>
              <Check size={13} /> Acknowledge
            </button>
            <button className="btn btn-mini btn-success" onClick={() => void alertFeedback(alert.id, "yes")}>
              <ThumbsUp size={13} /> Yes
            </button>
            <button className="btn btn-mini" onClick={() => void alertFeedback(alert.id, "no")}>
              <ThumbsDown size={13} /> No
            </button>
            <button className="btn btn-mini" onClick={() => void alertFeedback(alert.id, "not_sure")}>
              <X size={13} /> Unsure
            </button>
          </div>
        )}
      </div>
    </div>
  );
}