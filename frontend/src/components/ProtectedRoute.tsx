import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { UserRole } from "@/types/api";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[]; // omit to allow any authenticated role
}

/**
 * Wraps a route element:
 * - while session-restore is in progress -> shows a loading state (never
 *   a flash-redirect to /login before we actually know if there's a
 *   valid session)
 * - not logged in -> redirect to /login
 * - logged in but wrong role for this route -> redirect to /dashboard
 *   (their own role-appropriate home), NOT a raw 403 page
 * - logged in with an allowed role -> render the route
 */
export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-parchment">
        <p className="text-slate">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
