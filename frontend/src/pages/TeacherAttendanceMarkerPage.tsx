import { useState, useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import {
  useMyCourseSections, useEnrolledStudents, useClassAttendance,
  useBulkMarkAttendance, useCorrectAttendance,
} from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";

type Status = "present" | "absent" | "late" | "excused";

const statusOptions: { value: Status; label: string; className: string }[] = [
  { value: "present", label: "Present", className: "status-pill--success" },
  { value: "late", label: "Late", className: "status-pill--accent" },
  { value: "absent", label: "Absent", className: "status-pill--danger" },
  { value: "excused", label: "Excused", className: "status-pill--neutral" },
];

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function TeacherAttendanceMarkerPage() {
  const { data: sections } = useMyCourseSections();
  const [sectionId, setSectionId] = useState("");
  const [date, setDate] = useState(todayISO());
  const [statuses, setStatuses] = useState<Record<number, Status>>({});
  const { showToast } = useToast();

  const sectionIdNum = Number(sectionId);
  const { data: roster, isLoading: rosterLoading } = useEnrolledStudents(sectionIdNum);
  const { data: existingRecords, isLoading: recordsLoading } = useClassAttendance(sectionIdNum, date);
  const bulkMark = useBulkMarkAttendance();
  const correctAttendance = useCorrectAttendance();

  const alreadyMarked = (existingRecords?.length ?? 0) > 0;

  // default everyone to "present" when the roster loads for a fresh (unmarked) date
  useEffect(() => {
    if (roster && !alreadyMarked) {
      const initial: Record<number, Status> = {};
      roster.forEach((s) => { initial[s.student_id] = "present"; });
      setStatuses(initial);
    }
  }, [roster, alreadyMarked, date]);

  async function handleSubmit() {
    if (!sectionId) {
      showToast("Choose a course section first.", "error");
      return;
    }
    try {
      await bulkMark.mutateAsync({
        course_section_id: sectionIdNum,
        date,
        entries: Object.entries(statuses).map(([studentId, status]) => ({ student_id: Number(studentId), status })),
      });
      showToast("Attendance saved.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  async function handleCorrect(recordId: number, newStatus: Status) {
    const reason = window.prompt("Reason for this correction?");
    if (!reason) return;
    try {
      await correctAttendance.mutateAsync({ recordId, status: newStatus, reason });
      showToast("Attendance record corrected.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <AppLayout title="Attendance Marker">
      <div className="grid sm:grid-cols-2 gap-4 mb-6 max-w-xl">
        <div>
          <label className="block text-sm mb-1 text-slate">Course section</label>
          <select value={sectionId} onChange={(e) => setSectionId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">Select a section</option>
            {(sections ?? []).map((s) => (
              <option key={s.id} value={s.id}>{s.course_code} — {s.course_title} ({s.section_name})</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Date</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
      </div>

      {!sectionId && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center"><p className="text-slate">Select a section and date to mark attendance.</p></div>
      )}

      {sectionId && (rosterLoading || recordsLoading) && <p className="text-slate text-sm">Loading roster...</p>}

      {sectionId && !rosterLoading && !recordsLoading && (roster?.length ?? 0) === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center"><p className="text-slate">No students enrolled in this section yet.</p></div>
      )}

      {sectionId && !rosterLoading && !recordsLoading && (roster?.length ?? 0) > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          {alreadyMarked && (
            <p className="text-xs text-brass bg-brass/5 px-4 py-2 border-b border-slate/10">
              Attendance for this date is already marked — click a status pill below to correct an individual record.
            </p>
          )}
          <table className="ledger-table">
            <thead><tr><th>Roll</th><th>Name</th><th>Status</th></tr></thead>
            <tbody>
              {roster!.map((student) => {
                const existing = existingRecords?.find((r) => r.student_id === student.student_id);
                return (
                  <tr key={student.student_id}>
                    <td className="font-mono text-xs">{student.roll_number}</td>
                    <td className="font-medium">{student.full_name}</td>
                    <td>
                      {alreadyMarked ? (
                        <div className="flex gap-1">
                          {statusOptions.map((opt) => (
                            <button
                              key={opt.value}
                              onClick={() => existing && handleCorrect(existing.id, opt.value)}
                              className={
                                "status-pill " + opt.className +
                                (existing?.status === opt.value ? " ring-2 ring-offset-1 ring-ink" : " opacity-40 hover:opacity-100")
                              }
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          {statusOptions.map((opt) => (
                            <button
                              key={opt.value}
                              type="button"
                              onClick={() => setStatuses((prev) => ({ ...prev, [student.student_id]: opt.value }))}
                              className={
                                "status-pill " + opt.className +
                                (statuses[student.student_id] === opt.value ? " ring-2 ring-offset-1 ring-ink" : " opacity-40 hover:opacity-100")
                              }
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {sectionId && !alreadyMarked && (roster?.length ?? 0) > 0 && (
        <button
          onClick={handleSubmit}
          disabled={bulkMark.isPending}
          className="mt-4 bg-ink text-parchment rounded px-6 py-2.5 font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
        >
          {bulkMark.isPending ? "Saving..." : "Save Attendance"}
        </button>
      )}
    </AppLayout>
  );
}
