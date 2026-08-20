import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Modal } from "@/components/Modal";
import { useToast } from "@/contexts/ToastContext";
import { usePendingResults, useApproveResult } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { PendingResultItem } from "@/types/api";

export function AdminResultApprovalPage() {
  const { data, isLoading, isError } = usePendingResults();
  const approveResult = useApproveResult();
  const { showToast } = useToast();
  const [rejectingResult, setRejectingResult] = useState<PendingResultItem | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");

  const pending = data ?? [];

  async function handleApprove(result: PendingResultItem) {
    try {
      await approveResult.mutateAsync({ resultId: result.id, approved: true });
      showToast(`Approved and published: ${result.student_name} — ${result.course_code}.`, "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  async function handleRejectSubmit() {
    if (!rejectingResult) return;
    try {
      await approveResult.mutateAsync({
        resultId: rejectingResult.id, approved: false, rejectionReason,
      });
      showToast("Result sent back to the teacher with your feedback.", "success");
      setRejectingResult(null);
      setRejectionReason("");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <AppLayout title="Result Approval">
      {isLoading && <p className="text-slate text-sm">Loading pending results...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">Couldn't load pending results.</p>
      )}
      {!isLoading && !isError && pending.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">Nothing pending — all submitted results have been reviewed.</p>
        </div>
      )}

      {!isLoading && !isError && pending.length > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Course</th>
                <th>Marks</th>
                <th>Grade</th>
                <th>Submitted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {pending.map((r) => (
                <tr key={r.id}>
                  <td className="font-medium">{r.student_name}</td>
                  <td>{r.course_code} — {r.course_title}</td>
                  <td className="font-mono">{r.total_marks_obtained} / {r.total_marks_possible}</td>
                  <td className="font-mono">{r.grade_letter}</td>
                  <td className="text-slate text-xs font-mono">
                    {r.submitted_at ? new Date(r.submitted_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="space-x-3">
                    <button
                      onClick={() => handleApprove(r)}
                      disabled={approveResult.isPending}
                      className="text-field-green hover:underline text-xs font-medium"
                    >
                      Approve &amp; Publish
                    </button>
                    <button
                      onClick={() => setRejectingResult(r)}
                      className="text-brick hover:underline text-xs font-medium"
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        title={`Reject result for ${rejectingResult?.student_name ?? ""}`}
        isOpen={!!rejectingResult}
        onClose={() => setRejectingResult(null)}
      >
        <p className="text-slate text-sm mb-3">
          This sends the result back to the teacher as REJECTED, with your reason attached, so they can
          correct and resubmit it.
        </p>
        <label className="block text-sm mb-1 text-slate">Reason for rejection</label>
        <textarea
          value={rejectionReason}
          onChange={(e) => setRejectionReason(e.target.value)}
          rows={4}
          className="w-full border border-slate/30 rounded px-3 py-2 text-sm mb-4"
          placeholder="e.g. Marks don't match the exam submission, please recheck question 4."
        />
        <button
          onClick={handleRejectSubmit}
          disabled={approveResult.isPending || rejectionReason.trim().length === 0}
          className="w-full bg-brick text-white rounded py-2 text-sm font-medium hover:bg-brick/90 transition-colors disabled:opacity-50"
        >
          {approveResult.isPending ? "Sending..." : "Send rejection"}
        </button>
      </Modal>
    </AppLayout>
  );
}
