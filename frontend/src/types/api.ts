/**
 * Mirrors app/core/errors.py's standardized response shape exactly —
 * every error from the API has this shape, so the frontend can switch on
 * `code` (e.g. redirect to /login on TOKEN_EXPIRED) without parsing
 * free-text messages.
 */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
  };
}

export type UserRole = "student" | "teacher" | "admin" | "parent";

export interface CurrentUser {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  full_name?: string | null;
  phone?: string | null;
  address?: string | null;
  profile_photo_url?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export type ExamStatus = "draft" | "scheduled" | "open" | "closed" | "grading_done" | "published";

export interface ExamListItem {
  id: number;
  course_section_id: number;
  title: string;
  status: ExamStatus;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  total_marks: number;
}

export interface ExamOptionStudentView {
  id: number;
  option_text: string;
}

export interface ExamQuestionStudentView {
  id: number;
  question_type: "mcq" | "short_answer" | "descriptive" | "coding";
  question_text: string;
  marks: number;
  order_index: number;
  starter_code: string | null;
  options: ExamOptionStudentView[];
}

export interface ExamDetailStudentResponse extends ExamListItem {
  description: string | null;
  questions: ExamQuestionStudentView[];
}

export interface ExamAnswerSubmit {
  question_id: number;
  selected_option_id?: number | null;
  answer_text?: string | null;
}

export interface ExamAnswerResponse {
  question_id: number;
  selected_option_id: number | null;
  answer_text: string | null;
  score: number | null;
  feedback: string | null;
}

export interface ExamSubmissionResponse {
  id: number;
  exam_id: number;
  student_id: number;
  student_name: string;
  status: "in_progress" | "submitted" | "graded";
  started_at: string;
  submitted_at: string | null;
  total_score: number | null;
  answers: ExamAnswerResponse[];
}

export interface CourseSectionAttendanceSummary {
  course_section_id: number;
  total_classes: number;
  present_count: number;
  percentage: number;
  is_below_threshold: boolean;
}

export interface AttendanceRecordItem {
  id: number;
  course_section_id: number;
  student_id: number;
  date: string;
  status: "present" | "absent" | "late" | "excused";
  marked_by_teacher_id: number;
  corrected_by_teacher_id: number | null;
  corrected_at: string | null;
  correction_reason: string | null;
}

export interface StudentAttendanceStatus {
  student_id: number;
  student_name: string;
  summaries: CourseSectionAttendanceSummary[];
  records: AttendanceRecordItem[];
}

export interface MyAttendanceResponse {
  students: StudentAttendanceStatus[];
}

export type ResultStatus = "draft" | "submitted" | "approved" | "published" | "rejected";

export interface ResultItem {
  id: number;
  student_id: number;
  course_section_id: number;
  course_code: string;
  course_title: string;
  semester: string;
  academic_year: string;
  total_marks_obtained: number;
  total_marks_possible: number;
  grade_letter: string | null;
  grade_point: number | null;
  status: ResultStatus;
  submitted_at: string | null;
  approved_at: string | null;
  published_at: string | null;
  rejection_reason: string | null;
}

export interface PendingResultItem extends ResultItem {
  student_name: string;
}

export interface StudentResultsStatus {
  student_id: number;
  student_name: string;
  results: ResultItem[];
  cumulative_gpa: number | null;
}

export interface MyResultsResponse {
  students: StudentResultsStatus[];
}

export type InvoiceStatus = "pending" | "partial" | "paid" | "overdue" | "waived";

export interface InvoiceItem {
  id: number;
  student_id: number;
  student_name: string;
  fee_structure_id: number;
  amount_due: number;
  amount_paid: number;
  outstanding: number;
  status: InvoiceStatus;
  due_date: string;
  issued_at: string;
}

export interface PaymentItem {
  id: number;
  invoice_id: number;
  amount: number;
  method: "cash" | "bank_transfer" | "mobile_banking" | "card" | "other";
  transaction_ref: string | null;
  paid_at: string;
}

export interface CourseItem {
  id: number;
  department_id: number;
  code: string;
  title: string;
  credit_hours: number;
}

export interface DepartmentItem {
  id: number;
  name: string;
  code: string;
}

export interface StudentItem {
  id: number;
  user_id: number;
  email: string;
  is_active: boolean;
  department_id: number;
  roll_number: string;
  full_name: string;
  date_of_birth: string | null;
  phone: string | null;
  address: string | null;
  enrollment_year: number;
  current_semester: string | null;
}

export interface TeacherItem {
  id: number;
  user_id: number;
  email: string;
  is_active: boolean;
  department_id: number;
  employee_id: string;
  full_name: string;
  designation: string | null;
  phone: string | null;
  joined_at: string | null;
}

export interface ScheduleItem {
  id: number;
  course_section_id: number;
  course_code: string;
  course_title: string;
  teacher_id: number;
  teacher_name: string;
  day_of_week: "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday";
  start_time: string;
  end_time: string;
  room: string;
}

export interface ExamOptionCreate {
  option_text: string;
  is_correct: boolean;
}

export interface ExamQuestionCreate {
  question_type: "mcq" | "short_answer" | "descriptive" | "coding";
  question_text: string;
  marks: number;
  order_index: number;
  starter_code?: string | null;
  expected_output?: string | null;
  options: ExamOptionCreate[];
}

export interface ExamCreatePayload {
  course_section_id: number;
  title: string;
  description?: string | null;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  questions: ExamQuestionCreate[];
}

export interface ExamOptionTeacherView {
  id: number;
  option_text: string;
  is_correct: boolean;
}

export interface ExamQuestionTeacherView {
  id: number;
  question_type: "mcq" | "short_answer" | "descriptive" | "coding";
  question_text: string;
  marks: number;
  order_index: number;
  starter_code: string | null;
  expected_output: string | null;
  options: ExamOptionTeacherView[];
}

export interface ExamDetailTeacherResponse extends ExamListItem {
  description: string | null;
  questions: ExamQuestionTeacherView[];
}

export interface NotificationItem {
  id: number;
  type: "exam_published" | "result_published" | "attendance_warning" | "fee_due" | "fee_overdue" | "schedule_change" | "general";
  title: string;
  message: string;
  is_read: boolean;
  related_entity_type: string | null;
  related_entity_id: number | null;
  created_at: string;
}

export interface EnrolledStudent {
  student_id: number;
  full_name: string;
  roll_number: string;
}

export interface CourseSectionItem {
  id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  teacher_id: number;
  section_name: string;
  semester: string;
  academic_year: string;
}

export interface FeeDashboardSummary {
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
  invoice_count: number;
  overdue_count: number;
}

export interface StudentFeeStatus {
  student_id: number;
  student_name: string;
  invoices: InvoiceItem[];
  total_due: number;
  total_paid: number;
  total_outstanding: number;
}

export interface MyFeeStatusResponse {
  students: StudentFeeStatus[];
}
