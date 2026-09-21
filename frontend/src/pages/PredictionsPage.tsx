import { useEffect } from "react";
import { Waves } from "lucide-react";
import { useLive } from "../context/LiveContext";

export function PredictionsPage() {
  const { predictionHistory, refresh } = useLive();

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const rows = [...predictionHistory].sort((a, b) => {
    const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
    const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
    return tb - ta;
  });

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Predictions</h1>
          <p className="page-subtitle">Every risk estimate produced for your account.</p>
        </div>
      </header>

      {rows.length === 0 ? (
        <div className="empty-card">
          <Waves size={22} />
          <span>
            No predictions yet — run the Demo Lab or connect a Raspberry Pi to generate your first
            risk estimates.
          </span>
        </div>
      ) : (
        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Risk</th>
                <th>Score</th>
                <th>Window</th>
                <th>Source</th>
                <th>Model</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td>{p.timestamp ? new Date(p.timestamp).toLocaleString() : "—"}</td>
                  <td>
                    <span className={`badge badge-${p.risk_level}`}>{p.risk_level.toUpperCase()}</span>
                  </td>
                  <td className="cell-strong">{Math.round(p.risk_score)}%</td>
                  <td>{p.prediction_window} min</td>
                  <td>{p.source}</td>
                  <td className="cell-muted">{p.model_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}