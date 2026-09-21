import { useCountUp, useReveal } from "../../hooks/useReveal";

function Counter({ target, prefix = "", suffix = "" }: { target: number; prefix?: string; suffix?: string }) {
  const value = useCountUp(target);
  return (
    <span className="stat-value">
      {prefix}
      {Math.round(value)}
      {suffix}
    </span>
  );
}

const stats = [
  { value: 1, prefix: "", suffix: "B+", label: "People affected by migraine worldwide" },
  { value: 14, suffix: "", label: "Personalization questions" },
  { value: 6, suffix: "", label: "Physiological signals monitored" },
  { value: 60, prefix: "", suffix: " min", label: "Risk prediction window" },
];

export function TrustStats() {
  const [ref, visible] = useReveal<HTMLDivElement>();
  return (
    <section className="trust-stats">
      <div className="container">
        <div className={`stats-grid ${visible ? "is-visible" : ""}`} ref={ref}>
          {stats.map((stat) => (
            <div className="stat-card" key={stat.label}>
              <Counter target={stat.value} prefix={stat.prefix ?? ""} suffix={stat.suffix} />
              <p>{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}