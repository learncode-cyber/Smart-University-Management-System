import { useState, type FormEvent } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useToast } from "@/contexts/ToastContext";
import {
  useDepartments, useCreateDepartment, useCourses, useCreateCourse,
  useAllCourseSections, useCreateCourseSection, useCreateEnrollment,
  useTeachers, useStudents,
} from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";

type Tab = "departments" | "courses" | "sections" | "enrollments";

function DepartmentForm() {
  const createDepartment = useCreateDepartment();
  const { showToast } = useToast();
  const [name, setName] = useState("");
  const [code, setCode] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createDepartment.mutateAsync({ name, code });
      showToast("Department created.", "success");
      setName(""); setCode("");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-4 flex gap-3 items-end">
      <div className="flex-1">
        <label className="block text-sm mb-1 text-slate">Department name</label>
        <input required value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" placeholder="Computer Science & Engineering" />
      </div>
      <div className="w-32">
        <label className="block text-sm mb-1 text-slate">Code</label>
        <input required value={code} onChange={(e) => setCode(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" placeholder="CSE" />
      </div>
      <button type="submit" disabled={createDepartment.isPending} className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {createDepartment.isPending ? "Adding..." : "+ Add"}
      </button>
    </form>
  );
}

function CourseForm() {
  const { data: departments } = useDepartments();
  const createCourse = useCreateCourse();
  const { showToast } = useToast();
  const [departmentId, setDepartmentId] = useState("");
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [creditHours, setCreditHours] = useState(3);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createCourse.mutateAsync({ department_id: Number(departmentId), code, title, credit_hours: creditHours });
      showToast("Course created.", "success");
      setCode(""); setTitle("");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-4">
      <div className="grid sm:grid-cols-4 gap-3 items-end">
        <div>
          <label className="block text-sm mb-1 text-slate">Department</label>
          <select required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">Select</option>
            {(departments ?? []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Course code</label>
          <input required value={code} onChange={(e) => setCode(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" placeholder="CSE301" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Title</label>
          <input required value={title} onChange={(e) => setTitle(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" placeholder="Database Systems" />
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Credits</label>
          <input required type="number" min={1} max={6} value={creditHours} onChange={(e) => setCreditHours(Number(e.target.value))} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
      </div>
      <button type="submit" disabled={createCourse.isPending} className="mt-3 bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {createCourse.isPending ? "Adding..." : "+ Add course"}
      </button>
    </form>
  );
}

function CourseSectionForm() {
  const { data: courses } = useCourses();
  const { data: teachers } = useTeachers();
  const createSection = useCreateCourseSection();
  const { showToast } = useToast();
  const [courseId, setCourseId] = useState("");
  const [teacherId, setTeacherId] = useState("");
  const [sectionName, setSectionName] = useState("A");
  const [semester, setSemester] = useState("Spring");
  const [academicYear, setAcademicYear] = useState("2026-2027");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createSection.mutateAsync({
        course_id: Number(courseId), teacher_id: Number(teacherId),
        section_name: sectionName, semester, academic_year: academicYear,
      });
      showToast("Course section created.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-4">
      <div className="grid sm:grid-cols-3 gap-3 items-end mb-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Course</label>
          <select required value={courseId} onChange={(e) => setCourseId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">Select</option>
            {(courses ?? []).map((c) => <option key={c.id} value={c.id}>{c.code} — {c.title}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Teacher</label>
          <select required value={teacherId} onChange={(e) => setTeacherId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option value="">Select</option>
            {(teachers ?? []).map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Section name</label>
          <input value={sectionName} onChange={(e) => setSectionName(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" />
        </div>
      </div>
      <div className="grid sm:grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-sm mb-1 text-slate">Semester</label>
          <select value={semester} onChange={(e) => setSemester(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
            <option>Spring</option><option>Summer</option><option>Fall</option>
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1 text-slate">Academic year</label>
          <input value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2" placeholder="2026-2027" />
        </div>
      </div>
      <button type="submit" disabled={createSection.isPending} className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {createSection.isPending ? "Adding..." : "+ Add course section"}
      </button>
    </form>
  );
}

function EnrollmentForm() {
  const { data: students } = useStudents();
  const { data: sections } = useAllCourseSections();
  const createEnrollment = useCreateEnrollment();
  const { showToast } = useToast();
  const [studentId, setStudentId] = useState("");
  const [sectionId, setSectionId] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await createEnrollment.mutateAsync({ student_id: Number(studentId), course_section_id: Number(sectionId) });
      showToast("Student enrolled.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-slate/20 rounded bg-white p-5 mb-4 grid sm:grid-cols-3 gap-3 items-end">
      <div>
        <label className="block text-sm mb-1 text-slate">Student</label>
        <select required value={studentId} onChange={(e) => setStudentId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
          <option value="">Select</option>
          {(students ?? []).map((s) => <option key={s.id} value={s.id}>{s.roll_number} — {s.full_name}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-sm mb-1 text-slate">Course section</label>
        <select required value={sectionId} onChange={(e) => setSectionId(e.target.value)} className="w-full border border-slate/30 rounded px-3 py-2">
          <option value="">Select</option>
          {(sections ?? []).map((s) => <option key={s.id} value={s.id}>{s.course_code} ({s.section_name}, {s.semester} {s.academic_year})</option>)}
        </select>
      </div>
      <button type="submit" disabled={createEnrollment.isPending} className="bg-brass text-white rounded px-4 py-2 text-sm font-medium hover:bg-brass/90 transition-colors disabled:opacity-50">
        {createEnrollment.isPending ? "Enrolling..." : "+ Enroll student"}
      </button>
    </form>
  );
}

export function AdminAcademicStructurePage() {
  const [tab, setTab] = useState<Tab>("departments");
  const { data: departments } = useDepartments();
  const { data: courses } = useCourses();
  const { data: sections } = useAllCourseSections();

  const tabs: { key: Tab; label: string }[] = [
    { key: "departments", label: "Departments" },
    { key: "courses", label: "Courses" },
    { key: "sections", label: "Course Sections" },
    { key: "enrollments", label: "Enrollments" },
  ];

  return (
    <AppLayout title="Academic Structure">
      <p className="text-slate text-sm mb-4">
        Set up departments, courses, course sections, and student enrollments — the foundation
        exams, attendance, results, and schedules all build on.
      </p>

      <div className="flex gap-1 border border-slate/20 rounded p-1 w-fit bg-white mb-4">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={"px-4 py-1.5 rounded text-sm transition-colors " + (tab === t.key ? "bg-ink text-parchment" : "text-slate hover:text-ink")}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "departments" && (
        <>
          <DepartmentForm />
          <div className="border border-slate/20 rounded bg-white overflow-hidden">
            <table className="ledger-table">
              <thead><tr><th>Name</th><th>Code</th></tr></thead>
              <tbody>{(departments ?? []).map((d) => <tr key={d.id}><td>{d.name}</td><td className="font-mono">{d.code}</td></tr>)}</tbody>
            </table>
          </div>
        </>
      )}

      {tab === "courses" && (
        <>
          <CourseForm />
          <div className="border border-slate/20 rounded bg-white overflow-hidden">
            <table className="ledger-table">
              <thead><tr><th>Code</th><th>Title</th><th>Credits</th></tr></thead>
              <tbody>{(courses ?? []).map((c) => <tr key={c.id}><td className="font-mono">{c.code}</td><td>{c.title}</td><td>{c.credit_hours}</td></tr>)}</tbody>
            </table>
          </div>
        </>
      )}

      {tab === "sections" && (
        <>
          <CourseSectionForm />
          <div className="border border-slate/20 rounded bg-white overflow-hidden">
            <table className="ledger-table">
              <thead><tr><th>Course</th><th>Section</th><th>Semester</th></tr></thead>
              <tbody>{(sections ?? []).map((s) => <tr key={s.id}><td>{s.course_code} — {s.course_title}</td><td>{s.section_name}</td><td>{s.semester} {s.academic_year}</td></tr>)}</tbody>
            </table>
          </div>
        </>
      )}

      {tab === "enrollments" && <EnrollmentForm />}
    </AppLayout>
  );
}
