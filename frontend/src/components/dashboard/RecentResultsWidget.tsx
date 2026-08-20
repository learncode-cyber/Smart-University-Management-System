import { useMyResults } from "@/lib/queries";
import { WidgetCard } from "./WidgetCard";

export function RecentResultsWidget() {
  const { data, isLoading, isError } = useMyResults();
  const students = data?.students ?? [];

  return (
    <WidgetCard
      title="Recent Results"
      isLoading={isLoading}
      isError={isError}
      isEmpty={students.every((s) => s.results.length === 0)}
      emptyMessage="No published results yet."
    >
      <div className="space-y-4">
        {students.map((student) => (
          <div key={student.student_id}>
            <div className="flex items-center justify-between mb-1">
              {students.length > 1 ? (
                <p className="text-sm font-medium">{student.student_name}</p>
              ) : (
                <span />
              )}
              {student.cumulative_gpa !== null && (
                <span className="font-mono text-sm text-brass">GPA {student.cumulative_gpa.toFixed(2)}</span>
              )}
            </div>
            <ul className="divide-y divide-slate/10">
              {student.results.slice(0, 3).map((r) => (
                <li key={r.id} className="py-1.5 flex items-center justify-between text-sm">
                  <span className="text-slate">{r.course_code} — {r.course_title}</span>
                  <span className="font-mono">{r.grade_letter ?? "—"}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
