import { useAuth } from "@/contexts/AuthContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { UpcomingExamsWidget } from "@/components/dashboard/UpcomingExamsWidget";
import { AttendanceWidget } from "@/components/dashboard/AttendanceWidget";
import { FeeStatusWidget } from "@/components/dashboard/FeeStatusWidget";
import { RecentResultsWidget } from "@/components/dashboard/RecentResultsWidget";
import { AdminStatsWidget } from "@/components/dashboard/AdminStatsWidget";
import { TeacherExamsWidget } from "@/components/dashboard/TeacherExamsWidget";

/**
 * Widget selection per role — matches the proposal's Section 7 dashboard
 * description ("role-specific home screen with summary widgets") and
 * respects the same RBAC boundaries as the API: e.g. Teacher/Admin never
 * render AttendanceWidget/FeeStatusWidget since /attendance/me and
 * /fees/me are Student/Parent-only endpoints (would 403 if called).
 */
export function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <AppLayout title="Dashboard">
      <div className="mb-6">
        <p className="text-slate text-sm">
          Welcome back, <span className="text-ink font-medium">{user.email}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {user.role === "student" && (
          <>
            <UpcomingExamsWidget />
            <AttendanceWidget />
            <RecentResultsWidget />
            <FeeStatusWidget />
          </>
        )}

        {user.role === "teacher" && (
          <>
            <TeacherExamsWidget />
          </>
        )}

        {user.role === "admin" && (
          <div className="md:col-span-2">
            <AdminStatsWidget />
          </div>
        )}

        {user.role === "parent" && (
          <>
            <AttendanceWidget />
            <RecentResultsWidget />
            <FeeStatusWidget />
          </>
        )}
      </div>
    </AppLayout>
  );
}
