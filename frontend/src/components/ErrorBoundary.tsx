import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * Catches render-time errors anywhere below it in the tree so a bug in
 * one screen shows a recoverable message instead of a blank white page
 * (the "no blank white screens on failure" standard from Part 0).
 * This does NOT catch errors inside async event handlers or API calls —
 * those are handled per-screen via React Query's error state.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Unhandled UI error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-parchment px-4">
          <div className="max-w-md text-center">
            <h1 className="font-display text-2xl mb-2">Something went wrong</h1>
            <p className="text-slate mb-6">
              This screen ran into an unexpected problem. Reloading usually fixes it.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-ink text-parchment rounded hover:bg-ink/90 transition-colors"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
