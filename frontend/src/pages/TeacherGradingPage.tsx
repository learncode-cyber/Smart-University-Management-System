import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import { useExams, useExamDetailForTeacher, useExamResults, useGradeSubmission, useSubmitResultForApproval } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { ExamSubmissionResponse } from "@/types/api";

function SubmissionGrader({ examId, submission }: { examId: number; submission: ExamSubmissionResponse }) {
  const { data: exam } = useExamDetailForTeacher(examId);
  const gradeSubmission = useGradeSubmission(examId);
  const submitForApproval = useSubmitResultForApproval(examId);
  const { showToast } = useToast();

  const [scores, setScores] = useState<Record<number, string>>(() => {
    const initial: Record<number, string> = {};
    submission.answers.forEach((a) => {
      if (a.score !== null) initial[a.question_id] = String(a.score);
    });
    return initial;
  });
  const [feedback, setFeedback] = useState<Record<number, string>>(() => {
    const initial: Record<number, string> = {};
    submission.answers.forEach((a) => {
      if (a.feedback) initial[a.question_id] = a.feedback;
    });
    return initial;
  });

  if (!exam) return <p className="text-slate text-sm">Loading questions...</p>;

  async function handleSave() {
    const grades = submission.answers
      .filter((a) => scores[a.question_id] !== undefined && scores[a.question_id] !== "")
      .map((a) => ({
        question_id: a.question_id,
        score: Number(scores[a.question_id]),
        feedback: feedback[a.question_id] ?? "",
      }));
    if (grades.length === 0) {
      showToast("Enter at least one score before saving.", "error");
      return;
    }
    try {
      await gradeSubmission.mutateAsync({ student_id: submission.student_id, grades });
      showToast(`Saved grades for ${submission.student_name}.`, "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  async function handleSubmitForApproval() {
    try {
      await submitForApproval.mutateAsync({ student_id: submission.student_id });
      showToast(`${submission.student_name}'s result submitted to admin for approval.`, "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <div className="border border-slate/20 rounded bg-white p-5 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base">{submission.student_name}</h3>
        <span className={"status-pill " + (submission.status === "graded" ? "status-pill--success" : "status-pill--accent")}>
          {submission.status.replace("_", " ")}
          {submission.total_score !== null && ` · ${submission.total_score}/${exam.total_marks}`}
        </span>
      </div>

      <div className="space-y-4">
        {exam.questions.map((q) => {
          const answer = submission.answers.find((a) => a.question_id === q.id);
          if (!answer) return null;
          const isAutoGraded = q.question_type === "mcq";

          return (
            <div key={q.id} className="border-t border-slate/10 pt-3">
              <p className="text-sm text-slate mb-1">{q.question_text} · {q.marks} marks</p>

              {q.question_type === "mcq" ? (
                <p className="text-sm mb-2">
                  Selected: {q.options.find((o) => o.id === answer.selected_option_id)?.option_text ?? "(no answer)"}
                  {" — "}
                  <span className={answer.score === q.marks ? "text-field-green" : "text-brick"}>
                    auto-graded: {answer.score ?? 0}/{q.marks}
                  </span>
                </p>
              ) : (
                <div className="bg-parchment/60 border border-slate/10 rounded p-3 mb-2 text-sm whitespace-pre-wrap font-mono">
                  {answer.answer_text || "(no answer submitted)"}
                </div>
              )}

              {!isAutoGraded && (
                <div className="flex gap-3 items-start">
                  <div className="w-24">
                    <label className="block text-xs text-slate mb-1">Score</label>
                    <input
                      type="number" min={0} max={q.marks}
                      value={scores[q.id] ?? ""}
                      onChange={(e) => setScores((prev) => ({ ...prev, [q.id]: e.target.value }))}
                      className="w-full border border-slate/30 rounded px-2 py-1 text-sm"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs text-slate mb-1">Feedback</label>
                    <input
                      value={feedback[q.id] ?? ""}
                      onChange={(e) => setFeedback((prev) => ({ ...prev, [q.id]: e.target.value }))}
                      className="w-full border border-slate/30 rounded px-2 py-1 text-sm"
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex items-center gap-3 mt-4">
        <button
          onClick={handleSave}
          disabled={gradeSubmission.isPending}
          className="bg-ink text-parchment rounded px-4 py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
        >
          {gradeSubmission.isPending ? "Saving..." : "Save grades"}
        </button>
        <button
          onClick={handleSubmitForApproval}
          disabled={submission.status !== "graded" || submitForApproval.isPending}
          title={submission.status !== "graded" ? "All questions must be graded first" : ""}
          className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-40"
        >
          {submitForApproval.isPending ? "Submitting..." : "Submit for Approval"}
        </button>
      </div>
    </div>
  );
}

export function TeacherGradingPage() {
  const { data: exams } = useExams();
  const [selectedExamId, setSelectedExamId] = useState<string>("");
  const examId = Number(selectedExamId);
  const { data: results, isLoading, isError } = useExamResults(examId);

  const gradableExams = (exams ?? []).filter((e) => e.status !== "draft" && e.status !== "scheduled");

  return (
    <AppLayout title="Grading">
      <div className="mb-5 max-w-md">
        <label className="block text-sm mb-1 text-slate">Select an exam</label>
        <select
          value={selectedExamId}
          onChange={(e) => setSelectedExamId(e.target.value)}
          className="w-full border border-slate/30 rounded px-3 py-2"
        >
          <option value="">Choose an exam to grade</option>
          {gradableExams.map((e) => (
            <option key={e.id} value={e.id}>{e.title}</option>
          ))}
        </select>
      </div>

      {!selectedExamId && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">Select an exam above to see its submissions.</p>
        </div>
      )}

      {selectedExamId && isLoading && <p className="text-slate text-sm">Loading submissions...</p>}
      {selectedExamId && isError && (
        <p role="alert" className="text-brick text-sm">Couldn't load submissions for this exam.</p>
      )}
      {selectedExamId && !isLoading && !isError && (results?.submissions.length ?? 0) === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No submissions yet for this exam.</p>
        </div>
      )}

      {selectedExamId && !isLoading && !isError && results && results.submissions.map((s) => (
        <SubmissionGrader key={s.id} examId={examId} submission={s} />
      ))}
    </AppLayout>
  );
}
