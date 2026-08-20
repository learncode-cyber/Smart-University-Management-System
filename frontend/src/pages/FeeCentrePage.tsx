import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import { useMyFeeStatus, usePaymentHistory, downloadInvoice } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { StudentFeeStatus } from "@/types/api";

const statusPill: Record<string, string> = {
  pending: "status-pill--neutral",
  partial: "status-pill--accent",
  paid: "status-pill--success",
  overdue: "status-pill--danger",
  waived: "status-pill--neutral",
};

function InvoiceRow({ invoice }: { invoice: StudentFeeStatus["invoices"][number] }) {
  const { showToast } = useToast();
  const [isDownloading, setIsDownloading] = useState(false);

  async function handleDownload() {
    setIsDownloading(true);
    try {
      await downloadInvoice(invoice.id);
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <tr>
      <td className="font-mono text-xs">#{invoice.id}</td>
      <td className="font-mono">{invoice.amount_due.toFixed(2)}</td>
      <td className="font-mono">{invoice.amount_paid.toFixed(2)}</td>
      <td className="font-mono">{invoice.outstanding.toFixed(2)}</td>
      <td className="font-mono text-xs">{invoice.due_date}</td>
      <td>
        <span className={"status-pill " + (statusPill[invoice.status] ?? "status-pill--neutral")}>
          {invoice.status}
        </span>
      </td>
      <td>
        <button onClick={handleDownload} disabled={isDownloading} className="text-brass hover:underline text-xs">
          {isDownloading ? "..." : "Download"}
        </button>
      </td>
    </tr>
  );
}

function StudentFeeBlock({ student, showName }: { student: StudentFeeStatus; showName: boolean }) {
  const { data: payments, isLoading: paymentsLoading } = usePaymentHistory(student.student_id);

  return (
    <div className="border border-slate/20 rounded bg-white p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        {showName && <h2 className="font-display text-lg">{student.student_name}</h2>}
        <div className="text-right">
          <p className="text-slate text-xs">Outstanding balance</p>
          <p
            className={
              "font-display text-2xl " + (student.total_outstanding > 0 ? "text-brick" : "text-field-green")
            }
          >
            {student.total_outstanding.toFixed(2)}
          </p>
        </div>
      </div>

      {student.invoices.length === 0 ? (
        <p className="text-slate text-sm mb-4">No invoices yet.</p>
      ) : (
        <table className="ledger-table mb-6">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Due</th>
              <th>Paid</th>
              <th>Outstanding</th>
              <th>Due Date</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {student.invoices.map((inv) => (
              <InvoiceRow key={inv.id} invoice={inv} />
            ))}
          </tbody>
        </table>
      )}

      <h3 className="text-sm font-medium text-slate mb-2">Payment History</h3>
      {paymentsLoading && <p className="text-slate text-sm">Loading payment history...</p>}
      {!paymentsLoading && (payments?.length ?? 0) === 0 && (
        <p className="text-slate text-sm">No payments recorded yet.</p>
      )}
      {!paymentsLoading && payments && payments.length > 0 && (
        <table className="ledger-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Method</th>
              <th>Reference</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id}>
                <td className="font-mono text-xs">{new Date(p.paid_at).toLocaleDateString()}</td>
                <td className="font-mono">{p.amount.toFixed(2)}</td>
                <td className="capitalize">{p.method.replace("_", " ")}</td>
                <td className="text-slate text-xs">{p.transaction_ref ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export function FeeCentrePage() {
  const { data, isLoading, isError } = useMyFeeStatus();
  const students = data?.students ?? [];

  return (
    <AppLayout title="Fee Centre">
      {isLoading && <p className="text-slate text-sm">Loading fee status...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">
          Couldn't load fee status. Try refreshing the page.
        </p>
      )}
      {!isLoading && !isError && students.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No fee records yet.</p>
        </div>
      )}
      {!isLoading && !isError && students.map((s) => (
        <StudentFeeBlock key={s.student_id} student={s} showName={students.length > 1} />
      ))}
    </AppLayout>
  );
}
