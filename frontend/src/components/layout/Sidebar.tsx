import { NavLink } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { getNavItemsForRole } from "./navConfig";

interface SidebarProps {
  isOpen: boolean; // controls the off-canvas state on mobile
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth();
  if (!user) return null;
  const items = getNavItemsForRole(user.role);

  return (
    <>
      {/* mobile scrim, click to close */}
      {isOpen && (
        <div className="fixed inset-0 bg-ink/40 z-30 lg:hidden" onClick={onClose} aria-hidden="true" />
      )}

      <aside
        className={
          "fixed lg:static inset-y-0 left-0 z-40 w-64 bg-ink text-parchment flex flex-col transition-transform duration-150 " +
          (isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0")
        }
      >
        <div className="flex items-center gap-3 px-6 py-5 border-b border-parchment/10">
          <div className="w-8 h-8 rounded-full border-2 border-brass flex items-center justify-center font-display text-brass text-sm">
            U
          </div>
          <span className="font-display text-sm leading-tight">University
            <br />Management System</span>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          {items.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                "flex items-center gap-3 px-6 py-2.5 text-sm transition-colors " +
                (isActive
                  ? "bg-brass/15 text-brass border-r-2 border-brass"
                  : "text-parchment/70 hover:text-parchment hover:bg-parchment/5")
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-4 border-t border-parchment/10 text-xs text-parchment/40">
          Signed in as {user.role}
        </div>
      </aside>
    </>
  );
}
