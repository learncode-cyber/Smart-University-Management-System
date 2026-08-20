import { Link } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { useExams } from "@/lib/queries";
import type { ExamListItem } from "@/types/api";

const statusStyle: Record<string, string> = {
  draft: "status-pill--neutral",
  scheduled: "status-pill--accent",
  open: "status-pill--success",
  closed: "status-pill--neutral",
  grading_done: "status-pill--accent",
  published: "status-pill--success",
};

function formatWindow(exam: ExamListItem): string {
  const start = new Date(exam.start_time);
  const end = new Date(exam.end_time);
  return `${start.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} – ${end.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
}

export function ExamListPage() {
  const { data, isLoading, isError } = useExams();
  const exams = (data ?? []).slice().sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

  return (
    <AppLayout title="Exams">
      {isLoading && <p className="text-slate text-sm">Loading exams...</p>}

      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">
          Couldn't load your exams. Try refreshing the page.
        </p>
      )}

      {!isLoading && !isError && exams.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No exams to show yet.</p>
        </div>
      )}

      {!isLoading && !isError && exams.length > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Window</th>
                <th>Marks</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {exams.map((exam) => (
                <tr key={exam.id}>
                  <td className="font-medium">{exam.title}</td>
                  <td className="text-slate font-mono text-xs">{formatWindow(exam)}</td>
                  <td className="font-mono">{exam.total_marks}</td>
                  <td>
                    <span className={"status-pill " + (statusStyle[exam.status] ?? "status-pill--neutral")}>
                      {exam.status.replace("_", " ")}
                    </span>
                  </td>
                  <td>
                    {exam.status === "open" ? (
                      <Link to={`/exams/${exam.id}`} className="text-brass hover:underline text-sm font-medium">
                        Enter exam →
                      </Link>
                    ) : exam.status === "scheduled" ? (
                      <span className="text-slate text-xs">Not open yet</span>
                    ) : (
                      <Link to={`/exams/${exam.id}`} className="text-slate hover:text-ink text-sm">
                        View
                      </Link>
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
