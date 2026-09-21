import { useRef, useState } from "react";
import type { CSSProperties } from "react";
import { Activity, Loader2, Play, Send, Square } from "lucide-react";
import { useLive } from "../../context/LiveContext";
import { useReveal } from "../../hooks/useReveal";
import type { ScenarioName } from "../../types";
import "./DemoControls.css";

type SensorValues = {
  heart_rate: number;
  hrv: number;
  systolic_bp: number;
  diastolic_bp: number;
  spo2: number;
  temperature: number;
  activity: number;
};

const presets: { id: ScenarioName; label: string; note: string; values: SensorValues }[] = [
  { id: "normal", label: "NORMAL", note: "Healthy signals", values: { heart_rate: 70, hrv: 50, systolic_bp: 118, diastolic_bp: 76, spo2: 98, temperature: 36.5, activity: 0.55 } },
  { id: "moderate", label: "MODERATE", note: "Rising risk", values: { heart_rate: 82, hrv: 38, systolic_bp: 126, diastolic_bp: 82, spo2: 98, temperature: 36.7, activity: 0.3 } },
  { id: "high", label: "HIGH RISK", note: "Elevated pattern", values: { heart_rate: 92, hrv: 26, systolic_bp: 138, diastolic_bp: 88, spo2: 97, temperature: 36.9, activity: 0.15 } },
];

interface SliderSpec {
  key: keyof SensorValues;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  format: (v: number) => string;
}

const sliders: SliderSpec[] = [
  { key: "heart_rate", label: "Heart rate", unit: "BPM", min: 50, max: 140, step: 1, format: (v) => `${v}` },
  { key: "hrv", label: "Heart rate variability", unit: "ms", min: 10, max: 80, step: 1, format: (v) => `${v}` },
  { key: "systolic_bp", label: "Systolic BP", unit: "mmHg", min: 90, max: 165, step: 1, format: (v) => `${v}` },
  { key: "diastolic_bp", label: "Diastolic BP", unit: "mmHg", min: 55, max: 110, step: 1, format: (v) => `${v}` },
  { key: "spo2", label: "Oxygen saturation", unit: "%", min: 90, max: 100, step: 1, format: (v) => `${v}` },
  { key: "temperature", label: "Temperature", unit: "°C", min: 35.5, max: 38.5, step: 0.1, format: (v) => `${v.toFixed(1)}` },
  { key: "activity", label: "Activity", unit: "%", min: 0, max: 1, step: 0.05, format: (v) => `${Math.round(v * 100)}` },
];

export function DemoControls() {
  const { sendScenario, sendSensor, startDemo, stopDemo, demoRunning, demoScenario } = useLive();
  const [ref, visible] = useReveal<HTMLDivElement>();
  const [values, setValues] = useState<SensorValues>(presets[0].values);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const commit = (next: SensorValues) => {
    void sendSensor({ ...next, source: "demo", signal_quality: 90 });
  };

  const update = (key: keyof SensorValues, value: number) => {
    setValues((prev) => {
      const next = { ...prev, [key]: value };
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => commit(next), 500);
      return next;
    });
  };

  const selectPreset = (preset: (typeof presets)[number]) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setValues(preset.values);
    void sendScenario(preset.id);
  };

  const [starting, setStarting] = useState(false);

  const start = async () => {
    setStarting(true);
    try {
      await startDemo("moderate", { ...values });
    } finally {
      setStarting(false);
    }
  };

  const fillStyle = (spec: SliderSpec): CSSProperties => {
    const pct = ((values[spec.key] - spec.min) / (spec.max - spec.min)) * 100;
    return { "--fill": `${Math.min(100, Math.max(0, pct))}%` } as CSSProperties;
  };

  return (
    <div className="demo-controls" ref={ref}>
      <div className={`reveal ${visible ? "is-visible" : ""}`}>
        <div className="demo-controls-header">
          <span className="demo-controls-title">
            <Activity size={14} /> DEMO LAB — PIPELINE PRESETS
          </span>
          {demoRunning && (
            <span className="badge badge-ai">● STREAMING {demoScenario?.toUpperCase()}</span>
          )}
        </div>

        <div className="demo-presets">
          {presets.map((preset) => (
            <button
              key={preset.id}
              className={`preset-btn preset-${preset.id} ${
                !demoRunning && demoScenario === preset.id ? "active" : ""
              }`}
              onClick={() => selectPreset(preset)}
            >
              <strong>{preset.label}</strong>
              <span>{preset.note}</span>
            </button>
          ))}
        </div>

        <div className="demo-stream-row">
          <div className="demo-stream-controls">
            {!demoRunning ? (
              <button className="btn btn-primary" disabled={starting} onClick={() => void start()}>
                {starting ? <Loader2 size={15} className="spin" /> : <Play size={15} />}
                {starting ? "Starting Stream…" : "Start Simulated Stream"}
              </button>
            ) : (
              <button className="btn btn-secondary" onClick={() => void stopDemo()}>
                <Square size={15} /> Stop Stream
              </button>
            )}
          </div>
        </div>

        <div className="demo-sliders">
          <div className="demo-sliders-head">
            <span className="eyebrow">MANUAL SIGNALS</span>
            <button className="btn btn-secondary btn-sm" onClick={() => commit(values)}>
              <Send size={13} /> Send reading
            </button>
          </div>
          {sliders.map((spec) => (
            <label className="demo-slider" key={spec.key}>
              <span className="demo-slider-label">
                {spec.label}
                <strong>
                  {spec.format(values[spec.key])} {spec.unit}
                </strong>
              </span>
              <input
                type="range"
                style={fillStyle(spec)}
                min={spec.min}
                max={spec.max}
                step={spec.step}
                value={values[spec.key]}
                onChange={(e) => update(spec.key, Number(e.target.value))}
              />
            </label>
          ))}
        </div>

        <p className="demo-controls-note">
          Presets push one sample through the same pipeline used by the Raspberry Pi:
          preprocessing → features → model → SHAP → risk → alert. Sliders let you live-tune
          any sensor; each reading is stored like a Pi reading and appears in the dataset export.
        </p>
      </div>
    </div>
  );
}