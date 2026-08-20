import { useMyFeeStatus } from "@/lib/queries";
import { WidgetCard } from "./WidgetCard";

export function FeeStatusWidget() {
  const { data, isLoading, isError } = useMyFeeStatus();
  const students = data?.students ?? [];

  return (
    <WidgetCard
      title="Fee Status"
      isLoading={isLoading}
      isError={isError}
      isEmpty={students.every((s) => s.invoices.length === 0)}
      emptyMessage="No fee invoices yet."
    >
      <div className="space-y-3">
        {students.map((student) => (
          <div key={student.student_id} className="flex items-center justify-between text-sm">
            <div>
              {students.length > 1 && <p className="font-medium">{student.student_name}</p>}
              <p className="text-slate text-xs">Outstanding balance</p>
            </div>
            <span
              className={
                "font-mono font-medium " + (student.total_outstanding > 0 ? "text-brick" : "text-field-green")
              }
            >
              {student.total_outstanding.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
