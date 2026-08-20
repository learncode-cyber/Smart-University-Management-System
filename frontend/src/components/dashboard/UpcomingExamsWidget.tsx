import { useExams } from "@/lib/queries";
import { WidgetCard } from "./WidgetCard";

export function UpcomingExamsWidget() {
  const { data, isLoading, isError } = useExams();

  const upcoming = (data ?? [])
    .filter((e) => e.status === "scheduled" || e.status === "open")
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .slice(0, 5);

  return (
    <WidgetCard
      title="Upcoming Exams"
      isLoading={isLoading}
      isError={isError}
      isEmpty={upcoming.length === 0}
      emptyMessage="No upcoming exams scheduled."
    >
      <ul className="divide-y divide-slate/10">
        {upcoming.map((exam) => (
          <li key={exam.id} className="py-2 flex items-center justify-between text-sm">
            <span>{exam.title}</span>
            <span className="text-slate font-mono text-xs">
              {new Date(exam.start_time).toLocaleString(undefined, {
                month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
              })}
            </span>
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}
