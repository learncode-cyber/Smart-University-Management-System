import { AppLayout } from "@/components/layout/AppLayout";
import { useAttendanceReports } from "@/lib/queries";

export function AdminAttendanceReportsPage() {
  const { data, isLoading, isError } = useAttendanceReports();
  const rows = data ?? [];

  return (
    <AppLayout title="Attendance Reports">
      <p className="text-slate text-sm mb-4">
        Attendance percentage for every student, across every course section, university-wide.
      </p>

      {isLoading && <p className="text-slate text-sm">Loading report...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">Couldn't load the attendance report.</p>
      )}
      {!isLoading && !isError && rows.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No attendance records yet.</p>
        </div>
      )}
      {!isLoading && !isError && rows.length > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Course Section</th>
                <th>Present / Total</th>
                <th>Percentage</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.student_id}-${r.course_section_id}-${i}`}>
                  <td className="font-medium">{r.student_name}</td>
                  <td className="text-slate text-xs">#{r.course_section_id}</td>
                  <td className="font-mono">{r.present_count} / {r.total_classes}</td>
                  <td className="font-mono">{r.percentage}%</td>
                  <td>
                    {r.is_below_threshold && (
                      <span className="status-pill status-pill--danger">Below threshold</span>
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
