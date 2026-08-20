import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import {
  useMyCourseSections, useExams, useCreateExam, useDeleteExam,
} from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { ExamQuestionCreate } from "@/types/api";

const emptyQuestion = (order: number): ExamQuestionCreate => ({
  question_type: "mcq",
  question_text: "",
  marks: 5,
  order_index: order,
  starter_code: null,
  expected_output: null,
  options: [{ option_text: "", is_correct: true }, { option_text: "", is_correct: false }],
});

const statusStyle: Record<string, string> = {
  draft: "status-pill--neutral", scheduled: "status-pill--accent", open: "status-pill--success",
  closed: "status-pill--neutral", grading_done: "status-pill--accent", published: "status-pill--success",
};

function QuestionEditor({
  question, index, onChange, onRemove,
}: {
  question: ExamQuestionCreate;
  index: number;
  onChange: (q: ExamQuestionCreate) => void;
  onRemove: () => void;
}) {
  function updateOption(optIndex: number, field: "option_text" | "is_correct", value: string | boolean) {
    const options = question.options.map((o, i) => {
      if (field === "is_correct") {
        // MCQ = single correct answer — selecting one clears the others
        return { ...o, is_correct: i === optIndex ? (value as boolean) : false };
      }
      return i === optIndex ? { ...o, [field]: value } : o;
    });
    onChange({ ...question, options });
  }

  return (
    <div className="border border-slate/20 rounded p-4 mb-3 bg-parchment/40">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium">Question {index + 1}</p>
        <button type="button" onClick={onRemove} className="text-brick text-xs hover:underline">Remove</button>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-2">
        <div>
          <label className="block text-xs mb-1 text-slate">Type</label>
          <select
            value={question.question_type}
            onChange={(e) => onChange({ ...question, question_type: e.target.value as ExamQuestionCreate["question_type"] })}
            className="w-full border border-slate/30 rounded px-2 py-1.5 text-sm"
          >
            <option value="mcq">MCQ</option>
            <option value="short_answer">Short answer</option>
            <option value="descriptive">Descriptive</option>
            <option value="coding">Coding</option>
          </select>
        </div>
        <div>
          <label className="block text-xs mb-1 text-slate">Marks</label>
          <input
            type="number" min={1} value={question.marks}
            onChange={(e) => onChange({ ...question, marks: Number(e.target.value) })}
            className="w-full border border-slate/30 rounded px-2 py-1.5 text-sm"
          />
        </div>
      </div>

      <label className="block text-xs mb-1 text-slate">Question text</label>
      <textarea
        value={question.question_text}
        onChange={(e) => onChange({ ...question, question_text: e.target.value })}
        rows={2}
        className="w-full border border-slate/30 rounded px-2 py-1.5 text-sm mb-2"
      />

      {question.question_type === "mcq" && (
        <div>
          <label className="block text-xs mb-1 text-slate">Options (select the correct one)</label>
          {question.options.map((opt, i) => (
            <div key={i} className="flex items-center gap-2 mb-1.5">
              <input
                type="radio" checked={opt.is_correct} onChange={() => updateOption(i, "is_correct", true)}
              />
              <input
                value={opt.option_text}
                onChange={(e) => updateOption(i, "option_text", e.target.value)}
                placeholder={`Option ${i + 1}`}
                className="flex-1 border border-slate/30 rounded px-2 py-1 text-sm"
              />
              {question.options.length > 2 && (
                <button
                  type="button"
                  onClick={() => onChange({ ...question, options: question.options.filter((_, oi) => oi !== i) })}
                  className="text-brick text-xs"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => onChange({ ...question, options: [...question.options, { option_text: "", is_correct: false }] })}
            className="text-brass text-xs hover:underline"
          >
            + Add option
          </button>
        </div>
      )}

      {question.question_type === "coding" && (
        <div>
          <label className="block text-xs mb-1 text-slate">Starter code (hint)</label>
          <textarea
            value={question.starter_code ?? ""}
            onChange={(e) => onChange({ ...question, starter_code: e.target.value })}
            rows={4}
            className="w-full border border-slate/30 rounded px-2 py-1.5 text-sm font-mono"
          />
        </div>
      )}
    </div>
  );
}

export function TeacherExamBuilderPage() {
  const { data: sections } = useMyCourseSections();
  const { data: exams, isLoading, isError } = useExams();
  const createExam = useCreateExam();
  const deleteExam = useDeleteExam();
  const { showToast } = useToast();

  const [isBuilding, setIsBuilding] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [sectionId, setSectionId] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [questions, setQuestions] = useState<ExamQuestionCreate[]>([emptyQuestion(0)]);

  const totalMarks = questions.reduce((sum, q) => sum + (q.marks || 0), 0);

  function resetForm() {
    setTitle(""); setDescription(""); setSectionId(""); setStartTime(""); setEndTime("");
    setDurationMinutes(60); setQuestions([emptyQuestion(0)]);
    setIsBuilding(false);
  }

  async function handleCreate() {
    if (!sectionId) {
      showToast("Choose a course section first.", "error");
      return;
    }
    try {
      await createExam.mutateAsync({
        course_section_id: Number(sectionId),
        title, description,
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        duration_minutes: durationMinutes,
        questions: questions.map((q, i) => ({ ...q, order_index: i })),
      });
      showToast("Exam created as a draft.", "success");
      resetForm();
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  async function handleDelete(examId: number) {
    if (!window.confirm("Delete this exam? This can't be undone.")) return;
    try {
      await deleteExam.mutateAsync(examId);
      showToast("Exam deleted.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <AppLayout title="Exam Builder">
      <div className="flex items-center justify-between mb-4">
        <p className="text-slate text-sm">Exams you've created</p>
        <button
          onClick={() => setIsBuilding((v) => !v)}
          className="bg-brass text-white rounded px-4 py-1.5 text-sm font-medium hover:bg-brass/90 transition-colors"
        >
          {isBuilding ? "Cancel" : "+ New Exam"}
        </button>
      </div>

      {isBuilding && (
        <div className="border border-slate/20 rounded bg-white p-6 mb-6">
          <h2 className="font-display text-lg mb-4">New Exam</h2>

          <div className="grid sm:grid-cols-2 gap-4 mb-4">
            <div className="sm:col-span-2">
              <label className="block text-sm mb-1 text-slate">Title</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm mb-1 text-slate">Description</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="w-full border border-slate/30 rounded px-3 py-2" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm mb-1 text-slate">Course section</label>
              <select value={sectionId} onChange={(e) => setSectionId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
                <option value="">Select a section you teach</option>
                {(sections ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.course_code} — {s.course_title} ({s.section_name}, {s.semester} {s.academic_year})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">Start time</label>
              <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">End time</label>
              <input type="datetime-local" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">Duration (minutes)</label>
              <input type="number" min={1} value={durationMinutes} onChange={(e) => setDurationMinutes(Number(e.target.value))} className="w-full border border-slate/30 rounded px-3 py-2" />
            </div>
            <div className="flex items-end">
              <p className="text-slate text-sm">Total marks so far: <span className="font-mono font-medium">{totalMarks}</span></p>
            </div>
          </div>

          <h3 className="font-display text-base mb-2">Questions</h3>
          {questions.map((q, i) => (
            <QuestionEditor
              key={i}
              question={q}
              index={i}
              onChange={(updated) => setQuestions((prev) => prev.map((p, pi) => (pi === i ? updated : p)))}
              onRemove={() => setQuestions((prev) => prev.filter((_, pi) => pi !== i))}
            />
          ))}
          <button
            type="button"
            onClick={() => setQuestions((prev) => [...prev, emptyQuestion(prev.length)])}
            className="text-brass text-sm hover:underline mb-4"
          >
            + Add question
          </button>

          <button
            onClick={handleCreate}
            disabled={createExam.isPending}
            className="w-full bg-ink text-parchment rounded py-2.5 font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {createExam.isPending ? "Creating..." : "Create Exam (as Draft)"}
          </button>
        </div>
      )}

      {isLoading && <p className="text-slate text-sm">Loading exams...</p>}
      {!isLoading && isError && <p role="alert" className="text-brick text-sm">Couldn't load your exams.</p>}
      {!isLoading && !isError && (exams?.length ?? 0) === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center"><p className="text-slate">No exams yet — create your first one above.</p></div>
      )}
      {!isLoading && !isError && (exams?.length ?? 0) > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          <table className="ledger-table">
            <thead><tr><th>Title</th><th>Marks</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {exams!.map((e) => (
                <tr key={e.id}>
                  <td className="font-medium">{e.title}</td>
                  <td className="font-mono">{e.total_marks}</td>
                  <td><span className={"status-pill " + (statusStyle[e.status] ?? "status-pill--neutral")}>{e.status.replace("_", " ")}</span></td>
                  <td>
                    {(e.status === "draft" || e.status === "scheduled") && (
                      <button onClick={() => handleDelete(e.id)} className="text-brick hover:underline text-xs">Delete</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}
