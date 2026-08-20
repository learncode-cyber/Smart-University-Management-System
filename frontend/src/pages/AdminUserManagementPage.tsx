import { useState, type FormEvent } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Modal } from "@/components/Modal";
import { useToast } from "@/contexts/ToastContext";
import {
  useStudents, useTeachers, useDepartments,
  useCreateStudent, useUpdateStudent, useDeactivateStudent,
  useCreateTeacher, useUpdateTeacher,
} from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { StudentItem, TeacherItem } from "@/types/api";

type Tab = "students" | "teachers";

function StudentFormFields({
  departments, values, onChange,
}: {
  departments: { id: number; name: string }[];
  values: Record<string, string>;
  onChange: (field: string, value: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm mb-1 text-slate">Full name</label>
        <input
          required value={values.full_name} onChange={(e) => onChange("full_name", e.target.value)}
          className="w-full border border-slate/30 rounded px-3 py-2"
        />
      </div>
      <div>
        <label className="block text-sm mb-1 text-slate">Email</label>
        <input
          required type="email" value={values.email} onChange={(e) => onChange("email", e.target.value)}
          className="w-full border border-slate/30 rounded px-3 py-2"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Roll number</label>
          <input
            required value={values.roll_number} onChange={(e) => onChange("roll_number", e.target.value)}
            className="w-full border border-slate/30 rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Enrollment year</label>
          <input
            required type="number" value={values.enrollment_year}
            onChange={(e) => onChange("enrollment_year", e.target.value)}
            className="w-full border border-slate/30 rounded px-3 py-2"
          />
        </div>
      </div>
      <div>
        <label className="block text-sm mb-1 text-slate">Department</label>
        <select
          required value={values.department_id} onChange={(e) => onChange("department_id", e.target.value)}
          className="w-full border border-slate/30 rounded px-3 py-2"
        >
          <option value="">Select a department</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>
      {values.initial_password !== undefined && (
        <div>
          <label className="block text-sm mb-1 text-slate">Initial password</label>
          <input
            required type="text" minLength={8} value={values.initial_password}
            onChange={(e) => onChange("initial_password", e.target.value)}
            className="w-full border border-slate/30 rounded px-3 py-2 font-mono text-sm"
          />
          <p className="text-xs text-slate mt-1">Share this with the student — they can change it after first login.</p>
        </div>
      )}
    </div>
  );
}

function CreateStudentModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { data: departments } = useDepartments();
  const createStudent = useCreateStudent();
  const { showToast } = useToast();
  const [values, setValues] = useState({
    full_name: "", email: "", roll_number: "", enrollment_year: "", department_id: "", initial_password: "",
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createStudent.mutateAsync({
        email: values.email, initial_password: values.initial_password,
        department_id: Number(values.department_id), roll_number: values.roll_number,
        full_name: values.full_name, enrollment_year: Number(values.enrollment_year),
      });
      showToast("Student account created.", "success");
      onClose();
      setValues({ full_name: "", email: "", roll_number: "", enrollment_year: "", department_id: "", initial_password: "" });
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <Modal title="Create Student Account" isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <StudentFormFields
          departments={departments ?? []}
          values={values}
          onChange={(field, value) => setValues((prev) => ({ ...prev, [field]: value }))}
        />
        <button
          type="submit" disabled={createStudent.isPending}
          className="w-full bg-ink text-parchment rounded py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
        >
          {createStudent.isPending ? "Creating..." : "Create account"}
        </button>
      </form>
    </Modal>
  );
}

function EditStudentModal({ student, onClose }: { student: StudentItem | null; onClose: () => void }) {
  const { data: departments } = useDepartments();
  const updateStudent = useUpdateStudent(student?.id ?? 0);
  const { showToast } = useToast();
  const [fullName, setFullName] = useState(student?.full_name ?? "");
  const [departmentId, setDepartmentId] = useState(String(student?.department_id ?? ""));
  const [phone, setPhone] = useState(student?.phone ?? "");

  if (!student) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await updateStudent.mutateAsync({ full_name: fullName, department_id: Number(departmentId), phone });
      showToast("Student updated.", "success");
      onClose();
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <Modal title={`Edit ${student.full_name}`} isOpen={!!student} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Full name</label>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Department</label>
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            {(departments ?? []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Phone</label>
          <input value={phone ?? ""} onChange={(e) => setPhone(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <button type="submit" disabled={updateStudent.isPending} className="w-full bg-ink text-parchment rounded py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50">
          {updateStudent.isPending ? "Saving..." : "Save changes"}
        </button>
      </form>
    </Modal>
  );
}

function CreateTeacherModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { data: departments } = useDepartments();
  const createTeacher = useCreateTeacher();
  const { showToast } = useToast();
  const [values, setValues] = useState({
    full_name: "", email: "", employee_id: "", department_id: "", designation: "", initial_password: "",
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createTeacher.mutateAsync({
        email: values.email, initial_password: values.initial_password,
        department_id: Number(values.department_id), employee_id: values.employee_id,
        full_name: values.full_name, designation: values.designation,
      });
      showToast("Teacher account created.", "success");
      onClose();
      setValues({ full_name: "", email: "", employee_id: "", department_id: "", designation: "", initial_password: "" });
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <Modal title="Create Teacher Account" isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Full name</label>
          <input required value={values.full_name} onChange={(e) => setValues((p) => ({ ...p, full_name: e.target.value }))} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Email</label>
          <input required type="email" value={values.email} onChange={(e) => setValues((p) => ({ ...p, email: e.target.value }))} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Employee ID</label>
          <input required value={values.employee_id} onChange={(e) => setValues((p) => ({ ...p, employee_id: e.target.value }))} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Designation</label>
          <input value={values.designation} onChange={(e) => setValues((p) => ({ ...p, designation: e.target.value }))} placeholder="e.g. Lecturer" className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Department</label>
          <select required value={values.department_id} onChange={(e) => setValues((p) => ({ ...p, department_id: e.target.value }))} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">Select a department</option>
            {(departments ?? []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Initial password</label>
          <input required minLength={8} value={values.initial_password} onChange={(e) => setValues((p) => ({ ...p, initial_password: e.target.value }))} className="w-full border border-slate/30 rounded px-3 py-2 font-mono text-sm" />
        </div>
        <button type="submit" disabled={createTeacher.isPending} className="w-full bg-ink text-parchment rounded py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50">
          {createTeacher.isPending ? "Creating..." : "Create account"}
        </button>
      </form>
    </Modal>
  );
}

function EditTeacherModal({ teacher, onClose }: { teacher: TeacherItem | null; onClose: () => void }) {
  const { data: departments } = useDepartments();
  const updateTeacher = useUpdateTeacher(teacher?.id ?? 0);
  const { showToast } = useToast();
  const [fullName, setFullName] = useState(teacher?.full_name ?? "");
  const [departmentId, setDepartmentId] = useState(String(teacher?.department_id ?? ""));
  const [designation, setDesignation] = useState(teacher?.designation ?? "");

  if (!teacher) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await updateTeacher.mutateAsync({ full_name: fullName, department_id: Number(departmentId), designation });
      showToast("Teacher updated.", "success");
      onClose();
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <Modal title={`Edit ${teacher.full_name}`} isOpen={!!teacher} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Full name</label>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Designation</label>
          <input value={designation ?? ""} onChange={(e) => setDesignation(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Department</label>
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            {(departments ?? []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <button type="submit" disabled={updateTeacher.isPending} className="w-full bg-ink text-parchment rounded py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50">
          {updateTeacher.isPending ? "Saving..." : "Save changes"}
        </button>
      </form>
    </Modal>
  );
}

export function AdminUserManagementPage() {
  const [tab, setTab] = useState<Tab>("students");
  const [search, setSearch] = useState("");
  const [isCreateOpen, setCreateOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<StudentItem | null>(null);
  const [editingTeacher, setEditingTeacher] = useState<TeacherItem | null>(null);

  const { showToast } = useToast();
  const students = useStudents();
  const teachers = useTeachers();
  const deactivateStudent = useDeactivateStudent();

  const filteredStudents = (students.data ?? []).filter((s) =>
    (s.full_name + s.email + s.roll_number).toLowerCase().includes(search.toLowerCase())
  );
  const filteredTeachers = (teachers.data ?? []).filter((t) =>
    (t.full_name + t.email + t.employee_id).toLowerCase().includes(search.toLowerCase())
  );

  async function handleDeactivate(student: StudentItem) {
    if (!window.confirm(`Deactivate ${student.full_name}'s account? They will no longer be able to log in.`)) return;
    try {
      await deactivateStudent.mutateAsync(student.id);
      showToast("Student account deactivated.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  const isLoading = tab === "students" ? students.isLoading : teachers.isLoading;
  const isError = tab === "students" ? students.isError : teachers.isError;

  return (
    <AppLayout title="User Management">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex gap-1 border border-slate/20 rounded p-1 w-fit bg-white">
          {(["students", "teachers"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={"px-4 py-1.5 rounded text-sm capitalize transition-colors " + (tab === t ? "bg-ink text-parchment" : "text-slate hover:text-ink")}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            placeholder="Search by name, email, ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-slate/30 rounded px-3 py-1.5 text-sm w-64"
          />
          <button
            onClick={() => setCreateOpen(true)}
            className="bg-brass text-white rounded px-4 py-1.5 text-sm font-medium hover:bg-brass/90 transition-colors"
          >
            + New {tab === "students" ? "Student" : "Teacher"}
          </button>
        </div>
      </div>

      {isLoading && <p className="text-slate text-sm">Loading...</p>}
      {!isLoading && isError && <p role="alert" className="text-brick text-sm">Couldn't load {tab}.</p>}

      {!isLoading && !isError && tab === "students" && (
        filteredStudents.length === 0 ? (
          <div className="border border-slate/20 rounded bg-white p-8 text-center"><p className="text-slate">No students found.</p></div>
        ) : (
          <div className="border border-slate/20 rounded bg-white overflow-hidden">
            <table className="ledger-table">
              <thead><tr><th>Name</th><th>Roll</th><th>Email</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {filteredStudents.map((s) => (
                  <tr key={s.id}>
                    <td className="font-medium">{s.full_name}</td>
                    <td className="font-mono text-xs">{s.roll_number}</td>
                    <td className="text-slate">{s.email}</td>
                    <td>
                      <span className={"status-pill " + (s.is_active ? "status-pill--success" : "status-pill--danger")}>
                        {s.is_active ? "active" : "deactivated"}
                      </span>
                    </td>
                    <td className="space-x-3">
                      <button onClick={() => setEditingStudent(s)} className="text-brass hover:underline text-xs">Edit</button>
                      {s.is_active && (
                        <button onClick={() => handleDeactivate(s)} className="text-brick hover:underline text-xs">Deactivate</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {!isLoading && !isError && tab === "teachers" && (
        filteredTeachers.length === 0 ? (
          <div className="border border-slate/20 rounded bg-white p-8 text-center"><p className="text-slate">No teachers found.</p></div>
        ) : (
          <div className="border border-slate/20 rounded bg-white overflow-hidden">
            <table className="ledger-table">
              <thead><tr><th>Name</th><th>Employee ID</th><th>Designation</th><th>Email</th><th></th></tr></thead>
              <tbody>
                {filteredTeachers.map((t) => (
                  <tr key={t.id}>
                    <td className="font-medium">{t.full_name}</td>
                    <td className="font-mono text-xs">{t.employee_id}</td>
                    <td className="text-slate">{t.designation ?? "—"}</td>
                    <td className="text-slate">{t.email}</td>
                    <td>
                      <button onClick={() => setEditingTeacher(t)} className="text-brass hover:underline text-xs">Edit</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {tab === "students" ? (
        <CreateStudentModal isOpen={isCreateOpen} onClose={() => setCreateOpen(false)} />
      ) : (
        <CreateTeacherModal isOpen={isCreateOpen} onClose={() => setCreateOpen(false)} />
      )}
      <EditStudentModal student={editingStudent} onClose={() => setEditingStudent(null)} />
      <EditTeacherModal teacher={editingTeacher} onClose={() => setEditingTeacher(null)} />
    </AppLayout>
  );
}
