import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useLive } from "../../context/LiveContext";
import "./SensorChart.css";

export function SensorChart() {
  const { sensorHistory } = useLive();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const data = sensorHistory.map((reading, index) => ({
    time: `T-${sensorHistory.length - index}`,
    hr: reading?.heart_rate ?? null,
    hrv: reading?.hrv ?? null,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <span className="chart-title">Sensor History</span>
        <span className="chart-legend">
          <span className="legend-dot hr" /> HR
          <span className="legend-dot hrv" /> HRV
        </span>
      </div>
      <div className="chart-container">
        {mounted ? (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="hrGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="hrvGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--ai)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--ai)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={35}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="hr"
                stroke="var(--primary)"
                fill="url(#hrGrad)"
                strokeWidth={2}
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="hrv"
                stroke="var(--ai)"
                fill="url(#hrvGrad)"
                strokeWidth={2}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="chart-placeholder">Loading chart...</div>
        )}
      </div>
    </div>
  );
}