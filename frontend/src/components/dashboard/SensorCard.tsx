import { HeartPulse, Activity, Thermometer, Wind, Gauge, Cpu } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import "./SensorCard.css";

interface SensorCardProps {
  type: string;
  value: string;
  timestamp?: string;
  icon?: LucideIcon;
}

const iconMap: Record<string, LucideIcon> = {
  heart_rate: HeartPulse,
  hrv: Activity,
  blood_pressure: Gauge,
  spo2: Wind,
  temperature: Thermometer,
  pi_status: Cpu,
};

const labelMap: Record<string, string> = {
  heart_rate: "HEART RATE",
  hrv: "HEART RATE VARIABILITY",
  blood_pressure: "BLOOD PRESSURE",
  spo2: "SPO₂",
  temperature: "TEMPERATURE",
  pi_status: "RASPBERRY PI",
};

export function SensorCard({ type, value, timestamp }: SensorCardProps) {
  const Icon = iconMap[type] || Activity;
  const label = labelMap[type] || type.toUpperCase();

  return (
    <div className="sensor-card">
      <div className="sensor-card-icon">
        <Icon size={18} />
      </div>
      <div className="sensor-card-data">
        <span className="sensor-card-label">{label}</span>
        <strong className="sensor-card-value">{value}</strong>
        {timestamp && <time className="sensor-card-time">{timestamp}</time>}
      </div>
    </div>
  );
}