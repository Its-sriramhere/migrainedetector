import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { AssessmentQuestion } from "../../types";

interface OnboardingQuestionProps {
  question: AssessmentQuestion;
  index: number;
  total: number;
  selected: string[];
  onSelect: (value: string[]) => void;
  onNext: () => void;
  onBack: () => void;
  isLast: boolean;
}

export function OnboardingQuestion({
  question,
  index,
  total,
  selected,
  onSelect,
  onNext,
  onBack,
  isLast,
}: OnboardingQuestionProps) {
  const [animated, setAnimated] = useState(false);
  useEffect(() => {
    const timer = requestAnimationFrame(() => setAnimated(true));
    return () => cancelAnimationFrame(timer);
  }, [question]);

  const toggle = (value: string) => {
    if (question.question_type === "multi") {
      onSelect(selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value]);
    } else {
      onSelect([value]);
    }
  };

  return (
    <div className="onboarding-card">
      <div className="onboarding-progress">
        <span>
          Question {index} of {total}
        </span>
        <div className="onboarding-progress-track">
          <div className="onboarding-progress-fill" style={{ width: `${(index / total) * 100}%` }} />
        </div>
      </div>

      <div className={`onboarding-body ${animated ? "is-visible" : ""}`}>
        <span className="eyebrow">PERSONALIZATION · {question.question_type.toUpperCase()}</span>
        <h2 className="onboarding-question">{question.question_text}</h2>

        <div className="onboarding-options">
          {question.options.map((option) => {
            const isActive = selected.includes(option);
            return (
              <button
                key={option}
                className={`onboarding-option ${isActive ? "selected" : ""}`}
                onClick={() => toggle(option)}
              >
                <span className="onboarding-option-check">
                  {isActive ? "✓" : ""}
                </span>
                <span>{option}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="onboarding-nav">
        <button className="btn btn-secondary btn-sm" onClick={onBack} disabled={index === 1}>
          <ChevronLeft size={16} /> Back
        </button>
        <button
          className="btn btn-primary btn-sm"
          onClick={onNext}
          disabled={question.question_type === "single" ? selected.length !== 1 : selected.length === 0}
        >
          {isLast ? "Build My Profile" : "Next"} <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}