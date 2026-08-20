import { useExams } from "@/lib/queries";
import { WidgetCard } from "./WidgetCard";

const statusStyle: Record<string, string> = {
  draft: "status-pill--neutral",
  scheduled: "status-pill--accent",
  open: "status-pill--success",
  closed: "status-pill--neutral",
  grading_done: "status-pill--accent",
  published: "status-pill--success",
};

export function TeacherExamsWidget() {
  const { data, isLoading, isError } = useExams();
  const exams = data ?? [];

  return (
    <WidgetCard
      title="Your Exams"
      isLoading={isLoading}
      isError={isError}
      isEmpty={exams.length === 0}
      emptyMessage="You haven't created any exams yet."
    >
      <ul className="divide-y divide-slate/10">
        {exams.slice(0, 6).map((exam) => (
          <li key={exam.id} className="py-2 flex items-center justify-between text-sm">
            <span>{exam.title}</span>
            <span className={"status-pill " + (statusStyle[exam.status] ?? "status-pill--neutral")}>
              {exam.status.replace("_", " ")}
            </span>
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}
