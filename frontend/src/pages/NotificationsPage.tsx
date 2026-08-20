import { useToast } from "@/contexts/ToastContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { useMyNotifications, useMarkNotificationRead, useMarkAllNotificationsRead } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";
import type { NotificationItem } from "@/types/api";

const typeIcon: Record<NotificationItem["type"], string> = {
  exam_published: "📝",
  result_published: "📊",
  attendance_warning: "⚠️",
  fee_due: "💰",
  fee_overdue: "🔴",
  schedule_change: "🗓️",
  general: "🔔",
};

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function NotificationsPage() {
  const { data, isLoading, isError } = useMyNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();
  const { showToast } = useToast();

  const notifications = data ?? [];
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function handleMarkAllRead() {
    try {
      const result = await markAllRead.mutateAsync();
      showToast(result.message, "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  async function handleClick(notification: NotificationItem) {
    if (!notification.is_read) {
      try {
        await markRead.mutateAsync(notification.id);
      } catch (err) {
        showToast(extractApiErrorMessage(err), "error");
      }
    }
  }

  return (
    <AppLayout title="Notifications">
      <div className="flex items-center justify-between mb-4">
        <p className="text-slate text-sm">{unreadCount} unread</p>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            disabled={markAllRead.isPending}
            className="text-brass text-sm hover:underline"
          >
            Mark all as read
          </button>
        )}
      </div>

      {isLoading && <p className="text-slate text-sm">Loading notifications...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">Couldn't load notifications.</p>
      )}
      {!isLoading && !isError && notifications.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No notifications yet.</p>
        </div>
      )}

      {!isLoading && !isError && notifications.length > 0 && (
        <div className="border border-slate/20 rounded bg-white divide-y divide-slate/10 overflow-hidden">
          {notifications.map((n) => (
            <button
              key={n.id}
              onClick={() => handleClick(n)}
              className={
                "w-full text-left flex gap-3 px-5 py-4 transition-colors hover:bg-parchment/60 " +
                (n.is_read ? "" : "bg-brass/5")
              }
            >
              <span className="text-lg leading-none mt-0.5">{typeIcon[n.type] ?? "🔔"}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className={"text-sm " + (n.is_read ? "text-ink" : "font-medium text-ink")}>{n.title}</p>
                  <span className="text-slate text-xs font-mono whitespace-nowrap">{timeAgo(n.created_at)}</span>
                </div>
                <p className="text-slate text-sm mt-0.5">{n.message}</p>
              </div>
              {!n.is_read && <span className="w-2 h-2 rounded-full bg-brass mt-2 flex-shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
