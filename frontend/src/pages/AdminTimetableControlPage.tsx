import { useState, type FormEvent } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Modal } from "@/components/Modal";
import { useToast } from "@/contexts/ToastContext";
import {
  useAllSchedule, useAllCourseSections, useCreateSchedule, useUpdateSchedule, useDeleteSchedule, useScheduleConflicts,
} from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { ScheduleItem } from "@/types/api";

const days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

function CreateScheduleForm() {
  const { data: sections } = useAllCourseSections();
  const createSchedule = useCreateSchedule();
  const { showToast } = useToast();
  const [sectionId, setSectionId] = useState("");
  const [dayOfWeek, setDayOfWeek] = useState("sunday");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [room, setRoom] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createSchedule.mutateAsync({
        course_section_id: Number(sectionId), day_of_week: dayOfWeek,
        start_time: startTime, end_time: endTime, room,
      });
      showToast("Class scheduled.", "success");
      setRoom("");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-6">
      <h2 className="font-display text-base mb-3">Schedule a Class</h2>
      <p className="text-slate text-xs mb-3">
        Conflicting room/teacher/time slots are rejected automatically before saving.
      </p>
      <div className="grid sm:grid-cols-3 gap-3 mb-3">
        <div className="sm:col-span-3">
          <label className="block text-sm mb-1 text-slate">Course section</label>
          <select required value={sectionId} onChange={(e) => setSectionId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">Select</option>
            {(sections ?? []).map((s) => (
              <option key={s.id} value={s.id}>{s.course_code} — {s.course_title} ({s.section_name}, {s.semester} {s.academic_year})</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Day</label>
          <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2 capitalize">
            {days.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Start time</label>
          <input required type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">End time</label>
          <input required type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div className="sm:col-span-3">
          <label className="block text-sm mb-1 text-slate">Room</label>
          <input required value={room} onChange={(e) => setRoom(e.target.value)} placeholder="Room-101" className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
      </div>
      <button type="submit" disabled={createSchedule.isPending} className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {createSchedule.isPending ? "Scheduling..." : "+ Schedule class"}
      </button>
    </form>
  );
}

function EditScheduleModal({ entry, onClose }: { entry: ScheduleItem | null; onClose: () => void }) {
  const updateSchedule = useUpdateSchedule(entry?.id ?? 0);
  const { showToast } = useToast();
  const [dayOfWeek, setDayOfWeek] = useState(entry?.day_of_week ?? "sunday");
  const [startTime, setStartTime] = useState(entry?.start_time.slice(0, 5) ?? "");
  const [endTime, setEndTime] = useState(entry?.end_time.slice(0, 5) ?? "");
  const [room, setRoom] = useState(entry?.room ?? "");

  if (!entry) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await updateSchedule.mutateAsync({ day_of_week: dayOfWeek, start_time: startTime, end_time: endTime, room });
      showToast("Schedule entry updated.", "success");
      onClose();
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <Modal title={`Edit ${entry.course_code} schedule`} isOpen={!!entry} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Day</label>
          <select value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2 capitalize">
            {days.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm mb-1 text-slate">Start time</label>
            <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm mb-1 text-slate">End time</label>
            <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
          </div>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Room</label>
          <input value={room} onChange={(e) => setRoom(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <button type="submit" disabled={updateSchedule.isPending} className="w-full bg-ink text-parchment rounded py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50">
          {updateSchedule.isPending ? "Saving..." : "Save changes"}
        </button>
      </form>
    </Modal>
  );
}

export function AdminTimetableControlPage() {
  const { data: entries, isLoading, isError } = useAllSchedule();
  const { data: conflicts } = useScheduleConflicts();
  const deleteSchedule = useDeleteSchedule();
  const { showToast } = useToast();
  const [editingEntry, setEditingEntry] = useState<ScheduleItem | null>(null);

  async function handleDelete(id: number) {
    if (!window.confirm("Remove this class from the schedule?")) return;
    try {
      await deleteSchedule.mutateAsync(id);
      showToast("Removed from schedule.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <AppLayout title="Timetable Control">
      <CreateScheduleForm />

      {conflicts && conflicts.length > 0 && (
        <div className="border border-brick/30 bg-brick/5 rounded p-4 mb-6 text-sm text-brick">
          {conflicts.length} scheduling conflict(s) detected in the existing timetable — review entries below.
        </div>
      )}

      {isLoading && <p className="text-slate text-sm">Loading timetable...</p>}
      {!isLoading && isError && <p role="alert" className="text-brick text-sm">Couldn't load the timetable.</p>}
      {!isLoading && !isError && (entries?.length ?? 0) === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center"><p className="text-slate">No classes scheduled yet.</p></div>
      )}
      {!isLoading && !isError && (entries?.length ?? 0) > 0 && (
        <div className="border border-slate/20 rounded bg-white overflow-hidden">
          <table className="ledger-table">
            <thead><tr><th>Course</th><th>Day</th><th>Time</th><th>Room</th><th>Teacher</th><th></th></tr></thead>
            <tbody>
              {entries!.map((e) => (
                <tr key={e.id}>
                  <td>{e.course_code} — {e.course_title}</td>
                  <td className="capitalize">{e.day_of_week}</td>
                  <td className="font-mono text-xs">{e.start_time.slice(0, 5)}–{e.end_time.slice(0, 5)}</td>
                  <td>{e.room}</td>
                  <td>{e.teacher_name}</td>
                  <td className="space-x-3">
                    <button onClick={() => setEditingEntry(e)} className="text-brass hover:underline text-xs">Edit</button>
                    <button onClick={() => handleDelete(e.id)} className="text-brick hover:underline text-xs">Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <EditScheduleModal entry={editingEntry} onClose={() => setEditingEntry(null)} />
    </AppLayout>
  );
}
