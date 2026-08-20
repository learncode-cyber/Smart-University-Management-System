import { useState, type ReactNode } from "react";
import { useUnreadNotificationCount } from "@/lib/queries";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface AppLayoutProps {
  title: string;
  children: ReactNode;
}

/**
 * Every protected screen (Part 10 onward) renders inside this shell:
 *   <AppLayout title="Exams"><ExamsPage content/></AppLayout>
 * Keeps the sidebar/topbar/responsive-collapse logic in exactly one
 * place instead of re-implemented per screen.
 */
export function AppLayout({ title, children }: AppLayoutProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const { data: unreadCount } = useUnreadNotificationCount();

  return (
    <div className="min-h-screen flex bg-parchment">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar title={title} onMenuClick={() => setSidebarOpen(true)} unreadNotifications={unreadCount ?? 0} />
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
