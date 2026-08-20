import { useEffect, useState, type FormEvent } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { useUpdateProfile, useChangePassword } from "@/lib/queries";
import { extractApiErrorMessage } from "@/lib/apiClient";

export function ProfilePage() {
  const { user, setUser } = useAuth();
  const { showToast } = useToast();
  const updateProfile = useUpdateProfile();
  const changePassword = useChangePassword();

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // seed the form once the user is available (session-restore may still
  // be loading on first render)
  useEffect(() => {
    if (user) {
      setEmail(user.email);
      setFullName(user.full_name ?? "");
      setPhone(user.phone ?? "");
      setAddress(user.address ?? "");
    }
  }, [user]);

  if (!user) {
    return (
      <AppLayout title="Profile">
        <p className="text-slate text-sm">Loading...</p>
      </AppLayout>
    );
  }

  async function handleProfileSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const updated = await updateProfile.mutateAsync({
        email, full_name: fullName, phone, address,
      });
      setUser(updated);
      showToast("Profile updated.", "success");
    } catch (err) {
      showToast(extractApiErrorMessage(err), "error");
    }
  }

  async function handlePasswordSubmit(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation don't match.");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }
    try {
      await changePassword.mutateAsync({ current_password: currentPassword, new_password: newPassword });
      showToast("Password changed. Other devices have been signed out.", "success");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordError(extractApiErrorMessage(err));
    }
  }

  return (
    <AppLayout title="Profile">
      <div className="max-w-2xl space-y-6">
        {/* Personal information */}
        <form onSubmit={handleProfileSubmit} className="border border-slate/20 rounded bg-white p-6">
          <h2 className="font-display text-lg mb-1">Personal Information</h2>
          <p className="text-slate text-sm mb-5">
            Roll number, department, and employee ID are managed by your university's admin office
            and can't be changed here.
          </p>

          <div className="grid sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm mb-1 text-slate">Full name</label>
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">Phone</label>
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
              />
            </div>
            {user.role === "student" && (
              <div>
                <label className="block text-sm mb-1 text-slate">Address</label>
                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={updateProfile.isPending}
            className="bg-ink text-parchment rounded px-4 py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {updateProfile.isPending ? "Saving..." : "Save changes"}
          </button>
        </form>

        {/* Password change */}
        <form onSubmit={handlePasswordSubmit} className="border border-slate/20 rounded bg-white p-6">
          <h2 className="font-display text-lg mb-1">Change Password</h2>
          <p className="text-slate text-sm mb-5">
            Changing your password signs you out of every other device.
          </p>

          {passwordError && (
            <div role="alert" className="mb-4 rounded border border-brick/30 bg-brick/5 px-3 py-2 text-sm text-brick">
              {passwordError}
            </div>
          )}

          <div className="space-y-4 mb-4 max-w-sm">
            <div>
              <label className="block text-sm mb-1 text-slate">Current password</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">New password</label>
              <input
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate">Confirm new password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full border border-slate/30 rounded px-3 py-2 focus:border-brass transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={changePassword.isPending}
            className="bg-ink text-parchment rounded px-4 py-2 text-sm font-medium hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {changePassword.isPending ? "Changing..." : "Change password"}
          </button>
        </form>
      </div>
    </AppLayout>
  );
}
