import { useStudentCount, useTeacherCount, useOverdueInvoices } from "@/lib/queries";
import { WidgetCard } from "./WidgetCard";

export function AdminStatsWidget() {
  const students = useStudentCount();
  const teachers = useTeacherCount();
  const overdue = useOverdueInvoices();

  const isLoading = students.isLoading || teachers.isLoading || overdue.isLoading;
  const isError = students.isError || teachers.isError || overdue.isError;

  return (
    <WidgetCard title="University at a Glance" isLoading={isLoading} isError={isError}>
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="font-display text-3xl">{students.data}</p>
          <p className="text-slate text-xs">Students</p>
        </div>
        <div>
          <p className="font-display text-3xl">{teachers.data}</p>
          <p className="text-slate text-xs">Teachers</p>
        </div>
        <div>
          <p className="font-display text-3xl text-brick">{overdue.data?.length ?? 0}</p>
          <p className="text-slate text-xs">Overdue invoices</p>
        </div>
      </div>
    </WidgetCard>
  );
}
