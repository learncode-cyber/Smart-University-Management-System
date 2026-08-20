import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useMyAttendance } from "@/lib/queries";
import type { StudentAttendanceStatus } from "@/types/api";

const statusPill: Record<string, string> = {
  present: "status-pill--success",
  late: "status-pill--accent",
  absent: "status-pill--danger",
  excused: "status-pill--neutral",
};

function StudentAttendanceBlock({ student, showName }: { student: StudentAttendanceStatus; showName: boolean }) {
  const [selectedSection, setSelectedSection] = useState<number | null>(null);
  const { data: detail } = useMyAttendance(selectedSection ?? undefined);

  const myDetail = detail?.students.find((s) => s.student_id === student.student_id);

  return (
    <div className="border border-slate/20 rounded bg-white p-6 mb-6">
      {showName && <h2 className="font-display text-lg mb-3">{student.student_name}</h2>}

      {student.summaries.length === 0 ? (
        <p className="text-slate text-sm">No attendance records yet.</p>
      ) : (
        <>
          <div className="grid sm:grid-cols-3 gap-3 mb-5">
            {student.summaries.map((s) => (
              <button
                key={s.course_section_id}
                onClick={() => setSelectedSection(s.course_section_id)}
                className={
                  "text-left border rounded p-4 transition-colors " +
                  (selectedSection === s.course_section_id
                    ? "border-brass bg-brass/5"
                    : "border-slate/20 hover:border-slate/40")
                }
              >
                <p className="text-xs text-slate mb-1">Course section #{s.course_section_id}</p>
                <p
                  className={
                    "font-display text-2xl " + (s.is_below_threshold ? "text-brick" : "text-field-green")
                  }
                >
                  {s.percentage}%
                </p>
                <p className="text-xs text-slate">{s.present_count} / {s.total_classes} classes</p>
                {s.is_below_threshold && (
                  <span className="status-pill status-pill--danger mt-2">Below threshold</span>
                )}
              </button>
            ))}
          </div>

          {selectedSection !== null && myDetail && (
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {myDetail.records.map((record) => (
                  <tr key={record.id}>
                    <td className="font-mono text-xs">{record.date}</td>
                    <td>
                      <span className={"status-pill " + (statusPill[record.status] ?? "status-pill--neutral")}>
                        {record.status}
                      </span>
                    </td>
                    <td className="text-slate text-xs">
                      {record.correction_reason ? `Corrected: ${record.correction_reason}` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}

export function AttendancePage() {
  const { data, isLoading, isError } = useMyAttendance();
  const students = data?.students ?? [];

  return (
    <AppLayout title="Attendance">
      {isLoading && <p className="text-slate text-sm">Loading attendance...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">
          Couldn't load attendance. Try refreshing the page.
        </p>
      )}
      {!isLoading && !isError && students.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No attendance records yet.</p>
        </div>
      )}
      {!isLoading && !isError && students.map((s) => (
        <StudentAttendanceBlock key={s.student_id} student={s} showName={students.length > 1} />
      ))}
    </AppLayout>
  );
}
