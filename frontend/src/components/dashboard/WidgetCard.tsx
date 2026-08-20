import type { ReactNode } from "react";

interface WidgetCardProps {
  title: string;
  isLoading: boolean;
  isError: boolean;
  isEmpty?: boolean;
  emptyMessage?: string;
  errorMessage?: string;
  children: ReactNode;
}

/**
 * Every dashboard widget renders through this so loading/error/empty
 * states are handled identically everywhere (Part 0's "no blank white
 * screens on failure" standard) instead of each widget reinventing it.
 */
export function WidgetCard({
  title, isLoading, isError, isEmpty, emptyMessage = "Nothing to show yet.",
  errorMessage = "Couldn't load this. Try refreshing the page.", children,
}: WidgetCardProps) {
  return (
    <div className="border border-slate/20 rounded bg-white p-5">
      <h2 className="font-display text-base mb-3">{title}</h2>
      {isLoading && <p className="text-slate text-sm">Loading...</p>}
      {!isLoading && isError && (
        <p role="alert" className="text-brick text-sm">
          {errorMessage}
        </p>
      )}
      {!isLoading && !isError && isEmpty && <p className="text-slate text-sm">{emptyMessage}</p>}
      {!isLoading && !isError && !isEmpty && children}
    </div>
  );
}
