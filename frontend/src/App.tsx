import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import { ToastProvider } from "@/contexts/ToastContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { ExamListPage } from "@/pages/ExamListPage";
import { ExamRoomPage } from "@/pages/ExamRoomPage";
import { ResultsPage } from "@/pages/ResultsPage";
import { AttendancePage } from "@/pages/AttendancePage";
import { FeeCentrePage } from "@/pages/FeeCentrePage";
import { TimetablePage } from "@/pages/TimetablePage";
import { AdminUserManagementPage } from "@/pages/AdminUserManagementPage";
import { AdminResultApprovalPage } from "@/pages/AdminResultApprovalPage";
import { AdminFeeDashboardPage } from "@/pages/AdminFeeDashboardPage";
import { TeacherExamBuilderPage } from "@/pages/TeacherExamBuilderPage";
import { TeacherGradingPage } from "@/pages/TeacherGradingPage";
import { TeacherAttendanceMarkerPage } from "@/pages/TeacherAttendanceMarkerPage";
import { NotificationsPage } from "@/pages/NotificationsPage";
import { AdminAcademicStructurePage } from "@/pages/AdminAcademicStructurePage";
import { AdminTimetableControlPage } from "@/pages/AdminTimetableControlPage";
import { AdminAttendanceReportsPage } from "@/pages/AdminAttendanceReportsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <DashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <ProfilePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/exams"
                  element={
                    <ProtectedRoute allowedRoles={["student", "teacher", "admin"]}>
                      <ExamListPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/exams/:examId"
                  element={
                    <ProtectedRoute allowedRoles={["student"]}>
                      <ExamRoomPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/results"
                  element={
                    <ProtectedRoute allowedRoles={["student", "parent"]}>
                      <ResultsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/attendance"
                  element={
                    <ProtectedRoute allowedRoles={["student", "parent"]}>
                      <AttendancePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/fees"
                  element={
                    <ProtectedRoute allowedRoles={["student", "parent"]}>
                      <FeeCentrePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/timetable"
                  element={
                    <ProtectedRoute allowedRoles={["student", "teacher", "parent"]}>
                      <TimetablePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/users"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <AdminUserManagementPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/results"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <AdminResultApprovalPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/fees"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <AdminFeeDashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/teacher/exam-builder"
                  element={
                    <ProtectedRoute allowedRoles={["teacher"]}>
                      <TeacherExamBuilderPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/teacher/grading"
                  element={
                    <ProtectedRoute allowedRoles={["teacher"]}>
                      <TeacherGradingPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/teacher/attendance"
                  element={
                    <ProtectedRoute allowedRoles={["teacher"]}>
                      <TeacherAttendanceMarkerPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notifications"
                  element={
                    <ProtectedRoute>
                      <NotificationsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/academic"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <AdminAcademicStructurePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/timetable"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <AdminTimetableControlPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/attendance-reports"
                  element={
                    <ProtectedRoute allowedRoles={["admin"]}>
                      <AdminAttendanceReportsPage />
                    </ProtectedRoute>
                  }
                />
                {/* Part 10 adds one Route per screen here, each wrapped in
                    <ProtectedRoute allowedRoles={[...]}> as appropriate */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
