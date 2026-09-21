import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { OnboardingQuestion } from "../components/onboarding/OnboardingQuestion";
import { Spinner } from "../components/ui/Spinner";
import { api } from "../services/api";
import type { AssessmentQuestion } from "../types";

export function OnboardingPage() {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string[]>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<AssessmentQuestion[]>("/api/assessment/questions")
      .then((list) => setQuestions(list))
      .catch(() => setError("Could not load the assessment. Is the backend running?"));
  }, []);

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = Object.entries(answers).flatMap(([qid, values]) =>
        values.map((value) => ({ question_id: Number(qid), answer: value })),
      );
      await api.post("/api/assessment/responses", { answers: payload });
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your profile");
      setBusy(false);
    }
  };

  if (error && !questions.length) {
    return (
      <div className="page-wrapper">
        <div className="form-error">{error}</div>
      </div>
    );
  }

  if (!questions.length) {
    return (
      <div className="page-wrapper page-center">
        <Spinner />
      </div>
    );
  }

  const current = questions[index];
  const selected = answers[current.id] ?? [];
  const isLast = index === questions.length - 1;

  return (
    <div className="page-wrapper">
      <OnboardingQuestion
        question={current}
        index={index + 1}
        total={questions.length}
        selected={selected}
        onSelect={(values) => setAnswers((prev) => ({ ...prev, [current.id]: values }))}
        onBack={() => setIndex((i) => Math.max(0, i - 1))}
        onNext={() => {
          if (isLast) void submit();
          else setIndex((i) => i + 1);
        }}
        isLast={isLast}
      />
      {error && <div className="form-error onboarding-error">{error}</div>}
      {busy && (
        <div className="page-center">
          <Spinner />
          <p className="page-center-note">Building your personal baseline…</p>
        </div>
      )}
    </div>
  );
}