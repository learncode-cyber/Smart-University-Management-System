import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import { useMyResults, downloadTranscript } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { ResultItem, StudentResultsStatus } from "@/types/api";

function groupBySemester(results: ResultItem[]): Record<string, ResultItem[]> {
  return results.reduce<Record<string, ResultItem[]>>((acc, r) => {
    const key = `${r.semester} ${r.academic_year}`;
    (acc[key] ??= []).push(r);
    return acc;
  }, {});
}

function StudentResultsBlock({ student, showName }: { student: StudentResultsStatus; showName: boolean }) {
  const { showToast } = useToast();
  const [isDownloading, setIsDownloading] = useState(false);
  const grouped = groupBySemester(student.results);
  const semesters = Object.keys(grouped);

  async function handleDownload() {
    setIsDownloading(true);
    try {
      await downloadTranscript(student.student_id);
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="border border-slate/20 rounded bg-white p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          {showName && <h2 className="font-display text-lg">{student.student_name}</h2>}
          {student.cumulative_gpa !== null && (
            <p className="text-brass font-mono text-sm">Cumulative GPA: {student.cumulative_gpa.toFixed(2)} / 4.00</p>
          )}
        </div>
        <button
          onClick={handleDownload}
          disabled={isDownloading || student.results.length === 0}
          className="text-sm border border-brass text-brass rounded px-3 py-1.5 hover:bg-brass/10 transition-colors disabled:opacity-40"
        >
          {isDownloading ? "Preparing PDF..." : "Download transcript"}
        </button>
      </div>

      {student.results.length === 0 ? (
        <p className="text-slate text-sm">No published results yet.</p>
      ) : (
        semesters.map((semester) => (
          <div key={semester} className="mb-4">
            <h3 className="text-sm font-medium text-slate mb-2">{semester}</h3>
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Marks</th>
                  <th>Grade</th>
                  <th>Grade Point</th>
                </tr>
              </thead>
              <tbody>
                {grouped[semester].map((r) => (
                  <tr key={r.id}>
                    <td>{r.course_code} — {r.course_title}</td>
                    <td className="font-mono">{r.total_marks_obtained} / {r.total_marks_possible}</td>
                    <td className="font-mono">{r.grade_letter}</td>
                    <td className="font-mono">{r.grade_point?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}

export function ResultsPage() {
  const { data, isLoading, isError } = useMyResults();
  const students = data?.students ?? [];

  return (
    <AppLayout title="Results">
      {isLoading && <p className="text-slate text-sm">Loading results...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">
          Couldn't load results. Try refreshing the page.
        </p>
      )}
      {!isLoading && !isError && students.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No results to show yet.</p>
        </div>
      )}
      {!isLoading && !isError && students.map((s) => (
        <StudentResultsBlock key={s.student_id} student={s} showName={students.length > 1} />
      ))}
    </AppLayout>
  );
}
