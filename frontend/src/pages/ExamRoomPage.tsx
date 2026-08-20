import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import { useExamDetail, useSubmitExam } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { ExamAnswerSubmit } from "@/types/api";

function formatCountdown(totalSeconds: number): string {
  const clamped = Math.max(totalSeconds, 0);
  const h = Math.floor(clamped / 3600);
  const m = Math.floor((clamped % 3600) / 60);
  const s = clamped % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  return h > 0 ? `${pad(h)}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
}

export function ExamRoomPage() {
  const { examId } = useParams<{ examId: string }>();
  const id = Number(examId);
  const navigate = useNavigate();
  const { showToast } = useToast();

  const { data: exam, isLoading, isError } = useExamDetail(id);
  const submitExam = useSubmitExam(id);

  // answers keyed by question_id
  const [selectedOptions, setSelectedOptions] = useState<Record<number, number>>({});
  const [textAnswers, setTextAnswers] = useState<Record<number, string>>({});
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [hasSubmittedThisSession, setHasSubmittedThisSession] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<{ totalScore: number | null } | null>(null);

  // countdown ticks from exam.end_time, independent of the frontend's
  // own clock drift concerns — the SERVER is the real authority on the
  // deadline (Part 4), this is purely a UX countdown
  useEffect(() => {
    if (!exam) return;
    const endTime = new Date(exam.end_time).getTime();
    function tick() {
      setSecondsLeft(Math.floor((endTime - Date.now()) / 1000));
    }
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [exam]);

  const isTimeUp = secondsLeft !== null && secondsLeft <= 0;

  const buildAnswers = useMemo(
    () => (): ExamAnswerSubmit[] => {
      if (!exam) return [];
      return exam.questions.map((q) => ({
        question_id: q.id,
        selected_option_id: q.question_type === "mcq" ? selectedOptions[q.id] ?? null : null,
        answer_text: q.question_type !== "mcq" ? textAnswers[q.id] ?? "" : null,
      }));
    },
    [exam, selectedOptions, textAnswers]
  );

  async function handleSubmit() {
    if (!exam || hasSubmittedThisSession) return;
    try {
      const result = await submitExam.mutateAsync(buildAnswers());
      setHasSubmittedThisSession(true);
      setSubmissionResult({ totalScore: result.total_score });
      showToast("Exam submitted.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  // auto-submit once the countdown hits zero, so a student who leaves
  // the tab open past the deadline still gets their in-progress answers
  // in rather than silently losing them to a server-side rejection
  useEffect(() => {
    if (isTimeUp && !hasSubmittedThisSession && exam) {
      handleSubmit();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isTimeUp]);

  if (isLoading) {
    return (
      <AppLayout title="Exam">
        <p className="text-slate text-sm">Loading exam...</p>
      </AppLayout>
    );
  }

  if (isError || !exam) {
    return (
      <AppLayout title="Exam">
        <p role="alert" className="text-brick text-sm">
          Couldn't load this exam. It may not be open, or you may not be enrolled in this course section.
        </p>
      </AppLayout>
    );
  }

  if (hasSubmittedThisSession) {
    return (
      <AppLayout title={exam.title}>
        <div className="border border-slate/20 rounded bg-white p-8 text-center max-w-md mx-auto">
          <h2 className="font-display text-xl mb-2">Submitted</h2>
          <p className="text-slate mb-4">
            {submissionResult?.totalScore !== null && submissionResult?.totalScore !== undefined
              ? `Auto-graded score: ${submissionResult.totalScore} / ${exam.total_marks}`
              : "Your answers are in. Written/coding questions will be graded by your teacher — check back under Results."}
          </p>
          <button
            onClick={() => navigate("/exams")}
            className="bg-ink text-parchment rounded px-4 py-2 text-sm hover:bg-ink/90 transition-colors"
          >
            Back to Exams
          </button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title={exam.title}>
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6 sticky top-0 bg-parchment py-2 z-10">
          <p className="text-slate text-sm">{exam.total_marks} marks total</p>
          <span
            className={
              "font-mono text-lg px-3 py-1 rounded " +
              (secondsLeft !== null && secondsLeft < 60 ? "bg-brick/10 text-brick" : "bg-brass/10 text-brass")
            }
          >
            {secondsLeft !== null ? formatCountdown(secondsLeft) : "--:--"}
          </span>
        </div>

        <div className="space-y-6">
          {exam.questions.map((q, index) => (
            <div key={q.id} className="border border-slate/20 rounded bg-white p-5">
              <p className="text-sm text-slate mb-2">
                Question {index + 1} · {q.marks} marks
              </p>
              <p className="mb-4">{q.question_text}</p>

              {q.question_type === "mcq" && (
                <div className="space-y-2">
                  {q.options.map((opt) => (
                    <label key={opt.id} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="radio"
                        name={`question-${q.id}`}
                        checked={selectedOptions[q.id] === opt.id}
                        onChange={() => setSelectedOptions((prev) => ({ ...prev, [q.id]: opt.id }))}
                      />
                      {opt.option_text}
                    </label>
                  ))}
                </div>
              )}

              {q.question_type === "coding" && (
                <textarea
                  value={textAnswers[q.id] ?? q.starter_code ?? ""}
                  onChange={(e) => setTextAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                  rows={10}
                  className="w-full border border-slate/30 rounded px-3 py-2 font-mono text-sm bg-ink text-parchment focus:border-brass transition-colors"
                  spellCheck={false}
                />
              )}

              {(q.question_type === "short_answer" || q.question_type === "descriptive") && (
                <textarea
                  value={textAnswers[q.id] ?? ""}
                  onChange={(e) => setTextAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                  rows={q.question_type === "short_answer" ? 2 : 6}
                  className="w-full border border-slate/30 rounded px-3 py-2 text-sm focus:border-brass transition-colors"
                />
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-slate text-xs">You can only submit once — there's no resubmission.</p>
          <button
            onClick={handleSubmit}
            disabled={submitExam.isPending}
            className="bg-ink text-parchment rounded px-6 py-2.5 font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {submitExam.isPending ? "Submitting..." : "Submit exam"}
          </button>
        </div>
      </div>
    </AppLayout>
  );
}
