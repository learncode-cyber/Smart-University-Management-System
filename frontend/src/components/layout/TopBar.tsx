import { Menu, Bell, LogOut } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

interface TopBarProps {
  title: string;
  onMenuClick: () => void;
  unreadNotifications?: number; // wired to real data once the Notifications screen's query is shared up
}

export function TopBar({ title, onMenuClick, unreadNotifications = 0 }: TopBarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <header className="flex items-center justify-between px-4 lg:px-8 h-16 border-b border-slate/15 bg-white">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden text-ink"
          aria-label="Open navigation menu"
        >
          <Menu size={22} />
        </button>
        <h1 className="font-display text-lg">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <Link to="/notifications" className="relative text-slate hover:text-ink transition-colors" aria-label="Notifications">
          <Bell size={20} />
          {unreadNotifications > 0 && (
            <span className="absolute -top-1 -right-1 bg-brick text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
              {unreadNotifications > 9 ? "9+" : unreadNotifications}
            </span>
          )}
        </Link>

        <div className="hidden sm:block text-right">
          <p className="text-sm font-medium leading-tight">{user?.email}</p>
          <p className="text-xs text-slate leading-tight capitalize">{user?.role}</p>
        </div>

        <button
          onClick={handleLogout}
          className="text-slate hover:text-brick transition-colors"
          aria-label="Sign out"
          title="Sign out"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}
