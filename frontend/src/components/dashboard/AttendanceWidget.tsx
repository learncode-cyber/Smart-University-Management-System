import { useMyAttendance } from "@/lib/queries";
import { WidgetCard } from "./WidgetCard";

/**
 * Renders one block per entry in `students` — a Student caller gets one
 * block (themselves), a Parent caller gets one block per linked child.
 * Same component works for both because the backend now returns the
 * same shape either way (see the Part 10 backend patch).
 */
export function AttendanceWidget() {
  const { data, isLoading, isError } = useMyAttendance();
  const students = data?.students ?? [];

  return (
    <WidgetCard
      title="Attendance"
      isLoading={isLoading}
      isError={isError}
      isEmpty={students.every((s) => s.summaries.length === 0)}
      emptyMessage="No attendance records yet."
    >
      <div className="space-y-4">
        {students.map((student) => (
          <div key={student.student_id}>
            {students.length > 1 && <p className="text-sm font-medium mb-1">{student.student_name}</p>}
            {student.summaries.map((s) => (
              <div key={s.course_section_id} className="flex items-center justify-between text-sm py-1">
                <span className="text-slate">Course section #{s.course_section_id}</span>
                <span
                  className={
                    "status-pill " + (s.is_below_threshold ? "status-pill--danger" : "status-pill--success")
                  }
                >
                  {s.percentage}%
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
