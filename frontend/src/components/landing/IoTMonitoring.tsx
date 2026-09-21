import { Activity, Cpu, Gauge, HeartPulse, Thermometer, Wind } from "lucide-react";
import { Reveal } from "../ui/Reveal";

const sensors = [
  { icon: <HeartPulse size={18} />, name: "Heart Rate & HRV", chip: "MAX30102" },
  { icon: <Gauge size={18} />, name: "Blood Pressure", chip: "BP Module" },
  { icon: <Activity size={18} />, name: "Activity / IMU", chip: "MPU6050" },
  { icon: <Thermometer size={18} />, name: "Temperature", chip: "MAX30205" },
  { icon: <Wind size={18} />, name: "SpO₂", chip: "MAX30102" },
];

export function IoTMonitoring() {
  return (
    <section className="section iot-section">
      <div className="container">
        <div className="iot-wrap">
          <Reveal>
            <div className="iot-copy">
              <span className="eyebrow">04 — Raspberry Pi Monitoring</span>
              <h2 className="section-title">
                Continuous signals from an <span className="gradient-text">edge device.</span>
              </h2>
              <p className="section-subtitle">
                A Raspberry Pi reads physiological sensors, validates and filters the
                signal, buffers data locally, and securely uploads it to the backend.
              </p>

              <div className="sensor-tags">
                {sensors.map((sensor) => (
                  <span className="sensor-tag" key={sensor.name}>
                    <span className="sensor-tag-icon">{sensor.icon}</span>
                    <span>
                      <strong>{sensor.name}</strong>
                      <small>{sensor.chip}</small>
                    </span>
                  </span>
                ))}
              </div>
            </div>
          </Reveal>

          <Reveal>
            <div className="pi-visual">
              <div className="pi-chip">
                <Cpu size={30} />
              </div>
              <div className="pi-rings">
                <span className="pi-ring r1" />
                <span className="pi-ring r2" />
                <span className="pi-ring r3" />
              </div>
              <div className="pi-flow-labels">
                <span className="flow-label cyan">Sensor data</span>
                <span className="flow-label purple">Filtering</span>
                <span className="flow-label success">Upload</span>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}