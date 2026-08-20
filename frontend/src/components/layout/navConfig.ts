import {
  LayoutDashboard, FileText, BarChart3, CalendarCheck, Wallet, CalendarDays,
  UserCircle, Bell, Users, ClipboardCheck, PenSquare, ListChecks, BookOpen,
  type LucideIcon,
} from "lucide-react";
import type { UserRole } from "@/types/api";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
}

const commonBottom: NavItem[] = [
  { label: "Notifications", path: "/notifications", icon: Bell },
  { label: "Profile", path: "/profile", icon: UserCircle },
];

const navByRole: Record<UserRole, NavItem[]> = {
  student: [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Exams", path: "/exams", icon: FileText },
    { label: "Results", path: "/results", icon: BarChart3 },
    { label: "Attendance", path: "/attendance", icon: CalendarCheck },
    { label: "Fees", path: "/fees", icon: Wallet },
    { label: "Timetable", path: "/timetable", icon: CalendarDays },
    ...commonBottom,
  ],
  teacher: [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Exam Builder", path: "/teacher/exam-builder", icon: PenSquare },
    { label: "Grading", path: "/teacher/grading", icon: ListChecks },
    { label: "Attendance Marker", path: "/teacher/attendance", icon: CalendarCheck },
    { label: "Timetable", path: "/timetable", icon: CalendarDays },
    ...commonBottom,
  ],
  admin: [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "User Management", path: "/admin/users", icon: Users },
    { label: "Academic Structure", path: "/admin/academic", icon: BookOpen },
    { label: "Result Approval", path: "/admin/results", icon: ClipboardCheck },
    { label: "Fee Dashboard", path: "/admin/fees", icon: Wallet },
    { label: "Timetable Control", path: "/admin/timetable", icon: CalendarDays },
    { label: "Attendance Reports", path: "/admin/attendance-reports", icon: CalendarCheck },
    ...commonBottom,
  ],
  parent: [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Attendance", path: "/attendance", icon: CalendarCheck },
    { label: "Results", path: "/results", icon: BarChart3 },
    { label: "Fees", path: "/fees", icon: Wallet },
    ...commonBottom,
  ],
};

export function getNavItemsForRole(role: UserRole): NavItem[] {
  return navByRole[role];
}
