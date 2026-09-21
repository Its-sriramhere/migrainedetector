import { Reveal } from "../ui/Reveal";

const points = [
  {
    title: "No two people are the same",
    body: "Migraine patterns and triggers differ between individuals. A generic threshold misses the signals that matter for you.",
  },
  {
    title: "Signals precede symptoms",
    body: "Heart rate, HRV, blood pressure and activity quietly change before many episodes. Spotting the pattern early is the key.",
  },
  {
    title: "Know why, not just what",
    body: "A number alone is not enough. You need to understand which physiological changes are driving an elevated risk reading.",
  },
];

export function Problem() {
  return (
    <section className="section problem-section">
      <div className="container">
        <Reveal>
          <span className="eyebrow">01 — The Problem</span>
          <h2 className="section-title">
            Migraine patterns are <span className="gradient-text">different for everyone.</span>
          </h2>
          <p className="section-subtitle">
            Most tracking tools treat everyone the same. Migraine Detector learns what
            <em>normal</em> means for a single person — then watches for meaningful deviation.
          </p>
        </Reveal>

        <div className="grid-3 problem-grid">
          {points.map((point, index) => (
            <Reveal key={point.title} className="problem-card glass-card">
              <span className="problem-number">0{index + 1}</span>
              <h3>{point.title}</h3>
              <p>{point.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}