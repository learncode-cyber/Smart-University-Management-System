import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { extractApiErrorMessage } from "@/lib/apiClient";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFieldError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      const message = extractApiErrorMessage(err);
      setFieldError(message);
      showToast(message, "error");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-parchment">
      {/* Brand panel — hidden on mobile, the "seal" signature lives here */}
      <div className="hidden lg:flex lg:w-5/12 bg-ink text-parchment flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-brass flex items-center justify-center font-display text-brass text-lg">
            U
          </div>
          <span className="font-display text-lg tracking-wide">University Management System</span>
        </div>
        <div>
          <p className="font-display text-3xl leading-snug mb-4">
            One record.
            <br />
            Every role.
            <br />
            No spreadsheets.
          </p>
          <p className="text-parchment/60 text-sm max-w-sm">
            Attendance, exams, results, and fees — in one place for students, teachers,
            admins, and parents alike.
          </p>
        </div>
        <p className="text-parchment/40 text-xs">ICT Bangladesh · AI-Powered Software Engineering</p>
      </div>

      {/* Login card */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <form onSubmit={handleSubmit} className="w-full max-w-sm" noValidate>
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-full border-2 border-brass flex items-center justify-center font-display text-brass text-sm">
              U
            </div>
            <span className="font-display">University Management System</span>
          </div>

          <h1 className="font-display text-2xl mb-1">Sign in</h1>
          <p className="text-slate text-sm mb-8">Use the email and password issued by your university.</p>

          {fieldError && (
            <div role="alert" className="mb-4 rounded border border-brick/30 bg-brick/5 px-3 py-2 text-sm text-brick">
              {fieldError}
            </div>
          )}

          <label htmlFor="email" className="block text-sm mb-1 text-slate">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-slate/30 rounded px-3 py-2 mb-4 bg-white focus:border-brass transition-colors"
          />

          <label htmlFor="password" className="block text-sm mb-1 text-slate">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-slate/30 rounded px-3 py-2 mb-6 bg-white focus:border-brass transition-colors"
          />

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-ink text-parchment rounded py-2.5 font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-slate text-xs mt-6">
            Forgot your password, or don't have an account yet? Contact your university's
            admin office — accounts are issued centrally, not self-registered.
          </p>
        </form>
      </div>
    </div>
  );
}
