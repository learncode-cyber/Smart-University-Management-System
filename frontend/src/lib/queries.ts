import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./apiClient";
import type {
  ExamListItem, ExamDetailStudentResponse, ExamAnswerSubmit, ExamSubmissionResponse,
  MyAttendanceResponse, MyResultsResponse, MyFeeStatusResponse, InvoiceItem, PaymentItem, CurrentUser,
  ScheduleItem, DepartmentItem, StudentItem, TeacherItem, PendingResultItem, FeeDashboardSummary,
  CourseSectionItem, ExamCreatePayload, ExamDetailTeacherResponse, EnrolledStudent, AttendanceRecordItem,
  NotificationItem, CourseItem,
} from "@/types/api";

interface StudentListItem { id: number }
interface TeacherListItem { id: number }

/**
 * Thin React Query wrappers, one per "my ..." endpoint used across
 * dashboard/screens. Kept in one file so query keys stay consistent —
 * e.g. invalidating ["exams"] after a teacher creates an exam refreshes
 * every screen that reads it, without hunting through multiple files.
 */

export function useExams() {
  return useQuery({
    queryKey: ["exams"],
    queryFn: async () => (await apiClient.get<ExamListItem[]>("/exams")).data,
  });
}

export function useExamDetail(examId: number) {
  return useQuery({
    queryKey: ["exams", examId],
    queryFn: async () => (await apiClient.get<ExamDetailStudentResponse>(`/exams/${examId}`)).data,
    enabled: Number.isFinite(examId),
  });
}

export function useSubmitExam(examId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (answers: ExamAnswerSubmit[]) =>
      (await apiClient.post<ExamSubmissionResponse>(`/exams/${examId}/submit`, { answers })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useMyAttendance(courseSectionId?: number) {
  return useQuery({
    queryKey: ["attendance", "me", courseSectionId ?? "summary"],
    queryFn: async () =>
      (
        await apiClient.get<MyAttendanceResponse>("/attendance/me", {
          params: courseSectionId ? { course_section_id: courseSectionId } : undefined,
        })
      ).data,
  });
}

export function useMyResults() {
  return useQuery({
    queryKey: ["results", "me"],
    queryFn: async () => (await apiClient.get<MyResultsResponse>("/results/me")).data,
  });
}

export function useMyFeeStatus() {
  return useQuery({
    queryKey: ["fees", "me"],
    queryFn: async () => (await apiClient.get<MyFeeStatusResponse>("/fees/me")).data,
  });
}

export function usePaymentHistory(studentId: number) {
  return useQuery({
    queryKey: ["fees", "payments", studentId],
    queryFn: async () => (await apiClient.get<PaymentItem[]>(`/fees/payments/${studentId}`)).data,
    enabled: Number.isFinite(studentId),
  });
}

export async function downloadInvoice(invoiceId: number): Promise<void> {
  const response = await apiClient.get(`/fees/invoices/${invoiceId}`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `invoice_${invoiceId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function useMySchedule() {
  return useQuery({
    queryKey: ["schedule", "me"],
    queryFn: async () => (await apiClient.get<ScheduleItem[]>("/schedule/me")).data,
  });
}

// ---- Admin: Timetable Control ----

export function useAllSchedule() {
  return useQuery({
    queryKey: ["admin", "schedule"],
    queryFn: async () => (await apiClient.get<ScheduleItem[]>("/schedule")).data,
  });
}

export interface ScheduleCreatePayload {
  course_section_id: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  room: string;
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScheduleCreatePayload) =>
      (await apiClient.post<ScheduleItem>("/schedule", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["schedule"] }),
  });
}

export function useDeleteSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (scheduleId: number) => (await apiClient.delete(`/schedule/${scheduleId}`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["schedule"] }),
  });
}

export interface ScheduleUpdatePayload {
  day_of_week?: string;
  start_time?: string;
  end_time?: string;
  room?: string;
}

export function useUpdateSchedule(scheduleId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScheduleUpdatePayload) =>
      (await apiClient.put<ScheduleItem>(`/schedule/${scheduleId}`, payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["schedule"] }),
  });
}

export interface ScheduleConflictItem {
  slot_a_id: number | null;
  slot_b_id: number | null;
  reason: string;
}

export function useScheduleConflicts() {
  return useQuery({
    queryKey: ["schedule", "conflicts"],
    queryFn: async () => (await apiClient.get<ScheduleConflictItem[]>("/schedule/conflicts")).data,
  });
}

// ---- Admin: Attendance Reports ----

export interface AttendanceReportRow {
  student_id: number;
  student_name: string;
  course_section_id: number;
  total_classes: number;
  present_count: number;
  percentage: number;
  is_below_threshold: boolean;
}

export function useAttendanceReports(courseSectionId?: number) {
  return useQuery({
    queryKey: ["admin", "attendance-reports", courseSectionId ?? "all"],
    queryFn: async () =>
      (
        await apiClient.get<AttendanceReportRow[]>("/attendance/reports", {
          params: courseSectionId ? { course_section_id: courseSectionId } : undefined,
        })
      ).data,
  });
}

// ---- Admin: User Management ----

export function useDepartments() {
  return useQuery({
    queryKey: ["academic", "departments"],
    queryFn: async () => (await apiClient.get<DepartmentItem[]>("/academic/departments")).data,
  });
}

export function useStudents() {
  return useQuery({
    queryKey: ["admin", "students"],
    queryFn: async () => (await apiClient.get<StudentItem[]>("/users/students", { params: { limit: 500 } })).data,
  });
}

export function useTeachers() {
  return useQuery({
    queryKey: ["admin", "teachers"],
    queryFn: async () => (await apiClient.get<TeacherItem[]>("/users/teachers", { params: { limit: 500 } })).data,
  });
}

export interface StudentCreatePayload {
  email: string;
  initial_password: string;
  department_id: number;
  roll_number: string;
  full_name: string;
  enrollment_year: number;
  phone?: string;
  address?: string;
  current_semester?: string;
}

export function useCreateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: StudentCreatePayload) =>
      (await apiClient.post<StudentItem>("/users/students", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "students"] }),
  });
}

export interface StudentUpdatePayload {
  department_id?: number;
  full_name?: string;
  phone?: string;
  address?: string;
  current_semester?: string;
}

export function useUpdateStudent(studentId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: StudentUpdatePayload) =>
      (await apiClient.put<StudentItem>(`/users/students/${studentId}`, payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "students"] }),
  });
}

export function useDeactivateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (studentId: number) =>
      (await apiClient.delete(`/users/students/${studentId}`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "students"] }),
  });
}

export interface TeacherCreatePayload {
  email: string;
  initial_password: string;
  department_id: number;
  employee_id: string;
  full_name: string;
  designation?: string;
  phone?: string;
}

export function useCreateTeacher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TeacherCreatePayload) =>
      (await apiClient.post<TeacherItem>("/users/teachers", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "teachers"] }),
  });
}

export interface TeacherUpdatePayload {
  department_id?: number;
  full_name?: string;
  designation?: string;
  phone?: string;
}

export function useUpdateTeacher(teacherId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TeacherUpdatePayload) =>
      (await apiClient.put<TeacherItem>(`/users/teachers/${teacherId}`, payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "teachers"] }),
  });
}

// ---- Admin: Result Approval ----

export function usePendingResults() {
  return useQuery({
    queryKey: ["admin", "pending-results"],
    queryFn: async () => (await apiClient.get<PendingResultItem[]>("/results/pending")).data,
  });
}

export function useApproveResult() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ resultId, approved, rejectionReason }: { resultId: number; approved: boolean; rejectionReason?: string }) =>
      (await apiClient.post(`/results/${resultId}/approve`, { approved, rejection_reason: rejectionReason })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "pending-results"] }),
  });
}

// ---- Admin dashboard counts ----
// NOTE: these fetch full lists just to read .length — fine at the scale
// of a single university's records, but if a university grows into the
// tens of thousands of students this should become a dedicated
// COUNT-only backend endpoint instead. Flagged rather than optimized
// prematurely.

export function useStudentCount() {
  return useQuery({
    queryKey: ["admin", "student-count"],
    queryFn: async () => (await apiClient.get<StudentListItem[]>("/users/students", { params: { limit: 1000 } })).data.length,
  });
}

export function useTeacherCount() {
  return useQuery({
    queryKey: ["admin", "teacher-count"],
    queryFn: async () => (await apiClient.get<TeacherListItem[]>("/users/teachers", { params: { limit: 1000 } })).data.length,
  });
}

export async function downloadTranscript(studentId: number): Promise<void> {
  const response = await apiClient.get(`/results/${studentId}/transcript`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `transcript_${studentId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function useOverdueInvoices() {
  return useQuery({
    queryKey: ["admin", "overdue-invoices"],
    queryFn: async () => (await apiClient.get<InvoiceItem[]>("/fees/overdue")).data,
  });
}

export function useFeeDashboardSummary() {
  return useQuery({
    queryKey: ["admin", "fee-dashboard-summary"],
    queryFn: async () => (await apiClient.get<FeeDashboardSummary>("/fees/dashboard-summary")).data,
  });
}

export function useSendOverdueNotices() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await apiClient.post<{ message: string }>("/fees/overdue/send-notices")).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin"] }),
  });
}

export interface FeeStructureCreatePayload {
  department_id?: number | null;
  fee_type: string;
  semester: string;
  academic_year: string;
  amount: number;
  due_date: string;
}

export function useCreateFeeStructure() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: FeeStructureCreatePayload) =>
      (await apiClient.post<{ invoices_generated: number }>("/fees", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "fee-dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "overdue-invoices"] });
      queryClient.invalidateQueries({ queryKey: ["fees"] });
    },
  });
}

export interface PaymentRecordPayload {
  invoice_id: number;
  amount: number;
  method: string;
  transaction_ref?: string;
}

export function useRecordPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PaymentRecordPayload) =>
      (await apiClient.post<PaymentItem>("/fees/payments", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "fee-dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "overdue-invoices"] });
      queryClient.invalidateQueries({ queryKey: ["fees"] });
    },
  });
}

// ---- Teacher: Exam Builder ----

export function useMyCourseSections() {
  return useQuery({
    queryKey: ["academic", "my-course-sections"],
    queryFn: async () => (await apiClient.get<CourseSectionItem[]>("/academic/course-sections")).data,
  });
}

export function useExamDetailForTeacher(examId: number) {
  return useQuery({
    queryKey: ["exams", examId, "teacher-view"],
    queryFn: async () => (await apiClient.get<ExamDetailTeacherResponse>(`/exams/${examId}`)).data,
    enabled: Number.isFinite(examId) && examId > 0,
  });
}

export function useCreateExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ExamCreatePayload) =>
      (await apiClient.post<ExamDetailTeacherResponse>("/exams", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams"] }),
  });
}

export function useUpdateExam(examId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<ExamCreatePayload>) =>
      (await apiClient.put<ExamDetailTeacherResponse>(`/exams/${examId}`, payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams"] }),
  });
}

export function useDeleteExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (examId: number) => (await apiClient.delete(`/exams/${examId}`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams"] }),
  });
}

export function useExamResults(examId: number) {
  return useQuery({
    queryKey: ["exams", examId, "results"],
    queryFn: async () => (await apiClient.get<{ exam_id: number; submissions: ExamSubmissionResponse[] }>(`/exams/${examId}/results`)).data,
    enabled: Number.isFinite(examId) && examId > 0,
  });
}

export interface GradeSubmissionPayload {
  student_id: number;
  grades: { question_id: number; score: number; feedback?: string }[];
}

export function useGradeSubmission(examId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: GradeSubmissionPayload) =>
      (await apiClient.post<ExamSubmissionResponse>(`/exams/${examId}/grade`, payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams", examId, "results"] }),
  });
}

export interface SubmitResultPayload {
  student_id: number;
}

export function useSubmitResultForApproval(examId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SubmitResultPayload) =>
      (await apiClient.post(`/results/${examId}/submit`, payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exams", examId, "results"] }),
  });
}

// ---- Teacher: Attendance Marker ----

export function useEnrolledStudents(sectionId: number) {
  return useQuery({
    queryKey: ["academic", "roster", sectionId],
    queryFn: async () => (await apiClient.get<EnrolledStudent[]>(`/academic/course-sections/${sectionId}/students`)).data,
    enabled: Number.isFinite(sectionId) && sectionId > 0,
  });
}

export function useClassAttendance(sectionId: number, date: string) {
  return useQuery({
    queryKey: ["attendance", "class", sectionId, date],
    queryFn: async () =>
      (await apiClient.get<AttendanceRecordItem[]>(`/attendance/${sectionId}`, { params: { date_from: date, date_to: date } })).data,
    enabled: Number.isFinite(sectionId) && sectionId > 0 && !!date,
  });
}

export interface BulkMarkPayload {
  course_section_id: number;
  date: string;
  entries: { student_id: number; status: string }[];
}

export function useBulkMarkAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: BulkMarkPayload) =>
      (await apiClient.post<AttendanceRecordItem[]>("/attendance", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["attendance"] }),
  });
}

export function useCorrectAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ recordId, status, reason }: { recordId: number; status: string; reason: string }) =>
      (await apiClient.put<AttendanceRecordItem>(`/attendance/${recordId}`, { status, correction_reason: reason })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["attendance"] }),
  });
}

// ---- Notifications ----

export function useMyNotifications() {
  return useQuery({
    queryKey: ["notifications", "me"],
    queryFn: async () => (await apiClient.get<NotificationItem[]>("/notifications/me")).data,
    refetchInterval: 60_000, // light polling so the bell badge stays reasonably fresh without a websocket
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: async () => (await apiClient.get<{ unread_count: number }>("/notifications/me/unread-count")).data.unread_count,
    refetchInterval: 60_000,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId: number) =>
      (await apiClient.put<NotificationItem>(`/notifications/${notificationId}/read`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await apiClient.post<{ message: string }>("/notifications/read-all")).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

// ---- Admin: Academic Structure ----

export function useCreateDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name: string; code: string }) =>
      (await apiClient.post<DepartmentItem>("/academic/departments", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["academic", "departments"] }),
  });
}

export function useCourses() {
  return useQuery({
    queryKey: ["academic", "courses"],
    queryFn: async () => (await apiClient.get<CourseItem[]>("/academic/courses")).data,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { department_id: number; code: string; title: string; credit_hours: number }) =>
      (await apiClient.post<CourseItem>("/academic/courses", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["academic", "courses"] }),
  });
}

export function useAllCourseSections() {
  return useQuery({
    queryKey: ["academic", "all-course-sections"],
    queryFn: async () => (await apiClient.get<CourseSectionItem[]>("/academic/course-sections")).data,
  });
}

export function useCreateCourseSection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { course_id: number; teacher_id: number; section_name: string; semester: string; academic_year: string }) =>
      (await apiClient.post<CourseSectionItem>("/academic/course-sections", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["academic", "all-course-sections"] });
      queryClient.invalidateQueries({ queryKey: ["academic", "my-course-sections"] });
    },
  });
}

export function useCreateEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { student_id: number; course_section_id: number }) =>
      (await apiClient.post("/academic/enrollments", payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["academic"] }),
  });
}

// ---- Profile ----

export interface ProfileUpdatePayload {
  email?: string;
  full_name?: string;
  phone?: string;
  address?: string;
  profile_photo_url?: string;
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ProfileUpdatePayload) =>
      (await apiClient.put<CurrentUser>("/users/me", payload)).data,
    onSuccess: (data) => {
      // update the cached "me" value so the topbar/sidebar reflect
      // changes immediately without a full refetch
      queryClient.setQueryData(["users", "me"], data);
    },
  });
}

export interface PasswordChangePayload {
  current_password: string;
  new_password: string;
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (payload: PasswordChangePayload) =>
      (await apiClient.put<{ message: string }>("/auth/password", payload)).data,
  });
}
