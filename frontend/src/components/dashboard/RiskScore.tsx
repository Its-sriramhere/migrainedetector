import "./RiskScore.css";

interface RiskScoreProps {
  score: number;
  windowMinutes?: number;
  advice?: string[];
}

export function RiskScore({ score, windowMinutes = 60, advice = [] }: RiskScoreProps) {
  const radius = 85;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const level = score < 30 ? "LOW" : score < 70 ? "MODERATE" : "HIGH";

  return (
    <div className={`risk-card risk-${level.toLowerCase()}`}>
      <div className="risk-title">CURRENT MIGRAINE RISK</div>

      <div className="risk-ring">
        <svg viewBox="0 0 220 220" aria-hidden="true">
          <circle className="risk-track" cx="110" cy="110" r={radius} />
          <circle
            className="risk-progress"
            cx="110"
            cy="110"
            r={radius}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>

        <div className="risk-value">
          <strong>{score}%</strong>
          <span>{level}</span>
        </div>
      </div>

      <p>
        Estimated risk within the next <strong>{windowMinutes} minutes</strong>
      </p>

      <div className="risk-note">
        Based on your current pattern compared with your personal baseline.
      </div>

      {advice.length > 0 && (
        <div className="risk-advice">
          <span className="risk-advice-title">REDUCE RISK NOW</span>
          <ul>
            {advice.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}