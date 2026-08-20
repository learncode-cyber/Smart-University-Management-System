import { useState, type FormEvent } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import {
  useFeeDashboardSummary, useOverdueInvoices, useSendOverdueNotices,
  useDepartments, useCreateFeeStructure, useRecordPayment,
} from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";

function CreateFeeStructureForm() {
  const { data: departments } = useDepartments();
  const createStructure = useCreateFeeStructure();
  const { showToast } = useToast();
  const [departmentId, setDepartmentId] = useState("");
  const [feeType, setFeeType] = useState("");
  const [semester, setSemester] = useState("Spring");
  const [academicYear, setAcademicYear] = useState("2026-2027");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const result = await createStructure.mutateAsync({
        department_id: departmentId ? Number(departmentId) : null,
        fee_type: feeType, semester, academic_year: academicYear,
        amount: Number(amount), due_date: dueDate,
      });
      showToast(`Fee structure created — ${result.invoices_generated} invoice(s) generated.`, "success");
      setFeeType(""); setAmount(""); setDueDate("");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-6">
      <h2 className="font-display text-base mb-3">Define Fee Structure</h2>
      <p className="text-slate text-xs mb-3">
        Creates an invoice for every matching student immediately — leave department blank to apply university-wide.
      </p>
      <div className="grid sm:grid-cols-3 gap-3 mb-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Department (optional)</label>
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">All departments</option>
            {(departments ?? []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Fee type</label>
          <input required value={feeType} onChange={(e) => setFeeType(e.target.value)} placeholder="Tuition" className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Amount</label>
          <input required type="number" min={1} value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Semester</label>
          <select value={semester} onChange={(e) => setSemester(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option>Spring</option><option>Summer</option><option>Fall</option>
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Academic year</label>
          <input value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Due date</label>
          <input required type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
      </div>
      <button type="submit" disabled={createStructure.isPending} className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {createStructure.isPending ? "Creating..." : "Create & Generate Invoices"}
      </button>
    </form>
  );
}

function RecordPaymentForm() {
  const recordPayment = useRecordPayment();
  const { showToast } = useToast();
  const [invoiceId, setInvoiceId] = useState("");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("cash");
  const [transactionRef, setTransactionRef] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await recordPayment.mutateAsync({
        invoice_id: Number(invoiceId), amount: Number(amount), method, transaction_ref: transactionRef,
      });
      showToast("Payment recorded.", "success");
      setInvoiceId(""); setAmount(""); setTransactionRef("");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-6">
      <h2 className="font-display text-base mb-1">Record a Payment</h2>
      <p className="text-slate text-xs mb-3">
        Find the invoice ID from the student's Fee Centre or the overdue list below.
      </p>
      <div className="grid sm:grid-cols-4 gap-3 mb-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Invoice ID</label>
          <input required type="number" value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Amount</label>
          <input required type="number" min={0.01} step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Method</label>
          <select value={method} onChange={(e) => setMethod(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="cash">Cash</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="mobile_banking">Mobile Banking</option>
            <option value="card">Card</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Reference (optional)</label>
          <input value={transactionRef} onChange={(e) => setTransactionRef(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
      </div>
      <button type="submit" disabled={recordPayment.isPending} className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {recordPayment.isPending ? "Recording..." : "Record Payment"}
      </button>
    </form>
  );
}

export function AdminFeeDashboardPage() {
  const summary = useFeeDashboardSummary();
  const overdue = useOverdueInvoices();
  const sendNotices = useSendOverdueNotices();
  const { showToast } = useToast();
  const [hasSentThisSession, setHasSentThisSession] = useState(false);

  async function handleSendNotices() {
    if (!window.confirm(`Send an overdue reminder to all ${overdue.data?.length ?? 0} affected students?`)) return;
    try {
      const result = await sendNotices.mutateAsync();
      showToast(result.message, "success");
      setHasSentThisSession(true);
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <AppLayout title="Fee Dashboard">
      {summary.isLoading && <p className="text-slate text-sm mb-6">Loading revenue summary...</p>}
      {!summary.isLoading && summary.isError && (
        <p role="alert" className="text-brick text-sm mb-6">Couldn't load the revenue summary.</p>
      )}
      {!summary.isLoading && summary.data && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="border border-slate/20 rounded bg-white p-5">
            <p className="text-slate text-xs mb-1">Total Invoiced</p>
            <p className="font-display text-2xl">{summary.data.total_invoiced.toFixed(2)}</p>
          </div>
          <div className="border border-slate/20 rounded bg-white p-5">
            <p className="text-slate text-xs mb-1">Total Collected</p>
            <p className="font-display text-2xl text-field-green">{summary.data.total_collected.toFixed(2)}</p>
          </div>
          <div className="border border-slate/20 rounded bg-white p-5">
            <p className="text-slate text-xs mb-1">Outstanding</p>
            <p className="font-display text-2xl text-brass">{summary.data.total_outstanding.toFixed(2)}</p>
          </div>
          <div className="border border-slate/20 rounded bg-white p-5">
            <p className="text-slate text-xs mb-1">Overdue Invoices</p>
            <p className="font-display text-2xl text-brick">{summary.data.overdue_count}</p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-3">
        <h2 className="font-display text-lg">Overdue Accounts</h2>
        <button
          onClick={handleSendNotices}
          disabled={sendNotices.isPending || (overdue.data?.length ?? 0) === 0}
          className="bg-brick text-white rounded px-4 py-1.5 text-sm font-medium hover:bg-brick/90 transition-colors disabled:opacity-40"
        >
          {sendNotices.isPending ? "Sending..." : "Send Overdue Notices"}
        </button>
      </div>

      {hasSentThisSession && (
        <p className="text-field-green text-xs mb-3">
          Notices sent this session — students will see them in their Notifications panel.
        </p>
      )}

      {overdue.isLoading && <p className="text-slate text-sm">Loading overdue accounts...</p>}
      {!overdue.isLoading && overdue.isError && (
        <p role="alert" className="text-brick text-sm">Couldn't load overdue accounts.</p>
      )}
      {!overdue.isLoading && !overdue.isError && (overdue.data?.length ?? 0) === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No overdue accounts right now.</p>
        </div>
      )}
      {!overdue.isLoading && !overdue.isError && (overdue.data?.length ?? 0) > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Due</th>
                <th>Paid</th>
                <th>Outstanding</th>
                <th>Due Date</th>
              </tr>
            </thead>
            <tbody>
              {overdue.data!.map((inv) => (
                <tr key={inv.id}>
                  <td className="font-medium">{inv.student_name}</td>
                  <td className="font-mono">{inv.amount_due.toFixed(2)}</td>
                  <td className="font-mono">{inv.amount_paid.toFixed(2)}</td>
                  <td className="font-mono text-brick">{inv.outstanding.toFixed(2)}</td>
                  <td className="font-mono text-xs">{inv.due_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}
