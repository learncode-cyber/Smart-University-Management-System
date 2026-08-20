import { AppLayout } from "@/components/layout/AppLayout";
import { useMySchedule } from "@/lib/queries";
import type { ScheduleItem } from "@/types/api";

const days: ScheduleItem["day_of_week"][] = [
  "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
];

const dayLabel: Record<string, string> = {
  sunday: "Sun", monday: "Mon", tuesday: "Tue", wednesday: "Wed",
  thursday: "Thu", friday: "Fri", saturday: "Sat",
};

function formatTime(t: string): string {
  // backend sends "HH:MM:SS" — trim to "HH:MM"
  return t.slice(0, 5);
}

export function TimetablePage() {
  const { data, isLoading, isError } = useMySchedule();
  const entries = data ?? [];

  const byDay = days.map((day) => ({
    day,
    items: entries
      .filter((e) => e.day_of_week === day)
      .sort((a, b) => a.start_time.localeCompare(b.start_time)),
  }));

  return (
    <AppLayout title="Timetable">
      {isLoading && <p className="text-slate text-sm">Loading timetable...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">
          Couldn't load your timetable. Try refreshing the page.
        </p>
      )}
      {!isLoading && !isError && entries.length === 0 && (
        <div className="border border-slate/20 rounded bg-white p-8 text-center">
          <p className="text-slate">No classes scheduled yet.</p>
        </div>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-7 gap-3">
          {byDay.map(({ day, items }) => (
            <div key={day} className="border border-slate/20 rounded bg-white p-3">
              <h3 className="font-display text-sm mb-2 text-center border-b border-slate/10 pb-2">
                {dayLabel[day]}
              </h3>
              {items.length === 0 ? (
                <p className="text-slate text-xs text-center py-4">—</p>
              ) : (
                <div className="space-y-2">
                  {items.map((item) => (
                    <div key={item.id} className="border border-brass/20 bg-brass/5 rounded p-2">
                      <p className="text-xs font-mono text-brass">
                        {formatTime(item.start_time)}–{formatTime(item.end_time)}
                      </p>
                      <p className="text-sm font-medium leading-tight">{item.course_code}</p>
                      <p className="text-xs text-slate leading-tight">{item.course_title}</p>
                      <p className="text-xs text-slate mt-1">
                        {item.room} · {item.teacher_name}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
